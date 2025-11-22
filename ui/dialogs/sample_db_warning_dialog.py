"""
Sample database warning dialog shown when switching to sample database mode.
"""

import flet as ft
import sys
from typing import Optional, Callable
from ui.theme import theme_manager


class SampleDbWarningDialog(ft.AlertDialog):
    """Warning dialog about switching to sample database mode."""
    
    def __init__(self, on_confirm: Optional[Callable] = None, on_cancel: Optional[Callable] = None):
        self.page: Optional[ft.Page] = None
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        
        super().__init__(
            modal=True,
            title=ft.Text(theme_manager.t("sample_db_warning_title") or "Close Application?"),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE, size=24),
                        ft.Text(
                            theme_manager.t("sample_db_warning_message") or 
                            "Warning: Switching to sample database mode will disable real account login, logout functionality, and hide the Security tab. This mode is for testing data generation only. You need to close and restart the application for changes to take effect.",
                            size=14,
                            expand=True
                        )
                    ], spacing=10)
                ], spacing=10, width=500),
                padding=10
            ),
            actions=[
                ft.ElevatedButton(
                    theme_manager.t("close_app") or "Close App",
                    on_click=self._on_close_app_click,
                    bgcolor=theme_manager.primary_color,
                    color=ft.Colors.WHITE
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def set_page(self, page: ft.Page):
        """Set page reference."""
        self.page = page
    
    def _on_close_app_click(self, e):
        """Handle close app button click - closes the application cross-platform."""
        # Call on_confirm callback first if provided (to save settings)
        if self.on_confirm:
            try:
                self.on_confirm()
            except Exception as ex:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in on_confirm callback: {ex}", exc_info=True)
        
        # Close dialog first
        if self.page:
            try:
                self.page.close(self)
            except Exception:
                # Fallback if page.close() fails
                self.open = False
                if self.page:
                    self.page.update()
        
        # Close the application cross-platform
        self._close_application()
    
    def _close_application(self):
        """
        Close the application cross-platform.
        Works on Windows, macOS, and Linux.
        """
        if not self.page:
            return
        
        try:
            # Method 1: Try to close the window (cross-platform Flet method)
            if hasattr(self.page, 'window') and hasattr(self.page.window, 'close'):
                self.page.window.close()
                return
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Could not close window via page.window.close(): {e}")
        
        # Method 2: Fallback - exit the application process
        try:
            sys.exit(0)
        except Exception:
            # Final fallback - force exit
            try:
                import os
                os._exit(0)
            except Exception:
                pass

