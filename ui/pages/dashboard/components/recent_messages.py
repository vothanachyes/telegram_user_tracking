"""
Recent messages component for dashboard.
"""

import flet as ft
from typing import List, Optional
from datetime import datetime
from ui.theme import theme_manager
from database.models import Message


class RecentMessagesComponent:
    """Component for displaying recent messages."""
    
    def __init__(self):
        self.page: Optional[ft.Page] = None
    
    def _format_message_date(self, date_value) -> str:
        """Format message date, handling both string and datetime objects."""
        if not date_value:
            return ""
        
        if isinstance(date_value, str):
            try:
                date_obj = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return date_obj.strftime("%Y-%m-%d %H:%M")
            except:
                return date_value[:16] if len(date_value) >= 16 else date_value
        
        if isinstance(date_value, datetime):
            return date_value.strftime("%Y-%m-%d %H:%M")
        
        return str(date_value)
    
    def build(self, messages: List[Message], get_user_by_id) -> ft.Column:
        """Build and return the recent messages component."""
        if not messages:
            return ft.Column([
                ft.Text(
                    theme_manager.t("no_data"),
                    color=theme_manager.text_secondary_color
                )
            ])
        
        message_items = []
        for msg in messages:
            user = get_user_by_id(msg.user_id)
            user_name = user.full_name if user else "Unknown"
            
            message_items.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.MESSAGE, color=theme_manager.primary_color),
                    title=ft.Text(user_name, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(
                        msg.content[:100] + "..." if msg.content and len(msg.content) > 100 else msg.content or "",
                        max_lines=2
                    ),
                    trailing=ft.Text(
                        self._format_message_date(msg.date_sent),
                        size=theme_manager.font_size_small,
                        color=theme_manager.text_secondary_color
                    )
                )
            )
        
        return ft.Column(message_items, spacing=theme_manager.spacing_xs, scroll=ft.ScrollMode.AUTO, height=400)
    
    def set_page(self, page: ft.Page):
        """Set page reference."""
        self.page = page

