"""
Update checker for checking Firebase for new versions.
"""

import asyncio
import logging
import platform
from typing import Optional, Callable, Dict

from config.firebase_config import firebase_config
from services.auth_service import auth_service
from services.firestore.collection_listeners import AppUpdateListener, AppUpdateCallbacks
from services.polling.update_polling_service import UpdatePollingService
from utils.constants import (
    APP_VERSION,
    UPDATE_CHECK_INTERVAL_SECONDS
)
from utils.version_utils import is_newer_version

logger = logging.getLogger(__name__)


class UpdateChecker:
    """Handles checking for updates from Firebase."""
    
    def __init__(
        self,
        on_update_available: Optional[Callable] = None,
        is_fetch_running_callback: Optional[Callable[[], bool]] = None,
        trigger_update_check: Optional[Callable[[], None]] = None
    ):
        """
        Initialize update checker.
        
        Args:
            on_update_available: Callback when update is available (version, download_path)
            is_fetch_running_callback: Callback to check if fetch is running
            trigger_update_check: Optional callback to trigger UpdateService.check_for_updates()
        """
        self.on_update_available = on_update_available
        self.is_fetch_running_callback = is_fetch_running_callback
        self.trigger_update_check = trigger_update_check
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        self._realtime_listener: Optional[AppUpdateListener] = None
        self._realtime_active = False
        self._update_polling_service: Optional[UpdatePollingService] = None
    
    async def start(self):
        """Start background update checker with real-time listener."""
        if self._running:
            logger.warning("Update checker already running")
            return
        
        self._running = True
        
        # Try to start real-time listener first
        if auth_service.is_logged_in():
            success = await self._start_realtime_listener()
            if success:
                logger.info("Update checker started with real-time listener")
                # Still start polling as backup (with longer interval)
                await self._start_polling_service(fallback_mode=True)
                return
        
        # Fallback to polling if real-time fails or user not logged in
        logger.info("Update checker started with polling (real-time unavailable)")
        await self._start_polling_service(fallback_mode=False)
    
    async def _start_realtime_listener(self) -> bool:
        """
        Start real-time listener for app updates.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            def on_update_available(update_data: dict):
                """Handle app update document changed."""
                # Process the update info and trigger check
                # This will call check_for_updates which will download if needed
                asyncio.create_task(self._handle_realtime_update(update_data))
            
            callbacks = AppUpdateCallbacks(on_updated=on_update_available)
            self._realtime_listener = AppUpdateListener()
            
            success = await self._realtime_listener.start(callbacks)
            if success:
                self._realtime_active = True
                logger.info("Real-time app update listener started")
            else:
                logger.warning("Failed to start real-time app update listener")
            
            return success
        except Exception as e:
            logger.error(f"Error starting real-time listener: {e}", exc_info=True)
            return False
    
    async def _handle_realtime_update(self, update_data: dict):
        """
        Handle real-time update notification.
        Processes the update and triggers callback if update is available.
        The UpdateService will handle the actual download.
        
        Args:
            update_data: Update document data from Firestore
        """
        try:
            # Process update info - this will validate and trigger callback if update is available
            await self._process_update_info(update_data)
        except Exception as e:
            logger.error(f"Error handling real-time update: {e}", exc_info=True)
    
    async def _process_update_info(self, update_data: dict):
        """
        Process update info from real-time listener or polling.
        
        Args:
            update_data: Update document data from Firestore (already parsed by watch service)
        """
        try:
            # Check if update is available
            # Handle boolean conversion (Firestore returns string "true"/"false" sometimes)
            is_available = update_data.get('is_available', False)
            if isinstance(is_available, str):
                is_available = is_available.lower() == 'true'
            if not is_available:
                logger.debug("Update is not available (is_available=false)")
                return
            
            latest_version = update_data.get('version')
            if not latest_version:
                logger.warning("Update info missing version")
                return
            
            # Compare versions
            if not is_newer_version(latest_version, APP_VERSION):
                logger.debug(f"Current version {APP_VERSION} is up to date")
                return
            
            # Check min_version_required if specified
            min_version_required = update_data.get('min_version_required')
            if min_version_required:
                if is_newer_version(APP_VERSION, min_version_required):
                    logger.warning(
                        f"Current version {APP_VERSION} is older than minimum required {min_version_required}"
                    )
                    return
            
            logger.info(f"New version available: {latest_version} (current: {APP_VERSION})")
            
            # Get platform-specific download URL
            system = platform.system()
            if system == "Windows":
                download_url = update_data.get('download_url_windows')
                checksum = update_data.get('checksum_windows')
                file_size = update_data.get('file_size_windows')
            elif system == "Darwin":  # macOS
                download_url = update_data.get('download_url_macos')
                checksum = update_data.get('checksum_macos')
                file_size = update_data.get('file_size_macos')
            else:  # Linux
                download_url = update_data.get('download_url_linux')
                checksum = update_data.get('checksum_linux')
                file_size = update_data.get('file_size_linux')
            
            if not download_url:
                logger.warning(f"No download URL for platform {system}")
                return
            
            # For real-time updates, trigger UpdateService to check and download
            if self.trigger_update_check:
                logger.info(f"Real-time update detected: {latest_version}, triggering UpdateService.check_for_updates()")
                # Trigger UpdateService to check and download
                self.trigger_update_check()
            elif self.on_update_available:
                # Fallback: notify callback (UpdateService will handle download)
                logger.info(f"Real-time update detected: {latest_version}, notifying callback")
                self.on_update_available(latest_version, None)
            
        except Exception as e:
            logger.error(f"Error processing update info: {e}", exc_info=True)
    
    async def stop(self):
        """Stop background update checker."""
        self._running = False
        
        # Stop real-time listener
        if self._realtime_listener:
            self._realtime_listener.stop()
            self._realtime_listener = None
            self._realtime_active = False
        
        # Stop polling service
        if self._update_polling_service:
            await self._update_polling_service.stop()
            self._update_polling_service = None
        
        logger.info("Update checker stopped")
    
    async def _start_polling_service(self, fallback_mode: bool = False):
        """
        Start update polling service.
        
        Args:
            fallback_mode: If True, uses longer interval since real-time is primary
        """
        # Stop existing polling service if running
        if self._update_polling_service and self._update_polling_service.is_running:
            await self._update_polling_service.stop()
        
        # Create polling service
        self._update_polling_service = UpdatePollingService(
            on_update_available=self.on_update_available,
            fallback_mode=fallback_mode
        )
        
        # Set the check function
        self._update_polling_service.set_check_function(self.check_for_updates)
        
        # Set condition check: only poll if user is logged in
        def should_poll() -> bool:
            return auth_service.is_logged_in()
        
        self._update_polling_service.set_condition_check(should_poll)
        
        # Start the service
        await self._update_polling_service.start()
        logger.debug(f"Update polling service started (fallback_mode={fallback_mode})")
    
    async def check_for_updates(self) -> Optional[dict]:
        """
        Check Firebase for new app version.
        
        Returns:
            Update info dict if available, None otherwise
        """
        try:
            if not firebase_config.is_initialized():
                logger.debug("Firebase not initialized, skipping update check")
                return None
            
            update_info = firebase_config.get_app_update_info()
            if not update_info:
                logger.debug("No update info found in Firebase")
                return None
            
            # Check if update is available
            if not update_info.get('is_available', False):
                logger.debug("Update is not available (is_available=false)")
                return None
            
            latest_version = update_info.get('version')
            if not latest_version:
                logger.warning("Update info missing version")
                return None
            
            # Compare versions
            if not is_newer_version(latest_version, APP_VERSION):
                logger.debug(f"Current version {APP_VERSION} is up to date")
                return None
            
            # Check min_version_required if specified
            min_version_required = update_info.get('min_version_required')
            if min_version_required:
                if is_newer_version(APP_VERSION, min_version_required):
                    logger.warning(
                        f"Current version {APP_VERSION} is older than minimum required {min_version_required}"
                    )
                    return None
            
            logger.info(f"New version available: {latest_version} (current: {APP_VERSION})")
            
            # Get platform-specific download URL
            system = platform.system()
            if system == "Windows":
                download_url = update_info.get('download_url_windows')
                checksum = update_info.get('checksum_windows')
                file_size = update_info.get('file_size_windows')
            elif system == "Darwin":  # macOS
                download_url = update_info.get('download_url_macos')
                checksum = update_info.get('checksum_macos')
                file_size = update_info.get('file_size_macos')
            else:  # Linux
                download_url = update_info.get('download_url_linux')
                checksum = update_info.get('checksum_linux')
                file_size = update_info.get('file_size_linux')
            
            if not download_url:
                logger.warning(f"No download URL for platform {system}")
                return None
            
            # Return update info for downloader
            return {
                'version': latest_version,
                'download_url': download_url,
                'checksum': checksum,
                'file_size': file_size,
                'update_info': update_info
            }
            
        except Exception as e:
            logger.error(f"Error checking for updates: {e}", exc_info=True)
            return None

