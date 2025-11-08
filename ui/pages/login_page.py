"""
Login page with Firebase authentication.
"""

import flet as ft
import asyncio
import logging
import threading
import time
from typing import Callable, Optional, Tuple
from ui.theme import theme_manager
from services.auth_service import auth_service
from config.settings import settings
from utils.credential_storage import credential_storage
from utils.constants import SPLASH_SCREEN_DURATION

logger = logging.getLogger(__name__)


class LoginPage(ft.Container):
    """Login page for Firebase authentication."""
    
    def __init__(
        self,
        on_login_success: Callable[[], None],
        page: Optional[ft.Page] = None,
        splash_screen: Optional[ft.Container] = None
    ):
        self.on_login_success = on_login_success
        self.page = page
        self.splash_screen = splash_screen
        
        # Load saved credentials
        saved_email, saved_password = self._load_saved_credentials()
        
        # Create form fields
        self.email_field = theme_manager.create_text_field(
            label=theme_manager.t("email"),
            value=saved_email or "",
        )
        
        self.password_field = theme_manager.create_text_field(
            label=theme_manager.t("password"),
            password=True,
            can_reveal_password=True,
            value=saved_password or ""
        )
        
        self.remember_checkbox = ft.Checkbox(
            label=theme_manager.t("remember_me"),
            value=bool(saved_email and saved_password)
        )
        
        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED,
            size=14,
            visible=False
        )
        
        self.login_button = theme_manager.create_button(
            text=theme_manager.t("login"),
            icon=ft.Icons.LOGIN,
            on_click=self._handle_login
        )
        
        self.loading_indicator = ft.ProgressRing(visible=False)
        
        # Build layout
        super().__init__(
            content=ft.Column([
                ft.Container(height=50),
                # Logo/Title
                ft.Container(
                    content=ft.Column([
                        ft.Icon(
                            name=ft.Icons.TELEGRAM,
                            size=80,
                            color=theme_manager.primary_color
                        ),
                        ft.Text(
                            settings.app_name,
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            f"v{settings.app_version}",
                            size=14,
                            color=theme_manager.text_secondary_color,
                            text_align=ft.TextAlign.CENTER
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    alignment=ft.alignment.center
                ),
                ft.Container(height=30),
                # Login form
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Text(
                            theme_manager.t("login"),
                            size=24,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Container(height=10),
                        self.email_field,
                        self.password_field,
                        self.remember_checkbox,
                        self.error_text,
                        ft.Container(height=10),
                        ft.Row([
                            self.login_button,
                            self.loading_indicator
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                    ], horizontal_alignment=ft.CrossAxisAlignment.STRETCH, spacing=15),
                    width=400,
                    padding=30
                ),
                ft.Container(height=30),
                # Developer info
                ft.Text(
                    f"{settings.developer_name} • {settings.developer_contact}",
                    size=12,
                    color=theme_manager.text_secondary_color,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO),
            alignment=ft.alignment.center,
            expand=True,
            bgcolor=theme_manager.background_color
        )
        
        # Store flag for auto-login attempt
        self._should_auto_login = bool(saved_email and saved_password)
        self._pending_error = None
    
    def _trigger_auto_login(self):
        """Trigger auto-login after page is set up."""
        if not self._should_auto_login:
            return
        
        # Use page.run_task if available, otherwise use asyncio
        if self.page and hasattr(self.page, 'run_task'):
            self.page.run_task(self._delayed_auto_login)
        else:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._delayed_auto_login())
                else:
                    # Create new event loop in thread
                    def run_auto_login():
                        asyncio.run(self._delayed_auto_login())
                    threading.Thread(target=run_auto_login, daemon=True).start()
            except RuntimeError as e:
                logger.error(f"Could not create async task for auto-login: {e}", exc_info=True)
    
    async def _delayed_auto_login(self):
        """Delay auto-login to allow UI to render smoothly."""
        await asyncio.sleep(0.5)  # 500ms delay
        await self._attempt_auto_login()
    
    async def _attempt_auto_login(self):
        """Attempt to auto-login with saved credentials.
        
        Note: This always authenticates fresh with Firebase (not cached credentials).
        Firebase will verify:
        - Account exists and is not disabled
        - Password is correct
        - Device limits
        - License status
        """
        saved_email, saved_password = self._load_saved_credentials()
        
        if not saved_email or not saved_password:
            logger.warning("Auto-login: No saved credentials found")
            return  # No credentials to use
        
        # Initialize auth service
        if not auth_service.initialize():
            logger.warning("Auto-login: Failed to initialize auth service")
            if self.splash_screen and self.page:
                # Hide splash screen (it will ensure minimum duration from config)
                await self.splash_screen.hide(self.page)
                await self._show_login_after_splash()
            return  # Silent failure - user can manually login
        
        # Attempt login - this authenticates fresh with Firebase REST API
        # Firebase will verify account status, password, device limits, etc.
        success, error = auth_service.login(saved_email, saved_password)
        
        if success:
            logger.info("Auto-login successful!")
            
            # Hide splash screen if shown (it will ensure minimum duration from config)
            if self.splash_screen and self.page:
                await self.splash_screen.hide(self.page)
                # Wait a bit for fade out, then show main app
                await self._hide_splash_and_login()
            else:
                self.on_login_success()
        else:
            # Silent failure - user can manually login
            logger.warning(f"Auto-login failed: {error}")
            # Hide splash and show login form (it will ensure minimum duration from config)
            if self.splash_screen and self.page:
                await self.splash_screen.hide(self.page)
                # Show login page after splash fades out
                await self._show_login_after_splash()
            else:
                self._set_loading(False)
            # Show error for specific cases (device enforcement, device limit, etc.)
            if error and ("device" in error.lower() or "limit" in error.lower() or "disabled" in error.lower()):
                # Error will be shown after login page appears
                self._pending_error = error
    
    async def _hide_splash_and_login(self):
        """Hide splash screen and proceed to main app."""
        await asyncio.sleep(0.3)  # Wait for fade out animation
        if self.page:
            self.on_login_success()
    
    async def _show_login_after_splash(self):
        """Show login page after splash screen fades out."""
        await asyncio.sleep(0.3)  # Wait for fade out animation
        if self.page:
            # Replace splash with login page
            self.page.controls = [self]
            self.page.update()
            self._set_loading(False)
            # Show pending error if any
            if hasattr(self, '_pending_error') and self._pending_error:
                self._show_error(self._pending_error)
                delattr(self, '_pending_error')
    
    def _handle_login(self, e):
        """Handle login button click."""
        email = self.email_field.value
        password = self.password_field.value
        
        # Validate
        if not email or not password:
            self._show_error("Please enter email and password")
            return
        
        # Show loading
        self._set_loading(True)
        self.error_text.visible = False
        self.update()
        
        # Initialize auth service
        if not auth_service.initialize():
            self._show_error("Failed to initialize authentication. Please check Firebase configuration.")
            self._set_loading(False)
            return
        
        # Authenticate and login using Firebase REST API
        # The login method will automatically authenticate using REST API if no token is provided
        success, error = auth_service.login(email, password)
        if success:
            # Save or delete credentials based on "Remember Me" checkbox
            if self.remember_checkbox.value:
                self._save_credentials(email, password)
            else:
                self._delete_credentials()
            
            self.on_login_success()
        else:
            self._show_error(error or "Login failed")
            self._set_loading(False)
    
    def _show_error(self, message: str):
        """Show error message."""
        self.error_text.value = message
        self.error_text.visible = True
        self.update()
    
    def _set_loading(self, loading: bool):
        """Set loading state."""
        self.loading_indicator.visible = loading
        self.login_button.disabled = loading
        self.update()
    
    def _load_saved_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        """Load saved login credentials from database."""
        try:
            from config.settings import settings
            db_manager = settings.db_manager
            
            credential = db_manager.get_login_credential()
            if credential:
                # Decrypt password
                try:
                    password = credential_storage.decrypt(credential.encrypted_password)
                    return credential.email, password
                except Exception as e:
                    # If decryption fails, delete the corrupted credential
                    logger.warning(f"Failed to decrypt saved password: {e}, deleting corrupted credential")
                    db_manager.delete_login_credential(credential.email)
                    return None, None
            return None, None
        except Exception as e:
            # Silently fail - user can still login manually
            logger.error(f"Error loading saved credentials: {e}", exc_info=True)
            return None, None
    
    def _save_credentials(self, email: str, password: str):
        """Save login credentials to database (encrypted)."""
        try:
            from config.settings import settings
            db_manager = settings.db_manager
            
            # Encrypt password
            encrypted_password = credential_storage.encrypt(password)
            
            # Save to database
            db_manager.save_login_credential(email, encrypted_password)
        except Exception as e:
            # Silently fail - credentials not saved but login still succeeds
            pass
    
    def _delete_credentials(self):
        """Delete saved login credentials."""
        try:
            from config.settings import settings
            db_manager = settings.db_manager
            
            # Delete all saved credentials
            db_manager.delete_login_credential()
        except Exception as e:
            # Silently fail
            pass

