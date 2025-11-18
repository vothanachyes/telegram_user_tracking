"""
Top header component with greeting and About navigation.
"""

import flet as ft
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from ui.theme import theme_manager
from services.auth_service import auth_service
from services.fetch_state_manager import fetch_state_manager


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
        
        # Fetch indicator (shows when fetching)
        # Use secondary color (which is a Color constant) with opacity for dark mode,
        # or use a semi-transparent blue for light mode
        if theme_manager.is_dark:
            # Dark mode: use secondary color (sky blue) with opacity
            primary_color_with_opacity = ft.Colors.with_opacity(0.2, ft.Colors.CYAN_700)
        else:
            # Light mode: use primary-like color with opacity
            primary_color_with_opacity = ft.Colors.with_opacity(0.2, ft.Colors.BLUE_700)
        
        self.fetch_indicator = ft.Container(
            content=ft.Row([
                ft.ProgressRing(width=12, height=12, stroke_width=2),
                ft.Text(
                    "",
                    size=12,
                    color=theme_manager.text_color,
                    weight=ft.FontWeight.BOLD
                )
            ], spacing=5, tight=True),
            visible=False,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=theme_manager.corner_radius,
            bgcolor=primary_color_with_opacity,
            on_click=lambda e: self.on_navigate("fetch_data"),
            tooltip="Click to view fetch progress"
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
            self.fetch_indicator,
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
    
    def update_fetch_indicator(self):
        """Update fetch indicator visibility and text."""
        if fetch_state_manager.is_fetching:
            count = fetch_state_manager.processed_count
            indicator_text = self.fetch_indicator.content.controls[1]
            indicator_text.value = theme_manager.t("fetching_indicator").format(count=count) or f"Fetching: {count} messages"
            self.fetch_indicator.visible = True
        else:
            self.fetch_indicator.visible = False
        
        if hasattr(self, 'page') and self.page:
            try:
                self.page.update()
            except:
                pass
    
    async def start_fetch_indicator_updates(self):
        """Start periodic updates for fetch indicator (async coroutine for page.run_task)."""
        # Check if already running using a flag
        if hasattr(self, '_fetch_updates_running') and self._fetch_updates_running:
            return  # Already running
        
        self._fetch_updates_running = True
        
        try:
            # Periodically update fetch indicator
            while True:
                try:
                    await asyncio.sleep(0.5)  # Update every 0.5 seconds
                    if hasattr(self, 'page') and self.page:
                        self.update_fetch_indicator()
                except asyncio.CancelledError:
                    break
                except Exception:
                    pass
        finally:
            self._fetch_updates_running = False

