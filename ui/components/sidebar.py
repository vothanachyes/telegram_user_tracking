"""
Sidebar navigation component.
"""

import flet as ft
from typing import Callable, Optional
from ui.theme import theme_manager


class Sidebar(ft.Container):
    """Sidebar navigation with icon-only buttons."""
    
    def __init__(
        self,
        on_navigate: Callable[[str], None],
        on_fetch_data: Optional[Callable[[], None]] = None,
        current_page: str = "dashboard"
    ):
        self.on_navigate = on_navigate
        self.on_fetch_data = on_fetch_data
        self.current_page = current_page
        
        super().__init__(
            width=80,
            bgcolor=theme_manager.surface_color,
            border=ft.border.only(right=ft.BorderSide(1, theme_manager.border_color)),
            padding=ft.padding.only(top=20, bottom=20),
            content=ft.Column(
                controls=[
                    self._create_nav_button("dashboard", ft.Icons.DASHBOARD, theme_manager.t("dashboard")),
                    self._create_nav_button("telegram", ft.Icons.TELEGRAM, theme_manager.t("telegram")),
                    self._create_nav_button("settings", ft.Icons.SETTINGS, theme_manager.t("settings")),
                    ft.Container(expand=True),  # Spacer
                    self._create_fetch_button(),
                    self._create_nav_button("profile", ft.Icons.PERSON, theme_manager.t("profile")),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
    
    def _create_nav_button(
        self,
        page_id: str,
        icon: str,
        tooltip: str
    ) -> ft.Container:
        """Create a navigation button."""
        is_active = self.current_page == page_id
        
        return ft.Container(
            content=ft.IconButton(
                icon=icon,
                icon_color=ft.Colors.WHITE if is_active else theme_manager.text_secondary_color,
                icon_size=28,
                tooltip=tooltip,
                on_click=lambda _: self._handle_click(page_id)
            ),
            bgcolor=theme_manager.primary_color if is_active else None,
            border_radius=theme_manager.corner_radius,
            width=60,
            height=60,
            alignment=ft.alignment.center
        )
    
    def _handle_click(self, page_id: str):
        """Handle navigation button click."""
        if page_id != self.current_page:
            self.current_page = page_id
            self.on_navigate(page_id)
            self._update_buttons()
    
    def _create_fetch_button(self) -> ft.Container:
        """Create the fetch data button."""
        return ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.DOWNLOAD,
                icon_color=ft.Colors.WHITE,
                icon_size=28,
                tooltip=theme_manager.t("fetch_data"),
                on_click=lambda _: self._handle_fetch_click(),
                bgcolor=ft.Colors.GREEN
            ),
            border_radius=theme_manager.corner_radius,
            width=60,
            height=60,
            alignment=ft.alignment.center
        )
    
    def _handle_fetch_click(self):
        """Handle fetch data button click."""
        if self.on_fetch_data:
            self.on_fetch_data()
    
    def _update_buttons(self):
        """Update button styles based on current page."""
        # Recreate navigation
        self.content.controls = [
            self._create_nav_button("dashboard", ft.Icons.DASHBOARD, theme_manager.t("dashboard")),
            self._create_nav_button("telegram", ft.Icons.TELEGRAM, theme_manager.t("telegram")),
            self._create_nav_button("settings", ft.Icons.SETTINGS, theme_manager.t("settings")),
            ft.Container(expand=True),
            self._create_fetch_button(),
            self._create_nav_button("profile", ft.Icons.PERSON, theme_manager.t("profile")),
        ]
        self.update()

