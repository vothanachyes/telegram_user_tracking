"""
Admin dashboard page with analytics.
"""

import flet as ft
from admin.services.admin_analytics_service import admin_analytics_service
from admin.ui.components.stats_cards import StatsCard


class AdminDashboardPage(ft.Container):
    """Admin dashboard page."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    
    def __init__(self):
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
                    self.stats_cards,
                ],
                spacing=10,
                expand=True,
            ),
            padding=ft.padding.all(20),
            bgcolor=self.BG_COLOR,
            expand=True,
        )
        
        # Load initial stats
        self._refresh_stats()
    
    def _refresh_stats(self, e: ft.ControlEvent = None):
        """Refresh dashboard statistics."""
        try:
            user_stats = admin_analytics_service.get_user_stats()
            license_stats = admin_analytics_service.get_license_stats()
            device_stats = admin_analytics_service.get_device_stats()
            
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
            # Only update if control is on the page
            if hasattr(self, 'page') and self.page:
                self.update()
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error refreshing dashboard stats: {e}", exc_info=True)

