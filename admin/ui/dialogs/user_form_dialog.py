"""
User form dialog for creating and editing users.
"""

import flet as ft
from typing import Optional, Callable, Dict


class UserFormDialog(ft.AlertDialog):
    """Dialog for creating or editing a user."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    CARD_BG = "#252525"
    BORDER_COLOR = "#333333"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    
    def __init__(
        self,
        user_data: Optional[Dict] = None,
        on_submit: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
    ):
        """
        Initialize user form dialog.
        
        Args:
            user_data: Existing user data for editing (None for create)
            on_submit: Callback with (email, password, display_name, disabled)
            on_cancel: Optional callback when cancelled
        """
        self.is_edit = user_data is not None
        self.user_data = user_data
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        
        # Form fields
        self.email_field = ft.TextField(
            label="Email",
            hint_text="user@example.com",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            autofocus=True,
        )
        
        self.password_field = ft.TextField(
            label="Password",
            hint_text="Leave empty to keep current password (edit only)",
            password=True,
            can_reveal_password=True,
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            visible=not self.is_edit,  # Only show for create
        )
        
        self.display_name_field = ft.TextField(
            label="Display Name",
            hint_text="Optional",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.disabled_switch = ft.Switch(
            label="Disabled",
            value=False,
        )
        
        # Set initial values if editing
        if self.is_edit:
            self.email_field.value = user_data.get("email", "")
            self.display_name_field.value = user_data.get("display_name", "")
            self.disabled_switch.value = user_data.get("disabled", False)
        
        # Buttons
        cancel_button = ft.TextButton(
            text="Cancel",
            on_click=self._on_cancel_click,
        )
        
        submit_button = ft.ElevatedButton(
            text="Save" if self.is_edit else "Create",
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
            on_click=self._on_submit_click,
        )
        
        # Build form content
        form_controls = [
            self.email_field,
            self.password_field,
            self.display_name_field,
            self.disabled_switch,
        ]
        
        super().__init__(
            title=ft.Text(
                "Edit User" if self.is_edit else "Create User",
                color=self.TEXT_COLOR,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=form_controls,
                    spacing=15,
                    width=400,
                ),
                padding=ft.padding.all(10),
            ),
            actions=[
                cancel_button,
                submit_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True,
            bgcolor=self.BG_COLOR,
        )
    
    def _on_submit_click(self, e: ft.ControlEvent):
        """Handle submit button click."""
        # Validate
        email = self.email_field.value.strip()
        if not email:
            self._show_error("Email is required")
            return
        
        # Basic email validation
        if "@" not in email or "." not in email.split("@")[1]:
            self._show_error("Invalid email format")
            return
        
        password = self.password_field.value if not self.is_edit else None
        if not self.is_edit and not password:
            self._show_error("Password is required for new users")
            return
        
        # Password validation (min 6 chars for Firebase)
        if password and len(password) < 6:
            self._show_error("Password must be at least 6 characters")
            return
        
        display_name = self.display_name_field.value.strip() or None
        disabled = self.disabled_switch.value
        
        # Close dialog
        if self.page:
            self.page.close(self)
        
        # Call submit callback
        if self.on_submit:
            self.on_submit(
                email=email,
                password=password,
                display_name=display_name,
                disabled=disabled,
            )
    
    def _on_cancel_click(self, e: ft.ControlEvent):
        """Handle cancel button click."""
        # Close dialog
        if self.page:
            self.page.close(self)
        
        # Call cancel callback
        if self.on_cancel:
            self.on_cancel()
    
    def _show_error(self, message: str):
        """Show error message."""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()

