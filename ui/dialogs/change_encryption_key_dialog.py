"""
Dialog for changing database encryption key.
"""

import flet as ft
from typing import Optional, Callable
from ui.theme import theme_manager
from services.database.encryption_service import DatabaseEncryptionService


class ChangeEncryptionKeyDialog(ft.AlertDialog):
    """Dialog for changing database encryption key."""
    
    def __init__(
        self,
        current_key_hash: Optional[str],
        on_confirm: Optional[Callable[[str], None]] = None
    ):
        self.current_key_hash = current_key_hash
        self.on_confirm_callback = on_confirm
        
        # New key field
        self.new_key_field = theme_manager.create_text_field(
            label=theme_manager.t("new_encryption_key"),
            hint_text=theme_manager.t("enter_new_key_or_generate"),
            password=True
        )
        
        # Confirm key field
        self.confirm_key_field = theme_manager.create_text_field(
            label=theme_manager.t("confirm_encryption_key"),
            hint_text=theme_manager.t("re_enter_key_to_confirm"),
            password=True
        )
        
        # Generate key button
        self.generate_btn = ft.TextButton(
            text=theme_manager.t("generate_random_key"),
            icon=ft.Icons.REFRESH,
            on_click=self._generate_key
        )
        
        # Error text
        self.error_text = ft.Text("", color=ft.Colors.RED, visible=False)
        
        super().__init__(
            title=ft.Text(theme_manager.t("change_encryption_key")),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        theme_manager.t("encryption_key_change_warning"),
                        size=12,
                        color=theme_manager.text_secondary_color
                    ),
                    self.new_key_field,
                    self.confirm_key_field,
                    self.generate_btn,
                    self.error_text
                ], spacing=15, tight=True),
                width=400,
                padding=10
            ),
            actions=[
                ft.TextButton(
                    text=theme_manager.t("cancel"),
                    on_click=self._on_cancel
                ),
                ft.TextButton(
                    text=theme_manager.t("confirm"),
                    on_click=self._on_confirm
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True
        )
    
    def _generate_key(self, e):
        """Generate a random encryption key."""
        new_key = DatabaseEncryptionService.generate_encryption_key()
        self.new_key_field.value = new_key
        self.confirm_key_field.value = new_key
        if self.page:
            self.page.update()
    
    def _on_confirm(self, e):
        """Handle confirm button click."""
        new_key = self.new_key_field.value or ""
        confirm_key = self.confirm_key_field.value or ""
        
        # Validate
        if not new_key:
            self._show_error(theme_manager.t("encryption_key_required"))
            return
        
        if new_key != confirm_key:
            self._show_error(theme_manager.t("encryption_keys_mismatch"))
            return
        
        if len(new_key) < 16:
            self._show_error(theme_manager.t("encryption_key_too_short"))
            return
        
        # Call callback
        if self.on_confirm_callback:
            self.on_confirm_callback(new_key)
        
        # Close dialog
        if self.page:
            self.page.close(self)
    
    def _on_cancel(self, e):
        """Handle cancel button click."""
        if self.page:
            self.page.close(self)
    
    def _show_error(self, message: str):
        """Show error message."""
        self.error_text.value = message
        self.error_text.visible = True
        if self.page:
            self.page.update()

