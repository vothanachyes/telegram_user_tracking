"""
Authenticate settings tab component.
"""

import flet as ft
from typing import Optional, Callable
from database.models import AppSettings
from ui.theme import theme_manager
from config.settings import settings as app_settings


class AuthenticateTab:
    """Authenticate settings tab component."""
    
    def __init__(
        self,
        current_settings: AppSettings,
        telegram_service,
        db_manager,
        handlers
    ):
        self.current_settings = current_settings
        self.telegram_service = telegram_service
        self.db_manager = db_manager
        self.handlers = handlers
        
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
        self.error_text = ft.Text("", color=ft.Colors.RED, visible=False)
        
        # Update button states
        self._update_connection_buttons()
    
    def build(self) -> ft.Container:
        """Build the authenticate tab."""
        save_api_btn = theme_manager.create_button(
            text=theme_manager.t("save_api_credentials"),
            icon=ft.Icons.SAVE,
            on_click=self._save,
            style="success"
        )
        cancel_api_btn = theme_manager.create_button(
            text=theme_manager.t("cancel"),
            icon=ft.Icons.CANCEL,
            on_click=self._reset,
            style="error"
        )
        
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
                
                self.error_text,
                
                # Save/Cancel buttons for API credentials
                ft.Row([
                    cancel_api_btn,
                    save_api_btn,
                ], alignment=ft.MainAxisAlignment.END, spacing=10),
            ], scroll=ft.ScrollMode.AUTO, spacing=15),
            padding=10,
            expand=True
        )
    
    def update_settings(self, new_settings: AppSettings):
        """Update current settings."""
        self.current_settings = new_settings
        self._reset(None)
    
    def update_status(self):
        """Update status texts."""
        self.api_status_text.value = self._get_api_status_text()
        self.account_status_text.value = self._get_account_status_text()
    
    def update_connection_buttons(self):
        """Update connection button states."""
        is_configured = bool(
            self.current_settings.telegram_api_id and 
            self.current_settings.telegram_api_hash
        )
        is_connected = self.telegram_service and self.telegram_service.is_connected()
        
        self.connect_btn.disabled = not is_configured or is_connected
        self.disconnect_btn.visible = is_connected
        self.disconnect_btn.disabled = not is_connected
    
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
            credential = self.db_manager.get_default_credential()
            if credential:
                return f"{theme_manager.t('account_connected')} ({credential.phone_number})"
            return theme_manager.t("account_connected")
        return theme_manager.t("account_not_connected")
    
    def _save(self, e):
        """Save API credentials."""
        self.handlers.handle_save_authenticate(
            self.api_id_field,
            self.api_hash_field,
            self.error_text
        )
        self.current_settings = app_settings.load_settings()
    
    def _reset(self, e):
        """Reset to current settings."""
        self.current_settings = app_settings.load_settings()
        
        self.api_id_field.value = self.current_settings.telegram_api_id or ""
        self.api_hash_field.value = self.current_settings.telegram_api_hash or ""
        self.api_status_text.value = self._get_api_status_text()
        self.account_status_text.value = self._get_account_status_text()
        self._update_connection_buttons()
        self.error_text.visible = False
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _handle_telegram_connect(self, e):
        """Handle Telegram connection."""
        self.handlers.handle_telegram_connect(self.phone_field, self.error_text)
    
    def _handle_telegram_disconnect(self, e):
        """Handle Telegram disconnection."""
        self.handlers.handle_telegram_disconnect()

