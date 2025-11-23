"""
Dialog for Firebase password authentication as fallback for OS authentication.
"""

import flet as ft
from typing import Optional, Callable
from ui.theme import theme_manager
import logging

logger = logging.getLogger(__name__)


class FirebasePasswordDialog(ft.AlertDialog):
    """Dialog for entering Firebase password as fallback authentication."""
    
    def __init__(
        self,
        email: str,
        title: Optional[str] = None,
        message: Optional[str] = None,
        on_submit: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None
    ):
        self.on_submit_callback = on_submit
        self.on_cancel_callback = on_cancel
        self.submitted_value: Optional[str] = None
        self.email = email
        
        # Error text
        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED,
            size=12,
            visible=False
        )
        
        # Email field (read-only)
        self.email_field = theme_manager.create_text_field(
            label=theme_manager.t("email") or "Email",
            value=email,
            read_only=True
        )
        
        # Password field
        self.password_field = theme_manager.create_text_field(
            label=theme_manager.t("password") or "Password",
            password=True,
            autofocus=True,
            on_submit=self._handle_submit
        )
        
        # Dialog title
        dialog_title = title or (theme_manager.t("firebase_password_auth") or "Firebase Password Authentication")
        
        # Message if provided
        message_widget = None
        if message:
            message_widget = ft.Container(
                content=ft.Text(
                    message,
                    size=12,
                    color=theme_manager.text_secondary_color
                ),
                padding=ft.padding.only(bottom=10)
            )
        
        # Create dialog content
        content_list = []
        if message_widget:
            content_list.append(message_widget)
        content_list.extend([
            self.email_field,
            self.password_field,
            self.error_text
        ])
        
        # Create dialog
        super().__init__(
            title=ft.Text(dialog_title),
            content=ft.Container(
                content=ft.Column(
                    content_list,
                    tight=True,
                    spacing=15
                ),
                width=400,
                padding=10
            ),
            actions=[
                ft.TextButton(
                    theme_manager.t("cancel") or "Cancel",
                    on_click=self._handle_cancel
                ),
                ft.ElevatedButton(
                    theme_manager.t("authenticate") or "Authenticate",
                    icon=ft.Icons.VERIFIED_USER,
                    on_click=self._handle_submit,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=theme_manager.primary_color
                    )
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True
        )
    
    def _handle_submit(self, e):
        """Handle password submission."""
        password = self.password_field.value
        
        if not password:
            self._show_error(theme_manager.t("password_required") or "Password is required")
            return
        
        # Clear error
        self.error_text.visible = False
        self.error_text.value = ""
        if self.page:
            self.page.update()
        
        # Call callback
        if self.on_submit_callback:
            self.on_submit_callback(password)
        
        # Close dialog
        self.submitted_value = password
        if self.page:
            self.page.close(self)
    
    def _handle_cancel(self, e):
        """Handle dialog cancellation."""
        if self.on_cancel_callback:
            self.on_cancel_callback()
        
        if self.page:
            self.page.close(self)
    
    def _show_error(self, message: str):
        """Show error message."""
        self.error_text.value = message
        self.error_text.visible = True
        if self.page:
            self.page.update()

