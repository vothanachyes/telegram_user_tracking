"""
Notification polling service for background notification badge updates.
"""

import logging
from typing import Optional, Callable
from services.polling.base_polling_service import BasePollingService
from config.settings import (
    NOTIFICATION_POLLING_INTERVAL,
    ENABLE_NOTIFICATION_POLLING
)
from services.auth_service import auth_service
from services.notification_service import notification_service

logger = logging.getLogger(__name__)


class NotificationPollingService(BasePollingService):
    """
    Polling service for notification badge updates.
    Periodically fetches unread notification count and updates the badge.
    """
    
    def __init__(
        self,
        on_unread_count_changed: Optional[Callable[[int], None]] = None,
        interval_seconds: Optional[float] = None
    ):
        """
        Initialize notification polling service.
        
        Args:
            on_unread_count_changed: Optional callback when unread count changes
            interval_seconds: Optional custom interval (uses config default if None)
        """
        interval = interval_seconds or NOTIFICATION_POLLING_INTERVAL
        super().__init__(
            interval_seconds=interval,
            enabled=ENABLE_NOTIFICATION_POLLING,
            name="NotificationPolling"
        )
        self._on_unread_count_changed = on_unread_count_changed
        self._last_unread_count: Optional[int] = None
    
    def set_callback(self, callback: Optional[Callable[[int], None]]) -> None:
        """
        Set callback for unread count changes.
        
        Args:
            callback: Callback function that receives unread count
        """
        self._on_unread_count_changed = callback
    
    def _check_config_enabled(self) -> bool:
        """Check if notification polling is enabled via configuration."""
        return ENABLE_NOTIFICATION_POLLING
    
    async def _poll(self) -> None:
        """Perform notification polling - fetch unread count and update badge."""
        try:
            # Check if user is logged in
            current_user = auth_service.get_current_user()
            if not current_user:
                logger.debug("NotificationPolling: User not logged in, skipping poll")
                return
            
            user_id = current_user.get("uid")
            if not user_id:
                logger.debug("NotificationPolling: No user ID, skipping poll")
                return
            
            # Get unread count
            unread_count = notification_service.get_unread_count(user_id)
            
            # Only trigger callback if count changed
            if unread_count != self._last_unread_count:
                self._last_unread_count = unread_count
                
                if self._on_unread_count_changed:
                    try:
                        self._on_unread_count_changed(unread_count)
                    except Exception as e:
                        logger.error(f"NotificationPolling: Error in callback: {e}", exc_info=True)
                
                logger.debug(f"NotificationPolling: Unread count updated: {unread_count}")
        
        except Exception as e:
            logger.error(f"NotificationPolling: Error during poll: {e}", exc_info=True)
            # Don't re-raise - let base class handle retry logic

