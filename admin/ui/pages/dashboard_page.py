"""
Admin dashboard page with analytics.
"""

import flet as ft
import asyncio
import logging
from admin.services.admin_analytics_service import admin_analytics_service
from admin.ui.components.stats_cards import StatsCard
from services.page_cache_service import page_cache_service
from ui.components.loading_indicator import LoadingIndicator

logger = logging.getLogger(__name__)


class AdminDashboardPage(ft.Container):
    """Admin dashboard page."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    
    def __init__(self):
        self.page = None
        self.is_loading = True
        
        # Show loading indicator initially
        loading_indicator = LoadingIndicator.create(message="Loading dashboard...")
        
        self.stats_cards = ft.Row(
            controls=[],
            spacing=15,
            wrap=True,
        )
        self.refresh_button = ft.IconButton(
            icon=ft.Icons.REFRESH,
            icon_color=self.TEXT_COLOR,
            tooltip="Refresh",
            on_click=self._refresh_stats,
        )
        
        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Dashboard",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color=self.TEXT_COLOR,
                            ),
                            self.refresh_button,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=20, color="transparent"),
                    loading_indicator,  # Will be replaced with stats_cards
                ],
                spacing=10,
                expand=True,
            ),
            padding=ft.padding.all(20),
            bgcolor=self.BG_COLOR,
            expand=True,
        )
        
        self.loading_indicator = loading_indicator
    
    def set_page(self, page: ft.Page):
        """Set page reference and load stats asynchronously."""
        self.page = page
        
        # Load stats asynchronously
        if page and hasattr(page, 'run_task'):
            page.run_task(self._load_stats_async)
        else:
            asyncio.create_task(self._load_stats_async())
    
    async def _load_stats_async(self):
        """Load dashboard statistics asynchronously."""
        try:
            # Check cache
            cache_key = page_cache_service.generate_key("admin_dashboard")
            cached_stats = page_cache_service.get(cache_key)
            
            if cached_stats:
                user_stats = cached_stats.get("user_stats")
                license_stats = cached_stats.get("license_stats")
                device_stats = cached_stats.get("device_stats")
            else:
                # Load from service (may be slow - Firebase API calls)
                user_stats = admin_analytics_service.get_user_stats()
                license_stats = admin_analytics_service.get_license_stats()
                device_stats = admin_analytics_service.get_device_stats()
                
                # Cache for 60 seconds
                if page_cache_service.is_enabled():
                    page_cache_service.set(cache_key, {
                        "user_stats": user_stats,
                        "license_stats": license_stats,
                        "device_stats": device_stats
                    }, ttl=60)
            
            # Create stats cards
            cards = [
                StatsCard(
                    title="Total Users",
                    value=str(user_stats.get("total", 0)),
                    icon=ft.Icons.PEOPLE,
                ),
                StatsCard(
                    title="Active Users",
                    value=str(user_stats.get("active", 0)),
                    icon=ft.Icons.CHECK_CIRCLE,
                ),
                StatsCard(
                    title="New Users (30d)",
                    value=str(user_stats.get("new_last_30_days", 0)),
                    icon=ft.Icons.PERSON_ADD,
                ),
                StatsCard(
                    title="Total Licenses",
                    value=str(license_stats.get("total", 0)),
                    icon=ft.Icons.CARD_MEMBERSHIP,
                ),
                StatsCard(
                    title="Active Licenses",
                    value=str(license_stats.get("active", 0)),
                    icon=ft.Icons.VERIFIED,
                ),
                StatsCard(
                    title="Total Devices",
                    value=str(device_stats.get("total", 0)),
                    icon=ft.Icons.DEVICES,
                ),
            ]
            
            self.stats_cards.controls = cards
            
            # Replace loading indicator with stats cards
            self.content.controls[2] = self.stats_cards
            
            self.is_loading = False
            
            if self.page:
                self.page.update()
            
        except Exception as e:
            logger.error(f"Error loading dashboard stats: {e}", exc_info=True)
            self.is_loading = False
            if self.page:
                self.page.update()
    
    def _refresh_stats(self, e: ft.ControlEvent = None):
        """Refresh dashboard statistics (triggers async load)."""
        # Invalidate cache
        page_cache_service.invalidate("page:admin_dashboard")
        
        # Reload stats asynchronously
        if self.page and hasattr(self.page, 'run_task'):
            self.page.run_task(self._load_stats_async)
        else:
            asyncio.create_task(self._load_stats_async())

