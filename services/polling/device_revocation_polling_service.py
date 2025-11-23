"""
Device revocation polling service for background device status checks.
"""

import logging
from typing import Optional, Callable
from services.polling.base_polling_service import BasePollingService
from services.device_manager_service import device_manager_service
from services.auth_service import auth_service

logger = logging.getLogger(__name__)


class DeviceRevocationPollingService(BasePollingService):
    """
    Polling service for device revocation checks.
    Periodically checks if the current device has been revoked.
    """
    
    def __init__(
        self,
        on_revoked: Optional[Callable[[], None]] = None,
        interval_seconds: float = 30.0
    ):
        """
        Initialize device revocation polling service.
        
        Args:
            on_revoked: Optional callback when device is revoked
            interval_seconds: Polling interval in seconds (default: 30 seconds for quick detection)
        """
        super().__init__(
            interval_seconds=interval_seconds,
            enabled=True,  # Always enabled for security
            name="DeviceRevocationPolling"
        )
        self._on_revoked = on_revoked
    
    def set_callback(self, callback: Optional[Callable[[], None]]) -> None:
        """
        Set callback for device revocation.
        
        Args:
            callback: Callback function called when device is revoked
        """
        self._on_revoked = callback
    
    async def _poll(self) -> None:
        """Perform device revocation polling - check if device is revoked."""
        try:
            # Check if user is logged in
            if not auth_service.is_logged_in():
                logger.debug("DeviceRevocationPolling: User not logged in, skipping poll")
                return
            
            # Check device status
            is_revoked, error_msg = device_manager_service.check_device_status()
            
            if is_revoked:
                logger.warning("Device is revoked, triggering auto-logout")
                
                # Handle revocation (delete credentials, logout, etc.)
                await self._handle_revocation()
                
                # Stop polling after revocation (user will be logged out)
                await self.stop()
        
        except Exception as e:
            logger.error(f"DeviceRevocationPolling: Error during poll: {e}", exc_info=True)
            # Don't re-raise - let base class handle retry logic
    
    async def _handle_revocation(self):
        """
        Handle device revocation - delete credentials, call callback, and logout.
        """
        try:
            # Delete saved credentials to prevent auto-login
            try:
                # Try to get db_manager from auth_service first (most reliable)
                db_manager = getattr(auth_service, 'db_manager', None)
                if not db_manager:
                    # Fallback to settings
                    from config.settings import settings
                    db_manager = getattr(settings, 'db_manager', None)
                
                if db_manager:
                    db_manager.delete_login_credential()
                    logger.info("Deleted saved credentials due to device revocation")
            except Exception as e:
                logger.error(f"Error deleting credentials on revocation: {e}", exc_info=True)
            
            # Call callback if set
            if self._on_revoked:
                try:
                    self._on_revoked()
                except Exception as e:
                    logger.error(f"DeviceRevocationPolling: Error in callback: {e}", exc_info=True)
            
            # Logout user
            auth_service.logout()
            logger.info("User logged out due to device revocation")
        except Exception as e:
            logger.error(f"Error handling device revocation: {e}", exc_info=True)

