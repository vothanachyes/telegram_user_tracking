"""
Login page with Firebase authentication.
"""

import flet as ft
from typing import Callable
from ui.theme import theme_manager
from services.auth_service import auth_service
from config.settings import settings


class LoginPage(ft.Container):
    """Login page for Firebase authentication."""
    
    def __init__(self, on_login_success: Callable[[], None]):
        self.on_login_success = on_login_success
        
        # Create form fields
        self.email_field = theme_manager.create_text_field(
            label=theme_manager.t("email"),
            value="",
        )
        
        self.password_field = theme_manager.create_text_field(
            label=theme_manager.t("password"),
            password=True,
            can_reveal_password=True
        )
        
        self.remember_checkbox = ft.Checkbox(
            label=theme_manager.t("remember_me"),
            value=False
        )
        
        self.error_text = ft.Text(
            "",
            color=ft.colors.RED,
            size=14,
            visible=False
        )
        
        self.login_button = theme_manager.create_button(
            text=theme_manager.t("login"),
            icon=ft.icons.LOGIN,
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
                            name=ft.icons.TELEGRAM,
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
        
        # Note: In a real implementation, you would need to get the ID token
        # from client-side Firebase auth. For now, this is a placeholder.
        # You'll need to implement a web view or use Firebase REST API.
        
        # Placeholder: Initialize auth service
        if not auth_service.initialize():
            self._show_error("Failed to initialize authentication")
            self._set_loading(False)
            return
        
        # For demo purposes, we'll simulate a successful login
        # In production, you need proper Firebase client auth flow
        self._show_error("Firebase client authentication not yet implemented. Please configure Firebase web auth.")
        self._set_loading(False)
        
        # TODO: Implement proper Firebase authentication with web view or REST API
        # success, error = auth_service.login(email, password, id_token)
        # if success:
        #     self.on_login_success()
        # else:
        #     self._show_error(error or "Login failed")
        #     self._set_loading(False)
    
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

