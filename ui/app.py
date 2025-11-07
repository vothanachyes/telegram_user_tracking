"""
Main Flet application with navigation.
"""

import flet as ft
import logging
import asyncio
from typing import Optional
from ui.theme import theme_manager
from ui.pages import LoginPage
from ui.dialogs.fetch_data_dialog import FetchDataDialog
from database.db_manager import DatabaseManager
from ui.initialization import PageConfig, ServiceInitializer
from ui.navigation import Router, PageFactory

logger = logging.getLogger(__name__)


class TelegramUserTrackingApp:
    """Main application class."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.db_manager = DatabaseManager()
        self.is_logged_in = False
        self.connectivity_banner: Optional[ft.Container] = None
        
        # Initialize service initializer
        self.service_initializer = ServiceInitializer(self.db_manager)
        self.telegram_service = self.service_initializer.initialize_all(
            on_connectivity_change=self._on_connectivity_change
        )
        
        # Configure page
        PageConfig.configure_page(self.page)
        
        # Initialize router and page factory
        self.page_factory = PageFactory(
            page=self.page,
            db_manager=self.db_manager,
            telegram_service=self.telegram_service,
            on_settings_changed=self._on_settings_changed,
            on_logout=self._on_logout
        )
        
        self.router = Router(self.page, self.page_factory)
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build main UI."""
        try:
            # Check if Firebase is available and initialized
            from config.firebase_config import firebase_config
            firebase_available = getattr(firebase_config, 'is_available', False)
            firebase_initialized = (
                firebase_config.is_initialized() 
                if hasattr(firebase_config, 'is_initialized') 
                else False
            )
            
            # Show login only if Firebase is available and initialized
            if firebase_available and firebase_initialized:
                self._show_login()
            else:
                logger.info("Firebase not configured, showing main app directly")
                self.is_logged_in = True
                self._show_main_app()
        except Exception as e:
            logger.error(f"Error building UI: {e}", exc_info=True)
            try:
                self.is_logged_in = True
                self._show_main_app()
            except Exception as fallback_error:
                logger.error(f"Critical error showing UI: {fallback_error}", exc_info=True)
                self._show_error_ui(str(e))
    
    def _show_login(self):
        """Show login page."""
        login_page = LoginPage(on_login_success=self._on_login_success)
        self.page.controls = [login_page]
        self.page.update()
    
    def _on_login_success(self):
        """Handle successful login."""
        self.is_logged_in = True
        self._show_main_app()
        self._check_license_on_startup()
    
    def _show_main_app(self):
        """Show main application."""
        # Try to auto-load Telegram session in background
        if hasattr(self.page, 'run_task'):
            self.page.run_task(self._auto_load_telegram_session)
        else:
            asyncio.create_task(self._auto_load_telegram_session())
        
        # Create main layout using router
        main_layout, self.connectivity_banner = self.router.create_main_layout(
            on_fetch_data=self._show_fetch_dialog
        )
        
        self.page.controls = [main_layout]
        self.page.update()
    
    def _show_error_ui(self, error_message: str):
        """Show error UI."""
        self.page.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color=ft.Colors.RED),
                    ft.Text("Application Error", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Failed to initialize application: {error_message}", size=14, color=ft.Colors.RED),
                    ft.Text("Please check the logs for more details.", size=12, color=ft.Colors.GREY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                alignment=ft.alignment.center,
                padding=40,
                expand=True
            )
        ]
        self.page.update()
    
    def _on_settings_changed(self):
        """Handle settings change."""
        PageConfig.update_theme(self.page)
        
        # Rebuild UI
        if self.is_logged_in:
            self._show_main_app()
        
        self.page.update()
    
    def _on_logout(self):
        """Handle logout."""
        try:
            self.db_manager.delete_login_credential()
        except Exception:
            pass  # Silently fail
        
        self.is_logged_in = False
        self._show_login()
    
    def _show_fetch_dialog(self):
        """Show fetch data dialog."""
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
            
            dialog.page = self.page
            logger.info(f"Dialog created successfully. Type: {type(dialog)}")
            
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
        if self.router:
            self.router.refresh_current_page()
    
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
        if self.connectivity_banner and hasattr(self, 'router') and self.router:
            self.router.update_connectivity_banner(is_connected, self.connectivity_banner)
    
    def _check_license_on_startup(self):
        """Check license status on app startup."""
        try:
            from services.license_service import LicenseService
            from services.auth_service import auth_service
            license_service = LicenseService(self.db_manager, auth_service_instance=auth_service)
            status = license_service.check_license_status()
            
            if status['expired']:
                self._show_license_expired_dialog()
            elif status.get('days_until_expiration') is not None and status['days_until_expiration'] < 7:
                theme_manager.show_snackbar(
                    self.page,
                    f"License expiring in {status['days_until_expiration']} days. Please contact admin to renew.",
                    bgcolor=ft.Colors.ORANGE
                )
        except Exception as e:
            logger.error(f"Error checking license on startup: {e}")
    
    def _show_license_expired_dialog(self):
        """Show dialog when license is expired."""
        def contact_admin(e):
            dialog.open = False
            self.page.update()
            self.router.navigate_to("about")
            # Switch to pricing tab if available
            if (self.router.content_area and 
                hasattr(self.router.content_area.content, 'tabs')):
                self.router.content_area.content.tabs.selected_index = 1
                self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text(theme_manager.t("license_expired")),
            content=ft.Text(theme_manager.t("contact_admin_to_upgrade")),
            actions=[
                ft.TextButton(
                    theme_manager.t("close"),
                    on_click=lambda e: setattr(dialog, 'open', False) or self.page.update()
                ),
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
