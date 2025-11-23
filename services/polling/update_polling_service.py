"""
App update polling service for background update checking.
"""

import asyncio
import logging
from typing import Optional, Callable
from services.polling.base_polling_service import BasePollingService
from config.settings import (
    UPDATE_POLLING_INTERVAL,
    ENABLE_UPDATE_POLLING
)
from services.auth_service import auth_service
from utils.constants import UPDATE_CHECK_INTERVAL_SECONDS

logger = logging.getLogger(__name__)


class UpdatePollingService(BasePollingService):
    """
    Polling service for app update checking.
    Periodically checks Firebase for new app versions.
    """
    
    def __init__(
        self,
        on_update_available: Optional[Callable[[str, str], None]] = None,
        interval_seconds: Optional[float] = None,
        fallback_mode: bool = False
    ):
        """
        Initialize update polling service.
        
        Args:
            on_update_available: Optional callback when update is available (version: str, download_path: str)
            interval_seconds: Optional custom interval (uses config default if None)
            fallback_mode: If True, uses longer interval (2x) since real-time is primary
        """
        # Use config interval or fallback to constants
        if interval_seconds is None:
            base_interval = UPDATE_POLLING_INTERVAL or UPDATE_CHECK_INTERVAL_SECONDS
            interval_seconds = base_interval * 2 if fallback_mode else base_interval
        
        super().__init__(
            interval_seconds=interval_seconds,
            enabled=ENABLE_UPDATE_POLLING,
            name="UpdatePolling"
        )
        self._on_update_available = on_update_available
        self._fallback_mode = fallback_mode
        self._check_for_updates: Optional[Callable[[], None]] = None
    
    def set_callback(self, callback: Optional[Callable[[str, str], None]]) -> None:
        """
        Set callback for update availability.
        
        Args:
            callback: Callback function that receives (version: str, download_path: str)
        """
        self._on_update_available = callback
    
    def set_check_function(self, check_func: Callable[[], None]) -> None:
        """
        Set the function to call for checking updates.
        This should be the UpdateChecker.check_for_updates method.
        
        Args:
            check_func: Async function that checks for updates
        """
        self._check_for_updates = check_func
    
    def _check_config_enabled(self) -> bool:
        """Check if update polling is enabled via configuration."""
        return ENABLE_UPDATE_POLLING
    
    async def _poll(self) -> None:
        """Perform update polling - check for new app versions."""
        try:
            # Check if user is logged in
            if not auth_service.is_logged_in():
                logger.debug("UpdatePolling: User not logged in, skipping poll")
                return
            
            # Call the check function if provided
            if self._check_for_updates:
                try:
                    # The check function should handle update processing
                    if asyncio.iscoroutinefunction(self._check_for_updates):
                        result = await self._check_for_updates()
                    else:
                        result = self._check_for_updates()
                    
                    # If result is update data and callback is set, call it
                    # Callback expects (version: str, download_path: str)
                    if result and isinstance(result, dict) and self._on_update_available:
                        try:
                            version = result.get('version')
                            download_path = result.get('download_path')
                            
                            # Only call callback if both version and download_path are available (update downloaded)
                            if version and download_path:
                                self._on_update_available(version, download_path)
                            # If only version available (not downloaded yet), don't call callback
                            # UpdateService will handle download based on auto-download setting
                        except Exception as e:
                            logger.error(f"UpdatePolling: Error in callback: {e}", exc_info=True)
                except Exception as e:
                    logger.error(f"UpdatePolling: Error calling check function: {e}", exc_info=True)
            else:
                logger.warning("UpdatePolling: No check function set, skipping poll")
        
        except Exception as e:
            logger.error(f"UpdatePolling: Error during poll: {e}", exc_info=True)
            # Don't re-raise - let base class handle retry logic

