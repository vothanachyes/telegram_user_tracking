"""
UI components for groups page.
"""

import flet as ft
from typing import List, Optional, Callable
from database.models.telegram import TelegramGroup
from ui.theme import theme_manager
from datetime import datetime


class GroupsComponents:
    """UI components for groups page."""
    
    def __init__(
        self,
        on_group_click: Optional[Callable[[TelegramGroup], None]] = None
    ):
        self.on_group_click = on_group_click
    
    def build_group_list(self, groups: List[TelegramGroup]) -> ft.Column:
        """Build group list/cards."""
        if not groups:
            return self._build_empty_state()
        
        group_cards = []
        for group in groups:
            card = self._build_group_card(group)
            group_cards.append(card)
        
        return ft.Column(group_cards, spacing=10, scroll=ft.ScrollMode.AUTO)
    
    def _build_group_card(self, group: TelegramGroup) -> ft.Container:
        """Build a single group card."""
        # Format last fetch date
        last_fetch_text = "Never"
        if group.last_fetch_date:
            last_fetch_text = group.last_fetch_date.strftime("%Y-%m-%d %H:%M")
        
        # Group photo or default icon
        photo_content = ft.Icon(
            ft.Icons.GROUP,
            size=48,
            color=theme_manager.primary_color
        )
        
        if group.group_photo_path:
            try:
                photo_content = ft.Image(
                    src=group.group_photo_path,
                    width=48,
                    height=48,
                    fit=ft.ImageFit.COVER,
                    border_radius=theme_manager.corner_radius
                )
            except:
                pass
        
        def on_click(e):
            if self.on_group_click:
                self.on_group_click(group)
        
        return theme_manager.create_card(
            content=ft.Row([
                ft.Container(
                    content=photo_content,
                    width=48,
                    height=48,
                    border_radius=theme_manager.corner_radius,
                    bgcolor=theme_manager.surface_color,
                    padding=5
                ),
                ft.Column([
                    ft.Text(
                        group.group_name,
                        size=16,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        f"ID: {group.group_id}",
                        size=12,
                        color=theme_manager.text_secondary_color
                    ),
                    ft.Text(
                        f"Last fetch: {last_fetch_text}",
                        size=12,
                        color=theme_manager.text_secondary_color
                    ),
                    ft.Text(
                        f"Messages: {group.total_messages}",
                        size=12,
                        color=theme_manager.text_secondary_color
                    ),
                ], spacing=5, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=theme_manager.text_secondary_color)
            ], spacing=15),
            on_click=on_click,
            ink=True
        )
    
    def _build_empty_state(self) -> ft.Container:
        """Build empty state when no groups."""
        return ft.Container(
            content=ft.Column([
                ft.Icon(
                    ft.Icons.GROUP_OUTLINED,
                    size=64,
                    color=theme_manager.text_secondary_color
                ),
                ft.Text(
                    "No groups yet",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=theme_manager.text_secondary_color
                ),
                ft.Text(
                    "Add a group to get started",
                    size=14,
                    color=theme_manager.text_secondary_color
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            alignment=ft.alignment.center,
            padding=40
        )

