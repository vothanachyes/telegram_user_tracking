"""
Top header component with greeting and About navigation.
"""

import flet as ft
from datetime import datetime
from typing import Callable, Optional
from ui.theme import theme_manager
from services.auth_service import auth_service


class TopHeader(ft.Container):
    """Top header with time-based greeting and About button."""
    
    def __init__(self, on_navigate: Callable[[str], None]):
        self.on_navigate = on_navigate
        self.greeting_text = ft.Text(
            self._get_greeting(),
            size=18,
            weight=ft.FontWeight.BOLD,
            color=theme_manager.text_color
        )
        
        # About button
        self.about_button = ft.IconButton(
            icon=ft.Icons.INFO_OUTLINE,
            tooltip=theme_manager.t("about"),
            on_click=lambda e: self.on_navigate("about"),
            icon_color=theme_manager.text_color
        )
        
        super().__init__(
            content=ft.Row([
                ft.GestureDetector(
                    content=self.greeting_text,
                    on_tap=lambda e: self.on_navigate("dashboard")
                ),
                ft.Container(expand=True),  # Spacer
                self.about_button
            ], 
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=12, vertical=12),
            bgcolor=theme_manager.surface_color,
            border=ft.border.only(bottom=ft.BorderSide(1, theme_manager.border_color)),
            height=60
        )
    
    def _get_greeting(self) -> str:
        """Get time-based greeting with user name."""
        current_user = auth_service.get_current_user()
        user_name = current_user.get("display_name", "") if current_user else ""
        if not user_name:
            user_name = current_user.get("email", "").split("@")[0] if current_user else "User"
        
        hour = datetime.now().hour
        
        if hour < 12:
            greeting = theme_manager.t("good_morning")
        elif hour < 18:
            greeting = theme_manager.t("good_afternoon")
        else:
            greeting = theme_manager.t("good_evening")
        
        return f"{greeting}, {user_name}"
    
    def update_greeting(self):
        """Update greeting text (call when time changes or user changes)."""
        self.greeting_text.value = self._get_greeting()
        if hasattr(self, 'page') and self.page:
            self.page.update()

