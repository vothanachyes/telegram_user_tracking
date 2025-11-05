"""
Telegram service using Pyrogram for fetching messages and managing sessions.
"""

import logging
import asyncio
from typing import Optional, Callable, List, Tuple
from datetime import datetime
from pathlib import Path
import time

try:
    from pyrogram import Client
    from pyrogram.types import Message as PyrogramMessage
    from pyrogram.errors import FloodWait, BadRequest, Unauthorized
    PYROGRAM_AVAILABLE = True
except ImportError:
    PYROGRAM_AVAILABLE = False
    logging.warning("Pyrogram not installed")

from database.db_manager import DatabaseManager
from database.models import TelegramCredential, TelegramGroup, TelegramUser, Message
from config.settings import settings
from utils.helpers import get_telegram_message_link
from utils.validators import sanitize_username

logger = logging.getLogger(__name__)


class TelegramService:
    """Handles Telegram API operations using Pyrogram."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.client: Optional[Client] = None
        self.is_available = PYROGRAM_AVAILABLE
        self._session_path = Path("./data/sessions")
        self._session_path.mkdir(parents=True, exist_ok=True)
    
    def create_client(self, phone: str, api_id: str, api_hash: str) -> Optional[Client]:
        """Create Pyrogram client."""
        if not self.is_available:
            logger.error("Pyrogram is not available")
            return None
        
        try:
            session_name = f"session_{phone.replace('+', '')}"
            session_file = self._session_path / session_name
            
            client = Client(
                name=str(session_file),
                api_id=int(api_id),
                api_hash=api_hash,
                phone_number=phone,
                workdir=str(self._session_path)
            )
            
            return client
        except Exception as e:
            logger.error(f"Error creating Telegram client: {e}")
            return None
    
    async def start_session(
        self, 
        phone: str, 
        api_id: str, 
        api_hash: str,
        code_callback: Optional[Callable[[], str]] = None,
        password_callback: Optional[Callable[[], str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Start Telegram session with OTP flow.
        Returns (success, error_message)
        """
        try:
            client = self.create_client(phone, api_id, api_hash)
            if not client:
                return False, "Failed to create Telegram client"
            
            await client.connect()
            
            # Check if already authorized
            if await client.is_authorized():
                self.client = client
                logger.info(f"Already authorized for {phone}")
                return True, None
            
            # Send code
            sent_code = await client.send_code(phone)
            
            # Get code from user
            if code_callback:
                code = code_callback()
                if not code:
                    await client.disconnect()
                    return False, "Code not provided"
            else:
                await client.disconnect()
                return False, "Code callback not provided"
            
            # Sign in with code
            try:
                await client.sign_in(phone, sent_code.phone_code_hash, code)
            except Exception as e:
                # Check if 2FA is required
                if "password" in str(e).lower():
                    if password_callback:
                        password = password_callback()
                        if not password:
                            await client.disconnect()
                            return False, "Password not provided"
                        
                        await client.check_password(password)
                    else:
                        await client.disconnect()
                        return False, "Two-factor password required but callback not provided"
                else:
                    raise
            
            self.client = client
            
            # Save credential
            credential = TelegramCredential(
                phone_number=phone,
                session_string=str(client.workdir / client.name),
                is_default=True
            )
            self.db_manager.save_telegram_credential(credential)
            
            logger.info(f"Successfully authorized {phone}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            if self.client:
                await self.client.disconnect()
            return False, str(e)
    
    async def load_session(self, credential: TelegramCredential) -> Tuple[bool, Optional[str]]:
        """Load existing Telegram session."""
        try:
            if not settings.has_telegram_credentials:
                return False, "Telegram API credentials not configured"
            
            client = self.create_client(
                credential.phone_number,
                settings.telegram_api_id,
                settings.telegram_api_hash
            )
            
            if not client:
                return False, "Failed to create Telegram client"
            
            await client.connect()
            
            if not await client.is_authorized():
                await client.disconnect()
                return False, "Session expired or invalid"
            
            self.client = client
            logger.info(f"Session loaded for {credential.phone_number}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return False, str(e)
    
    async def disconnect(self):
        """Disconnect Telegram client."""
        if self.client:
            await self.client.disconnect()
            self.client = None
    
    async def fetch_group_info(self, group_id: int) -> Tuple[bool, Optional[TelegramGroup], Optional[str]]:
        """
        Fetch group information.
        Returns (success, group, error_message)
        """
        try:
            if not self.client:
                return False, None, "Not connected to Telegram"
            
            chat = await self.client.get_chat(group_id)
            
            group = TelegramGroup(
                group_id=chat.id,
                group_name=chat.title or "Unknown Group",
                group_username=chat.username
            )
            
            return True, group, None
            
        except Exception as e:
            logger.error(f"Error fetching group info: {e}")
            return False, None, str(e)
    
    async def fetch_messages(
        self,
        group_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        message_callback: Optional[Callable[[Message], None]] = None
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Fetch messages from a group.
        Returns (success, message_count, error_message)
        """
        try:
            if not self.client:
                return False, 0, "Not connected to Telegram"
            
            # Get group info
            success, group, error = await self.fetch_group_info(group_id)
            if not success:
                return False, 0, error
            
            # Save group
            self.db_manager.save_group(group)
            
            message_count = 0
            fetch_delay = settings.settings.fetch_delay_seconds
            
            # Fetch messages
            async for telegram_msg in self.client.get_chat_history(group_id):
                try:
                    # Check date range
                    if start_date and telegram_msg.date < start_date:
                        break  # Messages are in reverse chronological order
                    
                    if end_date and telegram_msg.date > end_date:
                        continue
                    
                    # Check if message is deleted
                    if self.db_manager.is_message_deleted(telegram_msg.id, group_id):
                        continue
                    
                    # Process user
                    if telegram_msg.from_user:
                        await self._process_user(telegram_msg.from_user)
                    
                    # Process message
                    message = await self._process_message(telegram_msg, group_id, group.group_username)
                    
                    if message:
                        self.db_manager.save_message(message)
                        message_count += 1
                        
                        if message_callback:
                            message_callback(message)
                        
                        if progress_callback:
                            progress_callback(message_count, -1)  # -1 for unknown total
                    
                    # Rate limiting
                    if fetch_delay > 0:
                        await asyncio.sleep(fetch_delay)
                    
                except FloodWait as e:
                    logger.warning(f"FloodWait: waiting {e.value} seconds")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    logger.error(f"Error processing message {telegram_msg.id}: {e}")
                    continue
            
            # Update group stats
            group.last_fetch_date = datetime.now()
            group.total_messages = self.db_manager.get_message_count(group_id)
            self.db_manager.save_group(group)
            
            logger.info(f"Fetched {message_count} messages from group {group_id}")
            return True, message_count, None
            
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return False, 0, str(e)
    
    async def _process_user(self, telegram_user) -> Optional[TelegramUser]:
        """Process and save Telegram user."""
        try:
            # Build full name
            full_name = telegram_user.first_name or ""
            if telegram_user.last_name:
                full_name += f" {telegram_user.last_name}"
            full_name = full_name.strip() or "Unknown User"
            
            user = TelegramUser(
                user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                full_name=full_name,
                phone=telegram_user.phone_number if hasattr(telegram_user, 'phone_number') else None
            )
            
            # Check if user is soft deleted
            existing = self.db_manager.get_user_by_id(telegram_user.id)
            if existing and existing.is_deleted:
                return None  # Skip deleted users
            
            self.db_manager.save_user(user)
            return user
            
        except Exception as e:
            logger.error(f"Error processing user: {e}")
            return None
    
    async def _process_message(
        self, 
        telegram_msg: 'PyrogramMessage', 
        group_id: int,
        group_username: Optional[str]
    ) -> Optional[Message]:
        """Process Telegram message."""
        try:
            if not telegram_msg.from_user:
                return None
            
            # Determine media type
            has_media = False
            media_type = None
            media_count = 0
            
            if telegram_msg.photo:
                has_media = True
                media_type = "photo"
                media_count = 1
            elif telegram_msg.video:
                has_media = True
                media_type = "video"
                media_count = 1
            elif telegram_msg.document:
                has_media = True
                media_type = "document"
                media_count = 1
            elif telegram_msg.audio or telegram_msg.voice:
                has_media = True
                media_type = "audio"
                media_count = 1
            elif telegram_msg.media_group_id:
                # TODO: Handle media groups
                has_media = True
                media_type = "media_group"
            
            # Get message content
            content = telegram_msg.text or telegram_msg.caption or ""
            
            # Generate message link
            message_link = get_telegram_message_link(group_username, group_id, telegram_msg.id)
            
            message = Message(
                message_id=telegram_msg.id,
                group_id=group_id,
                user_id=telegram_msg.from_user.id,
                content=content,
                caption=telegram_msg.caption,
                date_sent=telegram_msg.date,
                has_media=has_media,
                media_type=media_type,
                media_count=media_count,
                message_link=message_link
            )
            
            return message
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return None

