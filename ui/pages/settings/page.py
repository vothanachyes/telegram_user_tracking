"""
Settings page - main orchestration file.
"""

import flet as ft
from typing import Callable, Optional
from database.db_manager import DatabaseManager
from database.models import AppSettings
from ui.theme import theme_manager
from config.settings import settings as app_settings
from services.telegram import TelegramService
from ui.pages.settings.tabs import GeneralTab, AuthenticateTab, ConfigureTab, SecurityTab
from ui.pages.settings.handlers import SettingsHandlers


class SettingsPage(ft.Container):
    """Settings page for app configuration with tabbed interface."""
    
    def __init__(
        self, 
        on_settings_changed: Callable[[], None],
        telegram_service: Optional[TelegramService] = None,
        db_manager: Optional[DatabaseManager] = None
    ):
        self.on_settings_changed = on_settings_changed
        self.telegram_service = telegram_service
        self.db_manager = db_manager or DatabaseManager()
        self.current_settings = app_settings.load_settings()
        self.page: Optional[ft.Page] = None
        
        # Initialize handlers
        self.handlers = SettingsHandlers(
            page=None,  # Will be set when page is assigned
            telegram_service=self.telegram_service,
            db_manager=self.db_manager,
            current_settings=self.current_settings,
            on_settings_changed=self.on_settings_changed,
            authenticate_tab=None  # Will be set after tab creation
        )
        
        # Initialize tabs
        self.general_tab = GeneralTab(
            current_settings=self.current_settings,
            on_settings_changed=self.on_settings_changed
        )
        
        self.authenticate_tab = AuthenticateTab(
            current_settings=self.current_settings,
            telegram_service=self.telegram_service,
            db_manager=self.db_manager,
            handlers=self.handlers
        )
        
        self.configure_tab = ConfigureTab(
            current_settings=self.current_settings,
            handlers=self.handlers
        )
        
        self.security_tab = SecurityTab(
            current_settings=self.current_settings,
            db_manager=self.db_manager,
            handlers=self.handlers,
            on_settings_changed=self.on_settings_changed
        )
        
        # Update handlers reference
        self.handlers.authenticate_tab = self.authenticate_tab
        
        # Build UI
        super().__init__(
            content=self._build_tabs(),
            padding=20,
            expand=True
        )
    
    def _build_tabs(self) -> ft.Column:
        """Build the tabbed interface."""
        def on_tab_change(e):
            """Handle tab change - auto-refresh accounts when Authenticate tab is selected."""
            if e.control.selected_index == 1:  # Authenticate tab (index 1)
                # Auto-refresh accounts list when user enters Authenticate tab
                self.authenticate_tab.update_accounts_list()
        
        self.tabs_widget = ft.Tabs(
                selected_index=0,
                animation_duration=300,
            on_change=on_tab_change,
                tabs=[
                    ft.Tab(
                        text=theme_manager.t("general"),
                        icon=ft.Icons.SETTINGS,
                        content=self.general_tab.build()
                    ),
                    ft.Tab(
                        text=theme_manager.t("authenticate"),
                        icon=ft.Icons.VERIFIED_USER,
                        content=self.authenticate_tab.build()
                    ),
                    ft.Tab(
                        text=theme_manager.t("configure"),
                        icon=ft.Icons.TUNE,
                        content=self.configure_tab.build()
                    ),
                    ft.Tab(
                        text=theme_manager.t("security"),
                        icon=ft.Icons.SECURITY,
                        content=self.security_tab.build()
                    ),
                ],
            expand=True
        )
        
        return ft.Column([
            ft.Row([
                ft.Text(
                    theme_manager.t("settings"),
                    size=theme_manager.font_size_page_title,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(expand=True)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=0),
            self.tabs_widget,
        ], spacing=0, expand=True)
    
    def update_settings(self):
        """Update all tabs with current settings."""
        self.current_settings = app_settings.load_settings()
        self.handlers.current_settings = self.current_settings
        self.general_tab.update_settings(self.current_settings)
        self.authenticate_tab.update_settings(self.current_settings)
        self.configure_tab.update_settings(self.current_settings)
        self.security_tab.update_settings(self.current_settings)
    
    def set_page(self, page: ft.Page):
        """Set page reference for all tabs and handlers."""
        self.page = page
        self.handlers.page = page
        self.general_tab.page = page
        self.authenticate_tab.page = page
        self.configure_tab.page = page
        self.security_tab.page = page

