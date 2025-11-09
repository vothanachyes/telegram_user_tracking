"""
Telegram service orchestrator for Telegram API operations.
"""

import logging
from typing import Optional, Callable, List, Tuple, Dict
from datetime import datetime

try:
    from pyrogram import Client
    PYROGRAM_AVAILABLE = True
except ImportError:
    PYROGRAM_AVAILABLE = False
    Client = None

from database.db_manager import DatabaseManager
from database.models import TelegramCredential, TelegramGroup, Message
from services.telegram.client_manager import ClientManager
from services.telegram.user_processor import UserProcessor
from services.telegram.message_processor import MessageProcessor
from services.telegram.reaction_processor import ReactionProcessor
from services.telegram.group_manager import GroupManager
from services.telegram.session_manager import SessionManager
from services.telegram.message_fetcher import MessageFetcher
from services.telegram.group_fetcher import GroupFetcher
from services.telegram.account_status_checker import AccountStatusChecker
from services.telegram.client_utils import ClientUtils

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
        
        # Initialize sub-modules
        self.session_manager = SessionManager(db_manager, self.client_manager)
        self.client_utils = ClientUtils(self.client_manager)
        self.message_fetcher = MessageFetcher(
            db_manager,
            self.client_manager,
            self.user_processor,
            self.message_processor,
            self.client_utils
        )
        self.group_fetcher = GroupFetcher(
            db_manager,
            self.client_manager,
            self.client_utils
        )
        self.account_status_checker = AccountStatusChecker(db_manager, self.client_manager)
    
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
        return self.client_utils.create_client(phone, api_id, api_hash)
    
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
        return await self.session_manager.start_session(phone, api_id, api_hash, code_callback, password_callback)
    
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
        return await self.session_manager.start_session_qr(
            api_id, api_hash, qr_callback, status_callback, password_callback, cancelled_callback
        )
    
    async def load_session(
        self,
        credential: TelegramCredential
    ) -> Tuple[bool, Optional[str]]:
        """Load existing Telegram session."""
        return await self.session_manager.load_session(credential)
    
    async def disconnect(self):
        """Disconnect Telegram client."""
        await self.session_manager.disconnect()
        self._reaction_processor = None
        self._group_manager = None
    
    def is_connected(self) -> bool:
        """Check if Telegram client is connected and authorized."""
        return self.session_manager.is_connected()
    
    async def is_authorized(self) -> bool:
        """Check if Telegram client is authorized (async check)."""
        return await self.session_manager.is_authorized()
    
    async def auto_load_session(self) -> Tuple[bool, Optional[str]]:
        """
        Automatically load the default Telegram session if available.
        Returns (success, error_message)
        """
        return await self.session_manager.auto_load_session()
    
    async def fetch_group_info(
        self,
        group_id: int
    ) -> Tuple[bool, Optional[TelegramGroup], Optional[str]]:
        """
        Fetch group information using temporary client (connect on demand).
        Returns (success, group, error_message)
        """
        return await self.group_fetcher.fetch_group_info(group_id)
    
    async def fetch_messages(
        self,
        group_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        message_callback: Optional[Callable[[Message], None]] = None
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Fetch messages from a group using temporary client (connect on demand).
        Returns (success, message_count, error_message)
        """
        return await self.message_fetcher.fetch_messages(
            group_id, start_date, end_date, progress_callback, message_callback
        )
    
    async def check_account_status(
        self,
        credential: TelegramCredential,
        retry_count: int = 0
    ) -> str:
        """
        Check if account session is valid (on-demand).
        Returns: 'active', 'expired', 'not_connected', 'error'
        
        Args:
            credential: TelegramCredential to check
            retry_count: Internal retry counter for database lock errors
            
        Returns:
            Status string: 'active', 'expired', 'not_connected', or 'error'
        """
        return await self.account_status_checker.check_account_status(credential, retry_count)
    
    async def get_account_status(self, credential_id: int) -> Optional[Dict]:
        """
        Get status of specific account.
        
        Args:
            credential_id: ID of the credential
            
        Returns:
            Dict with credential and status, or None if not found
        """
        return await self.account_status_checker.get_account_status(credential_id)
    
    async def get_all_accounts_with_status(self) -> List[Dict]:
        """
        Get all accounts with status info.
        
        Returns:
            List of dicts with credential and status info
        """
        return await self.account_status_checker.get_all_accounts_with_status()
    
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
        return await self.message_fetcher.fetch_messages_with_account(
            credential, group_id, start_date, end_date, progress_callback, message_callback
        )
    
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
        return await self.group_fetcher.fetch_and_validate_group(account_credential, group_id)
