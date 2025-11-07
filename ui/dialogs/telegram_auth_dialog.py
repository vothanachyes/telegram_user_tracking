"""
Dialog for Telegram authentication (OTP and 2FA input).
"""

import flet as ft
from typing import Optional, Callable
from ui.theme import theme_manager
import logging

logger = logging.getLogger(__name__)


class TelegramAuthDialog(ft.AlertDialog):
    """Dialog for entering OTP code or 2FA password."""
    
    def __init__(
        self,
        is_2fa: bool = False,
        on_submit: Optional[Callable[[str], None]] = None
    ):
        self.is_2fa = is_2fa
        self.on_submit_callback = on_submit
        self.submitted_value: Optional[str] = None
        
        # Create input field
        if is_2fa:
            self.input_field = theme_manager.create_text_field(
                label=theme_manager.t("enter_2fa_password"),
                password=True,
                autofocus=True,
                on_submit=self._handle_submit
            )
            title_text = theme_manager.t("enter_2fa_password")
            submit_text = theme_manager.t("confirm")
        else:
            self.input_field = theme_manager.create_text_field(
                label=theme_manager.t("enter_otp_code"),
                hint_text="12345",
                autofocus=True,
                on_submit=self._handle_submit
            )
            title_text = theme_manager.t("enter_otp_code")
            submit_text = theme_manager.t("confirm")
        
        # Create dialog
        super().__init__(
            modal=True,
            title=ft.Text(title_text),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        theme_manager.t("enter_otp_code") if not is_2fa else theme_manager.t("enter_2fa_password"),
                        size=14,
                        color=theme_manager.text_secondary_color
                    ),
                    self.input_field,
                ], spacing=15, tight=True),
                width=400,
                padding=20
            ),
            actions=[
                ft.TextButton(
                    theme_manager.t("cancel"),
                    on_click=self._handle_cancel
                ),
                ft.ElevatedButton(
                    submit_text,
                    on_click=self._handle_submit,
                    icon=ft.Icons.CHECK
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _handle_submit(self, e):
        """Handle submit button click or Enter key."""
        value = self.input_field.value.strip() if self.input_field.value else ""
        if not value:
            return
        
        self.submitted_value = value
        
        if self.on_submit_callback:
            self.on_submit_callback(value)
        
        self.open = False
        if self.page:
            self.page.update()
    
    def _handle_cancel(self, e):
        """Handle cancel button click."""
        self.submitted_value = None
        self.open = False
        if self.page:
            self.page.update()
    
    def get_value(self) -> Optional[str]:
        """Get the submitted value."""
        return self.submitted_value

