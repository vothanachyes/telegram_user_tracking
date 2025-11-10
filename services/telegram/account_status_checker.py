"""
Account status checker for checking Telegram account session validity.
"""

import logging
import asyncio
import sqlite3
from typing import Optional, List, Dict
from datetime import datetime

try:
    from telethon.errors import UnauthorizedError, AuthKeyUnregisteredError, SessionRevokedError
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    UnauthorizedError = AuthKeyUnregisteredError = SessionRevokedError = None

from database.db_manager import DatabaseManager
from database.models import TelegramCredential
from config.settings import settings
from services.telegram.client_manager import ClientManager

logger = logging.getLogger(__name__)


class AccountStatusChecker:
    """Handles checking Telegram account session status."""
    
    def __init__(self, db_manager: DatabaseManager, client_manager: ClientManager):
        self.db_manager = db_manager
        self.client_manager = client_manager
    
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
        if not settings.has_telegram_credentials:
            return 'error'
        
        try:
            # Create temporary client to check status
            # Use stored session_path from credential if available
            session_path = credential.session_string if credential.session_string else None
            temp_client = self.client_manager.create_client(
                credential.phone_number,
                settings.telegram_api_id,
                settings.telegram_api_hash,
                session_path=session_path
            )
            
            if not temp_client:
                return 'error'
            
            try:
                await temp_client.connect()
                # Check if authorized
                if await temp_client.is_user_authorized():
                    me = await temp_client.get_me()
                    if me:
                        await temp_client.disconnect()
                        return 'active'
                await temp_client.disconnect()
                return 'expired'
            except Exception as e:
                # Disconnect client first
                try:
                    await temp_client.disconnect()
                except:
                    pass
                
                # Check for database lock errors and retry
                error_type = type(e).__name__
                error_str = str(e).lower()
                
                # Handle database lock errors - these come from Telethon's internal SQLite storage
                # Telethon uses SQLite for session storage, and concurrent access can cause locks
                if isinstance(e, sqlite3.OperationalError) and "database is locked" in error_str:
                    # This is Telethon's session database lock, not our app database
                    # Retry with longer delays to allow Telethon's session file to unlock
                    if retry_count < 2:  # Retry up to 2 times
                        wait_time = 0.5 * (retry_count + 1)  # Longer delay: 0.5s, 1.0s
                        logger.debug(
                            f"Telethon session database locked for {credential.phone_number} "
                            f"(attempt {retry_count + 1}), retrying in {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                        return await self.check_account_status(credential, retry_count + 1)
                    else:
                        logger.warning(
                            f"Telethon session database locked after {retry_count + 1} retries "
                            f"for {credential.phone_number}. This is usually due to concurrent session access."
                        )
                        return 'error'  # Mark as error, not expired - session might still be valid
                elif "database is locked" in error_str:
                    # String match for database lock (might be wrapped)
                    # This is Telethon's session database lock, not our app database
                    if retry_count < 2:  # Retry up to 2 times
                        wait_time = 0.5 * (retry_count + 1)  # Longer delay: 0.5s, 1.0s
                        logger.debug(
                            f"Telethon session database locked for {credential.phone_number} "
                            f"(attempt {retry_count + 1}), retrying in {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                        return await self.check_account_status(credential, retry_count + 1)
                    else:
                        logger.warning(
                            f"Telethon session database locked after {retry_count + 1} retries "
                            f"for {credential.phone_number}. This is usually due to concurrent session access."
                        )
                        return 'error'  # Mark as error, not expired - session might still be valid
                
                # Check for specific session expiration exceptions
                if UnauthorizedError and isinstance(e, UnauthorizedError):
                    logger.debug(f"Account {credential.phone_number} session expired (Unauthorized)")
                    return 'expired'
                elif AuthKeyUnregisteredError and isinstance(e, AuthKeyUnregisteredError):
                    logger.debug(f"Account {credential.phone_number} auth key unregistered")
                    return 'expired'
                elif SessionRevokedError and isinstance(e, SessionRevokedError):
                    logger.debug(f"Account {credential.phone_number} session revoked")
                    return 'expired'
                elif "unauthorized" in error_str or "auth key" in error_str or "session revoked" in error_str:
                    logger.debug(f"Account {credential.phone_number} session expired (string match)")
                    return 'expired'
                
                # Check for network/connection errors
                if isinstance(e, (ConnectionError, TimeoutError, OSError)):
                    logger.warning(f"Network error checking account {credential.phone_number}: {e}")
                    return 'error'
                elif "connection" in error_str or "timeout" in error_str or "network" in error_str:
                    logger.warning(f"Network error checking account {credential.phone_number}: {e}")
                    return 'error'
                
                # Unknown error - log for debugging but don't mark as expired
                logger.error(f"Error checking account {credential.phone_number} status: {e} (type: {error_type})")
                return 'error'
        except Exception as e:
            # Handle database lock in outer exception handler too
            error_str = str(e).lower()
            error_type = type(e).__name__
            
            # Check for SQLite OperationalError (database locked)
            if isinstance(e, sqlite3.OperationalError) and "database is locked" in error_str:
                if retry_count < 2:
                    await asyncio.sleep(0.1 * (retry_count + 1))
                    logger.debug(f"Retrying account status check for {credential.phone_number} (outer retry {retry_count + 1})")
                    return await self.check_account_status(credential, retry_count + 1)
                else:
                    logger.warning(f"Database locked after {retry_count + 1} retries for {credential.phone_number}")
                    return 'error'
            elif "database is locked" in error_str:
                # String match for database lock (might be wrapped)
                if retry_count < 2:
                    await asyncio.sleep(0.1 * (retry_count + 1))
                    logger.debug(f"Retrying account status check for {credential.phone_number} (outer retry {retry_count + 1})")
                    return await self.check_account_status(credential, retry_count + 1)
                else:
                    logger.warning(f"Database locked after {retry_count + 1} retries for {credential.phone_number}")
                    return 'error'
            
            # Log other errors (but not database locks - those are handled above)
            logger.error(f"Error checking account status: {e} (type: {error_type})")
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
        # CRITICAL: Read credentials FIRST with retry logic for database locks
        # This prevents holding a database connection while doing async status checks
        # The 'with' statement in get_telegram_credentials() ensures connection closes
        credentials_with_status = []
        max_retries = 5  # Increased retries
        for attempt in range(max_retries):
            try:
                # Add small delay before each attempt to let previous operations complete
                if attempt > 0:
                    await asyncio.sleep(0.2 * attempt)  # Exponential backoff
                
                credentials_with_status = self.db_manager.get_all_credentials_with_status()
                break  # Success, exit retry loop
            except sqlite3.OperationalError as e:
                error_str = str(e).lower()
                if "database is locked" in error_str and attempt < max_retries - 1:
                    # Retry with exponential backoff
                    wait_time = 0.2 * (attempt + 1)
                    logger.debug(f"Database locked reading credentials (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Database error reading credentials: {e} (attempt {attempt + 1}/{max_retries})")
                    if attempt == max_retries - 1:
                        return []  # Return empty list after all retries exhausted
            except Exception as e:
                error_str = str(e).lower()
                if "database is locked" in error_str and attempt < max_retries - 1:
                    # Retry with exponential backoff
                    wait_time = 0.2 * (attempt + 1)
                    logger.debug(f"Database locked reading credentials (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Error reading credentials from database: {e} (type: {type(e).__name__})")
                    return []
        
        if not credentials_with_status:
            return []
        
        # Now check status for each credential (no database access during this loop)
        # The database connection is already closed, so no lock conflicts
        for item in credentials_with_status:
            credential = item['credential']
            try:
                status = await self.check_account_status(credential)
                item['status'] = status
                item['status_checked_at'] = datetime.now()
            except Exception as e:
                # If status check fails, mark as error but continue
                # Don't log database lock errors here - they're handled in check_account_status
                error_str = str(e).lower()
                if "database is locked" not in error_str:
                    logger.warning(f"Error checking status for {credential.phone_number}: {e}")
                item['status'] = 'error'
                item['status_checked_at'] = datetime.now()
            
            # Delay between checks to:
            # 1. Prevent overwhelming Telegram API
            # 2. Allow Telethon's session SQLite files to unlock (avoid concurrent access)
            # 3. Give database time to release any locks
            await asyncio.sleep(0.3)  # Increased to 300ms to avoid Telethon session file locks
        
        return credentials_with_status

