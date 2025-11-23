"""
Admin sidebar navigation component.
"""

import flet as ft
from typing import Callable, Optional
from admin.utils.constants import (
    PAGE_DASHBOARD, PAGE_USERS, PAGE_LICENSES, PAGE_LICENSE_TIERS,
    PAGE_APP_UPDATES, PAGE_DEVICES, PAGE_USER_ACTIVITIES, PAGE_ACTIVITY_LOGS, 
    PAGE_BULK_OPERATIONS, PAGE_NOTIFICATIONS, PAGE_SUPPORT_TOOLS
)


class AdminSidebar(ft.Container):
    """Admin sidebar navigation."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    BORDER_COLOR = "#333333"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    HOVER_COLOR = "#2d2d2d"
    ACTIVE_COLOR = "#0078d4"
    
    def __init__(
        self,
        on_navigate: Callable[[str], None],
        on_logout: Optional[Callable[[], None]] = None,
        current_page: str = PAGE_DASHBOARD
    ):
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.current_page = current_page
        self._nav_buttons = []
        
        # Create navigation buttons
        nav_items = [
            (PAGE_DASHBOARD, ft.Icons.DASHBOARD, "Dashboard"),
            (PAGE_USERS, ft.Icons.PEOPLE, "Users"),
            (PAGE_LICENSES, ft.Icons.CARD_MEMBERSHIP, "Licenses"),
            (PAGE_LICENSE_TIERS, ft.Icons.STAR, "License Tiers"),
            (PAGE_APP_UPDATES, ft.Icons.UPDATE, "App Updates"),
            (PAGE_DEVICES, ft.Icons.DEVICES, "Devices"),
            (PAGE_USER_ACTIVITIES, ft.Icons.ANALYTICS, "User Activities"),
            (PAGE_ACTIVITY_LOGS, ft.Icons.HISTORY, "Activity Logs"),
            (PAGE_BULK_OPERATIONS, ft.Icons.BATCH_PREDICTION, "Bulk Operations"),
            (PAGE_NOTIFICATIONS, ft.Icons.NOTIFICATIONS, "Notifications"),
            (PAGE_SUPPORT_TOOLS, ft.Icons.SUPPORT_AGENT, "Support Tools"),
        ]
        
        self._nav_buttons = [
            self._create_nav_button(page_id, icon, label)
            for page_id, icon, label in nav_items
        ]
        
        # Add spacer and logout button
        self._nav_buttons.append(ft.Container(expand=True))
        if on_logout:
            self._nav_buttons.append(
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.LOGOUT,
                        icon_color=self.TEXT_SECONDARY,
                        icon_size=24,
                        tooltip="Logout",
                        on_click=lambda e: on_logout(),
                    ),
                    margin=ft.margin.only(bottom=10),
                )
            )
        
        super().__init__(
            width=200,
            bgcolor=self.BG_COLOR,
            border=ft.border.only(right=ft.BorderSide(1, self.BORDER_COLOR)),
            padding=ft.padding.only(top=20, bottom=20, left=10, right=10),
            content=ft.Column(
                controls=self._nav_buttons,
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH
            ),
        )
    
    def _create_nav_button(self, page_id: str, icon: str, label: str) -> ft.Container:
        """Create a navigation button."""
        is_active = self.current_page == page_id
        
        def make_click_handler(pid: str):
            def handler(e):
                self.on_navigate(pid)
            return handler
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        icon,
                        color=self.ACTIVE_COLOR if is_active else self.TEXT_SECONDARY,
                        size=20,
                    ),
                    ft.Text(
                        label,
                        color=self.TEXT_COLOR if is_active else self.TEXT_SECONDARY,
                        size=14,
                        weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.all(12),
            bgcolor=self.ACTIVE_COLOR if is_active else None,
            border_radius=5,
            on_click=make_click_handler(page_id),
            on_hover=lambda e: self._on_hover(e, page_id),
        )
    
    def _on_hover(self, e: ft.ControlEvent, page_id: str):
        """Handle hover effect."""
        if page_id != self.current_page:
            e.control.bgcolor = self.HOVER_COLOR if e.data == "true" else None
            e.control.update()
    
    def set_current_page(self, page_id: str):
        """Update current page highlight."""
        self.current_page = page_id
        # Only update if control is already on the page
        if hasattr(self, 'page') and self.page:
            self.update()

