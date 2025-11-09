"""
Automatic app update service that checks Firebase for new versions,
downloads updates, and tracks installations.
"""

import asyncio
import logging
import hashlib
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("requests library not installed")

from config.firebase_config import firebase_config
from database.db_manager import DatabaseManager
from services.auth_service import auth_service
from utils.constants import (
    APP_VERSION,
    UPDATE_CHECK_INTERVAL_SECONDS,
    UPDATES_DIR_NAME,
    USER_DATA_DIR
)
from utils.version_utils import is_newer_version

logger = logging.getLogger(__name__)


class UpdateService:
    """Background service for checking and downloading app updates."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        page=None,
        on_update_available: Optional[Callable] = None,
        is_fetch_running_callback: Optional[Callable[[], bool]] = None
    ):
        """
        Initialize update service.
        
        Args:
            db_manager: DatabaseManager instance
            page: Flet page instance for toast notifications
            on_update_available: Callback when update is available (version, download_path)
            is_fetch_running_callback: Callback to check if fetch is running
        """
        self.db_manager = db_manager
        self.page = page
        self.on_update_available = on_update_available
        self.is_fetch_running_callback = is_fetch_running_callback
        self._update_task: Optional[asyncio.Task] = None
        self._running = False
        self._current_download: Optional[dict] = None
        self._updates_dir = Path(USER_DATA_DIR) / UPDATES_DIR_NAME
        self._updates_dir.mkdir(parents=True, exist_ok=True)
    
    async def start(self):
        """Start background update checker."""
        if self._running:
            logger.warning("Update service already running")
            return
        
        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("Update service started")
    
    async def stop(self):
        """Stop background update checker."""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        logger.info("Update service stopped")
    
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
            
            # Download update
            download_path = await self.download_update(download_url, latest_version, checksum, file_size)
            if download_path:
                self._current_download = {
                    'version': latest_version,
                    'download_path': download_path,
                    'update_info': update_info
                }
                
                # Notify via callback
                if self.on_update_available:
                    self.on_update_available(latest_version, download_path)
                
                return self._current_download
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking for updates: {e}", exc_info=True)
            return None
    
    async def download_update(
        self,
        url: str,
        version: str,
        expected_checksum: Optional[str] = None,
        expected_size: Optional[int] = None
    ) -> Optional[Path]:
        """
        Download update file.
        
        Args:
            url: Download URL
            version: Version string
            expected_checksum: Expected SHA256 checksum
            expected_size: Expected file size in bytes
        
        Returns:
            Path to downloaded file or None if failed
        """
        if not REQUESTS_AVAILABLE:
            logger.error("requests library not available for downloading updates")
            return None
        
        try:
            # Determine file extension based on platform
            system = platform.system()
            if system == "Windows":
                ext = ".exe"
            elif system == "Darwin":
                ext = ".dmg"
            else:
                ext = ""
            
            filename = f"TelegramUserTracking-v{version}{ext}"
            download_path = self._updates_dir / filename
            
            # Skip if already downloaded and verified
            if download_path.exists():
                if expected_checksum:
                    if self.verify_checksum(download_path, expected_checksum):
                        logger.info(f"Update already downloaded: {download_path}")
                        return download_path
                    else:
                        # Corrupted file, delete and re-download
                        logger.warning(f"Corrupted download detected, re-downloading: {download_path}")
                        download_path.unlink()
            
            logger.info(f"Downloading update from {url}")
            
            # Download file
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Check file size if provided
            if expected_size:
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) != expected_size:
                    logger.warning(
                        f"File size mismatch: expected {expected_size}, got {content_length}"
                    )
            
            # Write file
            total_size = 0
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
            
            logger.info(f"Downloaded {total_size} bytes to {download_path}")
            
            # Verify checksum if provided
            if expected_checksum:
                if not self.verify_checksum(download_path, expected_checksum):
                    logger.error("Checksum verification failed")
                    download_path.unlink()
                    return None
                logger.info("Checksum verification passed")
            
            return download_path
            
        except Exception as e:
            logger.error(f"Error downloading update: {e}", exc_info=True)
            return None
    
    def verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """
        Verify file SHA256 checksum.
        
        Args:
            file_path: Path to file
            expected_checksum: Expected SHA256 checksum (hex string)
        
        Returns:
            True if checksum matches, False otherwise
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)
            
            actual_checksum = sha256_hash.hexdigest()
            matches = actual_checksum.lower() == expected_checksum.lower()
            
            if not matches:
                logger.warning(
                    f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}"
                )
            
            return matches
        except Exception as e:
            logger.error(f"Error verifying checksum: {e}")
            return False
    
    def is_fetch_running(self) -> bool:
        """
        Check if fetch operation is currently running.
        
        Returns:
            True if fetch is running, False otherwise
        """
        if self.is_fetch_running_callback:
            try:
                return self.is_fetch_running_callback()
            except Exception as e:
                logger.error(f"Error checking fetch state: {e}")
                return False
        return False
    
    def install_update(self, file_path: Optional[Path] = None) -> bool:
        """
        Launch installer for downloaded update.
        
        Args:
            file_path: Path to installer file (uses current download if None)
        
        Returns:
            True if installer launched successfully, False otherwise
        """
        # Check if fetch is running
        if self.is_fetch_running():
            logger.warning("Cannot install update while fetch is in progress")
            if self.page:
                from ui.components.toast import toast, ToastType
                toast.show(
                    "Cannot install update while fetch is in progress",
                    ToastType.WARNING,
                    duration=4000
                )
            return False
        
        try:
            if file_path is None:
                if not self._current_download:
                    logger.error("No current download available")
                    return False
                file_path = Path(self._current_download['download_path'])
            
            if not file_path.exists():
                logger.error(f"Update file not found: {file_path}")
                return False
            
            system = platform.system()
            logger.info(f"Installing update: {file_path} on {system}")
            
            # Get user email for tracking
            user_email = auth_service.get_user_email()
            version = self._current_download.get('version') if self._current_download else "unknown"
            
            # Platform-specific installation
            if system == "Windows":
                # Launch .exe installer
                subprocess.Popen([str(file_path)], shell=True)
            elif system == "Darwin":  # macOS
                # For .dmg, mount and copy .app to Applications
                # For .app, copy to Applications
                if file_path.suffix == '.dmg':
                    subprocess.Popen(['open', str(file_path)])
                else:
                    # Assume .app bundle
                    subprocess.Popen(['open', str(file_path)])
            else:  # Linux
                # Make executable and replace current binary
                file_path.chmod(0o755)
                # Note: Actual replacement should be handled by installer script
                subprocess.Popen([str(file_path)])
            
            # Record installation in database
            if user_email:
                self.db_manager.record_update_installation(
                    user_email=user_email,
                    version=version,
                    download_path=str(file_path)
                )
            
            logger.info(f"Update installer launched: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error installing update: {e}", exc_info=True)
            return False
    
    def get_current_download(self) -> Optional[dict]:
        """Get current download info."""
        return self._current_download

