"""
Page routing logic.
"""

import logging
from typing import Optional, Tuple
import flet as ft
from ui.components import Sidebar, TopHeader
from ui.components.gradient_background import GradientBackgroundService
from ui.theme import theme_manager
from services.connectivity_service import connectivity_service
from utils.helpers import safe_page_update

logger = logging.getLogger(__name__)


class Router:
    """Handles page navigation and routing."""
    
    def __init__(self, page: ft.Page, page_factory):
        """
        Initialize router.
        
        Args:
            page: Flet page instance
            page_factory: PageFactory instance for creating pages
        """
        self.page = page
        self.page_factory = page_factory
        self.current_page_id = "dashboard"
        self.sidebar: Optional[Sidebar] = None
        self.content_area: Optional[ft.Container] = None
        self.gradient_service: Optional[GradientBackgroundService] = None
        self._current_page_instance: Optional[ft.Control] = None
        # Store router reference in page for access
        if not hasattr(page, 'data') or page.data is None:
            page.data = {}
        page.data['router'] = self
    
    def navigate_to(self, page_id: str):
        """
        Navigate to a page by ID.
        
        Args:
            page_id: ID of the page to navigate to
        """
        try:
            # Check if current page is fetching (block navigation)
            if self._current_page_instance:
                # Check if it's a FetchDataPage and if it's fetching
                from ui.pages.fetch_data.page import FetchDataPage
                if isinstance(self._current_page_instance, FetchDataPage):
                    if hasattr(self._current_page_instance, 'view_model') and self._current_page_instance.view_model.is_fetching:
                        # Block navigation - show message
                        if self.page:
                            theme_manager.show_snackbar(
                                self.page,
                                "Cannot navigate while fetching data. Please wait for the fetch to complete or click Finish to stop.",
                                bgcolor=ft.Colors.ORANGE
                            )
                        logger.debug("Navigation blocked: fetch in progress")
                        return
            
            logger.debug(f"Navigating to page: {page_id}")
            self.current_page_id = page_id
            
            if not self.content_area:
                logger.error("content_area not found, cannot navigate")
                return
            
            # Create new page instance
            new_page = self.page_factory.create_page(page_id)
            self._current_page_instance = new_page
            self.content_area.content = new_page
            
            # Update sidebar to reflect new current page
            if self.sidebar:
                self.sidebar.set_current_page(page_id)
            
            if not safe_page_update(self.page):
                logger.debug(f"Page update failed (event loop may be closed) for page: {page_id}")
            else:
                logger.debug(f"Successfully navigated to page: {page_id}")
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                logger.debug(f"Event loop closed while navigating to page '{page_id}'")
            else:
                logger.error(f"Error navigating to page '{page_id}': {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error navigating to page '{page_id}': {e}", exc_info=True)
    
    def get_current_page_id(self) -> str:
        """Get current page ID."""
        return self.current_page_id
    
    def refresh_current_page(self):
        """Refresh the current page content."""
        if self.content_area and self.current_page_id:
            new_page = self.page_factory.create_page(self.current_page_id)
            self._current_page_instance = new_page
            self.content_area.content = new_page
            if not safe_page_update(self.page):
                logger.debug("Page update failed (event loop may be closed) while refreshing current page")
    
    def create_main_layout(
        self,
        on_fetch_data: callable
    ) -> Tuple[ft.Column, ft.Container]:
        """
        Create main application layout.
        
        Args:
            on_fetch_data: Callback for fetch data action
            
        Returns:
            Tuple of (main layout column, connectivity banner container)
        """
        # Create sidebar
        self.sidebar = Sidebar(
            on_navigate=self.navigate_to,
            on_fetch_data=on_fetch_data,
            current_page=self.current_page_id
        )
        self.sidebar.page = self.page
        
        # Create main content area
        initial_page = self.page_factory.create_page(self.current_page_id)
        self._current_page_instance = initial_page
        self.content_area = ft.Container(
            content=initial_page,
            expand=True,
            bgcolor=theme_manager.background_color
        )
        
        # Connectivity banner
        connectivity_banner = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.WIFI_OFF, color=ft.Colors.WHITE, size=16),
                ft.Text(
                    theme_manager.t("offline"),
                    color=ft.Colors.WHITE,
                    size=14
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.RED,
            padding=10,
            visible=not connectivity_service.is_connected
        )
        
        # Top header
        top_header = TopHeader(on_navigate=self.navigate_to)
        top_header.page = self.page
        
        # Main layout
        main_layout_column = ft.Column([
            connectivity_banner,
            top_header,
            ft.Row([
                self.sidebar,
                self.content_area,
            ], 
            expand=True,
            spacing=0,  # No spacing between sidebar and content
            vertical_alignment=ft.CrossAxisAlignment.START  # Align to top
            )
        ], spacing=0, expand=True)
        
        # Wrap in container with gradient background
        gradient_container = ft.Container(
            content=main_layout_column,
            expand=True,
            gradient=theme_manager.get_gradient_background(0)
        )
        
        # Start gradient rotation service
        self.gradient_service = GradientBackgroundService(self.page, gradient_container)
        self.gradient_service.start()
        
        return gradient_container, connectivity_banner
    
    def update_connectivity_banner(self, is_connected: bool, banner: ft.Container):
        """
        Update connectivity banner visibility and content.
        
        Args:
            is_connected: Whether device is connected
            banner: Connectivity banner container
        """
        banner.visible = not is_connected
        
        if is_connected:
            banner.bgcolor = ft.Colors.GREEN
            banner.content.controls[0].name = ft.Icons.WIFI
            banner.content.controls[1].value = theme_manager.t("online")
        else:
            banner.bgcolor = ft.Colors.RED
            banner.content.controls[0].name = ft.Icons.WIFI_OFF
            banner.content.controls[1].value = theme_manager.t("offline")
        
        if not safe_page_update(self.page):
            logger.debug("Page update failed (event loop may be closed) while updating connectivity banner")

