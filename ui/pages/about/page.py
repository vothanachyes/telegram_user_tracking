"""
Main about page orchestration.
"""

import os
import flet as ft
import asyncio
import logging
from database.db_manager import DatabaseManager
from services.license_service import LicenseService
from ui.theme import theme_manager
from ui.components.skeleton_loaders.about_skeleton import AboutSkeleton
from ui.pages.about.about_tab import AboutTab
from ui.pages.about.pricing_tab import PricingTab
from ui.pages.about.update_tab import UpdateTab

logger = logging.getLogger(__name__)


class AboutPage:
    """About page with About and Pricing tabs."""
    
    def __init__(self, page: ft.Page, db_manager: DatabaseManager, update_service=None):
        self.page = page
        self.db_manager = db_manager
        self.license_service = LicenseService(db_manager)
        self.update_service = update_service
        self.is_loading = True
        
        # Initialize tab components (will be created after license info loads)
        self.about_tab_component = None
        self.pricing_tab_component = None
        self.update_tab_component = UpdateTab(update_service=update_service, page=page)
        
        # Check if pricing tab should be enabled (default: disabled)
        self.pricing_tab_enabled = os.getenv("PRICING_TAB_ENABLED", "").lower() in ("true", "1", "yes")
        
        # Create skeleton loader
        self.loading_indicator = AboutSkeleton.create()
        
        # Create tabs with loading placeholders (will be updated after loading)
        self.tabs = ft.Tabs(
            selected_index=0,
            on_change=self._on_tab_change,
            tabs=[
                ft.Tab(
                    text=theme_manager.t("about"),
                    content=self.loading_indicator
                ),
                ft.Tab(
                    text=theme_manager.t("pricing"),
                    content=self.loading_indicator
                ),
                ft.Tab(
                    text=theme_manager.t("update") or "Update",
                    content=self.update_tab_component.build()
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
    
    def set_page(self, page: ft.Page):
        """Set page reference and load data asynchronously."""
        self.page = page
        
        # Update update tab with page reference
        if self.update_tab_component:
            self.update_tab_component.set_page(page)
            if self.update_service:
                self.update_tab_component.set_update_service(self.update_service)
        
        # Load license info and tiers asynchronously
        if page and hasattr(page, 'run_task'):
            page.run_task(self._load_license_info_async)
        else:
            asyncio.create_task(self._load_license_info_async())
    
    async def _load_license_info_async(self):
        """Load license info and tiers asynchronously."""
        try:
            from database.async_query_executor import async_query_executor
            
            # Load license info asynchronously
            license_info = await async_query_executor.execute(
                self.license_service.get_license_info
            )
            
            # Initialize tab components with license service
            # Note: AboutTab and PricingTab will load their own license info asynchronously
            self.about_tab_component = AboutTab(self.license_service)
            self.pricing_tab_component = PricingTab(self.license_service)
            
            # Build about tab (synchronous, but lightweight)
            about_tab_content = self._build_about_tab_with_callback()
            
            # Build pricing tab asynchronously (it calls Firebase)
            pricing_tab_content = await self._build_pricing_tab_async()
            
            # Update tabs with actual content
            self.tabs.tabs[0].content = about_tab_content
            self.tabs.tabs[1].content = pricing_tab_content
            
            self.is_loading = False
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            logger.error(f"Error loading license info: {e}", exc_info=True)
            self.is_loading = False
            if self.page:
                self.page.update()
    
    async def _build_pricing_tab_async(self):
        """Build pricing tab asynchronously."""
        try:
            from database.async_query_executor import async_query_executor
            from services.license.license_tier_service import license_tier_service
            
            # Load license info for pricing tab
            if self.pricing_tab_component.license_info is None:
                self.pricing_tab_component.license_info = await async_query_executor.execute(
                    self.license_service.get_license_info
                )
            
            # Load tiers asynchronously (Firebase call)
            tiers = await async_query_executor.execute(
                license_tier_service.get_all_tiers
            )
            
            # Build pricing tab with loaded data
            return self.pricing_tab_component.build_with_tiers(tiers)
            
        except Exception as e:
            logger.error(f"Error building pricing tab: {e}", exc_info=True)
            # Return error state
            return ft.Container(
                content=ft.Column([
                    ft.Text(
                        theme_manager.t("pricing"),
                        size=theme_manager.font_size_page_title,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        f"Error loading pricing: {str(e)}",
                        size=theme_manager.font_size_body,
                        color=theme_manager.text_secondary_color
                    )
                ], scroll=ft.ScrollMode.AUTO, spacing=theme_manager.spacing_sm),
                padding=theme_manager.padding_lg,
                expand=True
            )
    
    def build(self) -> ft.Container:
        """Build and return the about page container."""
        return self.container
    
    def _build_about_tab_with_callback(self) -> ft.Container:
        """Build about tab with pricing tab switch callback."""
        if self.about_tab_component is None:
            # Create component if not already created
            self.about_tab_component = AboutTab(self.license_service)
        
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
    
    def _on_tab_change(self, e):
        """Handle tab change - prevent switching to pricing tab if disabled."""
        # If trying to switch to pricing tab (index 1) and it's disabled, revert to about tab
        if e.control.selected_index == 1 and not self.pricing_tab_enabled:
            e.control.selected_index = 0
            self.page.update()
    
    def _switch_to_pricing_tab(self):
        """Switch to pricing tab."""
        # Check if pricing tab is enabled before switching
        if self.pricing_tab_enabled and len(self.tabs.tabs) > 1:
            self.tabs.selected_index = 1
            self.page.update()

