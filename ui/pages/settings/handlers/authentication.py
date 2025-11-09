"""
Authentication handlers for Telegram connection.
"""

import asyncio
import logging
import threading
import time
import flet as ft
from ui.theme import theme_manager
from utils.validators import validate_phone
from ui.dialogs.qr_code_dialog import QRCodeDialog
from ui.pages.settings.handlers.dialogs import DialogHandlerMixin

logger = logging.getLogger(__name__)


class AuthenticationHandlerMixin(DialogHandlerMixin):
    """Handlers for Telegram authentication."""
    
    def handle_telegram_connect(
        self,
        phone_field: ft.TextField,
        error_text: ft.Text
    ):
        """Handle Telegram connection."""
        # Get page from control if not set
        if not self.page and error_text.page:
            self.page = error_text.page
        
        if not self.telegram_service:
            self._show_error("Telegram service not available", error_text)
            return
        
        if not self.current_settings.telegram_api_id or not self.current_settings.telegram_api_hash:
            self._show_error("Please save API credentials first", error_text)
            return
        
        # Get phone input - handle both old TextField and new Column structure
        phone_input = phone_field
        if isinstance(phone_field, ft.Column):
            # New structure: use phone_input directly from authenticate_tab
            if hasattr(self.authenticate_tab, 'phone_input'):
                phone_input = self.authenticate_tab.phone_input
            else:
                # Try to extract from Column structure
                try:
                    row = phone_field.controls[1].controls[0]
                    if len(row.controls) > 1 and hasattr(row.controls[1].content, 'value'):
                        phone_input = row.controls[1].content
                except (IndexError, AttributeError):
                    pass
        
        phone = phone_input.value.strip() if phone_input.value else ""
        
        # Remove leading zero if present
        if phone.startswith("0"):
            phone = phone.lstrip("0")
        
        if not phone:
            self._show_error("Phone number is required", error_text)
            return
        
        # Add +855 prefix
        phone = f"+855{phone}"
        
        valid, error = validate_phone(phone)
        if not valid:
            self._show_error(error, error_text)
            return
        
        try:
            if self.page and hasattr(self.page, 'run_task'):
                self.page.run_task(
                    self._connect_telegram_async,
                    phone,
                    self.current_settings.telegram_api_id,
                    self.current_settings.telegram_api_hash,
                    error_text
                )
            else:
                asyncio.create_task(
                    self._connect_telegram_async(
                        phone,
                        self.current_settings.telegram_api_id,
                        self.current_settings.telegram_api_hash,
                        error_text
                    )
                )
        except Exception as e:
            logger.error(f"Error starting phone login: {e}", exc_info=True)
            self._show_error(f"Error: {str(e)}", error_text)
    
    async def _connect_telegram_async(
        self,
        phone: str,
        api_id: str,
        api_hash: str,
        error_text: ft.Text
    ):
        """Async method to connect to Telegram."""
        try:
            connect_btn = self.authenticate_tab.connect_btn
            connect_btn.disabled = True
            connect_btn.text = theme_manager.t("connecting")
            error_text.visible = False
            if self.page:
                self.page.update()
            
            otp_event = threading.Event()
            otp_value_container = {"value": None}
            
            def _wait_for_otp_blocking() -> str:
                """Blocking function to wait for OTP - runs in thread executor."""
                timeout = 300
                start_time = time.time()
                event_set = False
                
                while time.time() - start_time < timeout:
                    if otp_event.is_set():
                        event_set = True
                        break
                    time.sleep(0.1)
                
                if event_set:
                    value = otp_value_container["value"]
                    logger.info(f"✓ OTP received from user: {value}")
                    return value or ""
                
                logger.warning("OTP input timeout - no response from user")
                return ""
            
            async def get_otp_code() -> str:
                """Get OTP code from text field."""
                otp_event.clear()
                otp_value_container["value"] = None
                self.authenticate_tab.otp_field.value = ""
                
                # Update helper text to inform user where to find code
                # (will be updated after code request if sent via app)
                if hasattr(self.authenticate_tab, 'otp_helper'):
                    self.authenticate_tab.otp_helper.value = (
                        theme_manager.t("enter_otp_code_instructions") or 
                        "Enter the code sent to your phone or Telegram app"
                    )
                
                self._otp_event = otp_event
                self._otp_value_container = otp_value_container
                self._waiting_for_otp = True
                self.authenticate_tab.otp_submit_btn.disabled = False
                
                if self.page:
                    self.page.update()
                
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, _wait_for_otp_blocking)
                
                self._waiting_for_otp = False
                return result
            
            password_event = threading.Event()
            password_value_container = {"value": None}
            
            def on_password_submit(e):
                """Handle password submit (button click or Enter key)."""
                value = self.authenticate_tab.password_field.value
                if value and len(value.strip()) > 0:
                    password_value_container["value"] = value.strip()
                    password_event.set()
                    logger.info("2FA password submitted via button/Enter")
            
            self.authenticate_tab.password_field.on_submit = on_password_submit
            self.authenticate_tab.password_submit_btn.on_click = on_password_submit
            
            def _wait_for_password_blocking() -> str:
                """Blocking function to wait for 2FA password - runs in thread executor."""
                timeout = 300
                start_time = time.time()
                event_set = False
                
                while time.time() - start_time < timeout:
                    if password_event.is_set():
                        event_set = True
                        break
                    time.sleep(0.1)
                
                if event_set:
                    value = password_value_container["value"]
                    logger.info("2FA password received from user")
                    return value or ""
                
                logger.warning("2FA password input timeout")
                return ""
            
            async def get_2fa_password() -> str:
                """Get 2FA password from text field."""
                password_event.clear()
                password_value_container["value"] = None
                
                page_ref = self.page
                if not page_ref:
                    if hasattr(self.authenticate_tab, 'page') and self.authenticate_tab.page:
                        page_ref = self.authenticate_tab.page
                        self.page = page_ref
                    elif hasattr(self.authenticate_tab.password_field, 'page') and self.authenticate_tab.password_field.page:
                        page_ref = self.authenticate_tab.password_field.page
                        self.page = page_ref
                
                self.authenticate_tab.password_field.visible = True
                self.authenticate_tab.password_helper.visible = True
                self.authenticate_tab.password_submit_btn.visible = True
                self.authenticate_tab.password_field.value = ""
                
                if page_ref:
                    try:
                        page_ref.update()
                    except Exception as update_error:
                        logger.error(f"Error updating page: {update_error}", exc_info=True)
                        if hasattr(page_ref, 'run_task'):
                            async def update_ui():
                                page_ref.update()
                            page_ref.run_task(update_ui)
                else:
                    logger.error("No page available to show password field!")
                
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, _wait_for_password_blocking)
                
                self.authenticate_tab.password_field.visible = False
                self.authenticate_tab.password_helper.visible = False
                self.authenticate_tab.password_submit_btn.visible = False
                if self.page:
                    self.page.update()
                
                return result
            
            # Check activity limits before adding account
            auth_service = self._get_auth_service()
            user_email = None
            if auth_service:
                user_email = auth_service.get_user_email()
                if user_email:
                    can_perform, error_msg = self._check_account_activity_limit(user_email)
                    if not can_perform:
                        self._show_error(
                            error_msg or theme_manager.t("account_addition_limit_reached"),
                            error_text
                        )
                        connect_btn.disabled = False
                        connect_btn.text = theme_manager.t("connect_to_telegram")
                        if self.page:
                            self.page.update()
                        return
            
            success, error = await self.telegram_service.start_session(
                phone=phone,
                api_id=api_id,
                api_hash=api_hash,
                code_callback=get_otp_code,
                password_callback=get_2fa_password
            )
            
            if success:
                # Log account addition in activity log
                if user_email:
                    try:
                        self.db_manager.log_account_action(
                            user_email=user_email,
                            action='add',
                            phone_number=phone
                        )
                    except Exception as e:
                        logger.error(f"Error logging account addition: {e}")
                        # Continue even if logging fails
                
                self.authenticate_tab.update_status()
                # Remove +855 prefix if present
                phone_without_prefix = phone.replace("+855", "").lstrip("0")
                if hasattr(self.authenticate_tab, 'phone_input'):
                    self.authenticate_tab.phone_input.value = phone_without_prefix
                elif hasattr(self.authenticate_tab, 'phone_field'):
                    # Fallback for old structure
                    if isinstance(self.authenticate_tab.phone_field, ft.TextField):
                        self.authenticate_tab.phone_field.value = phone
                self.authenticate_tab.update_connection_buttons()
                
                if self.page:
                    theme_manager.show_snackbar(
                        self.page,
                        theme_manager.t("connection_success"),
                        bgcolor=ft.Colors.GREEN
                    )
            else:
                self._show_error(f"{theme_manager.t('connection_failed')}: {error}", error_text)
            
            connect_btn.disabled = False
            connect_btn.text = theme_manager.t("connect_to_telegram")
            if self.page:
                self.page.update()
                
        except Exception as ex:
            logger.error(f"Error connecting to Telegram: {ex}")
            self._show_error(f"{theme_manager.t('connection_failed')}: {str(ex)}", error_text)
            self.authenticate_tab.connect_btn.disabled = False
            self.authenticate_tab.connect_btn.text = theme_manager.t("connect_to_telegram")
            if self.page:
                self.page.update()
    
    def handle_telegram_connect_qr(self, error_text: ft.Text):
        """Handle Telegram connection via QR code."""
        if not self.page and error_text.page:
            self.page = error_text.page
        
        if not self.telegram_service:
            self._show_error("Telegram service not available", error_text)
            return
        
        if not self.current_settings.telegram_api_id or not self.current_settings.telegram_api_hash:
            self._show_error("Please save API credentials first", error_text)
            return
        
        try:
            if self.page and hasattr(self.page, 'run_task'):
                self.page.run_task(
                    self._connect_telegram_qr_async,
                    self.current_settings.telegram_api_id,
                    self.current_settings.telegram_api_hash,
                    error_text
                )
            else:
                asyncio.create_task(
                    self._connect_telegram_qr_async(
                        self.current_settings.telegram_api_id,
                        self.current_settings.telegram_api_hash,
                        error_text
                    )
                )
        except Exception as e:
            logger.error(f"Error starting QR login: {e}", exc_info=True)
            self._show_error(f"Error: {str(e)}", error_text)
    
    async def _connect_telegram_qr_async(
        self,
        api_id: str,
        api_hash: str,
        error_text: ft.Text
    ):
        """Async method to connect to Telegram via QR code."""
        try:
            connect_btn = self.authenticate_tab.connect_btn
            connect_btn.disabled = True
            connect_btn.text = theme_manager.t("connecting")
            error_text.visible = False
            self._qr_cancelled = False
            self._qr_token = None
            
            if not self.page:
                if hasattr(error_text, 'page') and error_text.page:
                    self.page = error_text.page
                    logger.debug("Got page from error_text")
                else:
                    logger.error("No page reference available for QR dialog")
                    self._show_error("Page not available", error_text)
                    connect_btn.disabled = False
                    connect_btn.text = theme_manager.t("connect_to_telegram")
                    return
            
            logger.debug(f"Opening QR code dialog. Page: {self.page}, Page type: {type(self.page)}")
            
            if self.page:
                self.page.update()
            
            self._qr_dialog = QRCodeDialog(
                qr_token="",
                on_cancel=self._on_qr_dialog_cancel,
                on_refresh=self._on_qr_dialog_refresh
            )
            
            self._qr_dialog.page = self.page
            
            try:
                logger.debug("Calling page.open() for QR dialog")
                self.page.open(self._qr_dialog)
                logger.info("QR code dialog opened successfully using page.open()")
            except AttributeError:
                logger.debug("page.open() not available, using page.dialog method")
                self.page.dialog = self._qr_dialog
                self._qr_dialog.open = True
                self.page.update()
                logger.info("QR code dialog opened using page.dialog method")
            except Exception as dialog_error:
                logger.error(f"Error opening QR dialog: {dialog_error}", exc_info=True)
                self.page.dialog = self._qr_dialog
                self._qr_dialog.open = True
                self.page.update()
                logger.info("QR code dialog opened using fallback method")
            
            await asyncio.sleep(0.1)
            
            def qr_callback(token: str):
                """Callback to update QR code in dialog."""
                logger.info(f"qr_callback invoked with token (len={len(token) if token else 0})")
                if self._qr_dialog and not self._qr_cancelled:
                    logger.info("Calling refresh_qr_code on dialog")
                    self._qr_dialog.refresh_qr_code(token)
                    self._qr_token = token
                else:
                    logger.warning(f"qr_callback skipped - dialog={self._qr_dialog is not None}, cancelled={self._qr_cancelled}")
            
            def status_callback(status: str):
                """Callback to update status in dialog."""
                logger.info(f"Status callback called with: {status}")
                if self._qr_dialog and not self._qr_cancelled:
                    is_success = "success" in status.lower() or "successful" in status.lower()
                    
                    if not self._qr_dialog.page and self.page:
                        self._qr_dialog.page = self.page
                        logger.debug("Set page reference on dialog from status callback")
                    
                    try:
                        self._qr_dialog.update_status(status, is_success=is_success)
                        logger.info(f"Dialog status updated to: {status} (success={is_success})")
                    except Exception as e:
                        logger.error(f"Error updating dialog status: {e}", exc_info=True)
                        try:
                            if self.page:
                                self._qr_dialog.status_text.value = status
                                if is_success:
                                    self._qr_dialog.status_text.color = ft.Colors.GREEN
                                self.page.update()
                                logger.info(f"Dialog status updated via page.update() to: {status}")
                        except Exception as e2:
                            logger.error(f"Error in alternative UI update: {e2}", exc_info=True)
                else:
                    logger.debug(f"Dialog not available or cancelled, ignoring status: {status}")
            
            def password_callback() -> str:
                """Callback to get 2FA password."""
                logger.info("2FA password required, showing password dialog")
                if self._qr_dialog:
                    self._qr_dialog.update_status("Two-factor authentication required. Please enter your password.", is_error=False)
                
                password = self._show_auth_dialog_nested(is_2fa=True, main_dialog=self._qr_dialog)
                
                return password
            
            def cancelled_callback() -> bool:
                """Callback to check if cancelled."""
                return self._qr_cancelled
            
            # Check activity limits before adding account
            auth_service = self._get_auth_service()
            user_email = None
            if auth_service:
                user_email = auth_service.get_user_email()
                if user_email:
                    can_perform, error_msg = self._check_account_activity_limit(user_email)
                    if not can_perform:
                        # Close QR dialog
                        if self._qr_dialog and self.page:
                            try:
                                if hasattr(self.page, 'close') and hasattr(self.page, 'overlay'):
                                    if self._qr_dialog in getattr(self.page.overlay, 'controls', []):
                                        self.page.close(self._qr_dialog)
                                else:
                                    self._qr_dialog.open = False
                                    if self.page.dialog == self._qr_dialog:
                                        self.page.dialog = None
                                self.page.update()
                            except:
                                pass
                        self._show_error(
                            error_msg or theme_manager.t("account_addition_limit_reached"),
                            error_text
                        )
                        connect_btn.disabled = False
                        connect_btn.text = theme_manager.t("connect_to_telegram")
                        if self.page:
                            self.page.update()
                        return
            
            success, error, phone_number = await self.telegram_service.start_session_qr(
                api_id=api_id,
                api_hash=api_hash,
                qr_callback=qr_callback,
                status_callback=status_callback,
                password_callback=password_callback,
                cancelled_callback=cancelled_callback
            )
            
            if self._qr_dialog and self.page:
                try:
                    if hasattr(self.page, 'close') and hasattr(self.page, 'overlay'):
                        if self._qr_dialog in getattr(self.page.overlay, 'controls', []):
                            self.page.close(self._qr_dialog)
                    else:
                        self._qr_dialog.open = False
                        if self.page.dialog == self._qr_dialog:
                            self.page.dialog = None
                    self.page.update()
                except Exception as close_error:
                    logger.debug(f"Error closing dialog: {close_error}")
                    self._qr_dialog.open = False
                    if self.page.dialog == self._qr_dialog:
                        self.page.dialog = None
                    self.page.update()
            
            if success:
                # Log account addition in activity log
                if user_email and phone_number:
                    try:
                        self.db_manager.log_account_action(
                            user_email=user_email,
                            action='add',
                            phone_number=phone_number
                        )
                    except Exception as e:
                        logger.error(f"Error logging account addition: {e}")
                        # Continue even if logging fails
                
                self.authenticate_tab.update_status()
                if phone_number:
                    # Remove +855 prefix if present
                    phone_without_prefix = phone_number.replace("+855", "").lstrip("0")
                    if hasattr(self.authenticate_tab, 'phone_input'):
                        self.authenticate_tab.phone_input.value = phone_without_prefix
                    elif hasattr(self.authenticate_tab, 'phone_field'):
                        # Fallback for old structure
                        if isinstance(self.authenticate_tab.phone_field, ft.TextField):
                            self.authenticate_tab.phone_field.value = phone_number
                self.authenticate_tab.update_connection_buttons()
                
                if self.page:
                    theme_manager.show_snackbar(
                        self.page,
                        theme_manager.t("connection_success"),
                        bgcolor=ft.Colors.GREEN
                    )
            else:
                if not self._qr_cancelled:
                    self._show_error(f"{theme_manager.t('connection_failed')}: {error}", error_text)
            
            connect_btn.disabled = False
            connect_btn.text = theme_manager.t("connect_to_telegram")
            if self.page:
                self.page.update()
                
        except Exception as ex:
            logger.error(f"Error connecting to Telegram via QR: {ex}", exc_info=True)
            if self._qr_dialog and self.page:
                try:
                    if hasattr(self.page, 'close') and hasattr(self.page, 'overlay'):
                        if self._qr_dialog in getattr(self.page.overlay, 'controls', []):
                            self.page.close(self._qr_dialog)
                    else:
                        self._qr_dialog.open = False
                        if self.page.dialog == self._qr_dialog:
                            self.page.dialog = None
                    self.page.update()
                except:
                    pass
            self._show_error(f"{theme_manager.t('connection_failed')}: {str(ex)}", error_text)
            self.authenticate_tab.connect_btn.disabled = False
            self.authenticate_tab.connect_btn.text = theme_manager.t("connect_to_telegram")
            if self.page:
                self.page.update()
    
    def _on_qr_dialog_cancel(self):
        """Handle QR dialog cancellation."""
        self._qr_cancelled = True
    
    def _on_qr_dialog_refresh(self) -> str:
        """Handle QR dialog refresh request."""
        return self._qr_token or ""
    
    def handle_telegram_disconnect(self):
        """Handle Telegram disconnection."""
        if not self.telegram_service:
            return
        
        if self.page and hasattr(self.page, 'run_task'):
            self.page.run_task(self._disconnect_telegram_async)
        else:
            asyncio.create_task(self._disconnect_telegram_async())
    
    async def _disconnect_telegram_async(self):
        """Async method to disconnect from Telegram."""
        try:
            await self.telegram_service.disconnect()
            self.authenticate_tab.update_status()
            self.authenticate_tab.update_connection_buttons()
            
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    "Disconnected successfully",
                    bgcolor=ft.Colors.GREEN
                )
                self.page.update()
        except Exception as ex:
            logger.error(f"Error disconnecting from Telegram: {ex}")
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    f"Error disconnecting: {str(ex)}",
                    bgcolor=ft.Colors.RED
                )
    
    def handle_otp_submit(self, e):
        """Handle OTP submit button click."""
        logger.info("OTP Confirm button clicked!")
        logger.info(f"Waiting for OTP: {self._waiting_for_otp}")
        logger.info(f"OTP event exists: {self._otp_event is not None}")
        logger.info(f"OTP container exists: {self._otp_value_container is not None}")
        
        if not hasattr(self, 'authenticate_tab') or not self.authenticate_tab:
            logger.error("Authenticate tab not available!")
            return
        
        value = self.authenticate_tab.otp_field.value
        logger.info(f"OTP field value: '{value}'")
        logger.info(f"OTP field value length: {len(value.strip()) if value else 0}")
        
        if not self._waiting_for_otp:
            logger.warning("OTP button clicked but not waiting for OTP - showing message to user")
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    "Please click 'Connect to Telegram' first",
                    bgcolor=ft.Colors.ORANGE
                )
            return
        
        if not self._otp_event or not self._otp_value_container:
            logger.error("OTP event or container not set - cannot process OTP")
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    "Error: OTP handler not ready. Please try connecting again.",
                    bgcolor=ft.Colors.RED
                )
            return
        
        if value and len(value.strip()) >= 4:
            self._otp_value_container["value"] = value.strip()
            self._otp_event.set()
            logger.info(f"✓ OTP submitted successfully: {self._otp_value_container['value']}")
        else:
            logger.warning(f"OTP too short: {len(value.strip()) if value else 0} characters (minimum 4)")
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    "OTP code must be at least 4 characters",
                    bgcolor=ft.Colors.RED
                )

