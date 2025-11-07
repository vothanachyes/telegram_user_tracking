"""
Telegram service using Pyrogram for fetching messages and managing sessions.
"""

import logging
import asyncio
import re
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
from database.models import TelegramCredential, TelegramGroup, TelegramUser, Message, Reaction
from config.settings import settings
from utils.helpers import get_telegram_message_link
from utils.validators import sanitize_username
from utils.constants import BASE_DIR

logger = logging.getLogger(__name__)

# URL pattern for detecting links in messages
URL_PATTERN = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)


class TelegramService:
    """Handles Telegram API operations using Pyrogram."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.client: Optional[Client] = None
        self.is_available = PYROGRAM_AVAILABLE
        self._session_path = BASE_DIR / "data" / "sessions"
        self._session_path.mkdir(parents=True, exist_ok=True)
    
    def create_client(self, phone: str, api_id: str, api_hash: str) -> Optional[Client]:
        """Create Pyrogram client."""
        if not self.is_available:
            logger.error("Pyrogram is not available")
            return None
        
        try:
            session_name = f"session_{phone.replace('+', '')}"
            
            client = Client(
                name=session_name,
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
            
            # Check if already authorized by trying to get user info
            try:
                me = await client.get_me()
                if me:
                    self.client = client
                    logger.info(f"Already authorized for {phone} as {me.first_name or me.phone_number}")
                    return True, None
            except Exception:
                # Not authorized, continue with authentication flow
                pass
            
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
            # Construct session file path properly
            session_file_path = Path(client.workdir) / client.name
            credential = TelegramCredential(
                phone_number=phone,
                session_string=str(session_file_path),
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
            
            # Check if authorized by trying to get user info
            try:
                me = await client.get_me()
                if not me:
                    await client.disconnect()
                    return False, "Session expired or invalid"
            except Exception:
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
    
    def is_connected(self) -> bool:
        """Check if Telegram client is connected and authorized."""
        return self.client is not None
    
    async def is_authorized(self) -> bool:
        """Check if Telegram client is authorized (async check)."""
        if not self.client:
            return False
        try:
            # Try to get user info to verify authorization
            me = await self.client.get_me()
            return me is not None
        except Exception as e:
            logger.error(f"Error checking authorization: {e}")
            return False
    
    async def auto_load_session(self) -> Tuple[bool, Optional[str]]:
        """
        Automatically load the default Telegram session if available.
        Returns (success, error_message)
        """
        try:
            # Get default credential
            credential = self.db_manager.get_default_credential()
            if not credential:
                return False, "No saved Telegram session found"
            
            # Load the session
            return await self.load_session(credential)
        except Exception as e:
            logger.error(f"Error auto-loading session: {e}")
            return False, str(e)
    
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
                        
                        # Process reactions if enabled
                        if settings.settings.track_reactions:
                            await self._process_reactions(
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
            
            # Determine media type and message type
            has_media = False
            media_type = None
            media_count = 0
            message_type = "text"
            has_sticker = False
            has_link = False
            sticker_emoji = None
            
            # Check for sticker
            if telegram_msg.sticker:
                has_sticker = True
                message_type = "sticker"
                if hasattr(telegram_msg.sticker, 'emoji') and telegram_msg.sticker.emoji:
                    sticker_emoji = telegram_msg.sticker.emoji
                has_media = True
                media_type = "sticker"
                media_count = 1
            # Check for photo
            elif telegram_msg.photo:
                has_media = True
                media_type = "photo"
                message_type = "photo"
                media_count = 1
            # Check for video
            elif telegram_msg.video:
                has_media = True
                media_type = "video"
                message_type = "video"
                media_count = 1
            # Check for video note
            elif telegram_msg.video_note:
                has_media = True
                media_type = "video_note"
                message_type = "video_note"
                media_count = 1
            # Check for animation (GIF)
            elif telegram_msg.animation:
                has_media = True
                media_type = "animation"
                message_type = "animation"
                media_count = 1
            # Check for document
            elif telegram_msg.document:
                has_media = True
                media_type = "document"
                message_type = "document"
                media_count = 1
            # Check for audio
            elif telegram_msg.audio:
                has_media = True
                media_type = "audio"
                message_type = "audio"
                media_count = 1
            # Check for voice
            elif telegram_msg.voice:
                has_media = True
                media_type = "voice"
                message_type = "voice"
                media_count = 1
            # Check for location
            elif telegram_msg.location:
                message_type = "location"
            # Check for contact
            elif telegram_msg.contact:
                message_type = "contact"
            # Check for poll
            elif telegram_msg.poll:
                message_type = "poll"
            # Check for media group
            elif telegram_msg.media_group_id:
                has_media = True
                media_type = "media_group"
                message_type = "media_group"
            
            # Get message content
            content = telegram_msg.text or telegram_msg.caption or ""
            
            # Detect links in content
            if content and URL_PATTERN.search(content):
                has_link = True
                if message_type == "text":
                    message_type = "link"
            
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
                message_link=message_link,
                message_type=message_type,
                has_sticker=has_sticker,
                has_link=has_link,
                sticker_emoji=sticker_emoji
            )
            
            return message
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return None
    
    async def _process_reactions(
        self,
        telegram_msg: 'PyrogramMessage',
        group_id: int,
        group_username: Optional[str],
        message_link: str
    ) -> int:
        """
        Process reactions for a message.
        Returns the number of reactions processed.
        """
        if not settings.settings.track_reactions:
            return 0
        
        if not self.client:
            return 0
        
        try:
            # Check if message has reactions
            if not hasattr(telegram_msg, 'reactions') or not telegram_msg.reactions:
                return 0
            
            reaction_count = 0
            reaction_delay = settings.settings.reaction_fetch_delay
            
            # Process each reaction type
            for reaction_obj in telegram_msg.reactions:
                try:
                    # Get emoji - Pyrogram reactions have emoji attribute
                    emoji = "👍"  # Default
                    if hasattr(reaction_obj, 'emoji'):
                        emoji = reaction_obj.emoji
                    elif hasattr(reaction_obj, 'custom_emoji_id'):
                        # Custom emoji - we'll store the ID as string
                        emoji = f"custom_{reaction_obj.custom_emoji_id}"
                    
                    # Try to get users who reacted with this emoji
                    # Pyrogram's get_reactions method signature: get_reactions(chat_id, message_id, limit=0, offset=0)
                    # But we need to filter by emoji, so we'll iterate through all reactions
                    try:
                        # Get all reactions for this message
                        # Note: This might require multiple API calls depending on Pyrogram version
                        reacted_users = []
                        try:
                            # Try to get reactions - this may return a list of users or reaction objects
                            reactions_result = await self.client.get_reactions(
                                group_id,
                                telegram_msg.id
                            )
                            
                            # Handle different return types
                            if isinstance(reactions_result, list):
                                for item in reactions_result:
                                    # Check if this reaction matches our emoji
                                    item_emoji = None
                                    if hasattr(item, 'emoji'):
                                        item_emoji = item.emoji
                                    elif hasattr(item, 'custom_emoji_id'):
                                        item_emoji = f"custom_{item.custom_emoji_id}"
                                    
                                    if item_emoji == emoji:
                                        # Extract user from reaction
                                        if hasattr(item, 'user_id'):
                                            # If it's just a user_id, we need to get the user
                                            user_id = item.user_id
                                            try:
                                                user = await self.client.get_users(user_id)
                                                if user:
                                                    reacted_users.append(user)
                                            except:
                                                # If we can't get user, create a minimal user record
                                                pass
                                        elif hasattr(item, 'user'):
                                            reacted_users.append(item.user)
                        except AttributeError:
                            # get_reactions might not be available in this Pyrogram version
                            # Try alternative approach - reactions might be in the message object
                            logger.debug(f"get_reactions method not available, skipping reaction user fetch")
                            continue
                        except BadRequest as e:
                            # Some reactions may not be accessible (privacy settings, etc.)
                            logger.debug(f"Could not fetch reactions for message {telegram_msg.id}: {e}")
                            continue
                        except FloodWait as e:
                            logger.warning(f"FloodWait when fetching reactions: waiting {e.value} seconds")
                            await asyncio.sleep(e.value)
                            continue
                        
                        # Save each reaction
                        for user in reacted_users:
                            # Process user first to ensure they exist in database
                            if user:
                                await self._process_user(user)
                                
                                reaction = Reaction(
                                    message_id=telegram_msg.id,
                                    group_id=group_id,
                                    user_id=user.id,
                                    emoji=emoji,
                                    message_link=message_link,
                                    reacted_at=telegram_msg.date  # Use message date as proxy
                                )
                                
                                self.db_manager.save_reaction(reaction)
                                reaction_count += 1
                                
                                # Rate limiting between reaction saves
                                if reaction_delay > 0:
                                    await asyncio.sleep(reaction_delay)
                    
                    except Exception as e:
                        logger.warning(f"Error fetching reactions for message {telegram_msg.id}: {e}")
                        continue
                
                except Exception as e:
                    logger.warning(f"Error processing reaction: {e}")
                    continue
            
            return reaction_count
            
        except Exception as e:
            logger.error(f"Error processing reactions for message {telegram_msg.id}: {e}")
            return 0

