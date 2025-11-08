"""
Background service for updating Telegram account statuses.
"""

import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from services.telegram.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class AccountStatusService:
    """Background service to periodically check and cache account statuses."""
    
    def __init__(self, telegram_service: TelegramService, db_manager: DatabaseManager):
        """
        Initialize account status service.
        
        Args:
            telegram_service: TelegramService instance
            db_manager: DatabaseManager instance
        """
        self.telegram_service = telegram_service
        self.db_manager = db_manager
        self._status_cache: Dict[int, Dict] = {}
        self._update_task: Optional[asyncio.Task] = None
        self._running = False
        self._update_interval = 300  # 5 minutes in seconds
    
    async def start(self):
        """Start background status update service."""
        if self._running:
            logger.warning("Account status service already running")
            return
        
        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("Account status service started")
    
    async def stop(self):
        """Stop background status update service."""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        logger.info("Account status service stopped")
    
    async def _update_loop(self):
        """Background loop to update account statuses periodically."""
        while self._running:
            try:
                await self.update_all_account_statuses()
                await asyncio.sleep(self._update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in status update loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def update_all_account_statuses(self):
        """
        Update status for all saved accounts.
        Updates in-memory cache (not database).
        """
        try:
            credentials = self.db_manager.get_telegram_credentials()
            logger.debug(f"Updating status for {len(credentials)} accounts")
            
            for credential in credentials:
                try:
                    status = await self.telegram_service.check_account_status(credential)
                    self._status_cache[credential.id] = {
                        'status': status,
                        'checked_at': datetime.now(),
                        'credential': credential
                    }
                except Exception as e:
                    logger.error(f"Error checking status for account {credential.id}: {e}")
                    self._status_cache[credential.id] = {
                        'status': 'error',
                        'checked_at': datetime.now(),
                        'credential': credential
                    }
            
            logger.debug(f"Updated status cache for {len(self._status_cache)} accounts")
        except Exception as e:
            logger.error(f"Error updating all account statuses: {e}")
    
    def get_cached_status(self, credential_id: int) -> Optional[Dict]:
        """
        Get cached status for an account.
        
        Args:
            credential_id: ID of the credential
            
        Returns:
            Cached status dict or None if not cached
        """
        return self._status_cache.get(credential_id)
    
    def get_all_cached_statuses(self) -> Dict[int, Dict]:
        """
        Get all cached statuses.
        
        Returns:
            Dict mapping credential_id to status info
        """
        return self._status_cache.copy()
    
    async def refresh_status(self, credential_id: int) -> Optional[str]:
        """
        Manually refresh status for a specific account.
        
        Args:
            credential_id: ID of the credential
            
        Returns:
            Status string or None if credential not found
        """
        credential = self.db_manager.get_credential_by_id(credential_id)
        if not credential:
            return None
        
        try:
            status = await self.telegram_service.check_account_status(credential)
            self._status_cache[credential_id] = {
                'status': status,
                'checked_at': datetime.now(),
                'credential': credential
            }
            return status
        except Exception as e:
            logger.error(f"Error refreshing status for account {credential_id}: {e}")
            return 'error'
    
    async def refresh_all_statuses(self):
        """Manually refresh all account statuses."""
        await self.update_all_account_statuses()

