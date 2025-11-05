"""
Main Flet application with navigation.
"""

import flet as ft
from typing import Optional
from ui.theme import theme_manager
from ui.components import Sidebar
from ui.pages import LoginPage, DashboardPage, SettingsPage, TelegramPage, ProfilePage
from database.db_manager import DatabaseManager
from services.auth_service import auth_service
from services.connectivity_service import connectivity_service
from config.settings import settings
from utils.constants import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT


class TelegramUserTrackingApp:
    """Main application class."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.db_manager = DatabaseManager()
        self.current_page_id = "dashboard"
        self.is_logged_in = False
        
        # Configure page
        self._configure_page()
        
        # Initialize services
        self._initialize_services()
        
        # Build UI
        self._build_ui()
    
    def _configure_page(self):
        """Configure page settings."""
        self.page.title = settings.app_name
        self.page.theme_mode = theme_manager.theme_mode
        self.page.theme = theme_manager.get_theme()
        self.page.window_width = DEFAULT_WINDOW_WIDTH
        self.page.window_height = DEFAULT_WINDOW_HEIGHT
        self.page.window_min_width = MIN_WINDOW_WIDTH
        self.page.window_min_height = MIN_WINDOW_HEIGHT
        self.page.padding = 0
        self.page.bgcolor = theme_manager.background_color
    
    def _initialize_services(self):
        """Initialize application services."""
        # Start connectivity monitoring
        connectivity_service.start_monitoring(self._on_connectivity_change)
        
        # Initialize auth service (optional, Firebase may not be configured)
        try:
            auth_service.initialize()
        except:
            pass  # Firebase not configured, will use without auth
    
    def _build_ui(self):
        """Build main UI."""
        # For demo purposes, skip login if Firebase is not configured
        if not auth_service.initialize():
            self.is_logged_in = True
            self._show_main_app()
        else:
            self._show_login()
    
    def _show_login(self):
        """Show login page."""
        login_page = LoginPage(on_login_success=self._on_login_success)
        self.page.controls = [login_page]
        self.page.update()
    
    def _on_login_success(self):
        """Handle successful login."""
        self.is_logged_in = True
        self._show_main_app()
    
    def _show_main_app(self):
        """Show main application."""
        # Create sidebar
        self.sidebar = Sidebar(
            on_navigate=self._navigate_to,
            current_page=self.current_page_id
        )
        
        # Create main content area
        self.content_area = ft.Container(
            content=self._get_page_content(self.current_page_id),
            expand=True,
            bgcolor=theme_manager.background_color
        )
        
        # Connectivity banner
        self.connectivity_banner = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.WIFI_OFF, color=ft.colors.WHITE, size=16),
                ft.Text(
                    theme_manager.t("offline"),
                    color=ft.colors.WHITE,
                    size=14
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.colors.RED,
            padding=10,
            visible=not connectivity_service.is_connected
        )
        
        # Main layout
        self.page.controls = [
            ft.Column([
                self.connectivity_banner,
                ft.Row([
                    self.sidebar,
                    self.content_area,
                ], expand=True)
            ], spacing=0, expand=True)
        ]
        
        self.page.update()
    
    def _navigate_to(self, page_id: str):
        """Navigate to a page."""
        self.current_page_id = page_id
        self.content_area.content = self._get_page_content(page_id)
        self.page.update()
    
    def _get_page_content(self, page_id: str) -> ft.Control:
        """Get page content by ID."""
        if page_id == "dashboard":
            return DashboardPage(self.db_manager)
        elif page_id == "telegram":
            return TelegramPage(self.db_manager)
        elif page_id == "settings":
            return SettingsPage(on_settings_changed=self._on_settings_changed)
        elif page_id == "profile":
            return ProfilePage(on_logout=self._on_logout)
        else:
            return ft.Container(
                content=ft.Text(f"Page '{page_id}' not found"),
                alignment=ft.alignment.center
            )
    
    def _on_settings_changed(self):
        """Handle settings change."""
        # Reload theme
        self.page.theme_mode = theme_manager.theme_mode
        self.page.theme = theme_manager.get_theme()
        self.page.bgcolor = theme_manager.background_color
        
        # Rebuild UI
        if self.is_logged_in:
            self._show_main_app()
        
        self.page.update()
    
    def _on_logout(self):
        """Handle logout."""
        self.is_logged_in = False
        self._show_login()
    
    def _on_connectivity_change(self, is_connected: bool):
        """Handle connectivity status change."""
        if hasattr(self, 'connectivity_banner'):
            self.connectivity_banner.visible = not is_connected
            
            if is_connected:
                self.connectivity_banner.bgcolor = ft.colors.GREEN
                self.connectivity_banner.content.controls[0].name = ft.icons.WIFI
                self.connectivity_banner.content.controls[1].value = theme_manager.t("online")
            else:
                self.connectivity_banner.bgcolor = ft.colors.RED
                self.connectivity_banner.content.controls[0].name = ft.icons.WIFI_OFF
                self.connectivity_banner.content.controls[1].value = theme_manager.t("offline")
            
            try:
                self.page.update()
            except:
                pass  # Page might not be ready


def main(page: ft.Page):
    """Application entry point for Flet."""
    TelegramUserTrackingApp(page)

