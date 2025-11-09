"""
Top header component with greeting and About navigation.
"""

import flet as ft
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from ui.theme import theme_manager
from services.auth_service import auth_service


class TopHeader(ft.Container):
    """Top header with time-based greeting and About button."""
    
    def __init__(self, on_navigate: Callable[[str], None]):
        self.on_navigate = on_navigate
        self.greeting_text = ft.Text(
            self._get_greeting(),
            size=theme_manager.font_size_body,
            weight=ft.FontWeight.BOLD,
            color=theme_manager.text_color
        )
        
        # Avatar icon (can be replaced with image later)
        self.avatar = ft.CircleAvatar(
            content=ft.Icon(ft.Icons.PERSON, size=theme_manager.font_size_body, color=theme_manager.text_color),
            radius=16,
            bgcolor=ft.Colors.TRANSPARENT
        )
        
        # About button
        self.about_button = ft.IconButton(
            icon=ft.Icons.INFO_OUTLINE,
            tooltip=theme_manager.t("about"),
            on_click=lambda e: self.on_navigate("about"),
            icon_color=theme_manager.text_color
        )
        
        # Check for background image
        project_root = Path(__file__).parent.parent.parent
        header_bg_path = None
        for ext in ['.png', '.jpg', '.jpeg']:
            bg_path = project_root / "assets" / f"header_background{ext}"
            if bg_path.exists():
                header_bg_path = str(bg_path)
                break
        
        # Create content row
        content_row = ft.Row([
            self.avatar,
            theme_manager.spacing_container("sm"),  # Spacing between avatar and text
            ft.GestureDetector(
                content=self.greeting_text,
                on_tap=lambda e: self.on_navigate("dashboard")
            ),
            ft.Container(expand=True),  # Spacer
            self.about_button
        ], 
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Create stack for gradient + image + content
        stack_children = []
        
        # Gradient background
        gradient_container = ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[theme_manager.primary_color, theme_manager.primary_dark]
            )
        )
        stack_children.append(gradient_container)
        
        # Background image (if exists)
        if header_bg_path:
            bg_image = ft.Image(
                src=header_bg_path,
                fit=ft.ImageFit.COVER,
                opacity=0.3,
                expand=True
            )
            stack_children.append(bg_image)
        
        # Content layer
        content_layer = ft.Container(
            content=content_row,
            padding=ft.padding.symmetric(horizontal=theme_manager.padding_sm, vertical=theme_manager.spacing_sm),
        )
        stack_children.append(content_layer)
        
        super().__init__(
            content=ft.Stack(stack_children),
            border=ft.border.only(bottom=ft.BorderSide(1, theme_manager.border_color)),
            height=45
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

