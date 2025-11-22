"""
Admin interface entry point.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import flet as ft
import logging
from admin.config.admin_config import admin_config
from admin.services.admin_auth_service import admin_auth_service
from admin.ui.pages.login_page import AdminLoginPage
from admin.ui.pages.dashboard_page import AdminDashboardPage
from admin.ui.pages.users_page import AdminUsersPage
from admin.ui.pages.licenses_page import AdminLicensesPage
from admin.ui.pages.app_updates_page import AdminAppUpdatesPage
from admin.ui.pages.devices_page import AdminDevicesPage
from admin.ui.pages.activity_logs_page import AdminActivityLogsPage
from admin.ui.pages.bulk_operations_page import AdminBulkOperationsPage
from admin.ui.components.sidebar import AdminSidebar
from admin.utils.constants import (
    PAGE_LOGIN, PAGE_DASHBOARD, PAGE_USERS, PAGE_LICENSES,
    PAGE_APP_UPDATES, PAGE_DEVICES, PAGE_ACTIVITY_LOGS, PAGE_BULK_OPERATIONS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdminApp:
    """Admin application."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_page_id = PAGE_LOGIN
        self.sidebar: ft.Control = None
        self.content_area: ft.Container = None
        
        # Configure page
        self._configure_page()
        
        # Build UI
        self._build_ui()
        
        # Check authentication
        self._check_auth()
    
    def _configure_page(self):
        """Configure Flet page."""
        self.page.title = "Admin Interface"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#1e1e1e"
        self.page.padding = 0
        self.page.window.width = 1400
        self.page.window.height = 900
        self.page.window.min_width = 1000
        self.page.window.min_height = 600
    
    def _build_ui(self):
        """Build main UI."""
        self.content_area = ft.Container(
            content=None,
            expand=True,
        )
        
        self.page.add(
            ft.Row(
                controls=[
                    self.content_area,
                ],
                expand=True,
                spacing=0,
            )
        )
    
    def _check_auth(self):
        """Check authentication and show appropriate page."""
        if admin_auth_service.is_authenticated():
            self._navigate_to(PAGE_DASHBOARD)
        else:
            self._navigate_to(PAGE_LOGIN)
    
    def _navigate_to(self, page_id: str):
        """Navigate to a page."""
        self.current_page_id = page_id
        
        if page_id == PAGE_LOGIN:
            # Show login page without sidebar
            self.content_area.content = AdminLoginPage(on_login_success=self._on_login_success)
            if self.sidebar:
                # Hide sidebar
                self.page.controls[0].controls = [self.content_area]
        else:
            # Show main pages with sidebar
            if not self.sidebar:
                self.sidebar = AdminSidebar(
                    on_navigate=self._navigate_to,
                    on_logout=self._on_logout,
                    current_page=page_id,
                )
                self.page.controls[0].controls = [self.sidebar, self.content_area]
            
            # Update sidebar current page
            if self.sidebar:
                self.sidebar.set_current_page(page_id)
            
            # Load page content
            page_content = self._create_page_content(page_id)
            self.content_area.content = page_content
        
        self.page.update()
    
    def _create_page_content(self, page_id: str) -> ft.Control:
        """Create page content based on page ID."""
        if page_id == PAGE_DASHBOARD:
            return AdminDashboardPage()
        elif page_id == PAGE_USERS:
            return AdminUsersPage(self.page)
        elif page_id == PAGE_LICENSES:
            return AdminLicensesPage(self.page)
        elif page_id == PAGE_APP_UPDATES:
            return AdminAppUpdatesPage(self.page)
        elif page_id == PAGE_DEVICES:
            return AdminDevicesPage(self.page)
        elif page_id == PAGE_ACTIVITY_LOGS:
            return AdminActivityLogsPage(self.page)
        elif page_id == PAGE_BULK_OPERATIONS:
            return AdminBulkOperationsPage(self.page)
        else:
            return ft.Container(
                content=ft.Text(f"Page not found: {page_id}"),
                padding=20,
            )
    
    def _on_login_success(self):
        """Handle successful login."""
        logger.info("Admin logged in successfully")
        self._navigate_to(PAGE_DASHBOARD)
    
    def _on_logout(self):
        """Handle logout."""
        admin_auth_service.logout()
        logger.info("Admin logged out")
        self._navigate_to(PAGE_LOGIN)


def main(page: ft.Page):
    """Main entry point."""
    # Check if Firebase Admin SDK is available
    if not admin_config.is_available:
        logger.error("Firebase Admin SDK is not installed")
        page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Error: Firebase Admin SDK not installed",
                            size=20,
                            color="#f44336",
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Divider(height=20, color="transparent"),
                        ft.Text(
                            "Please install the required package:",
                            size=14,
                            color="#aaaaaa",
                        ),
                        ft.Text(
                            "pip install firebase-admin",
                            size=14,
                            color="#0078d4",
                            weight=ft.FontWeight.BOLD,
                            selectable=True,
                        ),
                        ft.Divider(height=20, color="transparent"),
                        ft.Text(
                            "Note: The admin interface requires firebase-admin to manage users and licenses.",
                            size=12,
                            color="#aaaaaa",
                        ),
                    ],
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True,
                padding=40,
            )
        )
        return
    
    # Initialize Firebase Admin SDK
    if not admin_config.initialize():
        logger.error("Failed to initialize Firebase Admin SDK")
        page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Error: Failed to initialize Firebase Admin SDK",
                            size=20,
                            color="#f44336",
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Divider(height=20, color="transparent"),
                        ft.Text(
                            "Please ensure Firebase credentials are configured:",
                            size=14,
                            color="#aaaaaa",
                        ),
                        ft.Text(
                            "1. Place your Firebase Admin SDK credentials JSON file in the config/ directory",
                            size=12,
                            color="#aaaaaa",
                        ),
                        ft.Text(
                            "2. Or set the FIREBASE_CREDENTIALS_PATH environment variable",
                            size=12,
                            color="#aaaaaa",
                        ),
                    ],
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True,
                padding=40,
            )
        )
        return
    
    # Create admin app
    app = AdminApp(page)


if __name__ == "__main__":
    ft.app(target=main)

