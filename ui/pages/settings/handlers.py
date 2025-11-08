"""
Event handlers for Settings page.
"""

import flet as ft
import asyncio
import logging
import threading
from typing import Optional, Callable, Tuple
from database.models import AppSettings
from ui.theme import theme_manager
from config.settings import settings as app_settings
from utils.validators import (
    validate_telegram_api_id,
    validate_telegram_api_hash,
    validate_file_size,
    validate_delay,
    validate_path,
    validate_phone
)
from ui.dialogs.telegram_auth_dialog import TelegramAuthDialog
from ui.dialogs.qr_code_dialog import QRCodeDialog

logger = logging.getLogger(__name__)


class SettingsHandlers:
    """Event handlers for settings page."""
    
    def __init__(
        self,
        page: Optional[ft.Page],
        telegram_service,
        db_manager,
        current_settings: AppSettings,
        on_settings_changed: Callable[[], None],
        authenticate_tab
    ):
        self.page = page
        self.telegram_service = telegram_service
        self.db_manager = db_manager
        self.current_settings = current_settings
        self.on_settings_changed = on_settings_changed
        self.authenticate_tab = authenticate_tab
        
        # Track authentication state
        self._auth_event = threading.Event()
        self._auth_result: Optional[str] = None
        
        # Track QR code dialog state
        self._qr_dialog: Optional[QRCodeDialog] = None
        self._qr_cancelled = False
        self._qr_token: Optional[str] = None
        
        # Track OTP input state
        self._otp_event: Optional[threading.Event] = None
        self._otp_value_container: Optional[dict] = None
        self._waiting_for_otp = False
    
    def handle_save_authenticate(
        self,
        api_id_field: ft.TextField,
        api_hash_field: ft.TextField,
        error_text: ft.Text
    ):
        """Handle save authenticate settings."""
        error_text.visible = False
        
        api_id = api_id_field.value.strip() if api_id_field.value else ""
        api_hash = api_hash_field.value.strip() if api_hash_field.value else ""
        
        if api_id:
            valid, error = validate_telegram_api_id(api_id)
            if not valid:
                self._show_error(error, error_text)
                return
        
        if api_hash:
            valid, error = validate_telegram_api_hash(api_hash)
            if not valid:
                self._show_error(error, error_text)
                return
        
        new_settings = AppSettings(
            telegram_api_id=api_id if api_id else None,
            telegram_api_hash=api_hash if api_hash else None,
            theme=self.current_settings.theme,
            language=self.current_settings.language,
            corner_radius=self.current_settings.corner_radius,
            download_root_dir=self.current_settings.download_root_dir,
            download_media=self.current_settings.download_media,
            max_file_size_mb=self.current_settings.max_file_size_mb,
            fetch_delay_seconds=self.current_settings.fetch_delay_seconds,
            download_photos=self.current_settings.download_photos,
            download_videos=self.current_settings.download_videos,
            download_documents=self.current_settings.download_documents,
            download_audio=self.current_settings.download_audio
        )
        
        if app_settings.save_settings(new_settings):
            self.current_settings = new_settings
            self.authenticate_tab.update_status()
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("settings_saved"),
                bgcolor=ft.Colors.GREEN
            )
            if self.page:
                self.page.update()
        else:
            self._show_error("Failed to save API credentials", error_text)
    
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
                import time
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
                import time
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
    
    def handle_save_configure(
        self,
        download_dir_field: ft.TextField,
        download_media_switch: ft.Switch,
        max_file_size_slider: ft.Slider,
        fetch_delay_slider: ft.Slider,
        download_photos_cb: ft.Checkbox,
        download_videos_cb: ft.Checkbox,
        download_documents_cb: ft.Checkbox,
        download_audio_cb: ft.Checkbox,
        error_text: ft.Text
    ):
        """Handle save configure settings."""
        error_text.visible = False
        
        download_dir = download_dir_field.value
        max_size = int(max_file_size_slider.value)
        delay = fetch_delay_slider.value
        
        valid, error = validate_path(download_dir)
        if not valid:
            self._show_error(error, error_text)
            return
        
        valid, error = validate_file_size(max_size)
        if not valid:
            self._show_error(error, error_text)
            return
        
        valid, error = validate_delay(delay)
        if not valid:
            self._show_error(error, error_text)
            return
        
        new_settings = AppSettings(
            download_root_dir=download_dir,
            download_media=download_media_switch.value,
            max_file_size_mb=max_size,
            fetch_delay_seconds=delay,
            download_photos=download_photos_cb.value,
            download_videos=download_videos_cb.value,
            download_documents=download_documents_cb.value,
            download_audio=download_audio_cb.value,
            theme=self.current_settings.theme,
            language=self.current_settings.language,
            corner_radius=self.current_settings.corner_radius,
            telegram_api_id=self.current_settings.telegram_api_id,
            telegram_api_hash=self.current_settings.telegram_api_hash
        )
        
        if app_settings.save_settings(new_settings):
            self.current_settings = new_settings
            
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("settings_saved"),
                bgcolor=ft.Colors.GREEN
            )
            
            self.on_settings_changed()
        else:
            self._show_error("Failed to save settings", error_text)
    
    def _show_auth_dialog(self, is_2fa: bool = False) -> str:
        """Show authentication dialog and wait for user input."""
        return self._show_auth_dialog_nested(is_2fa=is_2fa, main_dialog=None)
    
    def _show_auth_dialog_nested(self, is_2fa: bool = False, main_dialog: Optional[ft.AlertDialog] = None) -> str:
        """Show authentication dialog and wait for user input, optionally as nested dialog."""
        if not self.page:
            logger.error("No page available for auth dialog")
            return ""
        
        logger.debug(f"Showing auth dialog (2FA: {is_2fa}, nested: {main_dialog is not None})")
        logger.debug(f"Page ID: {getattr(self.page, 'id', 'unknown')}, Page type: {type(self.page)}")
        
        self._auth_event.clear()
        self._auth_result = None
        
        dialog = TelegramAuthDialog(
            is_2fa=is_2fa,
            on_submit=self._on_auth_dialog_submit
        )
        
        dialog.page = self.page
        logger.debug(f"Dialog created, page reference set: {dialog.page is not None}")
        
        try:
            self.page.open(dialog)
            logger.info(f"Auth dialog opened using page.open() (2FA: {is_2fa}, nested: {main_dialog is not None})")
        except (AttributeError, Exception) as e:
            logger.warning(f"page.open() failed ({e}), using page.dialog method")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
            logger.info(f"Auth dialog opened using page.dialog (2FA: {is_2fa})")
        
        import time
        time.sleep(0.05)
        
        logger.debug("Waiting for user input in auth dialog...")
        timeout = 300
        start_time = time.time()
        event_set = False
        
        while time.time() - start_time < timeout:
            if self._auth_event.is_set():
                event_set = True
                break
            time.sleep(0.1)
        
        if event_set:
            result = self._auth_result or ""
            logger.debug(f"Auth dialog returned: {'***' if result else '(empty/cancelled)'}")
            
            try:
                if hasattr(self.page, 'close'):
                    self.page.close(dialog)
                    logger.debug("Dialog closed using page.close()")
                else:
                    dialog.open = False
                    if self.page.dialog == dialog:
                        self.page.dialog = None
                    self.page.update()
                    logger.debug("Dialog closed using page.dialog method")
            except Exception as close_error:
                logger.debug(f"Error closing dialog: {close_error}")
                try:
                    dialog.open = False
                    if self.page.dialog == dialog:
                        self.page.dialog = None
                    self.page.update()
                except:
                    pass
            
            if not result and main_dialog:
                try:
                    self.page.open(main_dialog)
                    logger.debug("Restored main dialog after auth dialog cancellation")
                except:
                    self.page.dialog = main_dialog
                    main_dialog.open = True
                    self.page.update()
            
            return result
        
        logger.warning("Auth dialog timed out")
        try:
            if hasattr(self.page, 'close'):
                self.page.close(dialog)
            else:
                dialog.open = False
                if self.page.dialog == dialog:
                    self.page.dialog = None
                self.page.update()
            
            if main_dialog:
                try:
                    self.page.open(main_dialog)
                except:
                    self.page.dialog = main_dialog
                    main_dialog.open = True
                    self.page.update()
        except:
            pass
        return ""
    
    def _on_auth_dialog_submit(self, value: str):
        """Handle authentication dialog submission."""
        self._auth_result = value
        self._auth_event.set()
    
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
    
    def _show_error(self, message: str, error_text_control: ft.Text):
        """Show error message."""
        error_text_control.value = message
        error_text_control.visible = True
        if self.page:
            self.page.update()
    
    def _get_auth_service(self):
        """Get auth service instance."""
        try:
            from services.auth_service import auth_service
            return auth_service
        except ImportError:
            logger.error("Failed to import auth_service")
            return None
    
    def _check_account_activity_limit(self, user_email: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user can perform account action (add/delete).
        
        Args:
            user_email: Email of the user
            
        Returns:
            (can_perform, error_message)
        """
        if not user_email:
            return False, "User email not available"
        
        try:
            can_perform = self.db_manager.can_perform_account_action(user_email)
            if not can_perform:
                return False, theme_manager.t("account_deletion_limit_reached")
            return True, None
        except Exception as e:
            logger.error(f"Error checking account activity limit: {e}")
            return False, f"Error checking limit: {str(e)}"
    
    def handle_remove_account(self, credential_id: int):
        """
        Handle account removal with activity limits and confirmation dialog.
        
        Args:
            credential_id: ID of the credential to remove
        """
        if not self.page:
            logger.error("Page not available for account removal")
            return
        
        # Get credential to get phone number for confirmation message
        credential = self.db_manager.get_credential_by_id(credential_id)
        if not credential:
            theme_manager.show_snackbar(
                self.page,
                "Account not found",
                bgcolor=ft.Colors.RED
            )
            return
        
        phone_number = credential.phone_number
        
        # Show confirmation dialog before deletion
        def on_confirm(e):
            """Handle confirmation - proceed with deletion."""
            logger.info(f"on_confirm called for credential_id: {credential_id}, phone: {phone_number}")
            
            try:
                # Get current user email
                auth_service = self._get_auth_service()
                if not auth_service:
                    logger.error("Auth service not available in on_confirm")
                    theme_manager.show_snackbar(
                        self.page,
                        "Authentication service not available",
                        bgcolor=ft.Colors.RED
                    )
                    return
                
                user_email = auth_service.get_user_email()
                logger.info(f"User email from auth_service: {user_email}")
                
                # Check activity limits only if user is logged in
                if user_email:
                    logger.info(f"User email: {user_email}, checking activity limits")
                    can_perform, error_msg = self._check_account_activity_limit(user_email)
                    if not can_perform:
                        logger.warning(f"Activity limit reached: {error_msg}")
                        theme_manager.show_snackbar(
                            self.page,
                            error_msg or theme_manager.t("account_deletion_limit_reached"),
                            bgcolor=ft.Colors.RED
                        )
                        return
                else:
                    logger.warning("User email not available - proceeding with deletion without activity limit check")
                
                # Delete session file from disk
                try:
                    from pathlib import Path
                    if credential.session_string:
                        session_path = Path(credential.session_string)
                        if session_path.exists():
                            session_path.unlink()
                            # Also delete journal file if exists
                            journal_path = session_path.with_suffix(session_path.suffix + '-journal')
                            if journal_path.exists():
                                journal_path.unlink()
                            logger.info(f"Deleted session file: {session_path}")
                except Exception as e:
                    logger.error(f"Error deleting session file: {e}", exc_info=True)
                    # Continue with deletion even if file deletion fails
                
                # Delete credential from database
                logger.info(f"Deleting credential from database: {credential_id}")
                success = self.db_manager.delete_telegram_credential(credential_id)
                if not success:
                    logger.error(f"Failed to delete credential {credential_id} from database")
                    theme_manager.show_snackbar(
                        self.page,
                        "Failed to delete account",
                        bgcolor=ft.Colors.RED
                    )
                    return
                
                logger.info(f"Successfully deleted credential {credential_id} from database")
                
                # Log deletion in activity log (only if user is logged in)
                if user_email:
                    try:
                        self.db_manager.log_account_action(
                            user_email=user_email,
                            action='delete',
                            phone_number=phone_number
                        )
                        logger.info(f"Logged account deletion action for {phone_number}")
                    except Exception as e:
                        logger.error(f"Error logging account deletion: {e}", exc_info=True)
                        # Continue even if logging fails
                else:
                    logger.info("Skipping activity log - user not logged in")
                
                # Show success message
                theme_manager.show_snackbar(
                    self.page,
                    f"Account {phone_number} removed successfully",
                    bgcolor=ft.Colors.GREEN
                )
                
                # Update authenticate tab if available
                if hasattr(self, 'authenticate_tab') and self.authenticate_tab:
                    logger.info("Updating accounts list in authenticate tab")
                    self.authenticate_tab.update_accounts_list()
                
                # Update page
                if self.page:
                    self.page.update()
                    logger.info("Page updated after account removal")
            except Exception as ex:
                logger.error(f"Error in on_confirm callback: {ex}", exc_info=True)
                theme_manager.show_snackbar(
                    self.page,
                    f"Error removing account: {str(ex)}",
                    bgcolor=ft.Colors.RED
                )
        
        def on_cancel(e):
            """Handle cancellation - do nothing."""
            pass
        
        # Show confirmation dialog using page.open() method
        from ui.dialogs.dialog import DialogManager
        confirm_title = theme_manager.t("confirm_removal") or "Confirm Removal"
        confirm_message = theme_manager.t("confirm_remove_account_message") or f"Are you sure you want to remove account {phone_number}? This action cannot be undone."
        
        # Use DialogManager to show confirmation dialog
        DialogManager.show_confirmation_dialog(
            page=self.page,
            title=confirm_title,
            message=confirm_message,
            on_confirm=on_confirm,
            on_cancel=on_cancel,
            confirm_text=theme_manager.t("remove") or "Remove",
            cancel_text=theme_manager.t("cancel") or "Cancel",
            confirm_color=ft.Colors.RED
        )
    
    def handle_add_account(self, e=None):
        """
        Handle add account button click.
        Shows add account dialog and handles account addition flow.
        
        Args:
            e: Optional event object (can be used to get page reference)
        """
        logger.info("=== handle_add_account() called ===")
        logger.info(f"Event provided: {e is not None}")
        logger.info(f"self.page available: {self.page is not None}")
        
        # Try to get page from event if self.page is not available
        page = self.page
        if not page and e:
            logger.debug("Attempting to get page from event")
            if hasattr(e, 'page') and e.page:
                page = e.page
                logger.info("Got page from e.page")
            elif hasattr(e, 'control') and hasattr(e.control, 'page') and e.control.page:
                page = e.control.page
                logger.info("Got page from e.control.page")
        
        if not page:
            logger.error("Page not available for adding account - handler exiting early")
            return
        
        logger.info(f"Page reference obtained: {page is not None}")
        
        # Get current user email and uid for license check
        logger.info("Getting auth service...")
        auth_service = self._get_auth_service()
        if not auth_service:
            logger.error("Auth service not available - returning early")
            theme_manager.show_snackbar(
                page,
                "Authentication service not available. Please restart the application.",
                bgcolor=ft.Colors.RED
            )
            return
        
        # Check if auth service is initialized
        if not hasattr(auth_service, 'get_current_user'):
            logger.error("Auth service does not have get_current_user method")
            theme_manager.show_snackbar(
                page,
                "Authentication service is not properly initialized. Please restart the application.",
                bgcolor=ft.Colors.RED
            )
            return
        
        # Check license limit before opening dialog
        try:
            current_user = auth_service.get_current_user()
        except Exception as e:
            logger.error(f"Error getting current user: {e}", exc_info=True)
            theme_manager.show_snackbar(
                page,
                "Error checking authentication status. Please try again or restart the application.",
                bgcolor=ft.Colors.RED
            )
            return
        
        if not current_user:
            logger.warning("Current user not available - user may not be logged in")
            # Show a more visible error message using dialog
            from ui.dialogs.dialog import DialogManager
            DialogManager.show_simple_dialog(
                page=page,
                title=theme_manager.t("error") or "Error",
                message="You are not logged in. Please log in to add Telegram accounts.\n\nThis feature requires authentication to verify your license and account limits."
            )
            return
        
        user_email = current_user.get('email')
        uid = current_user.get('uid')
        
        if not user_email or not uid:
            logger.error(f"User information incomplete - email: {user_email is not None}, uid: {uid is not None}")
            theme_manager.show_snackbar(
                page,
                "User information not available. Please log in again.",
                bgcolor=ft.Colors.RED
            )
            return
        
        # Check license limit
        logger.info(f"Checking license limit for user: {user_email}")
        from services.license_service import LicenseService
        license_service = LicenseService(self.db_manager, auth_service)
        can_add, error_msg, current_count, max_count = license_service.can_add_account(user_email, uid)
        
        if not can_add:
            logger.warning(f"License limit reached - current: {current_count}, max: {max_count}")
            theme_manager.show_snackbar(
                page,
                error_msg or theme_manager.t("account_limit_reached").format(current=current_count, max=max_count),
                bgcolor=ft.Colors.RED
            )
            return
        
        # Check activity limits
        can_perform, activity_error = self._check_account_activity_limit(user_email)
        if not can_perform:
            theme_manager.show_snackbar(
                page,
                activity_error or theme_manager.t("account_addition_limit_reached"),
                bgcolor=ft.Colors.RED
            )
            return
        
        logger.info("Creating AddAccountDialog...")
        # Show add account dialog
        from ui.dialogs.add_account_dialog import AddAccountDialog
        
        def on_success(phone: str):
            """Handle successful account addition."""
            logger.info(f"Account {phone} added successfully")
            # Refresh accounts list
            if self.authenticate_tab:
                self.authenticate_tab.update_accounts_list()
                self.authenticate_tab._update_account_count()
            # Show success message
            theme_manager.show_snackbar(
                page,
                theme_manager.t("account_added_successfully") or f"Account {phone} added successfully",
                bgcolor=ft.Colors.GREEN
            )
        
        def on_cancel():
            """Handle dialog cancellation."""
            pass
        
        dialog = AddAccountDialog(
            telegram_service=self.telegram_service,
            db_manager=self.db_manager,
            on_success=on_success,
            on_cancel=on_cancel
        )
        
        # Set page reference on dialog
        dialog.page = page
        logger.debug(f"AddAccountDialog created, page reference set: {dialog.page is not None}")
        logger.debug(f"Page ID: {getattr(page, 'id', 'unknown')}, Page type: {type(page)}")
        
        # Check if a dialog is already open - if so, don't open another one
        if hasattr(page, 'dialog') and page.dialog and hasattr(page.dialog, 'open') and page.dialog.open:
            logger.warning("Dialog already open, skipping AddAccountDialog")
            return
        
        # Open dialog using page.open() method (same as telegram_page.py and user_dashboard_page.py)
        # This is the preferred Flet method for opening dialogs
        try:
            logger.info("Opening AddAccountDialog using page.open() method")
            page.open(dialog)
            logger.info("AddAccountDialog opened successfully using page.open()")
        except Exception as dialog_error:
            logger.error(f"Error opening AddAccountDialog with page.open(): {dialog_error}", exc_info=True)
            # Fallback: try page.dialog method
            try:
                logger.debug("Trying page.dialog as fallback")
                page.dialog = dialog
                dialog.open = True
                page.update()
                logger.info("AddAccountDialog opened using page.dialog fallback")
            except Exception as fallback_error:
                logger.error(f"Failed to open dialog even with fallback: {fallback_error}", exc_info=True)
                theme_manager.show_snackbar(
                    page,
                    "Failed to open add account dialog",
                    bgcolor=ft.Colors.RED
                )

