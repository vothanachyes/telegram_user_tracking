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
        
        try:
            page.window.width = DEFAULT_WINDOW_WIDTH
            page.window.height = DEFAULT_WINDOW_HEIGHT
            page.window.min_width = MIN_WINDOW_WIDTH
            page.window.min_height = MIN_WINDOW_HEIGHT
        except AttributeError:
            pass
        
        page.padding = 0
        page.bgcolor = theme_manager.background_color
        
        from ui.components.toast import toast
        
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

