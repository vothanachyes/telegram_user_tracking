"""
Telegram service orchestrator for Telegram API operations.
"""

import logging
import asyncio
from typing import Optional, Callable, List, Tuple, Dict
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
            from pathlib import Path
            session_file_path = Path(client.workdir) / client.name
            credential = TelegramCredential(
                phone_number=phone,
                session_string=str(session_file_path),
                is_default=True
            )
            self.db_manager.save_telegram_credential(credential)
        
        return success, error
    
    async def start_session_qr(
        self,
        api_id: str,
        api_hash: str,
        qr_callback: Optional[Callable[[str], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        password_callback: Optional[Callable[[], str]] = None,
        cancelled_callback: Optional[Callable[[], bool]] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Start Telegram session with QR code flow.
        Returns (success, error_message, phone_number)
        """
        success, error, client, phone_number = await self.client_manager.start_session_qr(
            api_id, api_hash, qr_callback, status_callback, password_callback, cancelled_callback
        )
        
        if success and client and phone_number:
            from pathlib import Path
            session_file_path = Path(client.workdir) / client.name
            credential = TelegramCredential(
                phone_number=phone_number,
                session_string=str(session_file_path),
                is_default=True
            )
            self.db_manager.save_telegram_credential(credential)
        
        return success, error, phone_number
    
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
            
            if not self._group_manager:
                self._group_manager = GroupManager(self.db_manager, self.client)
            if not self._reaction_processor:
                self._reaction_processor = ReactionProcessor(
                    self.db_manager,
                    self.client,
                    self.user_processor
                )
            
            success, group, error = await self._group_manager.fetch_group_info(group_id)
            if not success:
                return False, 0, error
            
            self._group_manager.save_group(group)
            
            message_count = 0
            fetch_delay = settings.settings.fetch_delay_seconds
            
            async for telegram_msg in self.client.get_chat_history(group_id):
                try:
                    if start_date and telegram_msg.date < start_date:
                        break
                    
                    if end_date and telegram_msg.date > end_date:
                        continue
                    
                    if self.db_manager.is_message_deleted(telegram_msg.id, group_id):
                        continue
                    
                    if telegram_msg.from_user:
                        await self.user_processor.process_user(telegram_msg.from_user)
                    
                    message = await self.message_processor.process_message(
                        telegram_msg,
                        group_id,
                        group.group_username
                    )
                    
                    if message:
                        self.db_manager.save_message(message)
                        message_count += 1
                        
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
                            progress_callback(message_count, -1)
                    
                    if fetch_delay > 0:
                        await asyncio.sleep(fetch_delay)
                    
                except FloodWait as e:
                    logger.warning(f"FloodWait: waiting {e.value} seconds")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    logger.error(f"Error processing message {telegram_msg.id}: {e}")
                    continue
            
            total_messages = self.db_manager.get_message_count(group_id)
            self._group_manager.update_group_stats(group, total_messages)
            
            logger.info(f"Fetched {message_count} messages from group {group_id}")
            return True, message_count, None
            
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return False, 0, str(e)
    
    async def check_account_status(
        self,
        credential: TelegramCredential
    ) -> str:
        """
        Check if account session is valid (on-demand).
        Returns: 'active', 'expired', 'not_connected', 'error'
        
        Args:
            credential: TelegramCredential to check
            
        Returns:
            Status string: 'active', 'expired', 'not_connected', or 'error'
        """
        if not settings.has_telegram_credentials:
            return 'error'
        
        try:
            # Create temporary client to check status
            temp_client = self.client_manager.create_client(
                credential.phone_number,
                settings.telegram_api_id,
                settings.telegram_api_hash
            )
            
            if not temp_client:
                return 'error'
            
            try:
                await temp_client.connect()
                me = await temp_client.get_me()
                if me:
                    await temp_client.disconnect()
                    return 'active'
                else:
                    await temp_client.disconnect()
                    return 'expired'
            except Exception:
                try:
                    await temp_client.disconnect()
                except:
                    pass
                return 'expired'
        except Exception as e:
            logger.error(f"Error checking account status: {e}")
            return 'error'
    
    async def get_account_status(self, credential_id: int) -> Optional[Dict]:
        """
        Get status of specific account.
        
        Args:
            credential_id: ID of the credential
            
        Returns:
            Dict with credential and status, or None if not found
        """
        credential = self.db_manager.get_credential_by_id(credential_id)
        if not credential:
            return None
        
        status = await self.check_account_status(credential)
        return {
            'credential': credential,
            'status': status,
            'status_checked_at': datetime.now()
        }
    
    async def get_all_accounts_with_status(self) -> List[Dict]:
        """
        Get all accounts with status info.
        
        Returns:
            List of dicts with credential and status info
        """
        credentials_with_status = self.db_manager.get_all_credentials_with_status()
        
        # Check status for each credential
        for item in credentials_with_status:
            credential = item['credential']
            status = await self.check_account_status(credential)
            item['status'] = status
            item['status_checked_at'] = datetime.now()
        
        return credentials_with_status
    
    async def _create_temporary_client(
        self,
        credential: TelegramCredential
    ) -> Optional[Client]:
        """
        Create a temporary client for a specific credential.
        Does not affect the current connected client.
        
        Args:
            credential: TelegramCredential to create client for
            
        Returns:
            Temporary Client instance or None if failed
        """
        if not settings.has_telegram_credentials:
            return None
        
        try:
            client = self.client_manager.create_client(
                credential.phone_number,
                settings.telegram_api_id,
                settings.telegram_api_hash
            )
            
            if client:
                await client.connect()
                # Verify it's authorized
                me = await client.get_me()
                if not me:
                    await client.disconnect()
                    return None
                return client
            return None
        except Exception as e:
            logger.error(f"Error creating temporary client: {e}")
            return None
    
    async def fetch_messages_with_account(
        self,
        credential: TelegramCredential,
        group_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        message_callback: Optional[Callable[[Message], None]] = None
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Fetch messages using a specific account (temporary client).
        Keeps current session connected.
        
        Args:
            credential: TelegramCredential to use for fetching
            group_id: Group ID to fetch from
            start_date: Optional start date
            end_date: Optional end date
            progress_callback: Optional progress callback
            message_callback: Optional message callback
            
        Returns:
            (success, message_count, error_message)
        """
        temp_client = None
        try:
            # Create temporary client
            temp_client = await self._create_temporary_client(credential)
            if not temp_client:
                return False, 0, "Failed to create temporary client or session expired"
            
            # Create processors with temporary client
            temp_group_manager = GroupManager(self.db_manager, temp_client)
            temp_reaction_processor = ReactionProcessor(
                self.db_manager,
                temp_client,
                self.user_processor
            )
            
            # Fetch group info
            success, group, error = await temp_group_manager.fetch_group_info(group_id)
            if not success:
                return False, 0, error
            
            temp_group_manager.save_group(group)
            
            message_count = 0
            fetch_delay = settings.settings.fetch_delay_seconds
            
            async for telegram_msg in temp_client.get_chat_history(group_id):
                try:
                    if start_date and telegram_msg.date < start_date:
                        break
                    
                    if end_date and telegram_msg.date > end_date:
                        continue
                    
                    if self.db_manager.is_message_deleted(telegram_msg.id, group_id):
                        continue
                    
                    if telegram_msg.from_user:
                        await self.user_processor.process_user(telegram_msg.from_user)
                    
                    message = await self.message_processor.process_message(
                        telegram_msg,
                        group_id,
                        group.group_username
                    )
                    
                    if message:
                        self.db_manager.save_message(message)
                        message_count += 1
                        
                        if settings.settings.track_reactions:
                            await temp_reaction_processor.process_reactions(
                                telegram_msg,
                                group_id,
                                group.group_username,
                                message.message_link
                            )
                        
                        if message_callback:
                            message_callback(message)
                        
                        if progress_callback:
                            progress_callback(message_count, -1)
                    
                    if fetch_delay > 0:
                        await asyncio.sleep(fetch_delay)
                    
                except FloodWait as e:
                    logger.warning(f"FloodWait: waiting {e.value} seconds")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    logger.error(f"Error processing message {telegram_msg.id}: {e}")
                    continue
            
            total_messages = self.db_manager.get_message_count(group_id)
            temp_group_manager.update_group_stats(group, total_messages)
            
            logger.info(f"Fetched {message_count} messages from group {group_id} using account {credential.phone_number}")
            return True, message_count, None
            
        except Exception as e:
            logger.error(f"Error fetching messages with account: {e}")
            return False, 0, str(e)
        finally:
            # Clean up temporary client
            if temp_client:
                try:
                    await temp_client.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting temporary client: {e}")
    
    async def fetch_and_validate_group(
        self,
        account_credential: TelegramCredential,
        group_id: int
    ) -> Tuple[bool, Optional[TelegramGroup], Optional[str], bool]:
        """
        Fetch group info using specific account and validate access.
        Uses temporary client for validation.
        
        Args:
            account_credential: TelegramCredential to use
            group_id: Group ID to validate
            
        Returns:
            (success, group_info, error_message, has_access)
        """
        temp_client = None
        try:
            # Import Pyrogram errors for specific error handling
            try:
                from pyrogram.errors import ChatNotFound, Forbidden, Unauthorized, UsernameNotOccupied
            except ImportError:
                ChatNotFound = Forbidden = Unauthorized = UsernameNotOccupied = None
            
            # Create temporary client
            temp_client = await self._create_temporary_client(account_credential)
            if not temp_client:
                return False, None, "Account session expired or invalid", False
            
            # Create group manager with temporary client
            temp_group_manager = GroupManager(self.db_manager, temp_client)
            
            # Fetch group info
            success, group, error = await temp_group_manager.fetch_group_info(group_id)
            
            if not success:
                # Check for specific error types
                error_lower = (error or "").lower()
                
                # Check if it's a session/authorization error
                if "unauthorized" in error_lower or "expired" in error_lower or "invalid" in error_lower:
                    return False, None, "Account session expired, please reconnect", False
                
                # Check if it's a permission error
                if "forbidden" in error_lower or "permission" in error_lower:
                    return False, None, "permission_denied", False  # Special marker for permission error
                
                # Check if it's a not found/not member error
                if "not found" in error_lower or "chat not found" in error_lower or "not a member" in error_lower:
                    return False, None, "not_member", False  # Special marker for not member error
                
                # Generic error
                return False, None, error or "Group not found or invalid", False
            
            # If we got group info, account has access
            return True, group, None, True
            
        except Exception as e:
            # Handle Pyrogram-specific exceptions
            error_str = str(e).lower()
            error_type = type(e).__name__
            
            # Check for specific Pyrogram error types
            if ChatNotFound and isinstance(e, ChatNotFound):
                return False, None, "not_member", False
            elif Forbidden and isinstance(e, Forbidden):
                return False, None, "permission_denied", False
            elif Unauthorized and isinstance(e, Unauthorized):
                return False, None, "Account session expired, please reconnect", False
            elif "unauthorized" in error_str or "expired" in error_str:
                return False, None, "Account session expired, please reconnect", False
            elif "forbidden" in error_str or "permission" in error_str:
                return False, None, "permission_denied", False
            elif "not found" in error_str or "chat not found" in error_str:
                return False, None, "not_member", False
            
            logger.error(f"Error validating group access: {e}")
            return False, None, str(e), False
        finally:
            # Clean up temporary client
            if temp_client:
                try:
                    await temp_client.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting temporary client: {e}")

