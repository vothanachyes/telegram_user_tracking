"""
Configure dialog for fetch data page - same UI as configure tab but excludes download directory.
"""

import flet as ft
from database.models import AppSettings
from ui.theme import theme_manager
from config.settings import settings as app_settings
from utils.validators import validate_file_size, validate_delay


class FetchConfigureDialog(ft.AlertDialog):
    """Dialog for configuring fetch settings (excluding download directory)."""
    
    def __init__(self, current_settings: AppSettings):
        self.current_settings = current_settings
        
        # Fetch settings controls (excluding download directory)
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
        
        # Create dialog
        super().__init__(
            modal=True,
            title=ft.Text(theme_manager.t("fetch_settings") or "Fetch Settings"),
            content=self._build_content(),
            actions=[
                ft.TextButton(
                    theme_manager.t("cancel") or "Cancel",
                    on_click=self._on_cancel
                ),
                ft.ElevatedButton(
                    theme_manager.t("save") or "Save",
                    on_click=self._on_save,
                    bgcolor=theme_manager.primary_color,
                    color=ft.Colors.WHITE
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _build_content(self) -> ft.Container:
        """Build dialog content."""
        return ft.Container(
            content=ft.Column([
                theme_manager.create_card(
                    content=ft.Column([
                        self.download_media_switch,
                        ft.Text(theme_manager.t("max_file_size") or "Max File Size", size=14),
                        self.max_file_size_slider,
                        ft.Text(theme_manager.t("fetch_delay") or "Fetch Delay", size=14),
                        self.fetch_delay_slider,
                        ft.Text(theme_manager.t("media_types") or "Media Types", size=14, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            self.download_photos_cb,
                            self.download_videos_cb,
                            self.download_documents_cb,
                            self.download_audio_cb,
                        ], wrap=True),
                    ], spacing=20)
                ),
                self.error_text,
            ], scroll=ft.ScrollMode.AUTO, spacing=20),
            width=500,
            height=400
        )
    
    def _on_save(self, e):
        """Handle save button click."""
        self.error_text.visible = False
        
        max_size = int(self.max_file_size_slider.value)
        delay = self.fetch_delay_slider.value
        
        # Validate
        valid, error = validate_file_size(max_size)
        if not valid:
            self._show_error(error)
            return
        
        valid, error = validate_delay(delay)
        if not valid:
            self._show_error(error)
            return
        
        # Save settings
        new_settings = AppSettings(
            download_root_dir=self.current_settings.download_root_dir,  # Keep existing
            download_media=self.download_media_switch.value,
            max_file_size_mb=max_size,
            fetch_delay_seconds=delay,
            download_photos=self.download_photos_cb.value,
            download_videos=self.download_videos_cb.value,
            download_documents=self.download_documents_cb.value,
            download_audio=self.download_audio_cb.value,
            theme=self.current_settings.theme,
            language=self.current_settings.language,
            corner_radius=self.current_settings.corner_radius,
            telegram_api_id=self.current_settings.telegram_api_id,
            telegram_api_hash=self.current_settings.telegram_api_hash
        )
        
        if app_settings.save_settings(new_settings):
            self.current_settings = new_settings
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("settings_saved") or "Settings saved",
                    bgcolor=ft.Colors.GREEN
                )
            self._close_dialog()
        else:
            self._show_error("Failed to save settings")
    
    def _on_cancel(self, e):
        """Handle cancel button click."""
        self._close_dialog()
    
    def _show_error(self, message: str):
        """Show error message."""
        self.error_text.value = message
        self.error_text.visible = True
        if self.page:
            self.page.update()
    
    def _close_dialog(self):
        """Close the dialog."""
        if self.page:
            self.page.close(self)

