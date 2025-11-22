"""
Delete confirmation dialog with warning.
"""

import flet as ft
from typing import Optional, Callable


class DeleteConfirmDialog(ft.AlertDialog):
    """Delete confirmation dialog with warning and confirmation text input."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    CARD_BG = "#252525"
    BORDER_COLOR = "#333333"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    DANGER_COLOR = "#f44336"
    PRIMARY_COLOR = "#0078d4"
    
    def __init__(
        self,
        title: str,
        message: str,
        item_name: str,
        on_confirm: Callable,
        on_cancel: Optional[Callable] = None,
        require_confirmation_text: bool = True,
    ):
        """
        Initialize delete confirmation dialog.
        
        Args:
            title: Dialog title
            message: Warning message
            item_name: Name of item to delete (for confirmation text)
            on_confirm: Callback when confirmed
            on_cancel: Optional callback when cancelled
            require_confirmation_text: Whether to require typing item name
        """
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.item_name = item_name
        self.require_confirmation_text = require_confirmation_text
        
        # Confirmation text field (if required)
        self.confirmation_field = None
        self.confirm_button = None
        
        if require_confirmation_text:
            self.confirmation_field = ft.TextField(
                label=f"Type '{item_name}' to confirm",
                hint_text=item_name,
                bgcolor=self.CARD_BG,
                color=self.TEXT_COLOR,
                border_color=self.BORDER_COLOR,
                on_change=self._on_confirmation_text_change,
            )
            self.confirm_button = ft.ElevatedButton(
                text="Delete",
                bgcolor=self.DANGER_COLOR,
                color=self.TEXT_COLOR,
                on_click=self._on_confirm_click,
                disabled=True,
            )
        else:
            self.confirm_button = ft.ElevatedButton(
                text="Delete",
                bgcolor=self.DANGER_COLOR,
                color=self.TEXT_COLOR,
                on_click=self._on_confirm_click,
            )
        
        cancel_button = ft.TextButton(
            text="Cancel",
            on_click=self._on_cancel_click,
        )
        
        # Build content
        content_controls = [
            ft.Text(
                message,
                color=self.TEXT_COLOR,
                size=14,
            ),
        ]
        
        if require_confirmation_text:
            content_controls.append(
                ft.Divider(height=20, color="transparent")
            )
            content_controls.append(self.confirmation_field)
        
        super().__init__(
            title=ft.Text(
                title,
                color=self.TEXT_COLOR,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=content_controls,
                    spacing=10,
                    tight=True,
                ),
                padding=ft.padding.all(10),
            ),
            actions=[
                cancel_button,
                self.confirm_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True,
            bgcolor=self.BG_COLOR,
        )
    
    def _on_confirmation_text_change(self, e: ft.ControlEvent):
        """Enable/disable confirm button based on confirmation text."""
        if self.confirm_button:
            self.confirm_button.disabled = (
                self.confirmation_field.value != self.item_name
            )
            self.confirm_button.update()
    
    def _on_confirm_click(self, e: ft.ControlEvent):
        """Handle confirm button click."""
        if self.require_confirmation_text:
            if self.confirmation_field.value != self.item_name:
                return
        
        # Close dialog
        if self.page:
            self.page.close(self)
        
        # Call confirm callback
        if self.on_confirm:
            self.on_confirm()
    
    def _on_cancel_click(self, e: ft.ControlEvent):
        """Handle cancel button click."""
        # Close dialog
        if self.page:
            self.page.close(self)
        
        # Call cancel callback
        if self.on_cancel:
            self.on_cancel()

