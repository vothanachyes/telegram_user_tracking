"""
Settings page with appearance, Telegram auth, and fetch settings.
"""

import flet as ft
import asyncio
import logging
import threading
from typing import Callable, Optional
from ui.theme import theme_manager
from config.settings import settings as app_settings
from database.models import AppSettings
from database.db_manager import DatabaseManager
from services.telegram import TelegramService
from ui.dialogs.telegram_auth_dialog import TelegramAuthDialog
from utils.validators import (
    validate_telegram_api_id,
    validate_telegram_api_hash,
    validate_file_size,
    validate_delay,
    validate_path,
    validate_phone
)

logger = logging.getLogger(__name__)


class SettingsPage(ft.Container):
    """Settings page for app configuration with tabbed interface."""
    
    def __init__(
        self, 
        on_settings_changed: Callable[[], None],
        telegram_service: Optional[TelegramService] = None,
        db_manager: Optional[DatabaseManager] = None
    ):
        self.on_settings_changed = on_settings_changed
        self.telegram_service = telegram_service
        self.db_manager = db_manager or DatabaseManager()
        self.current_settings = app_settings.load_settings()
        
        # Track authentication state
        self._auth_event = threading.Event()
        self._auth_result: Optional[str] = None
        
        # Build UI with tabs
        super().__init__(
            content=self._build_tabs(),
            padding=20,
            expand=True
        )
    
    def _build_tabs(self) -> ft.Column:
        """Build the tabbed interface."""
        return ft.Column([
            ft.Row([
                ft.Text(
                    theme_manager.t("settings"),
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    expand=True
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=20),
            ft.Tabs(
                selected_index=0,
                animation_duration=300,
                tabs=[
                    ft.Tab(
                        text=theme_manager.t("general"),
                        icon=ft.Icons.SETTINGS,
                        content=self._create_general_tab()
                    ),
                    ft.Tab(
                        text=theme_manager.t("authenticate"),
                        icon=ft.Icons.VERIFIED_USER,
                        content=self._create_authenticate_tab()
                    ),
                    ft.Tab(
                        text=theme_manager.t("configure"),
                        icon=ft.Icons.TUNE,
                        content=self._create_configure_tab()
                    ),
                ],
                expand=True
            ),
        ], spacing=15, expand=True)
    
    def _create_general_tab(self) -> ft.Container:
        """Create General tab with appearance settings."""
        # Appearance controls
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
        
        # Error text
        self.general_error_text = ft.Text("", color=ft.Colors.RED, visible=False)
        
        # Save/Cancel buttons
        save_btn = theme_manager.create_button(
            text=theme_manager.t("save"),
            icon=ft.Icons.SAVE,
            on_click=self._save_general,
            style="success"
        )
        cancel_btn = theme_manager.create_button(
            text=theme_manager.t("cancel"),
            icon=ft.Icons.CANCEL,
            on_click=self._reset_general,
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
                        self.theme_switch,
                        self.language_dropdown,
                        ft.Text(theme_manager.t("corner_radius"), size=14),
                        self.corner_radius_slider,
                    ], spacing=15)
                ),
                self.general_error_text,
                ft.Row([
                    cancel_btn,
                    save_btn,
                ], alignment=ft.MainAxisAlignment.END, spacing=10),
            ], scroll=ft.ScrollMode.AUTO, spacing=15),
            padding=10,
            expand=True
        )
    
    def _create_authenticate_tab(self) -> ft.Container:
        """Create Authenticate tab with API App and Telegram account sections."""
        # API App Configuration section
        self.api_id_field = theme_manager.create_text_field(
            label=theme_manager.t("api_id"),
            value=self.current_settings.telegram_api_id or ""
        )
        
        self.api_hash_field = theme_manager.create_text_field(
            label=theme_manager.t("api_hash"),
            value=self.current_settings.telegram_api_hash or "",
            password=True
        )
        
        self.api_status_text = ft.Text(
            self._get_api_status_text(),
            size=14,
            color=theme_manager.text_secondary_color
        )
        
        # Telegram Account Connection section
        self.phone_field = theme_manager.create_text_field(
            label=theme_manager.t("phone_number"),
            hint_text="+1234567890",
            value=""
        )
        
        self.account_status_text = ft.Text(
            self._get_account_status_text(),
            size=14,
            color=theme_manager.text_secondary_color
        )
        
        self.connect_btn = theme_manager.create_button(
            text=theme_manager.t("connect_to_telegram"),
            icon=ft.Icons.LINK,
            on_click=self._handle_telegram_connect,
            style="primary"
        )
        
        self.disconnect_btn = theme_manager.create_button(
            text=theme_manager.t("disconnect"),
            icon=ft.Icons.LINK_OFF,
            on_click=self._handle_telegram_disconnect,
            style="error"
        )
        
        
        # Error text
        self.auth_error_text = ft.Text("", color=ft.Colors.RED, visible=False)
        
        # Save/Cancel buttons for API credentials
        save_api_btn = theme_manager.create_button(
            text=theme_manager.t("save_api_credentials"),
            icon=ft.Icons.SAVE,
            on_click=self._save_authenticate,
            style="success"
        )
        cancel_api_btn = theme_manager.create_button(
            text=theme_manager.t("cancel"),
            icon=ft.Icons.CANCEL,
            on_click=self._reset_authenticate,
            style="error"
        )
        
        # Update button states
        self._update_connection_buttons()
        
        return ft.Container(
            content=ft.Column([
                # API App Configuration section
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Text(
                            theme_manager.t("api_app_configuration"),
                            size=20,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        self.api_id_field,
                        self.api_hash_field,
                        ft.Text(
                            theme_manager.t("get_api_credentials"),
                            size=12,
                            color=theme_manager.text_secondary_color,
                            italic=True
                        ),
                        self.api_status_text,
                    ], spacing=15)
                ),
                
                # Telegram Account Connection section
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Text(
                            theme_manager.t("telegram_account_connection"),
                            size=20,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        self.phone_field,
                        self.account_status_text,
                        ft.Row([
                            self.connect_btn,
                            self.disconnect_btn,
                        ], spacing=10),
                    ], spacing=15)
                ),
                
                self.auth_error_text,
                
                # Save/Cancel buttons for API credentials
                ft.Row([
                    cancel_api_btn,
                    save_api_btn,
                ], alignment=ft.MainAxisAlignment.END, spacing=10),
            ], scroll=ft.ScrollMode.AUTO, spacing=15),
            padding=10,
            expand=True
        )
    
    def _create_configure_tab(self) -> ft.Container:
        """Create Configure tab with fetch and download settings."""
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
        self.configure_error_text = ft.Text("", color=ft.Colors.RED, visible=False)
        
        # Save/Cancel buttons
        save_btn = theme_manager.create_button(
            text=theme_manager.t("save"),
            icon=ft.Icons.SAVE,
            on_click=self._save_configure,
            style="success"
        )
        cancel_btn = theme_manager.create_button(
            text=theme_manager.t("cancel"),
            icon=ft.Icons.CANCEL,
            on_click=self._reset_configure,
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
                    ], spacing=15)
                ),
                self.configure_error_text,
                ft.Row([
                    cancel_btn,
                    save_btn,
                ], alignment=ft.MainAxisAlignment.END, spacing=10),
            ], scroll=ft.ScrollMode.AUTO, spacing=15),
            padding=10,
            expand=True
        )
    
    # ==================== General Tab Methods ====================
    
    def _on_theme_change(self, e):
        """Handle theme change."""
        # Update preview immediately
        theme_manager.set_theme("dark" if e.control.value else "light")
        self.on_settings_changed()
    
    def _save_general(self, e):
        """Save general settings."""
        self.general_error_text.visible = False
        
        # Build settings object with only general fields
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
            download_audio=self.current_settings.download_audio
        )
        
        # Save to database
        if app_settings.save_settings(new_settings):
            # Update theme manager
            theme_manager.set_theme(new_settings.theme)
            theme_manager.set_language(new_settings.language)
            theme_manager.set_corner_radius(new_settings.corner_radius)
            
            # Update current settings
            self.current_settings = new_settings
            
            # Show success
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("settings_saved"),
                bgcolor=ft.Colors.GREEN
            )
            
            # Notify parent
            self.on_settings_changed()
        else:
            self._show_error("Failed to save settings", self.general_error_text)
    
    def _reset_general(self, e):
        """Reset general tab to current settings."""
        self.current_settings = app_settings.load_settings()
        
        self.theme_switch.value = self.current_settings.theme == "dark"
        self.language_dropdown.value = "English" if self.current_settings.language == "en" else "ភាសាខ្មែរ"
        self.corner_radius_slider.value = self.current_settings.corner_radius
        
        self.general_error_text.visible = False
        self.update()
    
    # ==================== Authenticate Tab Methods ====================
    
    def _get_api_status_text(self) -> str:
        """Get API App status text."""
        if self.current_settings.telegram_api_id and self.current_settings.telegram_api_hash:
            return theme_manager.t("api_app_configured")
        return theme_manager.t("api_app_not_configured")
    
    def _get_account_status_text(self) -> str:
        """Get account connection status text."""
        if not self.telegram_service:
            return theme_manager.t("account_not_connected")
        
        if self.telegram_service.is_connected():
            # Try to get phone number from saved credential
            credential = self.db_manager.get_default_credential()
            if credential:
                return f"{theme_manager.t('account_connected')} ({credential.phone_number})"
            return theme_manager.t("account_connected")
        return theme_manager.t("account_not_connected")
    
    def _update_connection_buttons(self):
        """Update connection button states."""
        is_configured = bool(
            self.current_settings.telegram_api_id and 
            self.current_settings.telegram_api_hash
        )
        is_connected = self.telegram_service and self.telegram_service.is_connected()
        
        self.connect_btn.disabled = not is_configured or is_connected
        self.disconnect_btn.visible = is_connected
        self.disconnect_btn.disabled = not is_connected
    
    def _save_authenticate(self, e):
        """Save API credentials (does not connect to Telegram)."""
        self.auth_error_text.visible = False
        
        # Validate API credentials
        api_id = self.api_id_field.value.strip() if self.api_id_field.value else ""
        api_hash = self.api_hash_field.value.strip() if self.api_hash_field.value else ""
        
        if api_id:
            valid, error = validate_telegram_api_id(api_id)
            if not valid:
                self._show_error(error, self.auth_error_text)
                return
        
        if api_hash:
            valid, error = validate_telegram_api_hash(api_hash)
            if not valid:
                self._show_error(error, self.auth_error_text)
                return
        
        # Build settings object with only API credentials
        new_settings = AppSettings(
            telegram_api_id=api_id if api_id else None,
            telegram_api_hash=api_hash if api_hash else None,
            # Keep other settings unchanged
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
        
        # Save to database
        if app_settings.save_settings(new_settings):
            # Update current settings
            self.current_settings = new_settings
            
            # Update status text and button states
            self.api_status_text.value = self._get_api_status_text()
            self._update_connection_buttons()
            
            # Show success
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("settings_saved"),
                bgcolor=ft.Colors.GREEN
            )
            
            self.update()
        else:
            self._show_error("Failed to save API credentials", self.auth_error_text)
    
    def _reset_authenticate(self, e):
        """Reset authenticate tab to current settings."""
        self.current_settings = app_settings.load_settings()
        
        self.api_id_field.value = self.current_settings.telegram_api_id or ""
        self.api_hash_field.value = self.current_settings.telegram_api_hash or ""
        self.api_status_text.value = self._get_api_status_text()
        self.account_status_text.value = self._get_account_status_text()
        
        
        self._update_connection_buttons()
        self.auth_error_text.visible = False
        self.update()
    
    def _handle_telegram_connect(self, e):
        """Handle Telegram connection flow."""
        if not self.telegram_service:
            self._show_error("Telegram service not available", self.auth_error_text)
            return
        
        # Validate API credentials
        if not self.current_settings.telegram_api_id or not self.current_settings.telegram_api_hash:
            self._show_error("Please save API credentials first", self.auth_error_text)
            return
        
        # Validate phone number
        phone = self.phone_field.value.strip() if self.phone_field.value else ""
        if not phone:
            self._show_error("Phone number is required", self.auth_error_text)
            return
        
        valid, error = validate_phone(phone)
        if not valid:
            self._show_error(error, self.auth_error_text)
            return
        
        # Start connection process
        if self.page and hasattr(self.page, 'run_task'):
            self.page.run_task(
                self._connect_telegram_async,
                phone,
                self.current_settings.telegram_api_id,
                self.current_settings.telegram_api_hash
            )
        else:
            import asyncio
            asyncio.create_task(
                self._connect_telegram_async(
                    phone,
                    self.current_settings.telegram_api_id,
                    self.current_settings.telegram_api_hash
                )
            )
    
    async def _connect_telegram_async(self, phone: str, api_id: str, api_hash: str):
        """Async method to connect to Telegram with OTP/2FA handling."""
        try:
            # Show connecting status
            self.connect_btn.disabled = True
            self.connect_btn.text = theme_manager.t("connecting")
            self.auth_error_text.visible = False
            if self.page:
                self.page.update()
            
            # Define callbacks for OTP and 2FA
            def get_otp_code() -> str:
                """Callback to get OTP code from user."""
                return self._show_auth_dialog(is_2fa=False)
            
            def get_2fa_password() -> str:
                """Callback to get 2FA password from user."""
                return self._show_auth_dialog(is_2fa=True)
            
            # Start session
            success, error = await self.telegram_service.start_session(
                phone=phone,
                api_id=api_id,
                api_hash=api_hash,
                code_callback=get_otp_code,
                password_callback=get_2fa_password
            )
            
            if success:
                # Update status
                self.account_status_text.value = self._get_account_status_text()
                self.phone_field.value = phone
                self._update_connection_buttons()
                
                # Show success
                if self.page:
                    theme_manager.show_snackbar(
                        self.page,
                        theme_manager.t("connection_success"),
                        bgcolor=ft.Colors.GREEN
                    )
            else:
                self._show_error(f"{theme_manager.t('connection_failed')}: {error}", self.auth_error_text)
            
            # Reset button
            self.connect_btn.disabled = False
            self.connect_btn.text = theme_manager.t("connect_to_telegram")
            
            if self.page:
                self.page.update()
                
        except Exception as ex:
            logger.error(f"Error connecting to Telegram: {ex}")
            self._show_error(f"{theme_manager.t('connection_failed')}: {str(ex)}", self.auth_error_text)
            self.connect_btn.disabled = False
            self.connect_btn.text = theme_manager.t("connect_to_telegram")
            if self.page:
                self.page.update()
    
    def _handle_telegram_disconnect(self, e):
        """Handle Telegram disconnection."""
        if not self.telegram_service:
            return
        
        if self.page and hasattr(self.page, 'run_task'):
            self.page.run_task(self._disconnect_telegram_async)
        else:
            import asyncio
            asyncio.create_task(self._disconnect_telegram_async())
    
    async def _disconnect_telegram_async(self):
        """Async method to disconnect from Telegram."""
        try:
            await self.telegram_service.disconnect()
            
            # Update status
            self.account_status_text.value = self._get_account_status_text()
            self._update_connection_buttons()
            
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
    
    # ==================== Configure Tab Methods ====================
    
    def _save_configure(self, e):
        """Save configure settings."""
        self.configure_error_text.visible = False
        
        # Validate
        download_dir = self.download_dir_field.value
        max_size = int(self.max_file_size_slider.value)
        delay = self.fetch_delay_slider.value
        
        valid, error = validate_path(download_dir)
        if not valid:
            self._show_error(error, self.configure_error_text)
            return
        
        valid, error = validate_file_size(max_size)
        if not valid:
            self._show_error(error, self.configure_error_text)
            return
        
        valid, error = validate_delay(delay)
        if not valid:
            self._show_error(error, self.configure_error_text)
            return
        
        # Build settings object with only configure fields
        new_settings = AppSettings(
            download_root_dir=download_dir,
            download_media=self.download_media_switch.value,
            max_file_size_mb=max_size,
            fetch_delay_seconds=delay,
            download_photos=self.download_photos_cb.value,
            download_videos=self.download_videos_cb.value,
            download_documents=self.download_documents_cb.value,
            download_audio=self.download_audio_cb.value,
            # Keep other settings unchanged
            theme=self.current_settings.theme,
            language=self.current_settings.language,
            corner_radius=self.current_settings.corner_radius,
            telegram_api_id=self.current_settings.telegram_api_id,
            telegram_api_hash=self.current_settings.telegram_api_hash
        )
        
        # Save to database
        if app_settings.save_settings(new_settings):
            # Update current settings
            self.current_settings = new_settings
            
            # Show success
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("settings_saved"),
                bgcolor=ft.Colors.GREEN
            )
            
            # Notify parent
            self.on_settings_changed()
        else:
            self._show_error("Failed to save settings", self.configure_error_text)
    
    def _reset_configure(self, e):
        """Reset configure tab to current settings."""
        self.current_settings = app_settings.load_settings()
        
        self.download_dir_field.value = self.current_settings.download_root_dir
        self.download_media_switch.value = self.current_settings.download_media
        self.max_file_size_slider.value = self.current_settings.max_file_size_mb
        self.fetch_delay_slider.value = self.current_settings.fetch_delay_seconds
        self.download_photos_cb.value = self.current_settings.download_photos
        self.download_videos_cb.value = self.current_settings.download_videos
        self.download_documents_cb.value = self.current_settings.download_documents
        self.download_audio_cb.value = self.current_settings.download_audio
        
        self.configure_error_text.visible = False
        self.update()
    
    # ==================== Helper Methods ====================
    
    def _show_auth_dialog(self, is_2fa: bool = False) -> str:
        """Show authentication dialog and wait for user input."""
        if not self.page:
            return ""
        
        # Reset event and result
        self._auth_event.clear()
        self._auth_result = None
        
        # Create and show dialog
        dialog = TelegramAuthDialog(
            is_2fa=is_2fa,
            on_submit=self._on_auth_dialog_submit
        )
        
        # Show dialog on page
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
        
        # Wait for user input (with timeout)
        if self._auth_event.wait(timeout=300):  # 5 minutes timeout
            return self._auth_result or ""
        
        # Timeout - close dialog
        dialog.open = False
        if self.page:
            self.page.update()
        return ""
    
    def _on_auth_dialog_submit(self, value: str):
        """Handle authentication dialog submission."""
        self._auth_result = value
        self._auth_event.set()
    
    def _show_error(self, message: str, error_text_control: ft.Text):
        """Show error message in specified error text control."""
        error_text_control.value = message
        error_text_control.visible = True
        self.update()
