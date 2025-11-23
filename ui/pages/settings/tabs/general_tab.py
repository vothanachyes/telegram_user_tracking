"""
General settings tab component.
"""

import flet as ft
import logging
import threading
from typing import Callable, Optional
from database.models import AppSettings
from ui.theme import theme_manager
from config.settings import settings as app_settings
from ui.pages.settings.tabs.components.pin_section import PinSection

logger = logging.getLogger(__name__)


class GeneralTab:
    """General settings tab component."""
    
    def __init__(
        self,
        current_settings: AppSettings,
        on_settings_changed: Callable[[], None]
    ):
        self.current_settings = current_settings
        self.on_settings_changed = on_settings_changed
        self._page: Optional[ft.Page] = None
        self._is_saving_theme = False
        self._is_saving_language = False
        
        # Loading indicators
        self.theme_loading = ft.ProgressRing(width=16, height=16, visible=False)
        self.language_loading = ft.ProgressRing(width=16, height=16, visible=False)
        
        # Appearance controls
        self.theme_switch = ft.Switch(
            label=theme_manager.t("dark_mode"),
            value=self.current_settings.theme == "dark",
            on_change=self._on_theme_change
        )
        
        self.language_dropdown = theme_manager.create_dropdown(
            label=theme_manager.t("language"),
            options=["English", "ភាសាខ្មែរ"],
            value="English" if self.current_settings.language == "en" else "ភាសាខ្មែរ",
            width=180,
            on_change=self._on_language_change
        )
        
        self.corner_radius_slider = ft.Slider(
            min=0,
            max=30,
            value=self.current_settings.corner_radius,
            label="{value}px",
            divisions=30
        )
        
        # Auto-download updates switch
        self.auto_download_switch = ft.Switch(
            label=theme_manager.t("auto_download_updates") or "Auto-download available updates",
            value=self.current_settings.auto_download_update,
            tooltip="Automatically download updates when available"
        )
        
        # PIN section component
        self.pin_section = PinSection(
            current_settings=self.current_settings,
            on_settings_changed=self.on_settings_changed,
            on_error=self._show_error
        )
        
        # Error text
        self.error_text = ft.Text("", color=ft.Colors.RED, visible=False)
    
    @property
    def page(self) -> Optional[ft.Page]:
        """Get page reference."""
        return self._page
    
    @page.setter
    def page(self, value: Optional[ft.Page]):
        """Set page reference and forward to PIN section."""
        self._page = value
        if self.pin_section:
            self.pin_section.page = value
    
    def build(self) -> ft.Container:
        """Build the general tab."""
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
                            theme_manager.t("appearance"),
                            size=20,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        ft.Row([
                            self.theme_switch,
                            self.theme_loading,
                        ], spacing=10),
                        ft.Row([
                            self.language_dropdown,
                            self.language_loading,
                        ], spacing=10),
                        ft.Text(theme_manager.t("corner_radius"), size=14),
                        self.corner_radius_slider,
                    ], spacing=20)
                ),
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Text(
                            theme_manager.t("updates") or "Updates",
                            size=20,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        self.auto_download_switch,
                    ], spacing=20)
                ),
                self.pin_section.build(),
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
        self.pin_section.update_settings(new_settings)
        self._reset(None)
    
    def _on_theme_change(self, e):
        """Handle theme change - save immediately with loading indicator."""
        if self._is_saving_theme:
            return
        
        new_theme = "dark" if e.control.value else "light"
        
        # Show loading indicator
        self._is_saving_theme = True
        self.theme_loading.visible = True
        self.theme_switch.disabled = True
        if self.page:
            self.page.update()
        
        # Save in background thread
        def save_theme():
            try:
                new_settings = AppSettings(
                    theme=new_theme,
                    language=self.current_settings.language,
                    corner_radius=self.current_settings.corner_radius,
                    # Keep other settings unchanged
                    telegram_api_id=self.current_settings.telegram_api_id,
                    telegram_api_hash=self.current_settings.telegram_api_hash,
                    download_root_dir=self.current_settings.download_root_dir,
                    download_media=self.current_settings.download_media,
                    max_file_size_mb=self.current_settings.max_file_size_mb,
                    fetch_delay_seconds=self.current_settings.fetch_delay_seconds,
                    download_photos=self.current_settings.download_photos,
                    download_videos=self.current_settings.download_videos,
                    download_documents=self.current_settings.download_documents,
                    download_audio=self.current_settings.download_audio,
                    pin_enabled=self.current_settings.pin_enabled,
                    encrypted_pin=self.current_settings.encrypted_pin,
                    track_reactions=self.current_settings.track_reactions,
                    reaction_fetch_delay=self.current_settings.reaction_fetch_delay,
                    rate_limit_warning_last_seen=self.current_settings.rate_limit_warning_last_seen,
                    db_path=self.current_settings.db_path,
                    encryption_enabled=self.current_settings.encryption_enabled,
                    encryption_key_hash=self.current_settings.encryption_key_hash,
                    session_encryption_enabled=self.current_settings.session_encryption_enabled,
                    page_cache_enabled=self.current_settings.page_cache_enabled,
                    page_cache_ttl_seconds=self.current_settings.page_cache_ttl_seconds,
                    auto_download_update=self.current_settings.auto_download_update
                )
                
                if app_settings.save_settings(new_settings):
                    self.current_settings = new_settings
                    theme_manager.set_theme(new_theme)
                    
                    # Update UI (Flet page.update() is thread-safe)
                    try:
                        self._on_theme_saved()
                    except Exception as ex:
                        logger.error(f"Error updating UI after theme save: {ex}")
                else:
                    # Revert switch on error
                    try:
                        self._on_theme_save_failed()
                    except Exception as ex:
                        logger.error(f"Error updating UI after theme save failure: {ex}")
            except Exception as ex:
                logger.error(f"Error saving theme: {ex}")
                try:
                    self._on_theme_save_failed()
                except Exception as ex2:
                    logger.error(f"Error updating UI after theme save error: {ex2}")
        
        thread = threading.Thread(target=save_theme, daemon=True)
        thread.start()
    
    def _on_theme_saved(self):
        """Handle successful theme save."""
        self._is_saving_theme = False
        self.theme_loading.visible = False
        self.theme_switch.disabled = False
        self.on_settings_changed()
        if self.page:
            self.page.update()
    
    def _on_theme_save_failed(self):
        """Handle failed theme save - revert switch."""
        self._is_saving_theme = False
        self.theme_loading.visible = False
        self.theme_switch.disabled = False
        # Revert to current settings
        self.theme_switch.value = self.current_settings.theme == "dark"
        self._show_error(theme_manager.t("failed_to_save_settings") or "Failed to save settings")
        if self.page:
            self.page.update()
    
    def _on_language_change(self, e):
        """Handle language change - save immediately with loading indicator."""
        if self._is_saving_language:
            return
        
        new_language = "en" if e.control.value == "English" else "km"
        
        # Show loading indicator
        self._is_saving_language = True
        self.language_loading.visible = True
        self.language_dropdown.disabled = True
        if self.page:
            self.page.update()
        
        # Save in background thread
        def save_language():
            try:
                new_settings = AppSettings(
                    theme=self.current_settings.theme,
                    language=new_language,
                    corner_radius=self.current_settings.corner_radius,
                    # Keep other settings unchanged
                    telegram_api_id=self.current_settings.telegram_api_id,
                    telegram_api_hash=self.current_settings.telegram_api_hash,
                    download_root_dir=self.current_settings.download_root_dir,
                    download_media=self.current_settings.download_media,
                    max_file_size_mb=self.current_settings.max_file_size_mb,
                    fetch_delay_seconds=self.current_settings.fetch_delay_seconds,
                    download_photos=self.current_settings.download_photos,
                    download_videos=self.current_settings.download_videos,
                    download_documents=self.current_settings.download_documents,
                    download_audio=self.current_settings.download_audio,
                    pin_enabled=self.current_settings.pin_enabled,
                    encrypted_pin=self.current_settings.encrypted_pin,
                    track_reactions=self.current_settings.track_reactions,
                    reaction_fetch_delay=self.current_settings.reaction_fetch_delay,
                    rate_limit_warning_last_seen=self.current_settings.rate_limit_warning_last_seen,
                    db_path=self.current_settings.db_path,
                    encryption_enabled=self.current_settings.encryption_enabled,
                    encryption_key_hash=self.current_settings.encryption_key_hash,
                    session_encryption_enabled=self.current_settings.session_encryption_enabled,
                    page_cache_enabled=self.current_settings.page_cache_enabled,
                    page_cache_ttl_seconds=self.current_settings.page_cache_ttl_seconds,
                    auto_download_update=self.current_settings.auto_download_update
                )
                
                if app_settings.save_settings(new_settings):
                    self.current_settings = new_settings
                    theme_manager.set_language(new_language)
                    
                    # Update UI (Flet page.update() is thread-safe)
                    try:
                        self._on_language_saved()
                    except Exception as ex:
                        logger.error(f"Error updating UI after language save: {ex}")
                else:
                    # Revert dropdown on error
                    try:
                        self._on_language_save_failed()
                    except Exception as ex:
                        logger.error(f"Error updating UI after language save failure: {ex}")
            except Exception as ex:
                logger.error(f"Error saving language: {ex}")
                try:
                    self._on_language_save_failed()
                except Exception as ex2:
                    logger.error(f"Error updating UI after language save error: {ex2}")
        
        thread = threading.Thread(target=save_language, daemon=True)
        thread.start()
    
    def _on_language_saved(self):
        """Handle successful language save."""
        self._is_saving_language = False
        self.language_loading.visible = False
        self.language_dropdown.disabled = False
        self.on_settings_changed()
        if self.page:
            self.page.update()
    
    def _on_language_save_failed(self):
        """Handle failed language save - revert dropdown."""
        self._is_saving_language = False
        self.language_loading.visible = False
        self.language_dropdown.disabled = False
        # Revert to current settings
        self.language_dropdown.value = "English" if self.current_settings.language == "en" else "ភាសាខ្មែរ"
        self._show_error(theme_manager.t("failed_to_save_settings") or "Failed to save settings")
        if self.page:
            self.page.update()
    
    def _save(self, e):
        """Save general settings."""
        self.error_text.visible = False
        
        new_settings = AppSettings(
            theme="dark" if self.theme_switch.value else "light",
            language="en" if self.language_dropdown.value == "English" else "km",
            corner_radius=int(self.corner_radius_slider.value),
            # Keep other settings unchanged
            telegram_api_id=self.current_settings.telegram_api_id,
            telegram_api_hash=self.current_settings.telegram_api_hash,
            download_root_dir=self.current_settings.download_root_dir,
            download_media=self.current_settings.download_media,
            max_file_size_mb=self.current_settings.max_file_size_mb,
            fetch_delay_seconds=self.current_settings.fetch_delay_seconds,
            download_photos=self.current_settings.download_photos,
            download_videos=self.current_settings.download_videos,
            download_documents=self.current_settings.download_documents,
            download_audio=self.current_settings.download_audio,
            # Preserve PIN settings
            pin_enabled=self.current_settings.pin_enabled,
            encrypted_pin=self.current_settings.encrypted_pin,
            # Preserve other settings
            track_reactions=self.current_settings.track_reactions,
            reaction_fetch_delay=self.current_settings.reaction_fetch_delay,
            rate_limit_warning_last_seen=self.current_settings.rate_limit_warning_last_seen,
            db_path=self.current_settings.db_path,
            encryption_enabled=self.current_settings.encryption_enabled,
            encryption_key_hash=self.current_settings.encryption_key_hash,
            session_encryption_enabled=self.current_settings.session_encryption_enabled,
            page_cache_enabled=self.current_settings.page_cache_enabled,
            page_cache_ttl_seconds=self.current_settings.page_cache_ttl_seconds,
            auto_download_update=self.auto_download_switch.value
        )
        
        if app_settings.save_settings(new_settings):
            theme_manager.set_theme(new_settings.theme)
            theme_manager.set_language(new_settings.language)
            theme_manager.set_corner_radius(new_settings.corner_radius)
            
            self.current_settings = new_settings
            
            theme_manager.show_snackbar(
                self.page if hasattr(self, 'page') else None,
                theme_manager.t("settings_saved"),
                bgcolor=ft.Colors.GREEN
            )
            
            self.on_settings_changed()
        else:
            self._show_error("Failed to save settings")
    
    def _reset(self, e):
        """Reset to current settings."""
        self.current_settings = app_settings.load_settings()
        
        self.theme_switch.value = self.current_settings.theme == "dark"
        self.language_dropdown.value = "English" if self.current_settings.language == "en" else "ភាសាខ្មែរ"
        self.corner_radius_slider.value = self.current_settings.corner_radius
        self.auto_download_switch.value = self.current_settings.auto_download_update
        
        # Update PIN section
        self.pin_section.update_settings(self.current_settings)
        
        self.error_text.visible = False
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _show_error(self, message: str):
        """Show error message."""
        self.error_text.value = message
        self.error_text.visible = True
        if hasattr(self, 'page') and self.page:
            self.page.update()

