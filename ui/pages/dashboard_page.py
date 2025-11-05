"""
Dashboard page with statistics and activity feed.
"""

import flet as ft
from typing import Callable
from ui.theme import theme_manager
from ui.components import StatCard
from database.db_manager import DatabaseManager
from utils.constants import format_bytes


class DashboardPage(ft.Container):
    """Dashboard page with statistics."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
        # Create stat cards
        stats = self.db_manager.get_dashboard_stats()
        
        self.stat_cards = ft.Row([
            StatCard(
                title=theme_manager.t("total_messages"),
                value=str(stats['total_messages']),
                icon=ft.icons.MESSAGE,
                color=theme_manager.primary_color
            ),
            StatCard(
                title=theme_manager.t("total_users"),
                value=str(stats['total_users']),
                icon=ft.icons.PEOPLE,
                color=ft.colors.BLUE
            ),
            StatCard(
                title=theme_manager.t("total_groups"),
                value=str(stats['total_groups']),
                icon=ft.icons.GROUP,
                color=ft.colors.GREEN
            ),
            StatCard(
                title=theme_manager.t("media_storage"),
                value=format_bytes(stats['total_media_size']),
                icon=ft.icons.STORAGE,
                color=ft.colors.ORANGE
            ),
        ], spacing=15, wrap=True)
        
        # Monthly stats
        self.monthly_stats = theme_manager.create_card(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("statistics"),
                    size=20,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(),
                ft.Row([
                    ft.Column([
                        ft.Text(
                            theme_manager.t("messages_today"),
                            size=14,
                            color=theme_manager.text_secondary_color
                        ),
                        ft.Text(
                            str(stats['messages_today']),
                            size=32,
                            weight=ft.FontWeight.BOLD
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(),
                    ft.Column([
                        ft.Text(
                            theme_manager.t("messages_this_month"),
                            size=14,
                            color=theme_manager.text_secondary_color
                        ),
                        ft.Text(
                            str(stats['messages_this_month']),
                            size=32,
                            weight=ft.FontWeight.BOLD
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND, expand=True)
            ], spacing=10)
        )
        
        # Recent activity
        self.recent_activity = theme_manager.create_card(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        theme_manager.t("recent_activity"),
                        size=20,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.icons.REFRESH,
                        tooltip=theme_manager.t("refresh"),
                        on_click=self._refresh_data
                    )
                ]),
                ft.Divider(),
                self._get_recent_messages()
            ], spacing=10)
        )
        
        # Build layout
        super().__init__(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("dashboard"),
                    size=32,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(height=20),
                self.stat_cards,
                ft.Container(height=20),
                ft.Row([
                    self.monthly_stats,
                    self.recent_activity,
                ], spacing=15, expand=True),
            ], scroll=ft.ScrollMode.AUTO, spacing=10),
            padding=20,
            expand=True
        )
    
    def _get_recent_messages(self) -> ft.Column:
        """Get recent messages list."""
        messages = self.db_manager.get_messages(limit=10)
        
        if not messages:
            return ft.Column([
                ft.Text(
                    theme_manager.t("no_data"),
                    color=theme_manager.text_secondary_color
                )
            ])
        
        message_items = []
        for msg in messages:
            user = self.db_manager.get_user_by_id(msg.user_id)
            user_name = user.full_name if user else "Unknown"
            
            message_items.append(
                ft.ListTile(
                    leading=ft.Icon(ft.icons.MESSAGE, color=theme_manager.primary_color),
                    title=ft.Text(user_name, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(
                        msg.content[:100] + "..." if msg.content and len(msg.content) > 100 else msg.content or "",
                        max_lines=2
                    ),
                    trailing=ft.Text(
                        msg.date_sent.strftime("%Y-%m-%d %H:%M") if msg.date_sent else "",
                        size=12,
                        color=theme_manager.text_secondary_color
                    )
                )
            )
        
        return ft.Column(message_items, spacing=5, scroll=ft.ScrollMode.AUTO, height=400)
    
    def _refresh_data(self, e):
        """Refresh dashboard data."""
        stats = self.db_manager.get_dashboard_stats()
        
        # Update stat cards
        cards = self.stat_cards.controls
        cards[0].update_value(str(stats['total_messages']))
        cards[1].update_value(str(stats['total_users']))
        cards[2].update_value(str(stats['total_groups']))
        cards[3].update_value(format_bytes(stats['total_media_size']))
        
        # Update monthly stats
        monthly_content = self.monthly_stats.content
        monthly_content.controls[2].controls[0].controls[1].value = str(stats['messages_today'])
        monthly_content.controls[2].controls[2].controls[1].value = str(stats['messages_this_month'])
        
        # Update recent activity
        activity_content = self.recent_activity.content
        activity_content.controls[2] = self._get_recent_messages()
        
        self.update()

