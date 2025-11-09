"""
Rate limit warning dialog shown before fetching.
"""

import flet as ft
from typing import Optional, Callable
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from ui.theme import theme_manager


class RateLimitWarningDialog(ft.AlertDialog):
    """Warning dialog about Telegram rate limits."""
    
    def __init__(self, db_manager: DatabaseManager, on_confirm: Optional[Callable] = None):
        self.db_manager = db_manager
        self.page: Optional[ft.Page] = None
        self.on_confirm = on_confirm
        
        super().__init__(
            modal=True,
            title=ft.Text(theme_manager.t("rate_limit_warning_title") or "Telegram Rate Limit Warning"),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE, size=24),
                        ft.Text(
                            theme_manager.t("rate_limit_warning_message") or 
                            "Warning: Quickly fetching data from Telegram or excessive use may result in your account being blocked or disabled by Telegram. We recommend using a non-official account to avoid unexpected complaints from Telegram.",
                            size=14,
                            expand=True
                        )
                    ], spacing=10)
                ], spacing=10, width=500),
                padding=10
            ),
            actions=[
                ft.ElevatedButton(
                    theme_manager.t("confirm") or "Confirm",
                    on_click=self._on_confirm,
                    bgcolor=theme_manager.primary_color,
                    color=ft.Colors.WHITE
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def set_page(self, page: ft.Page):
        """Set page reference."""
        self.page = page
    
    def _on_confirm(self, e):
        """Handle confirm button click."""
        # Update last seen timestamp
        self.db_manager._settings.update_rate_limit_warning_last_seen(datetime.now())
        
        if self.page:
            self.page.close(self)
        
        # Call on_confirm callback if provided
        if self.on_confirm:
            self.on_confirm()
    
    @staticmethod
    def should_show(db_manager: DatabaseManager) -> bool:
        """
        Check if warning should be shown (every 10 minutes).
        
        Returns:
            True if warning should be shown, False otherwise
        """
        last_seen = db_manager._settings.get_rate_limit_warning_last_seen()
        if not last_seen:
            return True
        
        # Check if 10 minutes have passed
        time_diff = datetime.now() - last_seen
        return time_diff >= timedelta(minutes=10)

