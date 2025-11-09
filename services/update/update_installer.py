"""
Update installer for platform-specific installation logic.
"""

import logging
import platform
import subprocess
from pathlib import Path
from typing import Optional, Callable

from services.auth_service import auth_service
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class UpdateInstaller:
    """Handles platform-specific update installation."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        page=None,
        is_fetch_running_callback: Optional[Callable[[], bool]] = None
    ):
        """
        Initialize update installer.
        
        Args:
            db_manager: DatabaseManager instance
            page: Flet page instance for toast notifications
            is_fetch_running_callback: Callback to check if fetch is running
        """
        self.db_manager = db_manager
        self.page = page
        self.is_fetch_running_callback = is_fetch_running_callback
    
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
    
    def install_update(self, file_path: Path, version: str) -> bool:
        """
        Launch installer for downloaded update.
        
        Args:
            file_path: Path to installer file
            version: Version string
        
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
            if not file_path.exists():
                logger.error(f"Update file not found: {file_path}")
                return False
            
            system = platform.system()
            logger.info(f"Installing update: {file_path} on {system}")
            
            # Get user email for tracking
            user_email = auth_service.get_user_email()
            
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

