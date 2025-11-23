"""
Device revocation handler.
Handles periodic device status checks and auto-logout on revocation.
"""

import logging
import asyncio
from typing import Optional, Callable

from services.device_manager_service import device_manager_service
from services.auth_service import auth_service
from services.polling.device_revocation_polling_service import DeviceRevocationPollingService

logger = logging.getLogger(__name__)


class DeviceRevocationHandler:
    """Handles device revocation checks and auto-logout."""
    
    def __init__(self):
        self._on_revoked_callback: Optional[Callable[[], None]] = None
        self._polling_service: Optional[DeviceRevocationPollingService] = None
    
    def set_revoked_callback(self, callback: Callable[[], None]):
        """
        Set callback to be called when device is revoked.
        
        Args:
            callback: Function to call when device is revoked
        """
        self._on_revoked_callback = callback
    
    async def start_periodic_check(self):
        """
        Start periodic device status check using generic polling service.
        Checks every 30 seconds for quick revocation detection.
        """
        # Stop existing polling service if running
        if self._polling_service and self._polling_service.is_running:
            await self._polling_service.stop()
        
        # Do an immediate check first
        if auth_service.is_logged_in():
            is_revoked, error_msg = device_manager_service.check_device_status()
            if is_revoked:
                logger.warning("Device is revoked on startup, triggering immediate auto-logout")
                await self._handle_revocation()
                return
        
        # Create polling service
        self._polling_service = DeviceRevocationPollingService(
            on_revoked=self._on_revoked_callback,
            interval_seconds=30.0  # 30 seconds for quick detection
        )
        
        # Set condition check: only poll if user is logged in
        def should_poll() -> bool:
            return auth_service.is_logged_in()
        
        self._polling_service.set_condition_check(should_poll)
        
        # Start the service
        await self._polling_service.start()
        logger.info("Device revocation polling service started (every 30 seconds)")
    
    async def _handle_revocation(self):
        """
        Handle device revocation - logout user and notify.
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
            if self._on_revoked_callback:
                self._on_revoked_callback()
            
            # Logout user
            auth_service.logout()
            logger.info("User logged out due to device revocation")
        except Exception as e:
            logger.error(f"Error handling device revocation: {e}", exc_info=True)
    
    async def stop_periodic_check(self):
        """Stop periodic device status check."""
        if self._polling_service:
            await self._polling_service.stop()
            self._polling_service = None
            logger.info("Stopped periodic device revocation check")
    
    def check_now(self) -> bool:
        """
        Check device status immediately and synchronously.
        This is called before critical operations.
        
        Returns:
            True if device is revoked, False otherwise
        """
        if not auth_service.is_logged_in():
            return False
        
        try:
            is_revoked, error_msg = device_manager_service.check_device_status()
            
            if is_revoked:
                logger.warning("Device is revoked (immediate check) - logging out now")
                # Delete saved credentials immediately to prevent auto-login
                try:
                    # Try to get db_manager from auth_service first (most reliable)
                    db_manager = getattr(auth_service, 'db_manager', None)
                    if not db_manager:
                        # Fallback to settings
                        from config.settings import settings
                        db_manager = getattr(settings, 'db_manager', None)
                    
                    if db_manager:
                        db_manager.delete_login_credential()
                        logger.info("Deleted saved credentials due to immediate device revocation check")
                except Exception as e:
                    logger.error(f"Error deleting credentials: {e}", exc_info=True)
                
                # Handle revocation immediately (synchronously)
                # Use asyncio to ensure it runs in the event loop
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is running, create task
                        asyncio.create_task(self._handle_revocation())
                    else:
                        # If no loop running, run it
                        asyncio.run(self._handle_revocation())
                except RuntimeError:
                    # No event loop, create new one
                    asyncio.run(self._handle_revocation())
                return True
        except Exception as e:
            logger.error(f"Error in immediate device check: {e}", exc_info=True)
            # Don't block on error, but log it
            return False
        
        return False


# Global device revocation handler instance
device_revocation_handler = DeviceRevocationHandler()

