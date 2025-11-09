"""
Configuration handlers for settings.
"""

import flet as ft
from database.models import AppSettings
from ui.theme import theme_manager
from config.settings import settings as app_settings
from utils.validators import (
    validate_telegram_api_id,
    validate_telegram_api_hash,
    validate_file_size,
    validate_delay,
    validate_path
)
from ui.pages.settings.handlers.base import BaseHandlerMixin


class ConfigurationHandlerMixin(BaseHandlerMixin):
    """Handlers for configuration settings."""
    
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

