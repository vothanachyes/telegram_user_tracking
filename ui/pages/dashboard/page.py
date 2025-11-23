"""
Dashboard page with statistics and activity feed.
"""

import flet as ft
import asyncio
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from ui.theme import theme_manager
from ui.components import StatCard
from ui.components.skeleton_loaders.dashboard_skeleton import DashboardSkeleton
from ui.components.skeleton_loaders.base import SkeletonRow
from database.db_manager import DatabaseManager
from database.async_query_executor import async_query_executor
from services.page_cache_service import page_cache_service
from utils.constants import format_bytes
from ui.pages.dashboard.components.group_selector import GroupSelectorComponent
from ui.components import DateRangeSelector
from ui.pages.dashboard.components.active_users_list import ActiveUsersListComponent
from ui.pages.dashboard.components.recent_messages import RecentMessagesComponent

logger = logging.getLogger(__name__)


class DashboardPage(ft.Container):
    """Dashboard page with statistics."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.page: Optional[ft.Page] = None
        
        # Initialize data state
        self.groups: List = []
        self.selected_group_ids: List[int] = []
        self.selected_group_names: List[str] = []
        self.stats: dict = {}
        self.is_loading = True
        
        # Initialize date range (default: 1 month - last 30 days)
        today = datetime.now()
        one_month_ago = today - timedelta(days=30)
        self.start_date = one_month_ago.replace(hour=0, minute=0, second=0, microsecond=0)
        self.end_date = today
        
        # Create components (will be populated with data later)
        self.group_selector = GroupSelectorComponent(
            groups=[],
            selected_group_ids=[],
            selected_group_names=[],
            on_selection_changed=self._on_groups_changed
        )
        
        self.date_range_selector = DateRangeSelector(
            start_date=self.start_date,
            end_date=self.end_date,
            on_date_range_changed=self._on_date_range_changed,
            default_range="month"
        )
        
        self.active_users_component = ActiveUsersListComponent()
        self.recent_messages_component = RecentMessagesComponent()
        
        # Build components once and store references
        self.group_selector_widget = self.group_selector.build()
        self.date_range_selector_widget = self.date_range_selector.build()
        
        # Create placeholder stat cards (will be updated with real data)
        stat_cards_row = ft.Row([
            StatCard(
                title=theme_manager.t("total_messages"),
                value="...",
                icon=ft.Icons.MESSAGE,
                color=theme_manager.primary_color
            ),
            StatCard(
                title=theme_manager.t("total_users"),
                value="...",
                icon=ft.Icons.PEOPLE,
                color=ft.Colors.BLUE
            ),
            StatCard(
                title=theme_manager.t("total_groups"),
                value="...",
                icon=ft.Icons.GROUP,
                color=ft.Colors.GREEN
            ),
            StatCard(
                title=theme_manager.t("media_storage"),
                value="...",
                icon=ft.Icons.STORAGE,
                color=ft.Colors.ORANGE
            ),
        ], spacing=theme_manager.spacing_md, wrap=True, run_spacing=theme_manager.spacing_md)
        
        self.stat_cards = ft.Container(
            content=stat_cards_row,
            clip_behavior=ft.ClipBehavior.NONE,
            padding=ft.padding.all(5)  # Add padding to allow scale effect without clipping
        )
        
        # Monthly stats (placeholder)
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
                            "...",
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
                            "...",
                            size=theme_manager.font_size_large_number,
                            weight=ft.FontWeight.BOLD
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND, expand=True)
            ], spacing=theme_manager.spacing_sm)
        )
        
        # Recent activity (placeholder)
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
                # Skeleton rows for recent messages
                ft.Column([
                    SkeletonRow(
                        height=60,
                        item_widths=[40, None, 100],
                        delay=200 + (i * 50),
                        padding=ft.padding.all(10)
                    )
                    for i in range(5)
                ], spacing=10)
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
        """Set page reference and load data asynchronously."""
        self.page = page
        
        # Set page reference for components
        self.group_selector.set_page(page)
        if hasattr(self.date_range_selector, 'set_page'):
            self.date_range_selector.set_page(page)
        self.active_users_component.set_page(page)
        self.recent_messages_component.set_page(page)
        
        # Set page reference for stat cards
        for card in self.stat_cards.content.controls:
            card.page = page
        
        # Load data asynchronously
        if page and hasattr(page, 'run_task'):
            page.run_task(self._load_data_async)
        else:
            asyncio.create_task(self._load_data_async())
    
    async def _load_data_async(self):
        """Load dashboard data asynchronously."""
        try:
            self.is_loading = True
            
            # Load groups
            cache_key_groups = page_cache_service.generate_key("dashboard", type="groups")
            groups = page_cache_service.get(cache_key_groups)
            
            if not groups:
                groups = await async_query_executor.execute(self.db_manager.get_all_groups)
                if page_cache_service.is_enabled():
                    page_cache_service.set(cache_key_groups, groups, ttl=600)  # Cache groups for 10 minutes
            
            self.groups = groups
            self.selected_group_ids = [groups[0].group_id] if groups else []
            self.selected_group_names = [groups[0].group_name] if groups else []
            
            # Rebuild group selector with loaded groups
            self.group_selector = GroupSelectorComponent(
                groups=groups,
                selected_group_ids=self.selected_group_ids,
                selected_group_names=self.selected_group_names,
                on_selection_changed=self._on_groups_changed
            )
            self.group_selector.set_page(self.page)
            self.group_selector_widget = self.group_selector.build()
            
            # Update the header row to include the new group selector
            header_row = self.content.controls[0]
            header_row.controls[2] = self.group_selector_widget
            
            # Load stats
            cache_key_stats = page_cache_service.generate_key(
                "dashboard",
                group_ids=str(self.selected_group_ids),
                start_date=self.start_date.isoformat(),
                end_date=self.end_date.isoformat()
            )
            stats = page_cache_service.get(cache_key_stats)
            
            if not stats:
                stats = await async_query_executor.execute(
                    self.db_manager.get_dashboard_stats,
                    group_ids=self.selected_group_ids if self.selected_group_ids else None,
                    start_date=self.start_date,
                    end_date=self.end_date
                )
                if page_cache_service.is_enabled():
                    page_cache_service.set(cache_key_stats, stats)
            
            self.stats = stats
            
            # Update UI with loaded data
            self._update_ui_with_data()
            
            # Load active users and recent messages
            await self._load_active_users_async()
            await self._load_recent_messages_async()
            
            self.is_loading = False
            
            # Trigger animations
            if self.page:
                await asyncio.sleep(0.3)
                await self._animate_dashboard()
                self.page.update()
                
        except Exception as e:
            logger.error(f"Error loading dashboard data: {e}", exc_info=True)
            self.is_loading = False
            if self.page:
                self.page.update()
    
    def _update_ui_with_data(self):
        """Update UI components with loaded data."""
        # Update stat cards
        cards = self.stat_cards.content.controls
        cards[0].update_value(str(self.stats['total_messages']))
        cards[1].update_value(str(self.stats['total_users']))
        cards[2].update_value(str(self.stats['total_groups']))
        cards[3].update_value(format_bytes(self.stats['total_media_size']))
        
        # Update monthly stats
        monthly_content = self.monthly_stats.content
        monthly_content.controls[2].controls[0].controls[1].value = str(self.stats['messages_today'])
        monthly_content.controls[2].controls[2].controls[1].value = str(self.stats['messages_this_month'])
    
    async def _load_active_users_async(self):
        """Load active users asynchronously."""
        if not self.selected_group_ids:
            self.active_users_component.clear()
            return
        
        users = await async_query_executor.execute(
            self.db_manager.get_top_active_users_by_group,
            group_ids=self.selected_group_ids,
            start_date=self.start_date,
            end_date=self.end_date,
            limit=10
        )
        
        self.active_users_component.update_users(users)
    
    async def _load_recent_messages_async(self):
        """Load recent messages asynchronously."""
        messages = await async_query_executor.execute(
            self.db_manager.get_messages,
            group_ids=self.selected_group_ids if self.selected_group_ids else None,
            start_date=self.start_date,
            end_date=self.end_date,
            limit=10
        )
        
        # Update recent activity
        activity_content = self.recent_activity.content
        activity_content.controls[2] = self.recent_messages_component.build(
            messages,
            self.db_manager.get_user_by_id
        )
    
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
        # Invalidate cache for this page
        page_cache_service.invalidate("page:dashboard")
        
        # Load data asynchronously
        if self.page and hasattr(self.page, 'run_task'):
            self.page.run_task(self._load_data_async)
        else:
            asyncio.create_task(self._load_data_async())
    
    def _refresh_active_users(self):
        """Refresh active users list (deprecated - use async version)."""
        # This method is kept for backward compatibility but now uses async
        if self.page and hasattr(self.page, 'run_task'):
            self.page.run_task(self._load_active_users_async)
        else:
            asyncio.create_task(self._load_active_users_async())
    
    def _navigate_to_reports(self, e):
        """Navigate to reports page."""
        if self.page and hasattr(self.page, 'data') and self.page.data:
            router = self.page.data.get('router')
            if router:
                router.navigate_to("reports")
    
