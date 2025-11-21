"""
Page configuration utilities.
"""

import flet as ft
import platform
import logging
from pathlib import Path
from ui.theme import theme_manager
from config.settings import settings
import sys
from utils.constants import (
    BASE_DIR,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT
)

# Get the correct base directory for assets (works in both dev and bundle)
def get_assets_base_dir():
    """Get the base directory for assets, handling both dev and PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        # Running from PyInstaller bundle - assets are in Resources
        if platform.system() == 'Darwin':
            # macOS: Resources is in Contents/Resources
            bundle_dir = Path(sys.executable).parent.parent.parent
            return bundle_dir / 'Contents' / 'Resources'
        else:
            # Windows/Linux: assets are in the same directory as the executable
            return Path(sys.executable).parent
    else:
        # Development: use project root
        return BASE_DIR

logger = logging.getLogger(__name__)


class PageConfig:
    """Handles page configuration and setup."""
    
    @staticmethod
    def configure_page(page: ft.Page):
        """
        Configure page settings.
        
        Args:
            page: Flet page instance to configure
        """
        page.title = settings.app_name
        page.theme_mode = theme_manager.theme_mode
        page.theme = theme_manager.get_theme()
        
        try:
            page.window.width = DEFAULT_WINDOW_WIDTH
            page.window.height = DEFAULT_WINDOW_HEIGHT
            page.window.min_width = MIN_WINDOW_WIDTH
            page.window.min_height = MIN_WINDOW_HEIGHT
            
            # Set window icon from assets/icons directory
            system = platform.system()
            assets_base = get_assets_base_dir()
            
            if system == 'Windows':
                icon_path = assets_base / 'assets' / 'icons' / 'win' / 'icon.ico'
                if icon_path.exists():
                    try:
                        icon_path_abs = icon_path.resolve()
                        page.window.icon = str(icon_path_abs)
                        logger.info(f"Window icon set: {icon_path_abs}")
                    except (AttributeError, Exception) as e:
                        logger.warning(f"Could not set window icon: {e}")
            elif system == 'Darwin':  # macOS
                icon_path = assets_base / 'assets' / 'icons' / 'mac' / 'icon.icns'
                if icon_path.exists():
                    try:
                        icon_path_abs = icon_path.resolve()
                        page.window.icon = str(icon_path_abs)
                        logger.info(f"Window icon set: {icon_path_abs}")
                    except (AttributeError, Exception) as e:
                        logger.warning(f"Could not set window icon: {e}")
                else:
                    logger.warning(f"Mac icon not found at: {icon_path}")
            elif system == 'Linux':
                icon_path = assets_base / 'assets' / 'icons' / 'linux' / 'icon.png'
                if icon_path.exists():
                    try:
                        icon_path_abs = icon_path.resolve()
                        page.window.icon = str(icon_path_abs)
                        logger.info(f"Window icon set: {icon_path_abs}")
                    except (AttributeError, Exception) as e:
                        logger.warning(f"Could not set window icon: {e}")
        except AttributeError:
            pass
        
        page.padding = 0
        # Background will be handled by gradient container in router
        # Keep background color as fallback
        page.bgcolor = theme_manager.background_color
        
        from ui.components.toast import toast
        toast.initialize(page, position="top-right")
        
        page.update()
    
    @staticmethod
    def update_theme(page: ft.Page):
        """
        Update page theme after settings change.
        
        Args:
            page: Flet page instance
        """
        page.theme_mode = theme_manager.theme_mode
        page.theme = theme_manager.get_theme()
        # Background will be handled by gradient container in router
        # Keep background color as fallback
        page.bgcolor = theme_manager.background_color
        page.update()

