"""
Dashboard page with statistics and activity feed.
"""

import flet as ft
from datetime import datetime
from ui.theme import theme_manager
from ui.components import StatCard
from database.db_manager import DatabaseManager
from utils.constants import format_bytes
from ui.pages.dashboard.sample_data import SampleDataGenerator


class DashboardPage(ft.Container):
    """Dashboard page with statistics."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.sample_data_generator = SampleDataGenerator(db_manager)
        
        # Generate sample data if database is empty
        self.sample_data_generator.ensure_sample_data()
        
        # Check if we're showing sample data
        self.is_sample_data = self.sample_data_generator.is_sample_data()
        
        # Create stat cards
        stats = self.db_manager.get_dashboard_stats()
        
        self.stat_cards = ft.Row([
            StatCard(
                title=theme_manager.t("total_messages"),
                value=str(stats['total_messages']),
                icon=ft.Icons.MESSAGE,
                color=theme_manager.primary_color
            ),
            StatCard(
                title=theme_manager.t("total_users"),
                value=str(stats['total_users']),
                icon=ft.Icons.PEOPLE,
                color=ft.Colors.BLUE
            ),
            StatCard(
                title=theme_manager.t("total_groups"),
                value=str(stats['total_groups']),
                icon=ft.Icons.GROUP,
                color=ft.Colors.GREEN
            ),
            StatCard(
                title=theme_manager.t("media_storage"),
                value=format_bytes(stats['total_media_size']),
                icon=ft.Icons.STORAGE,
                color=ft.Colors.ORANGE
            ),
        ], spacing=theme_manager.spacing_md, wrap=True)
        
        # Monthly stats
        self.monthly_stats = theme_manager.create_card(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("statistics"),
                    size=theme_manager.font_size_section_title,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(),
                ft.Row([
                    ft.Column([
                        ft.Text(
                            theme_manager.t("messages_today"),
                            size=theme_manager.font_size_body,
                            color=theme_manager.text_secondary_color
                        ),
                        ft.Text(
                            str(stats['messages_today']),
                            size=theme_manager.font_size_large_number,
                            weight=ft.FontWeight.BOLD
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(),
                    ft.Column([
                        ft.Text(
                            theme_manager.t("messages_this_month"),
                            size=theme_manager.font_size_body,
                            color=theme_manager.text_secondary_color
                        ),
                        ft.Text(
                            str(stats['messages_this_month']),
                            size=theme_manager.font_size_large_number,
                            weight=ft.FontWeight.BOLD
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND, expand=True)
            ], spacing=theme_manager.spacing_sm)
        )
        
        # Recent activity
        self.recent_activity = theme_manager.create_card(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        theme_manager.t("recent_activity"),
                        size=theme_manager.font_size_section_title,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip=theme_manager.t("refresh"),
                        on_click=self._refresh_data
                    )
                ]),
                ft.Divider(),
                self._get_recent_messages()
            ], spacing=theme_manager.spacing_sm)
        )
        
        # Build layout
        super().__init__(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        theme_manager.t("dashboard"),
                        size=theme_manager.font_size_page_title,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(expand=True),
                    self._create_sample_data_badge() if self.is_sample_data else ft.Container(),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=0),
                self.stat_cards,
                theme_manager.spacing_container("lg"),
                ft.Row([
                    self.monthly_stats,
                    self.recent_activity,
                ], spacing=theme_manager.spacing_md, expand=True),
            ], scroll=ft.ScrollMode.AUTO, spacing=theme_manager.spacing_sm),
            padding=theme_manager.padding_lg,
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
    
    def _format_message_date(self, date_value) -> str:
        """Format message date, handling both string and datetime objects."""
        if not date_value:
            return ""
        
        # If it's already a string, parse it first
        if isinstance(date_value, str):
            try:
                # Try to parse ISO format datetime
                date_obj = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return date_obj.strftime("%Y-%m-%d %H:%M")
            except:
                # If parsing fails, return the string as-is (might already be formatted)
                return date_value[:16] if len(date_value) >= 16 else date_value
        
        # If it's a datetime object, format it
        if isinstance(date_value, datetime):
            return date_value.strftime("%Y-%m-%d %H:%M")
        
        return str(date_value)
    
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
    
    def _create_sample_data_badge(self) -> ft.Container:
        """Create a badge indicating sample data."""
        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.INFO_OUTLINED,
                    size=18,
                    color=ft.Colors.ORANGE_700 if theme_manager.is_dark else ft.Colors.ORANGE_600
                ),
                ft.Text(
                    "Sample Data",
                    size=theme_manager.font_size_small,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.ORANGE_700 if theme_manager.is_dark else ft.Colors.ORANGE_600
                )
            ], spacing=6, tight=True),
            bgcolor=ft.Colors.ORANGE_100 if not theme_manager.is_dark else ft.Colors.ORANGE_900,
            border=ft.border.all(1, ft.Colors.ORANGE_300 if not theme_manager.is_dark else ft.Colors.ORANGE_700),
            border_radius=20,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            tooltip="This dashboard is showing sample/demo data. Connect to Telegram to see real data."
        )

