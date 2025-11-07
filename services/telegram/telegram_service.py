"""
Telegram service orchestrator for Telegram API operations.
"""

import logging
import asyncio
from typing import Optional, Callable, List, Tuple
from datetime import datetime

try:
    from pyrogram import Client
    from pyrogram.types import Message as PyrogramMessage
    from pyrogram.errors import FloodWait
    PYROGRAM_AVAILABLE = True
except ImportError:
    PYROGRAM_AVAILABLE = False
    logging.warning("Pyrogram not installed")

from database.db_manager import DatabaseManager
from database.models import TelegramCredential, TelegramGroup, Message
from config.settings import settings
from services.telegram.client_manager import ClientManager
from services.telegram.user_processor import UserProcessor
from services.telegram.message_processor import MessageProcessor
from services.telegram.reaction_processor import ReactionProcessor
from services.telegram.group_manager import GroupManager

logger = logging.getLogger(__name__)


class TelegramService:
    """Orchestrates Telegram API operations using Pyrogram."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.client_manager = ClientManager()
        self.user_processor = UserProcessor(db_manager)
        self.message_processor = MessageProcessor()
        self._reaction_processor: Optional[ReactionProcessor] = None
        self._group_manager: Optional[GroupManager] = None
    
    @property
    def client(self) -> Optional[Client]:
        """Get current client instance."""
        return self.client_manager.get_client()
    
    @property
    def is_available(self) -> bool:
        """Check if Pyrogram is available."""
        return self.client_manager.is_available
    
    def create_client(self, phone: str, api_id: str, api_hash: str) -> Optional[Client]:
        """Create Pyrogram client."""
        return self.client_manager.create_client(phone, api_id, api_hash)
    
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
        success, error, client = await self.client_manager.start_session(
            phone, api_id, api_hash, code_callback, password_callback
        )
        
        if success and client:
            # Save credential
            from pathlib import Path
            session_file_path = Path(client.workdir) / client.name
            credential = TelegramCredential(
                phone_number=phone,
                session_string=str(session_file_path),
                is_default=True
            )
            self.db_manager.save_telegram_credential(credential)
        
        return success, error
    
    async def load_session(
        self,
        credential: TelegramCredential
    ) -> Tuple[bool, Optional[str]]:
        """Load existing Telegram session."""
        if not settings.has_telegram_credentials:
            return False, "Telegram API credentials not configured"
        
        success, error, client = await self.client_manager.load_session(
            credential,
            settings.telegram_api_id,
            settings.telegram_api_hash
        )
        
        return success, error
    
    async def disconnect(self):
        """Disconnect Telegram client."""
        await self.client_manager.disconnect()
        self._reaction_processor = None
        self._group_manager = None
    
    def is_connected(self) -> bool:
        """Check if Telegram client is connected and authorized."""
        return self.client_manager.is_connected()
    
    async def is_authorized(self) -> bool:
        """Check if Telegram client is authorized (async check)."""
        return await self.client_manager.is_authorized()
    
    async def auto_load_session(self) -> Tuple[bool, Optional[str]]:
        """
        Automatically load the default Telegram session if available.
        Returns (success, error_message)
        """
        try:
            credential = self.db_manager.get_default_credential()
            if not credential:
                return False, "No saved Telegram session found"
            
            return await self.load_session(credential)
        except Exception as e:
            logger.error(f"Error auto-loading session: {e}")
            return False, str(e)
    
    async def fetch_group_info(
        self,
        group_id: int
    ) -> Tuple[bool, Optional[TelegramGroup], Optional[str]]:
        """
        Fetch group information.
        Returns (success, group, error_message)
        """
        if not self._group_manager:
            self._group_manager = GroupManager(self.db_manager, self.client)
        
        return await self._group_manager.fetch_group_info(group_id)
    
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
            
            # Initialize managers
            if not self._group_manager:
                self._group_manager = GroupManager(self.db_manager, self.client)
            if not self._reaction_processor:
                self._reaction_processor = ReactionProcessor(
                    self.db_manager,
                    self.client,
                    self.user_processor
                )
            
            # Get group info
            success, group, error = await self._group_manager.fetch_group_info(group_id)
            if not success:
                return False, 0, error
            
            # Save group
            self._group_manager.save_group(group)
            
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
                        await self.user_processor.process_user(telegram_msg.from_user)
                    
                    # Process message
                    message = await self.message_processor.process_message(
                        telegram_msg,
                        group_id,
                        group.group_username
                    )
                    
                    if message:
                        self.db_manager.save_message(message)
                        message_count += 1
                        
                        # Process reactions if enabled
                        if settings.settings.track_reactions:
                            await self._reaction_processor.process_reactions(
                                telegram_msg,
                                group_id,
                                group.group_username,
                                message.message_link
                            )
                        
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
            total_messages = self.db_manager.get_message_count(group_id)
            self._group_manager.update_group_stats(group, total_messages)
            
            logger.info(f"Fetched {message_count} messages from group {group_id}")
            return True, message_count, None
            
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return False, 0, str(e)

