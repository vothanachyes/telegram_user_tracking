"""
PIN entry and setup dialogs.
"""

import flet as ft
import asyncio
import json
import platform
from typing import Optional, Callable
from ui.theme import theme_manager
from utils.pin_validator import validate_pin_format
from utils.pin_attempt_manager import PinAttemptManager
from utils.user_pin_encryption import get_or_create_user_encrypted_pin
from utils.windows_auth import WindowsAuth
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
        allow_cancel: bool = False,
        pin_attempt_manager: Optional[PinAttemptManager] = None
    ):
        self.on_submit_callback = on_submit
        self.on_cancel_callback = on_cancel
        self.submitted_value: Optional[str] = None
        self.pin_attempt_manager = pin_attempt_manager
        self._wait_timer_task = None
        self.db_manager = None  # Will be set from outside if needed
        
        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED,
            size=12,
            visible=False
        )
        
        # Lockout message widget
        self.lockout_text = ft.Text(
            "",
            color=ft.Colors.ORANGE_700,
            size=12,
            weight=ft.FontWeight.BOLD,
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
            on_submit=self._handle_submit,
            disabled=False  # Will be updated based on lockout status
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
        
        # Recovery button (shown on 20th attempt)
        self.recovery_button = ft.ElevatedButton(
            theme_manager.t("copy_pin_recovery_data") or "Copy PIN Recovery Data",
            icon=ft.Icons.COPY,
            on_click=self._handle_recovery_copy,
            visible=False,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.ORANGE_700
            )
        )
        
        # Create dialog
        content_list = []
        if warning_widget:
            content_list.append(warning_widget)
        content_list.extend([
            self.lockout_text,
            self.pin_dots,
            self.pin_field,
            self.error_text,
            self.recovery_button
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
        
        # Check lockout status after dialog is created
        self._check_lockout_status()
    
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
        
        self.submit_button = ft.ElevatedButton(
            theme_manager.t("confirm") or "Confirm",
            on_click=self._handle_submit,
            icon=ft.Icons.CHECK
        )
        actions.append(self.submit_button)
        
        return actions
    
    def _check_lockout_status(self):
        """Check if PIN entry is locked out and update UI accordingly."""
        if not self.pin_attempt_manager:
            return
        
        is_locked, lockout_until, remaining_seconds = self.pin_attempt_manager.is_locked_out()
        
        # Check attempt count for recovery button
        if self.db_manager:
            try:
                settings = self.db_manager.get_settings()
                attempt_count = settings.pin_attempt_count
                if attempt_count >= 20:
                    self.recovery_button.visible = True
                else:
                    self.recovery_button.visible = False
            except Exception as e:
                logger.error(f"Error checking attempt count: {e}")
                self.recovery_button.visible = False
        
        if is_locked and remaining_seconds is not None:
            # Disable input
            self.pin_field.disabled = True
            self.submit_button.disabled = True
            
            # Show lockout message
            wait_time_str = self.pin_attempt_manager.format_wait_time(remaining_seconds)
            lockout_msg = theme_manager.t("pin_locked_out") or "Too many failed attempts. Please wait {time} before trying again."
            self.lockout_text.value = lockout_msg.replace("{time}", wait_time_str)
            self.lockout_text.visible = True
            
            # Start timer to update countdown
            self._start_wait_timer(remaining_seconds)
        else:
            # Enable input
            self.pin_field.disabled = False
            self.submit_button.disabled = False
            self.lockout_text.visible = False
    
    def _start_wait_timer(self, initial_seconds: int):
        """Start a timer to update the wait time display."""
        if self._wait_timer_task:
            self._wait_timer_task.cancel()
        
        async def update_timer():
            remaining = initial_seconds
            while remaining > 0:
                await asyncio.sleep(1)
                remaining -= 1
                
                if remaining > 0:
                    wait_time_str = self.pin_attempt_manager.format_wait_time(remaining)
                    lockout_msg = theme_manager.t("pin_locked_out") or "Too many failed attempts. Please wait {time} before trying again."
                    self.lockout_text.value = lockout_msg.replace("{time}", wait_time_str)
                else:
                    # Lockout expired, re-enable input
                    self.pin_field.disabled = False
                    self.submit_button.disabled = False
                    self.lockout_text.visible = False
                
                if self.page:
                    self.page.update()
        
        # Start timer - page should be set by the time this is called
        if self.page:
            if hasattr(self.page, 'run_task'):
                try:
                    self._wait_timer_task = self.page.run_task(update_timer)
                except Exception as e:
                    logger.error(f"Error starting wait timer: {e}")
                    # Fallback to asyncio task
                    self._wait_timer_task = asyncio.create_task(update_timer())
            else:
                self._wait_timer_task = asyncio.create_task(update_timer())
        else:
            # Page not set yet, will be checked when page is set
            logger.warning("Page not set when starting wait timer")
    
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
        # Check if locked out
        if self.pin_field.disabled:
            return
        
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
        
        # Call callback - it will handle closing the dialog if PIN is correct
        # If PIN is incorrect, callback will call show_error() and dialog stays open
        if self.on_submit_callback:
            self.on_submit_callback(pin_value)
        
        # Don't close dialog here - let the callback decide based on PIN verification result
        # Dialog will be closed in on_pin_submit only if PIN is correct
    
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
        
        # Record failed attempt if attempt manager is available
        if self.pin_attempt_manager:
            attempt_count, wait_time_ms = self.pin_attempt_manager.record_failed_attempt()
            
            # Show recovery button on 20th attempt
            if attempt_count >= 20:
                self.recovery_button.visible = True
            else:
                self.recovery_button.visible = False
            
            # If lockout was applied, update UI
            if wait_time_ms:
                self._check_lockout_status()
            else:
                # Show attempt count in error message if approaching lockout
                if attempt_count >= 3:  # Show warning after 3 attempts
                    remaining_until_lockout = 5 - attempt_count
                    if remaining_until_lockout > 0:
                        message += f" ({remaining_until_lockout} attempts remaining before lockout)"
                    self.error_text.value = message
        
        if self.page:
            self.page.update()
    
    def _handle_recovery_copy(self, e):
        """Handle PIN recovery data copy button click."""
        # Require Windows authentication
        if not WindowsAuth.is_available():
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("windows_auth_not_available") or "Windows authentication not available",
                bgcolor=ft.Colors.RED
            )
            return
        
        # Authenticate
        success, error = WindowsAuth.authenticate(
            message=theme_manager.t("authenticate_to_copy_recovery") or "Please authenticate to copy PIN recovery data",
            title=theme_manager.t("security_authentication") or "Security Authentication"
        )
        
        if not success:
            theme_manager.show_snackbar(
                self.page,
                error or theme_manager.t("authentication_failed") or "Authentication failed",
                bgcolor=ft.Colors.RED
            )
            return
        
        # Generate PIN recovery data
        if not self.db_manager:
            theme_manager.show_snackbar(
                self.page,
                "Database manager not available",
                bgcolor=ft.Colors.RED
            )
            return
        
        try:
            # Get user-encrypted PIN
            user_encrypted_pin = get_or_create_user_encrypted_pin(self.db_manager)
            
            # Get Firebase user ID
            from services.auth_service import auth_service
            current_user = auth_service.get_current_user()
            user_id = current_user.get('uid') if current_user else ""
            
            if not user_id:
                theme_manager.show_snackbar(
                    self.page,
                    "User not logged in",
                    bgcolor=ft.Colors.RED
                )
                return
            
            # Generate recovery data
            recovery_data = {
                "hostname": platform.node(),
                "machine": platform.machine(),
                "system": platform.system(),
                "user_id": user_id,
                "encrypted_pin": user_encrypted_pin or ""
            }
            
            # Copy to clipboard
            recovery_json = json.dumps(recovery_data, indent=2)
            if self.page:
                self.page.set_clipboard(recovery_json)
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("pin_recovery_data_copied") or "PIN recovery data copied to clipboard",
                    bgcolor=ft.Colors.GREEN
                )
        except Exception as ex:
            logger.error(f"Error copying PIN recovery data: {ex}")
            theme_manager.show_snackbar(
                self.page,
                f"Failed to copy recovery data: {str(ex)}",
                bgcolor=ft.Colors.RED
            )


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

