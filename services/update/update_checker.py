"""
Update checker for checking Firebase for new versions.
"""

import asyncio
import logging
import platform
from typing import Optional, Callable, Dict

from config.firebase_config import firebase_config
from services.auth_service import auth_service
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
        is_fetch_running_callback: Optional[Callable[[], bool]] = None
    ):
        """
        Initialize update checker.
        
        Args:
            on_update_available: Callback when update is available (version, download_path)
            is_fetch_running_callback: Callback to check if fetch is running
        """
        self.on_update_available = on_update_available
        self.is_fetch_running_callback = is_fetch_running_callback
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start background update checker."""
        if self._running:
            logger.warning("Update checker already running")
            return
        
        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("Update checker started")
    
    async def stop(self):
        """Stop background update checker."""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        logger.info("Update checker stopped")
    
    async def _update_loop(self):
        """Background loop to check for updates periodically."""
        while self._running:
            try:
                # Only check if user is logged in
                if auth_service.is_logged_in():
                    await self.check_for_updates()
                await asyncio.sleep(UPDATE_CHECK_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in update check loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
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

