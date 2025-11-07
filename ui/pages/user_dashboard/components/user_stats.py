"""
User statistics display component.
"""

import flet as ft
from typing import Dict, Optional
from ui.theme import theme_manager


class UserStatsComponent:
    """User statistics display component."""
    
    def __init__(self):
        self.stats_container = ft.Container(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("select_user_to_view_statistics"),
                    size=16,
                    color=theme_manager.text_secondary_color,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
            padding=20,
            expand=True
        )
    
    def build(self) -> ft.Container:
        """Build the stats component."""
        return ft.Container(
            content=self.stats_container,
            padding=10,
            expand=True
        )
    
    def update_stats(self, stats: Dict):
        """Update statistics display."""
        stats_cards = [
            self._create_stat_card(
                theme_manager.t("total_messages"),
                str(stats.get('total_messages', 0)),
                ft.Icons.MESSAGE
            ),
            self._create_stat_card(
                theme_manager.t("total_reactions"),
                str(stats.get('total_reactions', 0)),
                ft.Icons.FAVORITE
            ),
            self._create_stat_card(
                theme_manager.t("total_stickers"),
                str(stats.get('total_stickers', 0)),
                ft.Icons.EMOJI_EMOTIONS
            ),
            self._create_stat_card(
                theme_manager.t("total_videos"),
                str(stats.get('total_videos', 0)),
                ft.Icons.VIDEOCAM
            ),
            self._create_stat_card(
                theme_manager.t("total_photos"),
                str(stats.get('total_photos', 0)),
                ft.Icons.PHOTO
            ),
            self._create_stat_card(
                theme_manager.t("total_links"),
                str(stats.get('total_links', 0)),
                ft.Icons.LINK
            ),
            self._create_stat_card(
                theme_manager.t("total_documents"),
                str(stats.get('total_documents', 0)),
                ft.Icons.DESCRIPTION
            ),
            self._create_stat_card(
                theme_manager.t("total_audio"),
                str(stats.get('total_audio', 0)),
                ft.Icons.AUDIOTRACK
            ),
        ]
        
        self.stats_container.content = ft.Column([
            ft.Text(
                theme_manager.t("user_activity_statistics"),
                size=20,
                weight=ft.FontWeight.BOLD
            ),
            ft.Divider(),
            ft.Row(
                stats_cards[:4],
                spacing=15,
                wrap=True
            ),
            ft.Row(
                stats_cards[4:],
                spacing=15,
                wrap=True
            ),
        ], spacing=15, expand=True)
    
    def show_empty_state(self):
        """Show empty state when no user is selected."""
        self.stats_container.content = ft.Column([
            ft.Text(
                theme_manager.t("select_user_to_view_statistics"),
                size=16,
                color=theme_manager.text_secondary_color,
                text_align=ft.TextAlign.CENTER
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
    
    def _create_stat_card(self, label: str, value: str, icon: str) -> ft.Container:
        """Create a statistics card."""
        return theme_manager.create_card(
            content=ft.Column([
                ft.Icon(icon, size=32, color=theme_manager.primary_color),
                ft.Text(
                    value,
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=theme_manager.primary_color
                ),
                ft.Text(
                    label,
                    size=12,
                    color=theme_manager.text_secondary_color
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            width=150
        )

