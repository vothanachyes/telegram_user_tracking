"""
Login page with Firebase authentication.
"""

import flet as ft
from typing import Callable, Optional, Tuple
from ui.theme import theme_manager
from services.auth_service import auth_service
from config.settings import settings
from utils.credential_storage import credential_storage


class LoginPage(ft.Container):
    """Login page for Firebase authentication."""
    
    def __init__(self, on_login_success: Callable[[], None]):
        self.on_login_success = on_login_success
        
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
                    db_manager.delete_login_credential(credential.email)
                    return None, None
            return None, None
        except Exception as e:
            # Silently fail - user can still login manually
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

