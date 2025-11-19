"""
Page configuration utilities.
"""

import flet as ft
import platform
from pathlib import Path
from ui.theme import theme_manager
from config.settings import settings
from utils.constants import (
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT
)


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
            project_root = Path(__file__).parent.parent.parent
            system = platform.system()
            
            if system == 'Windows':
                icon_path = project_root / 'assets' / 'icons' / 'win' / 'icon.ico'
                if icon_path.exists():
                    try:
                        page.window.icon = str(icon_path)
                    except AttributeError:
                        pass  # Window icon setting not available
            elif system == 'Darwin':  # macOS
                icon_path = project_root / 'assets' / 'icons' / 'mac' / 'icon.icns'
                if icon_path.exists():
                    try:
                        page.window.icon = str(icon_path)
                    except AttributeError:
                        pass  # Window icon setting not available
            elif system == 'Linux':
                icon_path = project_root / 'assets' / 'icons' / 'linux' / 'icon.png'
                if icon_path.exists():
                    try:
                        page.window.icon = str(icon_path)
                    except AttributeError:
                        pass  # Window icon setting not available
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

