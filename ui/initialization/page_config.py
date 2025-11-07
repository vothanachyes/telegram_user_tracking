"""
Page configuration utilities.
"""

import flet as ft
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
        
        # Window size settings only apply to desktop mode
        # In web mode, these are ignored
        try:
            page.window_width = DEFAULT_WINDOW_WIDTH
            page.window_height = DEFAULT_WINDOW_HEIGHT
            page.window_min_width = MIN_WINDOW_WIDTH
            page.window_min_height = MIN_WINDOW_HEIGHT
        except AttributeError:
            # Web mode doesn't support window size settings
            pass
        
        page.padding = 0
        page.bgcolor = theme_manager.background_color
        
        # Initialize toast notification system
        from ui.components.toast import toast
        toast.initialize(page, position="top-right")
        
        # Update page to apply window settings
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
        page.bgcolor = theme_manager.background_color
        page.update()

