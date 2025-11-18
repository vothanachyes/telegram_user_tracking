"""
Main Flet application with navigation.
"""

import flet as ft
import logging
import asyncio
import threading
from typing import Optional
from ui.theme import theme_manager
from ui.dialogs import dialog_manager
from ui.pages import LoginPage
from database.db_manager import DatabaseManager
from ui.initialization import PageConfig, ServiceInitializer
from ui.navigation import Router, PageFactory
from services.fetch_state_manager import fetch_state_manager

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
        
        # Set up window close handler
        self._setup_window_close_handler()
        
        # Initialize router and page factory
        self.page_factory = PageFactory(
            page=self.page,
            db_manager=self.db_manager,
            telegram_service=self.telegram_service,
            on_settings_changed=self._on_settings_changed,
            on_logout=self._on_logout
        )
        
        self.router = Router(self.page, self.page_factory)
        
        # Initialize update service
        self.update_service = None
        self._init_update_service()
        
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
        # Check if we should show splash screen (auto-login scenario)
        from ui.components.splash_screen import SplashScreen
        from ui.pages.login_page import LoginPage
        
        saved_email, saved_password = self._check_saved_credentials()
        show_splash = bool(saved_email and saved_password)
        
        if show_splash:
            # Show splash screen first
            splash = SplashScreen()
            self.page.controls = [splash]
            self.page.update()
            
            # Start animation after a brief delay to ensure page is rendered
            async def start_animation_delayed():
                await asyncio.sleep(0.1)
                splash.start_animation(self.page)
            
            if hasattr(self.page, 'run_task'):
                self.page.run_task(start_animation_delayed)
            else:
                asyncio.create_task(start_animation_delayed())
            
            # Create login page but don't show it yet
            login_page = LoginPage(
                on_login_success=self._on_login_success,
                page=self.page,
                splash_screen=splash
            )
            # Store login page reference for later use
            splash._login_page = login_page
            
            # Trigger auto-login which will hide splash on success
            # Use a small delay to ensure page is fully ready for async operations
            async def trigger_auto_login_delayed():
                await asyncio.sleep(0.2)  # Small delay to ensure page is ready
                login_page._trigger_auto_login()
            
            if hasattr(self.page, 'run_task'):
                try:
                    self.page.run_task(trigger_auto_login_delayed)
                except Exception as e:
                    logger.error(f"Error calling page.run_task(): {e}", exc_info=True)
            else:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(trigger_auto_login_delayed())
                    else:
                        def run_in_thread():
                            asyncio.run(trigger_auto_login_delayed())
                        threading.Thread(target=run_in_thread, daemon=True).start()
                except Exception as e:
                    logger.error(f"Error creating async task: {e}", exc_info=True)
        else:
            # No saved credentials, show login page directly
            login_page = LoginPage(on_login_success=self._on_login_success, page=self.page)
            self.page.controls = [login_page]
            self.page.update()
    
    def _check_saved_credentials(self):
        """Check if saved credentials exist."""
        try:
            from utils.credential_storage import credential_storage
            credential = self.db_manager.get_login_credential()
            if credential:
                try:
                    password = credential_storage.decrypt(credential.encrypted_password)
                    return credential.email, password
                except:
                    return None, None
        except:
            pass
        return None, None
    
    def _on_login_success(self):
        """Handle successful login."""
        self.is_logged_in = True
        
        # Start update service
        self._start_update_service()
        
        # Check if PIN is enabled
        settings = self.db_manager.get_settings()
        if settings.pin_enabled and settings.encrypted_pin:
            # Show PIN entry dialog
            self._show_pin_entry_dialog()
        else:
            # No PIN required, proceed to main app
            self._show_main_app()
            self._check_license_on_startup()
    
    def _show_pin_entry_dialog(self):
        """Show PIN entry dialog after login."""
        from ui.dialogs.pin_dialog import PinEntryDialog
        from utils.pin_validator import verify_pin
        
        # Get settings from database (includes PIN fields)
        settings = self.db_manager.get_settings()
        
        def on_pin_submit(pin: str):
            """Handle PIN submission."""
            try:
                # Verify PIN
                if verify_pin(pin, settings.encrypted_pin):
                    # Correct PIN, proceed to main app
                    self._show_main_app()
                    self._check_license_on_startup()
                else:
                    # Incorrect PIN, show error and retry
                    pin_dialog.show_error(theme_manager.t("pin_incorrect"))
            except Exception as e:
                logger.error(f"Error verifying PIN: {e}")
                pin_dialog.show_error(theme_manager.t("pin_incorrect"))
        
        def on_pin_cancel():
            """Handle PIN cancellation - logout user."""
            logger.info("PIN entry cancelled, logging out")
            self._on_logout()
        
        # Create and show PIN dialog
        pin_dialog = PinEntryDialog(
            title=theme_manager.t("pin_required"),
            message=theme_manager.t("pin_warning_dialog"),
            on_submit=on_pin_submit,
            on_cancel=on_pin_cancel,
            allow_cancel=True
        )
        pin_dialog.page = self.page
        
        # Use page.open() as per repo rules
        try:
            self.page.open(pin_dialog)
        except Exception as e:
            logger.error(f"page.open() failed: {e}")
            # Fallback to old pattern if page.open() fails
            self.page.dialog = pin_dialog
            pin_dialog.open = True
            self.page.update()
    
    def _show_main_app(self):
        """Show main application."""
        # No auto-connect on startup - connect on demand only
        # Create main layout using router
        main_layout, self.connectivity_banner = self.router.create_main_layout(
            on_fetch_data=self._navigate_to_fetch_data
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
        
        # Stop update service
        self._stop_update_service()
        
        self.is_logged_in = False
        self._show_login()
    
    def _navigate_to_fetch_data(self):
        """Navigate to fetch data page."""
        if self.router:
            self.router.navigate_to("fetch_data")
    
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
            self.router.navigate_to("about")
            # Switch to pricing tab if available
            if (self.router.content_area and 
                hasattr(self.router.content_area.content, 'tabs')):
                self.router.content_area.content.tabs.selected_index = 1
                self.page.update()
        
        # Create actions
        actions = [
            ft.TextButton(theme_manager.t("close")),
            ft.ElevatedButton(
                theme_manager.t("contact_admin"),
                on_click=contact_admin,
                bgcolor=theme_manager.primary_color,
                color=ft.Colors.WHITE
            )
        ]
        
        # Show simple dialog using centralized manager
        dialog_manager.show_simple_dialog(
            page=self.page,
            title=theme_manager.t("license_expired"),
            message=theme_manager.t("contact_admin_to_upgrade"),
            actions=actions
        )
    
    def _init_update_service(self):
        """Initialize update service."""
        try:
            from services.update_service import UpdateService
            from services.auth_service import auth_service
            
            # Create callback to check if fetch is running
            def is_fetch_running() -> bool:
                """Check if fetch operation is currently running."""
                try:
                    if not self.router:
                        return False
                    
                    # Get current page from router's content area
                    content_area = getattr(self.router, 'content_area', None)
                    if not content_area or not hasattr(content_area, 'content'):
                        return False
                    
                    current_page = content_area.content
                    if not current_page:
                        return False
                    
                    # Check if it's a FetchDataPage
                    from ui.pages.fetch_data.page import FetchDataPage
                    if isinstance(current_page, FetchDataPage):
                        # Check view model
                        if hasattr(current_page, 'view_model'):
                            return getattr(current_page.view_model, 'is_fetching', False)
                    
                    return False
                except Exception as e:
                    logger.error(f"Error checking fetch state: {e}")
                    return False
            
            # Create callback for when update is available
            def on_update_available(version: str, download_path: str):
                """Handle when update becomes available."""
                try:
                    from ui.components.update_toast import show_update_toast
                    
                    def on_install():
                        """Handle install button click."""
                        if self.update_service:
                            success = self.update_service.install_update()
                            if success:
                                logger.info(f"Update installer launched: {version}")
                            else:
                                logger.warning(f"Failed to launch update installer: {version}")
                    
                    def on_ignore():
                        """Handle ignore button click."""
                        logger.info(f"User ignored update: {version}")
                    
                    # Show update toast
                    show_update_toast(
                        page=self.page,
                        version=version,
                        download_path=download_path,
                        on_install=on_install,
                        on_ignore=on_ignore
                    )
                except Exception as e:
                    logger.error(f"Error showing update toast: {e}", exc_info=True)
            
            # Initialize update service
            self.update_service = UpdateService(
                db_manager=self.db_manager,
                page=self.page,
                on_update_available=on_update_available,
                is_fetch_running_callback=is_fetch_running
            )
            
            logger.info("Update service initialized")
        except Exception as e:
            logger.error(f"Error initializing update service: {e}", exc_info=True)
            self.update_service = None
    
    def _start_update_service(self):
        """Start update service (synchronous wrapper)."""
        if not self.update_service:
            return
        
        import asyncio
        
        async def start_async():
            """Start update service (async)."""
            if self.update_service:
                try:
                    await self.update_service.start()
                    logger.info("Update service started")
                except Exception as e:
                    logger.error(f"Error starting update service: {e}")
        
        if hasattr(self.page, 'run_task'):
            self.page.run_task(start_async)
        else:
            asyncio.create_task(start_async())
    
    def _stop_update_service(self):
        """Stop update service (synchronous wrapper)."""
        if not self.update_service:
            return
        
        import asyncio
        
        async def stop_async():
            """Stop update service (async)."""
            if self.update_service:
                try:
                    await self.update_service.stop()
                    logger.info("Update service stopped")
                except Exception as e:
                    logger.error(f"Error stopping update service: {e}")
        
        if hasattr(self.page, 'run_task'):
            self.page.run_task(stop_async)
        else:
            asyncio.create_task(stop_async())
    
    def _setup_window_close_handler(self):
        """Set up handler for window close event."""
        try:
            # Flet window close event handling
            if hasattr(self.page.window, 'on_event'):
                def handle_window_event(e):
                    """Handle window events."""
                    # Check if it's a close event
                    if hasattr(e, 'data') and e.data == "close":
                        self._handle_window_close()
                    elif str(e).lower().find("close") >= 0:
                        self._handle_window_close()
                
                self.page.window.on_event = handle_window_event
            else:
                # Fallback: Use page's window close handler if available
                if hasattr(self.page.window, 'on_close'):
                    def handle_close():
                        """Handle window close."""
                        self._handle_window_close()
                    
                    self.page.window.on_close = handle_close
        except Exception as e:
            logger.debug(f"Could not set up window close handler: {e}")
            # Try alternative approach using page events
            try:
                if hasattr(self.page, 'on_window_event'):
                    def handle_window_event(e):
                        if "close" in str(e).lower():
                            self._handle_window_close()
                    self.page.on_window_event = handle_window_event
            except Exception:
                pass
    
    def _handle_window_close(self):
        """Handle window close attempt."""
        # Check if fetch is in progress
        if fetch_state_manager.is_fetching:
            # Show confirmation dialog
            from ui.dialogs.dialog import DialogManager
            
            def on_confirm(e):
                """User confirmed - stop fetch and close."""
                fetch_state_manager.stop_fetch()
                # Allow window to close
                try:
                    if hasattr(self.page.window, 'close'):
                        self.page.window.close()
                except Exception:
                    pass
            
            def on_cancel(e):
                """User cancelled - prevent close."""
                # Do nothing, window stays open
                pass
            
            DialogManager.show_confirmation_dialog(
                page=self.page,
                title=theme_manager.t("close_app_during_fetch_title") or "Close Application?",
                message=theme_manager.t("close_app_during_fetch_message") or "Are you sure to close app? Fetching data.",
                on_confirm=on_confirm,
                on_cancel=on_cancel,
                confirm_text=theme_manager.t("yes") or "Yes",
                cancel_text=theme_manager.t("no") or "No"
            )
            
            # Prevent default close behavior
            return False
        else:
            # No fetch in progress, allow close
            return True


def main(page: ft.Page):
    """Application entry point for Flet."""
    TelegramUserTrackingApp(page)
