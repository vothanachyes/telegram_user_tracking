"""
Group fetcher for fetching and validating Telegram groups.
"""

import logging
from typing import Optional, Tuple

from database.db_manager import DatabaseManager
from database.models import TelegramCredential, TelegramGroup
from services.telegram.client_manager import ClientManager
from services.telegram.group_manager import GroupManager
from services.telegram.client_utils import ClientUtils

logger = logging.getLogger(__name__)


class GroupFetcher:
    """Handles fetching and validating Telegram group information."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        client_manager: ClientManager,
        client_utils: ClientUtils
    ):
        self.db_manager = db_manager
        self.client_manager = client_manager
        self.client_utils = client_utils
    
    async def fetch_group_info(
        self,
        group_id: int
    ) -> Tuple[bool, Optional[TelegramGroup], Optional[str]]:
        """
        Fetch group information using temporary client (connect on demand).
        Returns (success, group, error_message)
        """
        temp_client = None
        try:
            # Get default credential
            credential = self.db_manager.get_default_credential()
            if not credential:
                return False, None, "No Telegram account configured"
            
            # Create temporary client
            temp_client = await self.client_utils.create_temporary_client(credential)
            if not temp_client:
                return False, None, "Failed to connect or session expired"
            
            # Create group manager with temporary client
            temp_group_manager = GroupManager(self.db_manager, temp_client)
            
            return await temp_group_manager.fetch_group_info(group_id)
        except Exception as e:
            logger.error(f"Error fetching group info: {e}")
            return False, None, str(e)
        finally:
            # Always disconnect temporary client
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
            temp_client = await self.client_utils.create_temporary_client(account_credential)
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

