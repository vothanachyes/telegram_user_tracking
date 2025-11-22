"""
Admin login page.
"""

import os
import flet as ft
from typing import Callable, Optional
from admin.services.admin_auth_service import admin_auth_service

# Try to load .env file
try:
    from dotenv import load_dotenv
    from pathlib import Path
    # Load from project root .env file
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Fallback to current directory
        load_dotenv()
except ImportError:
    # dotenv not available, just use os.getenv
    pass


class AdminLoginPage(ft.Container):
    """Admin login page."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    CARD_BG = "#252525"
    BORDER_COLOR = "#333333"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    ERROR_COLOR = "#f44336"
    
    def __init__(self, on_login_success: Callable[[], None]):
        self.on_login_success = on_login_success
        self.error_message = ft.Text("", color=self.ERROR_COLOR, size=12)
        
        # Get credentials from environment variables
        admin_email = os.getenv("ADMIN_FIREBASE_ACC", "").strip()
        admin_password = os.getenv("ADMIN_FIREBASE_PASS", "").strip()
        
        self.email_field = ft.TextField(
            label="Email",
            hint_text="Enter your email",
            value=admin_email,
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            width=320,
        )
        self.password_field = ft.TextField(
            label="Password",
            hint_text="Enter your password",
            value=admin_password,
            password=True,
            can_reveal_password=True,
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            width=320,
        )
        self.login_button = ft.ElevatedButton(
            text="Login",
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
            on_click=self._handle_login,
            width=320,
            height=45,
        )
        
        super().__init__(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Admin Login",
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            color=self.TEXT_COLOR,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Divider(height=30, color="transparent"),
                        self.email_field,
                        ft.Divider(height=5, color="transparent"),
                        self.password_field,
                        ft.Divider(height=5, color="transparent"),
                        self.error_message,
                        ft.Divider(height=15, color="transparent"),
                        self.login_button,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                    tight=True,
                ),
                padding=ft.padding.symmetric(horizontal=40, vertical=50),
                bgcolor=self.CARD_BG,
                border=ft.border.all(1, self.BORDER_COLOR),
                border_radius=12,
                width=400,
            ),
            alignment=ft.alignment.center,
            bgcolor=self.BG_COLOR,
            expand=True,
        )
    
    def _handle_login(self, e: ft.ControlEvent):
        """Handle login button click."""
        email = self.email_field.value
        password = self.password_field.value
        
        if not email or not password:
            self.error_message.value = "Please enter both email and password"
            self.error_message.update()
            return
        
        # Disable button during login
        self.login_button.disabled = True
        self.login_button.text = "Logging in..."
        self.login_button.update()
        
        # Attempt login
        success, error_msg = admin_auth_service.login(email, password)
        
        if success:
            self.error_message.value = ""
            self.on_login_success()
        else:
            self.error_message.value = error_msg or "Login failed"
            self.error_message.update()
            self.login_button.disabled = False
            self.login_button.text = "Login"
            self.login_button.update()

