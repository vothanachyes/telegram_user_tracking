"""
Settings page with appearance, Telegram auth, and fetch settings.
"""

import flet as ft
from typing import Callable
from ui.theme import theme_manager
from config.settings import settings as app_settings
from database.models import AppSettings
from utils.validators import (
    validate_telegram_api_id,
    validate_telegram_api_hash,
    validate_file_size,
    validate_delay,
    validate_path
)


class SettingsPage(ft.Container):
    """Settings page for app configuration."""
    
    def __init__(self, on_settings_changed: Callable[[], None]):
        self.on_settings_changed = on_settings_changed
        self.current_settings = app_settings.load_settings()
        
        # Appearance section
        self.theme_switch = ft.Switch(
            label=theme_manager.t("dark_mode"),
            value=self.current_settings.theme == "dark",
            on_change=self._on_theme_change
        )
        
        self.language_dropdown = theme_manager.create_dropdown(
            label=theme_manager.t("language"),
            options=["English", "ភាសាខ្មែរ"],
            value="English" if self.current_settings.language == "en" else "ភាសាខ្មែរ"
        )
        
        self.corner_radius_slider = ft.Slider(
            min=0,
            max=30,
            value=self.current_settings.corner_radius,
            label="{value}px",
            divisions=30
        )
        
        # Telegram auth section
        self.api_id_field = theme_manager.create_text_field(
            label=theme_manager.t("api_id"),
            value=self.current_settings.telegram_api_id or ""
        )
        
        self.api_hash_field = theme_manager.create_text_field(
            label=theme_manager.t("api_hash"),
            value=self.current_settings.telegram_api_hash or "",
            password=True
        )
        
        # Fetch settings section
        self.download_dir_field = theme_manager.create_text_field(
            label=theme_manager.t("download_directory"),
            value=self.current_settings.download_root_dir
        )
        
        self.download_media_switch = ft.Switch(
            label=theme_manager.t("download_media"),
            value=self.current_settings.download_media
        )
        
        self.max_file_size_slider = ft.Slider(
            min=1,
            max=2000,
            value=self.current_settings.max_file_size_mb,
            label="{value} MB",
            divisions=100
        )
        
        self.fetch_delay_slider = ft.Slider(
            min=0,
            max=10,
            value=self.current_settings.fetch_delay_seconds,
            label="{value}s",
            divisions=20
        )
        
        self.download_photos_cb = ft.Checkbox(
            label=theme_manager.t("photos"),
            value=self.current_settings.download_photos
        )
        
        self.download_videos_cb = ft.Checkbox(
            label=theme_manager.t("videos"),
            value=self.current_settings.download_videos
        )
        
        self.download_documents_cb = ft.Checkbox(
            label=theme_manager.t("documents"),
            value=self.current_settings.download_documents
        )
        
        self.download_audio_cb = ft.Checkbox(
            label=theme_manager.t("audio"),
            value=self.current_settings.download_audio
        )
        
        # Error text
        self.error_text = ft.Text("", color=ft.colors.RED, visible=False)
        
        # Build layout
        super().__init__(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("settings"),
                    size=32,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(height=20),
                
                # Appearance section
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Text(
                            theme_manager.t("appearance"),
                            size=20,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        self.theme_switch,
                        self.language_dropdown,
                        ft.Text(theme_manager.t("corner_radius"), size=14),
                        self.corner_radius_slider,
                    ], spacing=15)
                ),
                
                # Telegram auth section
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Text(
                            theme_manager.t("telegram_auth"),
                            size=20,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        self.api_id_field,
                        self.api_hash_field,
                    ], spacing=15)
                ),
                
                # Fetch settings section
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Text(
                            theme_manager.t("fetch_settings"),
                            size=20,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        self.download_dir_field,
                        self.download_media_switch,
                        ft.Text(theme_manager.t("max_file_size"), size=14),
                        self.max_file_size_slider,
                        ft.Text(theme_manager.t("fetch_delay"), size=14),
                        self.fetch_delay_slider,
                        ft.Text(theme_manager.t("media_types"), size=14, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            self.download_photos_cb,
                            self.download_videos_cb,
                            self.download_documents_cb,
                            self.download_audio_cb,
                        ], wrap=True),
                    ], spacing=15)
                ),
                
                self.error_text,
                
                # Action buttons
                ft.Row([
                    theme_manager.create_button(
                        text=theme_manager.t("save"),
                        icon=ft.icons.SAVE,
                        on_click=self._save_settings,
                        style="success"
                    ),
                    theme_manager.create_button(
                        text=theme_manager.t("cancel"),
                        icon=ft.icons.CANCEL,
                        on_click=self._reset_form,
                        style="error"
                    ),
                ], spacing=10),
                
            ], scroll=ft.ScrollMode.AUTO, spacing=15),
            padding=20,
            expand=True
        )
    
    def _on_theme_change(self, e):
        """Handle theme change."""
        # Update preview immediately
        theme_manager.set_theme("dark" if e.control.value else "light")
        self.on_settings_changed()
    
    def _save_settings(self, e):
        """Save settings."""
        self.error_text.visible = False
        
        # Validate
        api_id = self.api_id_field.value
        api_hash = self.api_hash_field.value
        download_dir = self.download_dir_field.value
        max_size = int(self.max_file_size_slider.value)
        delay = self.fetch_delay_slider.value
        
        # Validate API credentials if provided
        if api_id:
            valid, error = validate_telegram_api_id(api_id)
            if not valid:
                self._show_error(error)
                return
        
        if api_hash:
            valid, error = validate_telegram_api_hash(api_hash)
            if not valid:
                self._show_error(error)
                return
        
        # Validate other fields
        valid, error = validate_path(download_dir)
        if not valid:
            self._show_error(error)
            return
        
        valid, error = validate_file_size(max_size)
        if not valid:
            self._show_error(error)
            return
        
        valid, error = validate_delay(delay)
        if not valid:
            self._show_error(error)
            return
        
        # Build settings object
        new_settings = AppSettings(
            theme="dark" if self.theme_switch.value else "light",
            language="en" if self.language_dropdown.value == "English" else "km",
            corner_radius=int(self.corner_radius_slider.value),
            telegram_api_id=api_id if api_id else None,
            telegram_api_hash=api_hash if api_hash else None,
            download_root_dir=download_dir,
            download_media=self.download_media_switch.value,
            max_file_size_mb=max_size,
            fetch_delay_seconds=delay,
            download_photos=self.download_photos_cb.value,
            download_videos=self.download_videos_cb.value,
            download_documents=self.download_documents_cb.value,
            download_audio=self.download_audio_cb.value
        )
        
        # Save to database
        if app_settings.save_settings(new_settings):
            # Update theme manager
            theme_manager.set_theme(new_settings.theme)
            theme_manager.set_language(new_settings.language)
            theme_manager.set_corner_radius(new_settings.corner_radius)
            
            # Show success
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("settings_saved"),
                bgcolor=ft.colors.GREEN
            )
            
            # Notify parent
            self.on_settings_changed()
        else:
            self._show_error("Failed to save settings")
    
    def _reset_form(self, e):
        """Reset form to current settings."""
        self.current_settings = app_settings.load_settings()
        
        self.theme_switch.value = self.current_settings.theme == "dark"
        self.language_dropdown.value = "English" if self.current_settings.language == "en" else "ភាសាខ្មែរ"
        self.corner_radius_slider.value = self.current_settings.corner_radius
        self.api_id_field.value = self.current_settings.telegram_api_id or ""
        self.api_hash_field.value = self.current_settings.telegram_api_hash or ""
        self.download_dir_field.value = self.current_settings.download_root_dir
        self.download_media_switch.value = self.current_settings.download_media
        self.max_file_size_slider.value = self.current_settings.max_file_size_mb
        self.fetch_delay_slider.value = self.current_settings.fetch_delay_seconds
        self.download_photos_cb.value = self.current_settings.download_photos
        self.download_videos_cb.value = self.current_settings.download_videos
        self.download_documents_cb.value = self.current_settings.download_documents
        self.download_audio_cb.value = self.current_settings.download_audio
        
        self.error_text.visible = False
        self.update()
    
    def _show_error(self, message: str):
        """Show error message."""
        self.error_text.value = message
        self.error_text.visible = True
        self.update()

