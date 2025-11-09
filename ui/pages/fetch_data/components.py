"""
UI components for fetch data page.
"""

import flet as ft
from typing import Optional
from datetime import datetime
from ui.theme import theme_manager
from database.models import Message, TelegramUser
from utils.helpers import format_datetime


class MessageCard(ft.Container):
    """Animated message card component."""
    
    def __init__(
        self,
        message: Optional[Message] = None,
        user: Optional[TelegramUser] = None,
        error: Optional[str] = None,
        position: str = "center",  # "left", "center", "right"
        on_animation_complete: Optional[callable] = None
    ):
        self.message = message
        self.user = user
        self.error = error
        self.position = position
        self.on_animation_complete = on_animation_complete
        
        # Calculate size and position based on position
        width, height, opacity, scale = self._get_position_props()
        
        super().__init__(
            content=self._build_content(),
            width=width,
            height=height,
            opacity=opacity,
            scale=scale,
            animate=ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT),
            border_radius=theme_manager.corner_radius,
            padding=theme_manager.padding_md,
            bgcolor=theme_manager.surface_color,
            border=ft.border.all(1, theme_manager.border_color),
        )
    
    def _get_position_props(self) -> tuple:
        """Get width, height, opacity, and scale based on position."""
        if self.position == "center":
            return 500, 300, 1.0, 1.0
        elif self.position == "left":
            return 300, 200, 0.6, 0.8
        elif self.position == "right":
            return 300, 200, 0.6, 0.8
        else:
            return 300, 200, 0.0, 0.8
    
    def _build_content(self) -> ft.Column:
        """Build card content."""
        if self.error:
            return self._build_error_content()
        elif self.message:
            return self._build_message_content()
        else:
            return self._build_empty_content()
    
    def _build_error_content(self) -> ft.Column:
        """Build error state content."""
        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED, size=theme_manager.font_size_page_title),
                ft.Text(
                    "Error",
                    size=theme_manager.font_size_subsection_title,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED
                )
            ], spacing=theme_manager.spacing_sm),
            ft.Divider(),
            ft.Text(
                self.error or "Unknown error",
                size=theme_manager.font_size_body,
                color=ft.Colors.RED,
                max_lines=3,
                overflow=ft.TextOverflow.ELLIPSIS
            )
        ], spacing=theme_manager.spacing_sm, tight=True)
    
    def _build_message_content(self) -> ft.Column:
        """Build message content."""
        # Sender profile section
        sender_name = self.user.full_name if self.user else "Unknown"
        sender_username = f"@{self.user.username}" if self.user and self.user.username else "N/A"
        sender_phone = self.user.phone if self.user and self.user.phone else "N/A"
        
        # Message preview
        message_preview = self.message.content[:100] + "..." if self.message.content and len(self.message.content) > 100 else (self.message.content or "No content")
        
        # Media indicator
        media_indicator = ""
        if self.message.has_media:
            media_type = self.message.media_type or "Media"
            media_indicator = f"📎 {media_type}"
        
        # Date
        date_str = format_datetime(self.message.date_sent, "%Y-%m-%d %H:%M") if self.message.date_sent else "N/A"
        
        return ft.Column([
            # Sender profile
            ft.Row([
                ft.Icon(ft.Icons.PERSON, size=40, color=theme_manager.primary_color),
                ft.Column([
                    ft.Text(sender_name, size=theme_manager.font_size_body, weight=ft.FontWeight.BOLD),
                    ft.Text(sender_username, size=theme_manager.font_size_small, color=theme_manager.text_secondary_color),
                    ft.Text(f"📱 {sender_phone}", size=theme_manager.font_size_small, color=theme_manager.text_secondary_color),
                ], spacing=theme_manager.spacing_xs, tight=True)
            ], spacing=theme_manager.spacing_sm),
            ft.Divider(),
            # Message content
            ft.Text(
                message_preview,
                size=theme_manager.font_size_body,
                max_lines=4,
                overflow=ft.TextOverflow.ELLIPSIS
            ),
            # Media and date
            ft.Row([
                ft.Text(media_indicator, size=theme_manager.font_size_small, color=theme_manager.text_secondary_color) if media_indicator else ft.Container(),
                ft.Container(expand=True),
                ft.Text(date_str, size=theme_manager.font_size_small, color=theme_manager.text_secondary_color),
            ], spacing=theme_manager.spacing_sm)
        ], spacing=theme_manager.spacing_sm, tight=True, scroll=ft.ScrollMode.AUTO)
    
    def _build_empty_content(self) -> ft.Column:
        """Build empty state content."""
        return ft.Column([
            ft.Text(
                "Waiting for messages...",
                size=theme_manager.font_size_body,
                color=theme_manager.text_secondary_color,
                italic=True
            )
        ], spacing=theme_manager.spacing_sm, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    def update_position(self, new_position: str):
        """Update card position with animation."""
        self.position = new_position
        width, height, opacity, scale = self._get_position_props()
        self.width = width
        self.height = height
        self.opacity = opacity
        self.scale = scale
        self.update()
    
    def update_message(self, message: Optional[Message], user: Optional[TelegramUser] = None, error: Optional[str] = None):
        """Update card with new message data."""
        self.message = message
        self.user = user
        self.error = error
        self.content = self._build_content()
        self.update()


class SummaryTable(ft.Container):
    """Post-fetch summary table component."""
    
    def __init__(self, summary_data: list, user_map: dict):
        """
        Initialize summary table.
        
        Args:
            summary_data: List of dicts with user_id, messages, reactions, media
            user_map: Dict mapping user_id to TelegramUser for name lookup
        """
        self.summary_data = summary_data
        self.user_map = user_map
        
        super().__init__(
            content=self._build_table(),
            padding=theme_manager.padding_md,
            bgcolor=theme_manager.surface_color,
            border_radius=theme_manager.corner_radius,
            border=ft.border.all(1, theme_manager.border_color),
        )
    
    def _build_table(self) -> ft.Column:
        """Build summary table."""
        if not self.summary_data:
            return ft.Column([
                ft.Text(
                    "No data to display",
                    size=theme_manager.font_size_body,
                    color=theme_manager.text_secondary_color,
                    italic=True
                )
            ], spacing=theme_manager.spacing_sm)
        
        # Create table rows
        rows = []
        for idx, data in enumerate(self.summary_data, 1):
            user = self.user_map.get(data['user_id'])
            user_name = user.full_name if user else f"User {data['user_id']}"
            
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(idx))),
                        ft.DataCell(ft.Text(user_name)),
                        ft.DataCell(ft.Text(str(data['messages']))),
                        ft.DataCell(ft.Text(str(data['reactions']))),
                        ft.DataCell(ft.Text(str(data['media']))),
                    ]
                )
            )
        
        return ft.Column([
            ft.Text(
                "Fetch Summary",
                size=theme_manager.font_size_subsection_title,
                weight=ft.FontWeight.BOLD
            ),
            ft.Divider(),
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("No")),
                    ft.DataColumn(ft.Text("User Name")),
                    ft.DataColumn(ft.Text("Messages Sent")),
                    ft.DataColumn(ft.Text("Reactions Given")),
                    ft.DataColumn(ft.Text("Media Shared")),
                ],
                rows=rows,
                heading_row_color=theme_manager.primary_color,
                heading_text_style=ft.TextStyle(color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            )
        ], spacing=theme_manager.spacing_sm)

