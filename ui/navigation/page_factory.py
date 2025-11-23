"""
Page creation factory.
"""

import logging
import flet as ft
from typing import Optional, Callable
from database.db_manager import DatabaseManager
from services.telegram import TelegramService
from ui.pages import (
    LoginPage,
    DashboardPage,
    SettingsPage,
    TelegramPage,
    ProfilePage,
    UserDashboardPage,
    AboutPage,
    FetchDataPage,
    GroupsPage,
    ReportsPage
)
from ui.pages.notifications.page import NotificationsPage

logger = logging.getLogger(__name__)


class PageFactory:
    """Factory for creating page instances."""
    
    def __init__(
        self,
        page: ft.Page,
        db_manager: DatabaseManager,
        telegram_service: TelegramService,
        on_settings_changed: Optional[Callable[[], None]] = None,
        on_logout: Optional[Callable[[], None]] = None,
        update_service=None
    ):
        """
        Initialize page factory.
        
        Args:
            page: Flet page instance
            db_manager: Database manager instance
            telegram_service: Telegram service instance
            on_settings_changed: Optional callback for settings changes
            on_logout: Optional callback for logout
            update_service: Optional update service instance
        """
        self.page = page
        self.db_manager = db_manager
        self.telegram_service = telegram_service
        self.update_service = update_service
        self.on_settings_changed = on_settings_changed
        self.on_logout = on_logout
    
    def create_page(self, page_id: str) -> ft.Control:
        """
        Create a page instance by ID.
        
        Args:
            page_id: ID of the page to create
            
        Returns:
            Page control instance
        """
        try:
            if page_id == "dashboard":
                return self._create_dashboard_page()
            elif page_id == "telegram":
                return self._create_telegram_page()
            elif page_id == "settings":
                return self._create_settings_page()
            elif page_id == "profile":
                return self._create_profile_page()
            elif page_id == "groups":
                return self._create_groups_page()
            elif page_id == "user_dashboard":
                return self._create_user_dashboard_page()
            elif page_id == "about":
                return self._create_about_page()
            elif page_id == "fetch_data":
                return self._create_fetch_data_page()
            elif page_id == "reports":
                return self._create_reports_page()
            elif page_id == "notifications":
                return self._create_notifications_page()
            else:
                return self._create_error_page(f"Page '{page_id}' not found")
        except Exception as e:
            logger.error(f"Error loading page '{page_id}': {e}", exc_info=True)
            return self._create_error_page(str(e))
    
    def _create_dashboard_page(self) -> DashboardPage:
        """Create dashboard page."""
        page_content = DashboardPage(self.db_manager)
        page_content.set_page(self.page)
        return page_content
    
    def _create_telegram_page(self) -> TelegramPage:
        """Create telegram page."""
        page_content = TelegramPage(self.db_manager)
        page_content.set_page(self.page)
        return page_content
    
    def _create_settings_page(self) -> SettingsPage:
        """Create settings page."""
        page_content = SettingsPage(
            on_settings_changed=self.on_settings_changed or (lambda: None),
            telegram_service=self.telegram_service,
            db_manager=self.db_manager
        )
        page_content.set_page(self.page)
        return page_content
    
    def _create_profile_page(self) -> ft.Control:
        """Create profile page."""
        profile_page = ProfilePage(
            page=self.page,
            on_logout=self.on_logout or (lambda: None),
            db_manager=self.db_manager
        )
        return profile_page.build()
    
    def _create_user_dashboard_page(self) -> UserDashboardPage:
        """Create user dashboard page."""
        page_content = UserDashboardPage(self.db_manager)
        page_content.set_page(self.page)
        return page_content
    
    def _create_about_page(self) -> ft.Control:
        """Create about page."""
        page_content = AboutPage(self.page, self.db_manager, update_service=self.update_service)
        # Call set_page to trigger async loading
        if hasattr(page_content, 'set_page'):
            page_content.set_page(self.page)
        return page_content.build()
    
    def _create_fetch_data_page(self) -> FetchDataPage:
        """Create fetch data page."""
        page_content = FetchDataPage(
            db_manager=self.db_manager,
            telegram_service=self.telegram_service
        )
        page_content.set_page(self.page)
        return page_content
    
    def _create_groups_page(self) -> GroupsPage:
        """Create groups page."""
        page_content = GroupsPage(
            db_manager=self.db_manager,
            telegram_service=self.telegram_service
        )
        page_content.set_page(self.page)
        return page_content
    
    def _create_reports_page(self) -> ReportsPage:
        """Create reports page."""
        page_content = ReportsPage(
            db_manager=self.db_manager,
            on_navigate=None  # Can be extended later if needed
        )
        page_content.set_page(self.page)
        return page_content
    
    def _create_notifications_page(self) -> ft.Control:
        """Create notifications page."""
        page_content = NotificationsPage(self.page)
        # Call set_page to trigger async loading
        if hasattr(page_content, 'set_page'):
            page_content.set_page(self.page)
        return page_content.build()
    
    def _create_error_page(self, error_message: str) -> ft.Container:
        """Create error page."""
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color=ft.Colors.RED),
                ft.Text("Error loading page", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(error_message, size=14, color=ft.Colors.RED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            alignment=ft.alignment.center,
            padding=40
        )

