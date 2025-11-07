"""
Main Flet application with navigation.
"""

import flet as ft
import logging
from typing import Optional
from ui.theme import theme_manager
from ui.components import Sidebar, TopHeader
from ui.pages import LoginPage, DashboardPage, SettingsPage, TelegramPage, ProfilePage, UserDashboardPage, AboutPage
from ui.dialogs.fetch_data_dialog import FetchDataDialog
from database.db_manager import DatabaseManager
from services.auth_service import auth_service
from services.connectivity_service import connectivity_service
from services.telegram_service import TelegramService
from services.license_service import LicenseService
from config.settings import settings
from utils.constants import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT

logger = logging.getLogger(__name__)


class TelegramUserTrackingApp:
    """Main application class."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.db_manager = DatabaseManager()
        self.telegram_service = TelegramService(self.db_manager)
        self.current_page_id = "dashboard"
        self.is_logged_in = False
        
        # Configure page
        self._configure_page()
        
        # Initialize services
        self._initialize_services()
        
        # Initialize auth service with db_manager for license checks
        from services.auth_service import auth_service
        auth_service.db_manager = self.db_manager
        auth_service.license_service = LicenseService(self.db_manager, auth_service_instance=auth_service)
        
        # Build UI
        self._build_ui()
    
    def _configure_page(self):
        """Configure page settings."""
        self.page.title = settings.app_name
        self.page.theme_mode = theme_manager.theme_mode
        self.page.theme = theme_manager.get_theme()
        
        # Window size settings only apply to desktop mode
        # In web mode, these are ignored
        try:
            self.page.window_width = DEFAULT_WINDOW_WIDTH
            self.page.window_height = DEFAULT_WINDOW_HEIGHT
            self.page.window_min_width = MIN_WINDOW_WIDTH
            self.page.window_min_height = MIN_WINDOW_HEIGHT
        except AttributeError:
            # Web mode doesn't support window size settings
            pass
        
        self.page.padding = 0
        self.page.bgcolor = theme_manager.background_color
        
        # Initialize toast notification system
        from ui.components.toast import toast
        toast.initialize(self.page, position="top-right")
        
        # Update page to apply window settings
        self.page.update()
    
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
        try:
            # Check if Firebase is available and initialized
            # If Firebase is not configured or initialization failed, skip login
            from config.firebase_config import firebase_config
            firebase_available = firebase_config.is_available if hasattr(firebase_config, 'is_available') else False
            firebase_initialized = firebase_config.is_initialized() if hasattr(firebase_config, 'is_initialized') else False
            
            # Show login only if Firebase is available and initialized
            # Otherwise, show main app directly (skip login)
            if firebase_available and firebase_initialized:
                self._show_login()
            else:
                # Firebase not configured or not available - skip login
                logger.info("Firebase not configured, showing main app directly")
                self.is_logged_in = True
                self._show_main_app()
        except Exception as e:
            # If anything fails, show main app as fallback
            logger.error(f"Error building UI: {e}", exc_info=True)
            try:
                self.is_logged_in = True
                self._show_main_app()
            except Exception as fallback_error:
                # Last resort: show error message
                logger.error(f"Critical error showing UI: {fallback_error}", exc_info=True)
                self.page.controls = [
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color=ft.Colors.RED),
                            ft.Text("Application Error", size=20, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Failed to initialize application: {str(e)}", size=14, color=ft.Colors.RED),
                            ft.Text("Please check the logs for more details.", size=12, color=ft.Colors.GREY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                        alignment=ft.alignment.center,
                        padding=40,
                        expand=True
                    )
                ]
                self.page.update()
    
    def _show_login(self):
        """Show login page."""
        login_page = LoginPage(on_login_success=self._on_login_success)
        self.page.controls = [login_page]
        self.page.update()
    
    def _on_login_success(self):
        """Handle successful login."""
        self.is_logged_in = True
        self._show_main_app()
        # Check license status after login
        self._check_license_on_startup()
    
    def _show_main_app(self):
        """Show main application."""
        # Try to auto-load Telegram session in background
        if self.page and hasattr(self.page, 'run_task'):
            self.page.run_task(self._auto_load_telegram_session)
        else:
            import asyncio
            asyncio.create_task(self._auto_load_telegram_session())
        
        # Create sidebar
        self.sidebar = Sidebar(
            on_navigate=self._navigate_to,
            on_fetch_data=self._show_fetch_dialog,
            current_page=self.current_page_id
        )
        # Store page reference in sidebar for updates
        self.sidebar.page = self.page
        
        # Create main content area
        self.content_area = ft.Container(
            content=self._get_page_content(self.current_page_id),
            expand=True,
            bgcolor=theme_manager.background_color
        )
        
        # Connectivity banner
        self.connectivity_banner = ft.Container(
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
        self.top_header = TopHeader(on_navigate=self._navigate_to)
        self.top_header.page = self.page
        
        # Main layout
        self.page.controls = [
            ft.Column([
                self.connectivity_banner,
                self.top_header,
                ft.Row([
                    self.sidebar,
                    self.content_area,
                ], 
                expand=True,
                spacing=0,  # No spacing between sidebar and content
                vertical_alignment=ft.CrossAxisAlignment.START  # Align to top
                )
            ], spacing=0, expand=True)
        ]
        
        self.page.update()
    
    def _navigate_to(self, page_id: str):
        """Navigate to a page."""
        try:
            logger.debug(f"Navigating to page: {page_id}")
            self.current_page_id = page_id
            if hasattr(self, 'content_area'):
                self.content_area.content = self._get_page_content(page_id)
            else:
                logger.error("content_area not found, cannot navigate")
                return
            # Update sidebar to reflect new current page
            if hasattr(self, 'sidebar'):
                self.sidebar.set_current_page(page_id)
            self.page.update()
            logger.debug(f"Successfully navigated to page: {page_id}")
        except Exception as e:
            logger.error(f"Error navigating to page '{page_id}': {e}", exc_info=True)
    
    def _get_page_content(self, page_id: str) -> ft.Control:
        """Get page content by ID."""
        try:
            if page_id == "dashboard":
                page_content = DashboardPage(self.db_manager)
                page_content.page = self.page
                return page_content
            elif page_id == "telegram":
                page_content = TelegramPage(self.db_manager)
                page_content.set_page(self.page)
                return page_content
            elif page_id == "settings":
                page_content = SettingsPage(
                    on_settings_changed=self._on_settings_changed,
                    telegram_service=self.telegram_service,
                    db_manager=self.db_manager
                )
                page_content.page = self.page
                return page_content
            elif page_id == "profile":
                # ProfilePage now requires page reference in constructor
                profile_page = ProfilePage(page=self.page, on_logout=self._on_logout, db_manager=self.db_manager)
                return profile_page.build()
            elif page_id == "user_dashboard":
                page_content = UserDashboardPage(self.db_manager)
                page_content.set_page(self.page)
                return page_content
            elif page_id == "about":
                page_content = AboutPage(self.page, self.db_manager)
                return page_content.build()
            else:
                return ft.Container(
                    content=ft.Text(f"Page '{page_id}' not found"),
                    alignment=ft.alignment.center
                )
        except Exception as e:
            logger.error(f"Error loading page '{page_id}': {e}", exc_info=True)
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color=ft.Colors.RED),
                    ft.Text("Error loading page", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(str(e), size=14, color=ft.Colors.RED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                alignment=ft.alignment.center,
                padding=40
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
        # Clear saved credentials
        try:
            self.db_manager.delete_login_credential()
        except Exception:
            pass  # Silently fail
        
        self.is_logged_in = False
        self._show_login()
    
    def _show_fetch_dialog(self):
        """Show fetch data dialog."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("=== FETCH DIALOG BUTTON CLICKED ===")
        
        if not self.page:
            logger.error("No page reference available!")
            return
        
        try:
            logger.info("Creating FetchDataDialog...")
            dialog = FetchDataDialog(
                db_manager=self.db_manager,
                telegram_service=self.telegram_service,
                on_fetch_complete=self._on_fetch_complete
            )
            
            # Set page reference for dialog
            dialog.page = self.page
            logger.info(f"Dialog created successfully. Type: {type(dialog)}")
            logger.info(f"Dialog.open value: {dialog.open}")
            logger.info(f"Dialog.modal value: {dialog.modal}")
            
            # Show dialog
            self.page.open(dialog)
            logger.info("Dialog opened using page.open()")
            
        except Exception as e:
            logger.error(f"Error showing dialog: {e}", exc_info=True)
            theme_manager.show_snackbar(
                self.page,
                f"Error opening dialog: {str(e)}",
                bgcolor=ft.Colors.RED
            )
    
    def _on_fetch_complete(self):
        """Handle fetch completion - refresh current page."""
        # Refresh the current page content
        if self.current_page_id == "telegram" or self.current_page_id == "dashboard":
            self.content_area.content = self._get_page_content(self.current_page_id)
            self.page.update()
    
    async def _auto_load_telegram_session(self):
        """Automatically load Telegram session if available."""
        try:
            success, error = await self.telegram_service.auto_load_session()
            if success:
                logger.info("Telegram session auto-loaded successfully")
            else:
                logger.info(f"Could not auto-load Telegram session: {error}")
        except Exception as e:
            logger.error(f"Error auto-loading Telegram session: {e}")
    
    def _on_connectivity_change(self, is_connected: bool):
        """Handle connectivity status change."""
        if hasattr(self, 'connectivity_banner'):
            self.connectivity_banner.visible = not is_connected
            
            if is_connected:
                self.connectivity_banner.bgcolor = ft.Colors.GREEN
                self.connectivity_banner.content.controls[0].name = ft.Icons.WIFI
                self.connectivity_banner.content.controls[1].value = theme_manager.t("online")
            else:
                self.connectivity_banner.bgcolor = ft.Colors.RED
                self.connectivity_banner.content.controls[0].name = ft.Icons.WIFI_OFF
                self.connectivity_banner.content.controls[1].value = theme_manager.t("offline")
            
            try:
                self.page.update()
            except:
                pass  # Page might not be ready
    
    def _check_license_on_startup(self):
        """Check license status on app startup."""
        try:
            from services.license_service import LicenseService
            from services.auth_service import auth_service
            license_service = LicenseService(self.db_manager, auth_service_instance=auth_service)
            status = license_service.check_license_status()
            
            if status['expired']:
                # Show expiration dialog
                self._show_license_expired_dialog()
            elif status['days_until_expiration'] is not None and status['days_until_expiration'] < 7:
                # Show warning for expiring soon
                from ui.theme import theme_manager
                theme_manager.show_snackbar(
                    self.page,
                    f"License expiring in {status['days_until_expiration']} days. Please contact admin to renew.",
                    bgcolor=ft.Colors.ORANGE
                )
        except Exception as e:
            logger.error(f"Error checking license on startup: {e}")
    
    def _show_license_expired_dialog(self):
        """Show dialog when license is expired."""
        from ui.theme import theme_manager
        
        def contact_admin(e):
            dialog.open = False
            self.page.update()
            self._navigate_to("about")
            # Switch to pricing tab
            if hasattr(self, 'content_area') and hasattr(self.content_area.content, 'tabs'):
                self.content_area.content.tabs.selected_index = 1
                self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text(theme_manager.t("license_expired")),
            content=ft.Text(theme_manager.t("contact_admin_to_upgrade")),
            actions=[
                ft.TextButton(theme_manager.t("close"), on_click=lambda e: setattr(dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton(
                    theme_manager.t("contact_admin"),
                    on_click=contact_admin,
                    bgcolor=theme_manager.primary_color,
                    color=ft.Colors.WHITE
                )
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()


def main(page: ft.Page):
    """Application entry point for Flet."""
    TelegramUserTrackingApp(page)

