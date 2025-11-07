"""
Event handlers for Settings page.
"""

import flet as ft
import asyncio
import logging
import threading
from typing import Optional, Callable
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
        if not self.telegram_service:
            self._show_error("Telegram service not available", error_text)
            return
        
        if not self.current_settings.telegram_api_id or not self.current_settings.telegram_api_hash:
            self._show_error("Please save API credentials first", error_text)
            return
        
        phone = phone_field.value.strip() if phone_field.value else ""
        if not phone:
            self._show_error("Phone number is required", error_text)
            return
        
        valid, error = validate_phone(phone)
        if not valid:
            self._show_error(error, error_text)
            return
        
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
            
            def get_otp_code() -> str:
                return self._show_auth_dialog(is_2fa=False)
            
            def get_2fa_password() -> str:
                return self._show_auth_dialog(is_2fa=True)
            
            success, error = await self.telegram_service.start_session(
                phone=phone,
                api_id=api_id,
                api_hash=api_hash,
                code_callback=get_otp_code,
                password_callback=get_2fa_password
            )
            
            if success:
                self.authenticate_tab.update_status()
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
        if not self.page:
            return ""
        
        self._auth_event.clear()
        self._auth_result = None
        
        dialog = TelegramAuthDialog(
            is_2fa=is_2fa,
            on_submit=self._on_auth_dialog_submit
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
        
        if self._auth_event.wait(timeout=300):
            return self._auth_result or ""
        
        dialog.open = False
        if self.page:
            self.page.update()
        return ""
    
    def _on_auth_dialog_submit(self, value: str):
        """Handle authentication dialog submission."""
        self._auth_result = value
        self._auth_event.set()
    
    def _show_error(self, message: str, error_text_control: ft.Text):
        """Show error message."""
        error_text_control.value = message
        error_text_control.visible = True
        if self.page:
            self.page.update()

