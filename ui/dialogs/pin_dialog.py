"""
PIN entry and setup dialogs.
"""

import flet as ft
from typing import Optional, Callable
from ui.theme import theme_manager
from utils.pin_validator import validate_pin_format
import logging

logger = logging.getLogger(__name__)


class PinEntryDialog(ft.AlertDialog):
    """Dialog for entering PIN code (6 digits)."""
    
    def __init__(
        self,
        title: Optional[str] = None,
        message: Optional[str] = None,
        on_submit: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        allow_cancel: bool = False
    ):
        self.on_submit_callback = on_submit
        self.on_cancel_callback = on_cancel
        self.submitted_value: Optional[str] = None
        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED,
            size=12,
            visible=False
        )
        
        # Create PIN input field (numeric only, max 6 digits)
        self.pin_field = theme_manager.create_text_field(
            label=theme_manager.t("enter_pin") or "Enter PIN",
            password=True,
            autofocus=True,
            max_length=6,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_pin_change,
            on_submit=self._handle_submit
        )
        
        # Create visual feedback (dots for entered digits)
        self.pin_dots = ft.Row(
            controls=[
                ft.Container(
                    width=12,
                    height=12,
                    border_radius=6,
                    bgcolor=theme_manager.text_secondary_color,
                    border=ft.border.all(1, theme_manager.border_color)
                ) for _ in range(6)
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        # Dialog title
        dialog_title = title or (theme_manager.t("enter_pin") or "Enter PIN")
        
        # Warning message if provided
        warning_widget = None
        if message:
            warning_widget = ft.Container(
                content=ft.Text(
                    message,
                    size=12,
                    color=ft.Colors.ORANGE_700,
                    weight=ft.FontWeight.BOLD
                ),
                padding=ft.padding.only(bottom=10)
            )
        
        # Create dialog
        content_list = []
        if warning_widget:
            content_list.append(warning_widget)
        content_list.extend([
            self.pin_dots,
            self.pin_field,
            self.error_text
        ])
        
        super().__init__(
            modal=True,
            title=ft.Text(dialog_title),
            content=ft.Container(
                content=ft.Column(
                    content_list,
                    spacing=15,
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                width=350,
                padding=20
            ),
            actions=self._create_actions(allow_cancel),
            actions_alignment=ft.MainAxisAlignment.END,
            elevation=24
        )
    
    def _create_actions(self, allow_cancel: bool) -> list:
        """Create action buttons."""
        actions = []
        
        if allow_cancel:
            actions.append(
                ft.TextButton(
                    theme_manager.t("cancel") or "Cancel",
                    on_click=self._handle_cancel
                )
            )
        
        actions.append(
            ft.ElevatedButton(
                theme_manager.t("confirm") or "Confirm",
                on_click=self._handle_submit,
                icon=ft.Icons.CHECK
            )
        )
        
        return actions
    
    def _on_pin_change(self, e):
        """Update visual feedback when PIN changes."""
        pin_value = self.pin_field.value or ""
        pin_length = len(pin_value)
        
        # Update dots
        for i, dot in enumerate(self.pin_dots.controls):
            if i < pin_length:
                dot.bgcolor = theme_manager.primary_color
            else:
                dot.bgcolor = theme_manager.text_secondary_color
        
        # Hide error when user types
        if self.error_text.visible:
            self.error_text.visible = False
            if self.page:
                self.page.update()
    
    def _handle_submit(self, e):
        """Handle submit button click or Enter key."""
        pin_value = self.pin_field.value.strip() if self.pin_field.value else ""
        
        # Validate PIN format
        is_valid, error = validate_pin_format(pin_value)
        if not is_valid:
            self.error_text.value = error or theme_manager.t("pin_invalid") or "Invalid PIN"
            self.error_text.visible = True
            if self.page:
                self.page.update()
            return
        
        self.submitted_value = pin_value
        
        if self.on_submit_callback:
            self.on_submit_callback(pin_value)
        
        self.open = False
        if self.page:
            self.page.update()
    
    def _handle_cancel(self, e):
        """Handle cancel button click."""
        self.submitted_value = None
        
        if self.on_cancel_callback:
            self.on_cancel_callback()
        
        self.open = False
        if self.page:
            self.page.update()
    
    def get_value(self) -> Optional[str]:
        """Get the submitted PIN value."""
        return self.submitted_value
    
    def show_error(self, message: str):
        """Show error message in dialog."""
        self.error_text.value = message
        self.error_text.visible = True
        if self.page:
            self.page.update()


class PinSetupDialog(ft.AlertDialog):
    """Dialog for setting or changing PIN (with confirmation)."""
    
    def __init__(
        self,
        title: Optional[str] = None,
        on_submit: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None
    ):
        self.on_submit_callback = on_submit
        self.on_cancel_callback = on_cancel
        self.submitted_value: Optional[str] = None
        
        # Warning message
        warning_text = theme_manager.t("pin_warning_dialog") or "Your PIN is stored locally on this device only. We do not store your PIN on our servers."
        
        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED,
            size=12,
            visible=False
        )
        
        # Create PIN input fields
        self.pin_field = theme_manager.create_text_field(
            label=theme_manager.t("enter_pin") or "Enter PIN",
            password=True,
            autofocus=True,
            max_length=6,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_pin_change
        )
        
        self.confirm_pin_field = theme_manager.create_text_field(
            label=theme_manager.t("confirm_pin") or "Confirm PIN",
            password=True,
            max_length=6,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_confirm_pin_change,
            on_submit=self._handle_submit
        )
        
        # Visual feedback for PIN
        self.pin_dots = ft.Row(
            controls=[
                ft.Container(
                    width=12,
                    height=12,
                    border_radius=6,
                    bgcolor=theme_manager.text_secondary_color,
                    border=ft.border.all(1, theme_manager.border_color)
                ) for _ in range(6)
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        # Visual feedback for confirm PIN
        self.confirm_pin_dots = ft.Row(
            controls=[
                ft.Container(
                    width=12,
                    height=12,
                    border_radius=6,
                    bgcolor=theme_manager.text_secondary_color,
                    border=ft.border.all(1, theme_manager.border_color)
                ) for _ in range(6)
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        # Dialog title
        dialog_title = title or (theme_manager.t("set_pin") or "Set PIN")
        
        # Create dialog
        super().__init__(
            modal=True,
            title=ft.Text(dialog_title),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Text(
                            warning_text,
                            size=12,
                            color=ft.Colors.ORANGE_700,
                            weight=ft.FontWeight.BOLD
                        ),
                        padding=ft.padding.only(bottom=10)
                    ),
                    ft.Text(
                        theme_manager.t("enter_pin") or "Enter PIN",
                        size=14,
                        weight=ft.FontWeight.BOLD
                    ),
                    self.pin_dots,
                    self.pin_field,
                    ft.Container(height=10),
                    ft.Text(
                        theme_manager.t("confirm_pin") or "Confirm PIN",
                        size=14,
                        weight=ft.FontWeight.BOLD
                    ),
                    self.confirm_pin_dots,
                    self.confirm_pin_field,
                    self.error_text
                ], spacing=10, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=400,
                padding=20
            ),
            actions=[
                ft.TextButton(
                    theme_manager.t("cancel") or "Cancel",
                    on_click=self._handle_cancel
                ),
                ft.ElevatedButton(
                    theme_manager.t("confirm") or "Confirm",
                    on_click=self._handle_submit,
                    icon=ft.Icons.CHECK
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            elevation=24
        )
    
    def _on_pin_change(self, e):
        """Update visual feedback when PIN changes."""
        pin_value = self.pin_field.value or ""
        pin_length = len(pin_value)
        
        # Update dots
        for i, dot in enumerate(self.pin_dots.controls):
            if i < pin_length:
                dot.bgcolor = theme_manager.primary_color
            else:
                dot.bgcolor = theme_manager.text_secondary_color
        
        # Clear error when user types
        if self.error_text.visible:
            self.error_text.visible = False
            if self.page:
                self.page.update()
    
    def _on_confirm_pin_change(self, e):
        """Update visual feedback when confirm PIN changes."""
        pin_value = self.confirm_pin_field.value or ""
        pin_length = len(pin_value)
        
        # Update dots
        for i, dot in enumerate(self.confirm_pin_dots.controls):
            if i < pin_length:
                dot.bgcolor = theme_manager.primary_color
            else:
                dot.bgcolor = theme_manager.text_secondary_color
        
        # Clear error when user types
        if self.error_text.visible:
            self.error_text.visible = False
            if self.page:
                self.page.update()
    
    def _handle_submit(self, e):
        """Handle submit button click or Enter key."""
        pin_value = self.pin_field.value.strip() if self.pin_field.value else ""
        confirm_pin_value = self.confirm_pin_field.value.strip() if self.confirm_pin_field.value else ""
        
        # Validate PIN format
        is_valid, error = validate_pin_format(pin_value)
        if not is_valid:
            self.error_text.value = error or theme_manager.t("pin_invalid") or "Invalid PIN"
            self.error_text.visible = True
            if self.page:
                self.page.update()
            return
        
        # Check if PINs match
        if pin_value != confirm_pin_value:
            self.error_text.value = theme_manager.t("pin_mismatch") or "PINs do not match"
            self.error_text.visible = True
            if self.page:
                self.page.update()
            return
        
        self.submitted_value = pin_value
        
        if self.on_submit_callback:
            self.on_submit_callback(pin_value)
        
        self.open = False
        if self.page:
            self.page.update()
    
    def _handle_cancel(self, e):
        """Handle cancel button click."""
        self.submitted_value = None
        
        if self.on_cancel_callback:
            self.on_cancel_callback()
        
        self.open = False
        if self.page:
            self.page.update()
    
    def get_value(self) -> Optional[str]:
        """Get the submitted PIN value."""
        return self.submitted_value

