"""
Dialog for adding a new Telegram account with OTP and 2FA support.
"""

import flet as ft
import asyncio
import threading
from typing import Optional, Callable
from ui.theme import theme_manager
from utils.validators import validate_phone
from config.settings import settings as app_settings
from ui.dialogs.qr_code_dialog import QRCodeDialog
import logging

logger = logging.getLogger(__name__)


class AddAccountDialog(ft.AlertDialog):
    """Dialog for adding a new Telegram account with complete authentication flow."""
    
    def __init__(
        self,
        telegram_service,
        db_manager,
        on_success: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None
    ):
        self.telegram_service = telegram_service
        self.db_manager = db_manager
        self.on_success_callback = on_success
        self.on_cancel_callback = on_cancel
        
        # State management
        self.state = "method_selection"  # method_selection, phone_input, qr_scanning, otp_input, password_input, loading, error
        self.submitted_phone: Optional[str] = None
        self.current_phone: Optional[str] = None
        self.login_method = "phone"  # "phone" or "qr"
        
        # QR code dialog reference
        self._qr_dialog = None
        self._qr_cancelled = False
        self._qr_token = None
        
        # Async task tracking for proper cleanup
        self._auth_task: Optional[asyncio.Task] = None
        self._is_closing = False
        
        # OTP and password event handling
        self._otp_event: Optional[threading.Event] = None
        self._otp_value_container: Optional[dict] = None
        self._password_event: Optional[threading.Event] = None
        self._password_value_container: Optional[dict] = None
        
        # Login method selection
        self.login_method_group = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="phone", label=theme_manager.t("phone_login") or "Phone Login"),
                ft.Radio(value="qr", label=theme_manager.t("qr_code_login") or "QR Code Login"),
            ], spacing=20),
            value="phone",
            on_change=self._on_login_method_change
        )
        
        # Phone instruction text
        self.phone_instruction_text = ft.Text(
            theme_manager.t("enter_phone_number_to_add_account") or "Enter phone number to add a new Telegram account",
            size=14,
            color=theme_manager.text_secondary_color,
            visible=False
        )
        
        # Phone number input field with +855 prefix
        self.phone_input = theme_manager.create_text_field(
            label="",
            hint_text="123456789",
            autofocus=False,
            on_submit=self._handle_submit,
            on_change=self._handle_phone_change
        )
        
        # Create phone field with prefix UI
        prefix_container = ft.Container(
            content=ft.Text("+855", size=16, weight=ft.FontWeight.BOLD, color=theme_manager.text_color),
            padding=ft.padding.symmetric(horizontal=12, vertical=16),
            alignment=ft.alignment.center_left,
            bgcolor=theme_manager.surface_color,
            border=ft.border.only(
                left=ft.BorderSide(1, theme_manager.border_color),
                top=ft.BorderSide(1, theme_manager.border_color),
                bottom=ft.BorderSide(1, theme_manager.border_color)
            ),
            border_radius=ft.border_radius.only(top_left=theme_manager.corner_radius, bottom_left=theme_manager.corner_radius),
            height=56
        )
        
        self.phone_input.label = None
        
        self.phone_field = ft.Column([
            ft.Text(theme_manager.t("phone_number"), size=12, color=theme_manager.text_secondary_color),
            ft.Row([
                prefix_container,
                ft.Container(
                    content=self.phone_input,
                    expand=True,
                    border=ft.border.only(
                        right=ft.BorderSide(1, theme_manager.border_color),
                        top=ft.BorderSide(1, theme_manager.border_color),
                        bottom=ft.BorderSide(1, theme_manager.border_color)
                    ),
                    border_radius=ft.border_radius.only(top_right=theme_manager.corner_radius, bottom_right=theme_manager.corner_radius),
                )
            ], spacing=0, tight=True)
        ], spacing=4, tight=True)
        
        # OTP input field
        self.otp_field = theme_manager.create_text_field(
            label=theme_manager.t("enter_otp_code"),
            hint_text="12345",
            value="",
            visible=False,
            autofocus=False,
            on_submit=self._handle_otp_submit
        )
        
        self.otp_helper = ft.Text(
            theme_manager.t("enter_otp_code_instructions") or "Enter the code sent to your Telegram app",
            size=12,
            color=theme_manager.text_secondary_color,
            visible=False
        )
        
        # 2FA password field
        self.password_field = theme_manager.create_text_field(
            label=theme_manager.t("enter_2fa_password"),
            password=True,
            value="",
            visible=False,
            autofocus=False,
            on_submit=self._handle_password_submit
        )
        
        self.password_helper = ft.Text(
            theme_manager.t("enter_2fa_password_instructions") or "Enter your 2FA password",
            size=12,
            color=theme_manager.text_secondary_color,
            visible=False
        )
        
        # Loading indicator
        self.loading_indicator = ft.ProgressRing(
            visible=False,
            width=40,
            height=40
        )
        
        self.loading_text = ft.Text(
            "",
            size=14,
            color=theme_manager.text_secondary_color,
            visible=False
        )
        
        # Error message
        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED,
            visible=False,
            size=12
        )
        
        # Submit button (will change text based on state)
        self.submit_btn = ft.ElevatedButton(
            theme_manager.t("continue") or "Continue",
            on_click=self._handle_submit,
            icon=ft.Icons.ARROW_FORWARD
        )
        
        # Create dialog
        super().__init__(
            modal=True,
            title=ft.Text(theme_manager.t("add_account") or "Add Account"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        theme_manager.t("choose_login_method") or "Choose login method:",
                        size=14,
                        color=theme_manager.text_secondary_color,
                        weight=ft.FontWeight.BOLD
                    ),
                    self.login_method_group,
                    ft.Container(height=10),
                    self.phone_instruction_text,
                    self.phone_field,
                    self.otp_field,
                    self.otp_helper,
                    self.password_field,
                    self.password_helper,
                    ft.Row([
                        self.loading_indicator,
                        self.loading_text,
                    ], spacing=10),
                    self.error_text,
                ], spacing=15, tight=True),
                width=400,
                padding=20
            ),
            actions=[
                ft.TextButton(
                    theme_manager.t("cancel"),
                    on_click=self._handle_cancel
                ),
                self.submit_btn,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _on_login_method_change(self, e):
        """Handle login method change."""
        self.login_method = self.login_method_group.value
        # Show/hide phone field and instruction text based on method
        phone_visible = (self.login_method == "phone")
        self.phone_field.visible = phone_visible
        if hasattr(self, 'phone_instruction_text'):
            self.phone_instruction_text.visible = phone_visible
        if self.page:
            self.page.update()
    
    def _handle_phone_change(self, e):
        """Handle phone number input change - remove leading zero."""
        if self.phone_input.value and self.phone_input.value.startswith("0"):
            self.phone_input.value = self.phone_input.value.lstrip("0")
            if self.page:
                self.page.update()
    
    def _handle_submit(self, e):
        """Handle submit button click or Enter key."""
        if self.state == "method_selection":
            # Start authentication based on selected method
            if self.login_method == "qr":
                self._handle_qr_login()
            else:
                self._handle_phone_submit()
        elif self.state == "phone_input":
            self._handle_phone_submit()
        elif self.state == "otp_input":
            self._handle_otp_submit(e)
        elif self.state == "password_input":
            self._handle_password_submit(e)
    
    def _handle_qr_login(self):
        """Handle QR code login initiation."""
        # Check if API credentials are configured
        if not app_settings.has_telegram_credentials:
            self._show_error("Please configure API credentials first in Settings > Configuration")
            return
        
        # Cancel any existing auth task
        if self._auth_task and not self._auth_task.done():
            self._auth_task.cancel()
        
        # Start QR code authentication flow
        if self.page and hasattr(self.page, 'run_task'):
            # Use run_task which should handle coroutine wrapping
            self._auth_task = self.page.run_task(
                self._authenticate_telegram_qr,
                app_settings.telegram_api_id,
                app_settings.telegram_api_hash
            )
        else:
            # Fallback: create task directly
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._auth_task = loop.create_task(
                    self._authenticate_telegram_qr(
                        app_settings.telegram_api_id,
                        app_settings.telegram_api_hash
                    )
                )
            else:
                self._auth_task = asyncio.create_task(
                    self._authenticate_telegram_qr(
                        app_settings.telegram_api_id,
                        app_settings.telegram_api_hash
                    )
                )
    
    def _handle_phone_submit(self):
        """Handle phone number submission."""
        phone_input = self.phone_input.value.strip() if self.phone_input.value else ""
        
        # Remove leading zero if present
        if phone_input.startswith("0"):
            phone_input = phone_input.lstrip("0")
        
        if not phone_input:
            self._show_error(theme_manager.t("phone_number_required") or "Phone number is required")
            return
        
        # Add +855 prefix
        phone = f"+855{phone_input}"
        
        # Validate phone number format
        valid, error = validate_phone(phone)
        if not valid:
            self._show_error(error)
            return
        
        # Check if API credentials are configured
        if not app_settings.has_telegram_credentials:
            self._show_error("Please configure API credentials first in Settings > Configuration")
            return
        
        self.current_phone = phone
        self.submitted_phone = phone
        
        # Cancel any existing auth task
        if self._auth_task and not self._auth_task.done():
            self._auth_task.cancel()
        
        # Start authentication flow
        if self.page and hasattr(self.page, 'run_task'):
            # Use run_task which should handle coroutine wrapping
            self._auth_task = self.page.run_task(
                self._authenticate_telegram,
                phone,
                app_settings.telegram_api_id,
                app_settings.telegram_api_hash
            )
        else:
            # Fallback: create task directly
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._auth_task = loop.create_task(
                    self._authenticate_telegram(
                        phone,
                        app_settings.telegram_api_id,
                        app_settings.telegram_api_hash
                    )
                )
            else:
                self._auth_task = asyncio.create_task(
                    self._authenticate_telegram(
                        phone,
                        app_settings.telegram_api_id,
                        app_settings.telegram_api_hash
                    )
                )
    
    def _handle_otp_submit(self, e):
        """Handle OTP submission."""
        otp_code = self.otp_field.value.strip() if self.otp_field.value else ""
        
        if not otp_code:
            self._show_error("OTP code is required")
            return
        
        # Set OTP value and signal event
        if self._otp_value_container:
            self._otp_value_container["value"] = otp_code
        if self._otp_event:
            self._otp_event.set()
    
    def _handle_password_submit(self, e):
        """Handle 2FA password submission."""
        password = self.password_field.value.strip() if self.password_field.value else ""
        
        if not password:
            self._show_error("2FA password is required")
            return
        
        # Set password value and signal event
        if self._password_value_container:
            self._password_value_container["value"] = password
        if self._password_event:
            self._password_event.set()
    
    def _transition_to_otp(self):
        """Transition dialog to OTP input state."""
        self.state = "otp_input"
        self.phone_field.visible = False
        self.otp_field.visible = True
        self.otp_helper.visible = True
        self.password_field.visible = False
        self.password_helper.visible = False
        self.loading_indicator.visible = False
        self.loading_text.visible = False
        self.error_text.visible = False
        
        # Update button
        self.submit_btn.text = theme_manager.t("confirm") or "Confirm"
        self.submit_btn.icon = ft.Icons.CHECK
        self.submit_btn.disabled = False
        
        # Update title
        self.title.value = theme_manager.t("enter_otp_code") or "Enter OTP Code"
        
        # Focus OTP field
        self.otp_field.autofocus = True
        
        if self.page:
            self.page.update()
    
    def _transition_to_password(self):
        """Transition dialog to 2FA password input state."""
        self.state = "password_input"
        self.phone_field.visible = False
        self.otp_field.visible = False
        self.otp_helper.visible = False
        self.password_field.visible = True
        self.password_helper.visible = True
        self.loading_indicator.visible = False
        self.loading_text.visible = False
        self.error_text.visible = False
        
        # Update button
        self.submit_btn.text = theme_manager.t("confirm") or "Confirm"
        self.submit_btn.icon = ft.Icons.CHECK
        self.submit_btn.disabled = False
        
        # Update title
        self.title.value = theme_manager.t("enter_2fa_password") or "Enter 2FA Password"
        
        # Focus password field
        self.password_field.autofocus = True
        
        if self.page:
            self.page.update()
    
    def _show_loading(self, message: str = ""):
        """Show loading state."""
        self.state = "loading"
        self.phone_field.visible = False
        self.otp_field.visible = False
        self.otp_helper.visible = False
        self.password_field.visible = False
        self.password_helper.visible = False
        self.loading_indicator.visible = True
        self.loading_text.value = message or theme_manager.t("authenticating") or "Authenticating..."
        self.loading_text.visible = True
        self.error_text.visible = False
        self.submit_btn.disabled = True
        
        if self.page:
            self.page.update()
    
    def _show_error(self, message: str):
        """Show error message."""
        self.state = "error"
        self.error_text.value = message
        self.error_text.visible = True
        self.loading_indicator.visible = False
        self.loading_text.visible = False
        self.submit_btn.disabled = False
        # Keep current field visibility (don't hide fields on error)
        
        if self.page:
            self.page.update()
    
    async def _authenticate_telegram(self, phone: str, api_id: str, api_hash: str):
        """Authenticate Telegram account with OTP and 2FA support."""
        try:
            # Check if already cancelled
            if self._is_closing:
                return
            
            # Show loading state
            self._show_loading(theme_manager.t("sending_otp") or "Sending OTP code...")
            
            # Setup OTP callback
            otp_event = threading.Event()
            otp_value_container = {"value": None}
            self._otp_event = otp_event
            self._otp_value_container = otp_value_container
            
            def _wait_for_otp_blocking() -> str:
                """Blocking function to wait for OTP."""
                import time
                timeout = 300
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    if otp_event.is_set():
                        value = otp_value_container["value"]
                        logger.info(f"OTP received: {value}")
                        return value or ""
                    time.sleep(0.1)
                
                logger.warning("OTP input timeout")
                return ""
            
            async def get_otp_code() -> str:
                """Get OTP code from dialog."""
                otp_event.clear()
                otp_value_container["value"] = None
                self.otp_field.value = ""
                
                # Transition to OTP input
                self._transition_to_otp()
                
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, _wait_for_otp_blocking)
                return result
            
            # Setup password callback
            password_event = threading.Event()
            password_value_container = {"value": None}
            self._password_event = password_event
            self._password_value_container = password_value_container
            
            def _wait_for_password_blocking() -> str:
                """Blocking function to wait for 2FA password."""
                import time
                timeout = 300
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    if password_event.is_set():
                        value = password_value_container["value"]
                        logger.info("2FA password received")
                        return value or ""
                    time.sleep(0.1)
                
                logger.warning("2FA password input timeout")
                return ""
            
            async def get_2fa_password() -> str:
                """Get 2FA password from dialog."""
                password_event.clear()
                password_value_container["value"] = None
                self.password_field.value = ""
                
                # Transition to password input
                self._transition_to_password()
                
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, _wait_for_password_blocking)
                return result
            
            # Start session
            self._show_loading(theme_manager.t("authenticating") or "Authenticating...")
            success, error = await self.telegram_service.start_session(
                phone=phone,
                api_id=api_id,
                api_hash=api_hash,
                code_callback=get_otp_code,
                password_callback=get_2fa_password
            )
            
            # Check if cancelled before proceeding
            if self._is_closing:
                return
            
            if success:
                # Account saved automatically by telegram_service.start_session
                # (save_telegram_credential handles duplicates with ON CONFLICT UPDATE)
                logger.info(f"Account {phone} authenticated and saved successfully")
                
                # Close dialog
                if not self._is_closing:
                    self.open = False
                    if self.page:
                        self.page.update()
                    
                    # Call success callback
                    if self.on_success_callback:
                        self.on_success_callback(phone)
            else:
                # Show error and allow retry
                if not self._is_closing:
                    error_msg = error or theme_manager.t("authentication_failed") or "Authentication failed. Please try again."
                    self._show_error(error_msg)
                    # Reset to phone input for retry
                    self.state = "phone_input"
                    self.phone_field.visible = True
                    self.otp_field.visible = False
                    self.otp_helper.visible = False
                    self.password_field.visible = False
                    self.password_helper.visible = False
                    self.submit_btn.text = theme_manager.t("add_account") or "Add Account"
                    self.submit_btn.icon = ft.Icons.ADD
                    self.title.value = theme_manager.t("add_account") or "Add Account"
                
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            logger.info("Phone authentication cancelled")
            raise  # Re-raise to properly handle cancellation
        except Exception as e:
            logger.error(f"Error authenticating Telegram account: {e}", exc_info=True)
            if not self._is_closing:
                self._show_error(f"Error: {str(e)}")
                # Reset to phone input
                self.state = "phone_input"
                self.phone_field.visible = True
                self.otp_field.visible = False
                self.otp_helper.visible = False
                self.password_field.visible = False
                self.password_helper.visible = False
                self.submit_btn.text = theme_manager.t("add_account") or "Add Account"
                self.submit_btn.icon = ft.Icons.ADD
                self.title.value = theme_manager.t("add_account") or "Add Account"
    
    async def _authenticate_telegram_qr(self, api_id: str, api_hash: str):
        """Authenticate Telegram account via QR code."""
        try:
            # Check if already cancelled
            if self._is_closing or self._qr_cancelled:
                return
            
            self._show_loading(theme_manager.t("generating_qr_code") or "Generating QR code...")
            self._qr_cancelled = False
            self._qr_token = None
            
            # Check again after UI update
            if self._is_closing:
                return
            
            # Create QR code dialog
            self._qr_dialog = QRCodeDialog(
                qr_token="",
                on_cancel=self._on_qr_dialog_cancel,
                on_refresh=self._on_qr_dialog_refresh
            )
            self._qr_dialog.page = self.page
            
            # Open QR dialog
            if self.page and not self._is_closing:
                try:
                    self.page.open(self._qr_dialog)
                except Exception:
                    if not self._is_closing:
                        self.page.dialog = self._qr_dialog
                        self._qr_dialog.open = True
                        self.page.update()
            
            await asyncio.sleep(0.1)
            
            # Check cancellation after sleep
            if self._is_closing or self._qr_cancelled:
                return
            
            def qr_callback(token: str):
                """Callback to update QR code in dialog."""
                if not self._is_closing and self._qr_dialog and not self._qr_cancelled:
                    try:
                        self._qr_dialog.refresh_qr_code(token)
                        self._qr_token = token
                    except Exception:
                        pass  # Dialog may be closed
            
            def status_callback(status: str):
                """Callback to update status in dialog."""
                if not self._is_closing and self._qr_dialog and not self._qr_cancelled:
                    try:
                        is_success = "success" in status.lower() or "successful" in status.lower()
                        self._qr_dialog.update_status(status, is_success=is_success)
                    except Exception:
                        pass  # Dialog may be closed
            
            async def password_callback() -> str:
                """Callback to get 2FA password."""
                if self._is_closing:
                    return ""
                
                if self._qr_dialog:
                    try:
                        self._qr_dialog.update_status("Two-factor authentication required. Please enter your password.", is_error=False)
                    except Exception:
                        pass  # Dialog may be closed
                
                # Show password input in main dialog
                password_event = threading.Event()
                password_value_container = {"value": None}
                self._password_event = password_event
                self._password_value_container = password_value_container
                
                # Transition to password input
                if not self._is_closing:
                    self._transition_to_password()
                
                # Wait for password (async)
                def _wait_for_password_blocking() -> str:
                    """Blocking function to wait for 2FA password."""
                    import time
                    timeout = 300
                    start_time = time.time()
                    
                    while time.time() - start_time < timeout:
                        if self._is_closing or self._qr_cancelled:
                            return ""
                        if password_event.is_set():
                            value = password_value_container["value"]
                            return value or ""
                        time.sleep(0.1)
                    
                    return ""
                
                if self._is_closing:
                    return ""
                
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, _wait_for_password_blocking)
                return result
            
            def cancelled_callback() -> bool:
                """Callback to check if cancelled."""
                return self._qr_cancelled
            
            # Start QR session
            try:
                success, error, phone_number = await self.telegram_service.start_session_qr(
                    api_id=api_id,
                    api_hash=api_hash,
                    qr_callback=qr_callback,
                    status_callback=status_callback,
                    password_callback=password_callback,
                    cancelled_callback=cancelled_callback
                )
            except asyncio.CancelledError:
                # Task was cancelled, clean up and return
                logger.info("QR authentication task cancelled")
                if self._qr_dialog and self.page and not self._is_closing:
                    try:
                        if hasattr(self.page, 'close'):
                            self.page.close(self._qr_dialog)
                        else:
                            self._qr_dialog.open = False
                            if self.page.dialog == self._qr_dialog:
                                self.page.dialog = None
                            self.page.update()
                    except Exception:
                        pass
                raise  # Re-raise to properly handle cancellation
            
            # Close QR dialog
            if self._qr_dialog and self.page and not self._is_closing:
                try:
                    if hasattr(self.page, 'close'):
                        self.page.close(self._qr_dialog)
                    else:
                        self._qr_dialog.open = False
                        if self.page.dialog == self._qr_dialog:
                            self.page.dialog = None
                        self.page.update()
                except Exception:
                    pass
            
            # Check if cancelled before proceeding
            if self._is_closing or self._qr_cancelled:
                return
            
            if success:
                # Account saved automatically by telegram_service.start_session_qr
                logger.info(f"Account {phone_number} authenticated via QR code and saved successfully")
                self.submitted_phone = phone_number
                
                # Close dialog
                if not self._is_closing:
                    self.open = False
                    if self.page:
                        self.page.update()
                    
                    # Call success callback
                    if self.on_success_callback:
                        self.on_success_callback(phone_number)
            else:
                # Show error and allow retry
                if not self._is_closing:
                    error_msg = error or theme_manager.t("authentication_failed") or "Authentication failed. Please try again."
                    self._show_error(error_msg)
                    # Reset to method selection
                    self.state = "method_selection"
                    self.phone_field.visible = (self.login_method == "phone")
                    self.submit_btn.text = theme_manager.t("add_account") or "Add Account"
                    self.submit_btn.icon = ft.Icons.ADD
                    self.title.value = theme_manager.t("add_account") or "Add Account"
                
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            logger.info("QR authentication cancelled")
            if self._qr_dialog and self.page and not self._is_closing:
                try:
                    if hasattr(self.page, 'close'):
                        self.page.close(self._qr_dialog)
                    else:
                        self._qr_dialog.open = False
                        if self.page.dialog == self._qr_dialog:
                            self.page.dialog = None
                        self.page.update()
                except Exception:
                    pass
            raise  # Re-raise to properly handle cancellation
        except Exception as e:
            logger.error(f"Error authenticating Telegram account via QR: {e}", exc_info=True)
            if not self._is_closing:
                self._show_error(f"Error: {str(e)}")
                # Reset to method selection
                self.state = "method_selection"
                self.phone_field.visible = (self.login_method == "phone")
                self.submit_btn.text = theme_manager.t("add_account") or "Add Account"
                self.submit_btn.icon = ft.Icons.ADD
                self.title.value = theme_manager.t("add_account") or "Add Account"
    
    def _on_qr_dialog_cancel(self):
        """Handle QR dialog cancellation."""
        self._qr_cancelled = True
    
    def _on_qr_dialog_refresh(self) -> str:
        """Handle QR dialog refresh request."""
        return self._qr_token or ""
    
    def _handle_cancel(self, e):
        """Handle cancel button click."""
        # Mark as closing to prevent further UI updates
        self._is_closing = True
        self._qr_cancelled = True
        
        # Cancel any running auth task
        if self._auth_task and not self._auth_task.done():
            self._auth_task.cancel()
        
        # Close QR dialog if open
        if self._qr_dialog and self.page:
            try:
                if hasattr(self.page, 'close'):
                    self.page.close(self._qr_dialog)
                else:
                    self._qr_dialog.open = False
                    if self.page.dialog == self._qr_dialog:
                        self.page.dialog = None
                    self.page.update()
            except Exception:
                pass
        
        self.submitted_phone = None
        self.current_phone = None
        self.open = False
        if self.on_cancel_callback:
            self.on_cancel_callback()
        if self.page:
            self.page.update()
    
    def get_phone(self) -> Optional[str]:
        """Get the submitted phone number."""
        return self.submitted_phone
