"""
Main about page orchestration.
"""

import flet as ft
from database.db_manager import DatabaseManager
from services.license_service import LicenseService
from ui.theme import theme_manager
from ui.pages.about.about_tab import AboutTab
from ui.pages.about.pricing_tab import PricingTab


class AboutPage:
    """About page with About and Pricing tabs."""
    
    def __init__(self, page: ft.Page, db_manager: DatabaseManager):
        self.page = page
        self.db_manager = db_manager
        self.license_service = LicenseService(db_manager)
        
        # Initialize tabs
        self.about_tab_component = AboutTab(self.license_service)
        self.pricing_tab_component = PricingTab(self.license_service)
        
        # Create tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(
                    text=theme_manager.t("about"),
                    content=self._build_about_tab_with_callback()
                ),
                ft.Tab(
                    text=theme_manager.t("pricing"),
                    content=self.pricing_tab_component.build()
                )
            ],
            expand=True
        )
        
        self.container = ft.Container(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("about"),
                    size=theme_manager.font_size_page_title,
                    weight=ft.FontWeight.BOLD
                ),
                self.tabs
            ], scroll=ft.ScrollMode.AUTO, spacing=0),
            padding=theme_manager.padding_lg,
            expand=True
        )
    
    def build(self) -> ft.Container:
        """Build and return the about page container."""
        return self.container
    
    def _build_about_tab_with_callback(self) -> ft.Container:
        """Build about tab with pricing tab switch callback."""
        tab_content = self.about_tab_component.build()
        
        # Find and update the view pricing button
        def update_button(container):
            if hasattr(container, 'content'):
                content = container.content
                if isinstance(content, ft.Column):
                    for control in content.controls:
                        if isinstance(control, ft.Container):
                            if hasattr(control.content, 'controls'):
                                for sub_control in control.content.controls:
                                    if isinstance(sub_control, ft.ElevatedButton):
                                        if sub_control.text == theme_manager.t("view_pricing"):
                                            sub_control.on_click = lambda e: self._switch_to_pricing_tab()
                        update_button(control)
        
        update_button(tab_content)
        return tab_content
    
    def _switch_to_pricing_tab(self):
        """Switch to pricing tab."""
        self.tabs.selected_index = 1
        self.page.update()

