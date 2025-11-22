"""
Dashboard page with statistics and activity feed.
"""

import flet as ft
import asyncio
from typing import Optional, List
from datetime import datetime, timedelta
from ui.theme import theme_manager
from ui.components import StatCard
from database.db_manager import DatabaseManager
from utils.constants import format_bytes
from ui.pages.dashboard.sample_data import SampleDataGenerator
from ui.pages.dashboard.components.group_selector import GroupSelectorComponent
from ui.pages.dashboard.components.date_range_selector import DateRangeSelectorComponent
from ui.pages.dashboard.components.active_users_list import ActiveUsersListComponent
from ui.pages.dashboard.components.recent_messages import RecentMessagesComponent


class DashboardPage(ft.Container):
    """Dashboard page with statistics."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.page: Optional[ft.Page] = None
        self.sample_data_generator = SampleDataGenerator(db_manager)
        
        # Generate sample data if database is empty
        self.sample_data_generator.ensure_sample_data()
        self.is_sample_data = self.sample_data_generator.is_sample_data()
        
        # Get groups and set default selected groups
        groups = self.db_manager.get_all_groups()
        self.selected_group_ids = [groups[0].group_id] if groups else []
        self.selected_group_names = [groups[0].group_name] if groups else []
        
        # Initialize date range (default: 1 month - last 30 days)
        today = datetime.now()
        one_month_ago = today - timedelta(days=30)
        self.start_date = one_month_ago.replace(hour=0, minute=0, second=0, microsecond=0)
        self.end_date = today
        
        # Create components
        self.group_selector = GroupSelectorComponent(
            groups=groups,
            selected_group_ids=self.selected_group_ids,
            selected_group_names=self.selected_group_names,
            on_selection_changed=self._on_groups_changed
        )
        
        self.date_range_selector = DateRangeSelectorComponent(
            start_date=self.start_date,
            end_date=self.end_date,
            on_date_range_changed=self._on_date_range_changed
        )
        
        self.active_users_component = ActiveUsersListComponent()
        self.recent_messages_component = RecentMessagesComponent()
        
        # Build components once and store references
        self.group_selector_widget = self.group_selector.build()
        self.date_range_selector_widget = self.date_range_selector.build()
        
        # Create stat cards
        stats = self.db_manager.get_dashboard_stats(
            group_ids=self.selected_group_ids if self.selected_group_ids else None,
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        # Wrap stat cards in container with padding to prevent edge clipping on hover
        # Make stat cards bigger and responsive
        stat_cards_row = ft.Row([
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
        ], spacing=theme_manager.spacing_md, wrap=True, run_spacing=theme_manager.spacing_md)
        
        self.stat_cards = ft.Container(
            content=stat_cards_row,
            clip_behavior=ft.ClipBehavior.NONE,
            padding=ft.padding.all(5)  # Add padding to allow scale effect without clipping
        )
        
        # Monthly stats
        self.monthly_stats = self._create_modern_card(
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
        self.recent_activity = self._create_modern_card(
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
                self.recent_messages_component.build(
                    self.db_manager.get_messages(
                        group_ids=self.selected_group_ids if self.selected_group_ids else None,
                        start_date=self.start_date,
                        end_date=self.end_date,
                        limit=10
                    ),
                    self.db_manager.get_user_by_id
                )
            ], spacing=theme_manager.spacing_sm)
        )
        
        # Top active users card
        self.active_users_card = self._create_modern_card(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        theme_manager.t("top_active_users"),
                        size=theme_manager.font_size_section_title,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.MORE_VERT,
                        tooltip=theme_manager.t("more_options"),
                        on_click=self._navigate_to_reports
                    ),
                ]),
                ft.Divider(),
                ft.Container(
                    content=self.active_users_component.build(),
                    height=450,
                    width=None,
                    padding=ft.padding.all(5),
                    clip_behavior=ft.ClipBehavior.NONE
                ),
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
                    self.group_selector_widget,
                    self._create_sample_data_badge() if self.is_sample_data else ft.Container(),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=10),
                ft.Container(height=10),
                self.date_range_selector_widget,
                self.stat_cards,
                ft.Container(height=theme_manager.spacing_md),
                ft.Row([
                    self.monthly_stats,
                    self.recent_activity,
                ], spacing=theme_manager.spacing_md, expand=True),
                ft.Container(height=theme_manager.spacing_md),
                self.active_users_card,
            ], scroll=ft.ScrollMode.AUTO, spacing=theme_manager.spacing_md),
            padding=theme_manager.padding_lg,
            expand=True
        )
        
        # Load initial data
        self._refresh_active_users()
        self._animation_initialized = False
    
    def _create_modern_card(self, content: ft.Control) -> ft.Container:
        """Create a modernized card with shadows, animations, and hover effects."""
        default_shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=8,
            color=ft.Colors.BLACK12 if not theme_manager.is_dark else ft.Colors.BLACK38,
            offset=ft.Offset(0, 2),
        )
        
        hover_shadow = ft.BoxShadow(
            spread_radius=2,
            blur_radius=15,
            color=ft.Colors.BLACK26 if not theme_manager.is_dark else ft.Colors.BLACK54,
            offset=ft.Offset(0, 4),
        )
        
        card = ft.Container(
            content=content,
            bgcolor=theme_manager.surface_color,
            border=ft.border.all(1, theme_manager.border_color),
            border_radius=theme_manager.corner_radius,
            padding=theme_manager.padding_md,
            shadow=[default_shadow],
            animate=ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT),
            animate_opacity=ft.Animation(duration=400, curve=ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT),
            opacity=0,
            scale=1.0,
            on_hover=lambda e: self._on_card_hover(e, card, default_shadow, hover_shadow)
        )
        
        return card
    
    def _on_card_hover(self, e: ft.ControlEvent, card: ft.Container, default_shadow: ft.BoxShadow, hover_shadow: ft.BoxShadow):
        """Handle card hover events."""
        is_hovered = e.data == "true"
        
        if is_hovered:
            card.scale = 1.01
            card.shadow = [hover_shadow]
        else:
            card.scale = 1.0
            card.shadow = [default_shadow]
        
        if self.page:
            self.page.update()
        else:
            card.update()
    
    async def _animate_dashboard(self):
        """Animate dashboard components with staggered delays."""
        if self._animation_initialized:
            return
        
        self._animation_initialized = True
        
        for idx, card in enumerate(self.stat_cards.content.controls):
            await asyncio.sleep(0.1 * idx)
            if hasattr(card, '_animate_in'):
                card._animate_in()
        
        await asyncio.sleep(0.1)
        self.monthly_stats.opacity = 1
        if self.page:
            self.page.update()
        
        await asyncio.sleep(0.1)
        self.recent_activity.opacity = 1
        if self.page:
            self.page.update()
        
        await asyncio.sleep(0.1)
        self.active_users_card.opacity = 1
        if self.page:
            self.page.update()
    
    def set_page(self, page: ft.Page):
        """Set page reference and trigger animations."""
        self.page = page
        
        # Set page reference for components
        self.group_selector.set_page(page)
        self.date_range_selector.set_page(page)
        self.active_users_component.set_page(page)
        self.recent_messages_component.set_page(page)
        
        # Set page reference for stat cards
        for card in self.stat_cards.content.controls:
            card.page = page
        
        # Trigger animations
        if page and hasattr(page, 'run_task'):
            async def start_animations():
                await asyncio.sleep(0.3)
                await self._animate_dashboard()
            page.run_task(start_animations)
        elif page:
            async def start_animations():
                await asyncio.sleep(0.3)
                await self._animate_dashboard()
            asyncio.create_task(start_animations())
    
    def _on_groups_changed(self, group_ids: List[int], group_names: List[str]):
        """Handle group selection change."""
        self.selected_group_ids = group_ids
        self.selected_group_names = group_names
        self._refresh_all_data()
    
    def _on_date_range_changed(self, start_date: datetime, end_date: datetime):
        """Handle date range change."""
        self.start_date = start_date
        self.end_date = end_date
        self._refresh_all_data()
    
    def _refresh_data(self, e):
        """Refresh dashboard data."""
        self._refresh_all_data()
        self.update()
    
    def _refresh_all_data(self):
        """Refresh all dashboard data based on selected groups and date range."""
        # Update stats
        stats = self.db_manager.get_dashboard_stats(
            group_ids=self.selected_group_ids if self.selected_group_ids else None,
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        # Update stat cards (access through Container -> Row -> controls)
        cards = self.stat_cards.content.controls
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
        activity_content.controls[2] = self.recent_messages_component.build(
            self.db_manager.get_messages(
                group_ids=self.selected_group_ids if self.selected_group_ids else None,
                start_date=self.start_date,
                end_date=self.end_date,
                limit=10
            ),
            self.db_manager.get_user_by_id
        )
        
        # Update active users
        self._refresh_active_users()
        
        # Update more options button
        if hasattr(self, 'active_users_card'):
            content = self.active_users_card.content
            more_btn = content.controls[0].controls[2]
            more_btn.disabled = not self.selected_group_ids
    
    def _refresh_active_users(self):
        """Refresh active users list."""
        if not self.selected_group_ids:
            self.active_users_component.clear()
            return
        
        users = self.db_manager.get_top_active_users_by_group(
            group_ids=self.selected_group_ids,
            start_date=self.start_date,
            end_date=self.end_date,
            limit=10
        )
        
        self.active_users_component.update_users(users)
    
    def _navigate_to_reports(self, e):
        """Navigate to reports page."""
        if self.page and hasattr(self.page, 'data') and self.page.data:
            router = self.page.data.get('router')
            if router:
                router.navigate_to("reports")
    
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
