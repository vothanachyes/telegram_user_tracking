"""
Configure settings tab component.
"""

import flet as ft
from database.models import AppSettings
from ui.theme import theme_manager
from config.settings import settings as app_settings


class ConfigureTab:
    """Configure settings tab component."""
    
    def __init__(
        self,
        current_settings: AppSettings,
        handlers
    ):
        self.current_settings = current_settings
        self.handlers = handlers
        
        # Fetch settings controls
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
        self.error_text = ft.Text("", color=ft.Colors.RED, visible=False)
    
    def build(self) -> ft.Container:
        """Build the configure tab."""
        save_btn = theme_manager.create_button(
            text=theme_manager.t("save"),
            icon=ft.Icons.SAVE,
            on_click=self._save,
            style="success"
        )
        cancel_btn = theme_manager.create_button(
            text=theme_manager.t("cancel"),
            icon=ft.Icons.CANCEL,
            on_click=self._reset,
            style="error"
        )
        
        return ft.Container(
            content=ft.Column([
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
                    ], spacing=20)
                ),
                self.error_text,
                ft.Row([
                    cancel_btn,
                    save_btn,
                ], alignment=ft.MainAxisAlignment.END, spacing=10),
            ], scroll=ft.ScrollMode.AUTO, spacing=20),
            padding=10,
            expand=True
        )
    
    def update_settings(self, new_settings: AppSettings):
        """Update current settings."""
        self.current_settings = new_settings
        self._reset(None)
    
    def _save(self, e):
        """Save configure settings."""
        self.handlers.handle_save_configure(
            self.download_dir_field,
            self.download_media_switch,
            self.max_file_size_slider,
            self.fetch_delay_slider,
            self.download_photos_cb,
            self.download_videos_cb,
            self.download_documents_cb,
            self.download_audio_cb,
            self.error_text
        )
        self.current_settings = app_settings.load_settings()
    
    def _reset(self, e):
        """Reset to current settings."""
        self.current_settings = app_settings.load_settings()
        
        self.download_dir_field.value = self.current_settings.download_root_dir
        self.download_media_switch.value = self.current_settings.download_media
        self.max_file_size_slider.value = self.current_settings.max_file_size_mb
        self.fetch_delay_slider.value = self.current_settings.fetch_delay_seconds
        self.download_photos_cb.value = self.current_settings.download_photos
        self.download_videos_cb.value = self.current_settings.download_videos
        self.download_documents_cb.value = self.current_settings.download_documents
        self.download_audio_cb.value = self.current_settings.download_audio
        
        self.error_text.visible = False
        if hasattr(self, 'page') and self.page:
            self.page.update()

