"""
Automatic app update service that checks Firebase for new versions,
downloads updates, and tracks installations.
"""

import logging
from typing import Optional, Callable
from pathlib import Path

from database.db_manager import DatabaseManager
from services.update.update_checker import UpdateChecker
from services.update.update_downloader import UpdateDownloader
from services.update.update_installer import UpdateInstaller

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
        
        # Initialize sub-modules
        self.checker = UpdateChecker(on_update_available, is_fetch_running_callback)
        self.downloader = UpdateDownloader()
        self.installer = UpdateInstaller(db_manager, page, is_fetch_running_callback)
        
        self._current_download: Optional[dict] = None
    
    async def start(self):
        """Start background update checker."""
        await self.checker.start()
    
    async def stop(self):
        """Stop background update checker."""
        await self.checker.stop()
    
    async def check_for_updates(self) -> Optional[dict]:
        """
        Check Firebase for new app version.
        
        Returns:
            Update info dict if available, None otherwise
        """
        update_info = await self.checker.check_for_updates()
        
        if not update_info:
            return None
        
        # Download update
        download_path = await self.downloader.download_update(
            update_info['download_url'],
            update_info['version'],
            update_info.get('checksum'),
            update_info.get('file_size')
        )
        
        if download_path:
            self._current_download = {
                'version': update_info['version'],
                'download_path': download_path,
                'update_info': update_info['update_info']
            }
            
            # Notify via callback
            if self.on_update_available:
                self.on_update_available(update_info['version'], download_path)
            
            return self._current_download
        
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
        return await self.downloader.download_update(url, version, expected_checksum, expected_size)
    
    def verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """
        Verify file SHA256 checksum.
        
        Args:
            file_path: Path to file
            expected_checksum: Expected SHA256 checksum (hex string)
        
        Returns:
            True if checksum matches, False otherwise
        """
        return self.downloader.verify_checksum(file_path, expected_checksum)
    
    def is_fetch_running(self) -> bool:
        """
        Check if fetch operation is currently running.
        
        Returns:
            True if fetch is running, False otherwise
        """
        return self.installer.is_fetch_running()
    
    def install_update(self, file_path: Optional[Path] = None) -> bool:
        """
        Launch installer for downloaded update.
        
        Args:
            file_path: Path to installer file (uses current download if None)
        
        Returns:
            True if installer launched successfully, False otherwise
        """
        if file_path is None:
            if not self._current_download:
                logger.error("No current download available")
                return False
            file_path = Path(self._current_download['download_path'])
            version = self._current_download.get('version', "unknown")
        else:
            version = self._current_download.get('version', "unknown") if self._current_download else "unknown"
        
        return self.installer.install_update(file_path, version)
    
    def get_current_download(self) -> Optional[dict]:
        """Get current download info."""
        return self._current_download
