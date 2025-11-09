"""
Main authenticate tab page - orchestrates components, view model, and utils.
"""

import flet as ft
import asyncio
import logging
from typing import Optional, Callable
from database.models import AppSettings
from ui.theme import theme_manager
from config.settings import settings as app_settings
from ui.pages.settings.tabs.authenticate_tab.components import AuthenticateTabComponents
from ui.pages.settings.tabs.authenticate_tab.view_model import AuthenticateTabViewModel
from ui.pages.settings.tabs.authenticate_tab.utils import AuthenticateTabUtils

logger = logging.getLogger(__name__)


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
        
        # Initialize sub-components
        self.components = AuthenticateTabComponents(self)
        self.view_model = AuthenticateTabViewModel(self)
        
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
            AuthenticateTabUtils.get_api_status_text(self.current_settings),
            size=14,
            color=theme_manager.text_secondary_color
        )
        
        ENABLE_QR_LOGIN = True
        
        qr_radio = ft.Radio(
            value="qr",
            label=theme_manager.t("qr_code_login") or "QR Code Login",
            disabled=not ENABLE_QR_LOGIN
        )
        
        self.login_method = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="phone", label=theme_manager.t("phone_login")),
                qr_radio,
            ], spacing=20),
            value="phone"
        )
        
        # Phone number input field with +855 prefix
        self.phone_input = theme_manager.create_text_field(
            label="",  # Label will be on the Row
            hint_text="123456789",
            value="",
            on_change=self._handle_phone_change
        )
        
        # Create phone field with prefix UI
        prefix_container = ft.Container(
            content=ft.Text("+855", size=16, weight=ft.FontWeight.BOLD, color=theme_manager.text_color),
            padding=ft.padding.symmetric(horizontal=12, vertical=16),
            alignment=ft.alignment.center_left,
            bgcolor=theme_manager.surface_color,
            border=ft.border.only(
                left=ft.BorderSide(1, theme_manager.border_color),
                top=ft.BorderSide(1, theme_manager.border_color),
                bottom=ft.BorderSide(1, theme_manager.border_color)
            ),
            border_radius=ft.border_radius.only(top_left=theme_manager.corner_radius, bottom_left=theme_manager.corner_radius),
            height=56
        )
        
        # Remove label from phone_input since we'll add it above
        self.phone_input.label = None
        
        self.phone_field = ft.Column([
            ft.Text(theme_manager.t("phone_number"), size=12, color=theme_manager.text_secondary_color),
            ft.Row([
                prefix_container,
                ft.Container(
                    content=self.phone_input,
                    expand=True,
                    border=ft.border.only(
                        right=ft.BorderSide(1, theme_manager.border_color),
                        top=ft.BorderSide(1, theme_manager.border_color),
                        bottom=ft.BorderSide(1, theme_manager.border_color)
                    ),
                    border_radius=ft.border_radius.only(top_right=theme_manager.corner_radius, bottom_right=theme_manager.corner_radius),
                )
            ], spacing=0, tight=True)
        ], spacing=4, tight=True)
        
        self.otp_field = theme_manager.create_text_field(
            label=theme_manager.t("enter_otp_code"),
            hint_text="12345",
            value="",
            visible=True
        )
        
        self.otp_helper = ft.Text(
            theme_manager.t("enter_otp_code_instructions") or "Enter the code sent to your Telegram app",
            size=12,
            color=theme_manager.text_secondary_color,
            visible=True
        )
        
        self.otp_submit_btn = theme_manager.create_button(
            text=theme_manager.t("confirm") or "Confirm",
            icon=ft.Icons.CHECK,
            on_click=lambda e: self._handle_otp_submit(e),
            style="success",
            visible=True
        )
        
        self.password_field = theme_manager.create_text_field(
            label=theme_manager.t("enter_2fa_password"),
            password=True,
            value="",
            visible=False
        )
        
        self.password_helper = ft.Text(
            theme_manager.t("enter_2fa_password_instructions") or "Enter your 2FA password",
            size=12,
            color=theme_manager.text_secondary_color,
            visible=False
        )
        
        self.password_submit_btn = theme_manager.create_button(
            text=theme_manager.t("confirm") or "Confirm",
            icon=ft.Icons.CHECK,
            on_click=None,
            style="success",
            visible=False
        )
        
        self.account_status_text = ft.Text(
            AuthenticateTabUtils.get_account_status_text(self.telegram_service, self.db_manager),
            size=14,
            color=theme_manager.text_secondary_color
        )
        
        self.connect_btn = theme_manager.create_button(
            text=theme_manager.t("connect_to_telegram"),
            icon=ft.Icons.LINK,
            on_click=self._handle_telegram_connect,
            style="primary"
        )
        
        self.login_method.on_change = self._on_login_method_change
        
        self.disconnect_btn = theme_manager.create_button(
            text=theme_manager.t("disconnect"),
            icon=ft.Icons.LINK_OFF,
            on_click=self._handle_telegram_disconnect,
            style="error"
        )
        
        self.error_text = ft.Text("", color=ft.Colors.RED, visible=False)
        
        # Account management section
        self.accounts_list = ft.Column([], spacing=10)
        self.refresh_status_btn = theme_manager.create_button(
            text=theme_manager.t("refresh_account_status"),
            icon=ft.Icons.REFRESH,
            on_click=self._handle_refresh_accounts,
            style="primary"
        )
        self.accounts_section = self.components._build_accounts_section()
        
        # Navigation state
        self.selected_section = "accounts"  # "accounts" or "configuration"
        
        # Account count display
        self.account_count_text = ft.Text(
            "",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=theme_manager.text_secondary_color
        )
        
        # Add Account button
        self.add_account_btn = theme_manager.create_button(
            text=theme_manager.t("add_account"),
            icon=ft.Icons.ADD,
            on_click=self._handle_add_account,
            style="primary"
        )
        
        # Content area container (will be set in build())
        self.content_area_container = None
        
        # Flag to prevent concurrent account list refreshes
        self._refreshing_accounts = False
        
        # Semaphore to prevent concurrent database operations
        # Only allows 1 database operation at a time to prevent locks
        self._db_semaphore = asyncio.Semaphore(1)
        
        self.update_connection_buttons()
        self.view_model._update_account_count()
    
    def build(self) -> ft.Container:
        """Build the authenticate tab with left navigation."""
        return self.components.build()
    
    def _switch_section(self, section: str):
        """Switch between sections."""
        self.selected_section = section
        
        # Update navigation button styles
        if hasattr(self, 'accounts_nav_btn') and hasattr(self, 'config_nav_btn'):
            self.accounts_nav_btn.style = ft.ButtonStyle(
                bgcolor=theme_manager.primary_color if self.selected_section == "accounts" else None,
                color=ft.Colors.WHITE if self.selected_section == "accounts" else None
            )
            self.config_nav_btn.style = ft.ButtonStyle(
                bgcolor=theme_manager.primary_color if self.selected_section == "configuration" else None,
                color=ft.Colors.WHITE if self.selected_section == "configuration" else None
            )
        
        if self.content_area_container:
            # Rebuild the content area
            if self.selected_section == "accounts":
                content = self.components._build_accounts_section_content()
                # Auto-refresh accounts list when switching to Accounts section
                self.update_accounts_list()
            else:
                content = self.components._build_configuration_section_content()
            self.content_area_container.content = content
            if hasattr(self, 'page') and self.page:
                self.page.update()
    
    def _handle_add_account(self, e):
        """Handle add account button click."""
        logger.info("=== _handle_add_account() in authenticate_tab called ===")
        logger.info(f"Event: {e}")
        logger.info(f"Handlers available: {self.handlers is not None}")
        logger.info(f"Has handle_add_account method: {self.handlers and hasattr(self.handlers, 'handle_add_account')}")
        
        if self.handlers and hasattr(self.handlers, 'handle_add_account'):
            logger.info("Calling handlers.handle_add_account()")
            self.handlers.handle_add_account(e)
            # Update account count after addition
            self.view_model._update_account_count()
        else:
            logger.error("Handlers not available or handle_add_account method not found")
    
    def update_settings(self, new_settings: AppSettings):
        """Update current settings."""
        self.view_model.update_settings(new_settings)
    
    def update_status(self):
        """Update status texts."""
        self.view_model.update_status()
    
    def update_connection_buttons(self):
        """Update connection button states."""
        self.view_model.update_connection_buttons()
    
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
        self.api_status_text.value = AuthenticateTabUtils.get_api_status_text(self.current_settings)
        self.account_status_text.value = AuthenticateTabUtils.get_account_status_text(
            self.telegram_service, 
            self.db_manager
        )
        self.update_connection_buttons()
        self.error_text.visible = False
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _on_login_method_change(self, e):
        """Handle login method change."""
        selected_method = self.login_method.value
        # Show phone field only for phone login
        self.phone_field.visible = (selected_method == "phone")
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _handle_telegram_connect(self, e):
        """Handle Telegram connection."""
        try:
            if not hasattr(self, 'page') or not self.page:
                if e and hasattr(e, 'control') and e.control.page:
                    self.page = e.control.page
                elif self.connect_btn.page:
                    self.page = self.connect_btn.page
            
            if self.page and not self.handlers.page:
                self.handlers.page = self.page
            
            # Check which login method is selected
            selected_method = self.login_method.value if hasattr(self, 'login_method') else "phone"
            logger.debug(f"Connect button clicked. Login method: {selected_method}")
            
            if selected_method == "qr":
                # Use QR code login
                self.handlers.handle_telegram_connect_qr(self.error_text)
            else:
                # Use phone login
                self.handlers.handle_telegram_connect(self.phone_field, self.error_text)
        except Exception as ex:
            logger.error(f"Error in _handle_telegram_connect: {ex}", exc_info=True)
            self.error_text.value = f"Error: {str(ex)}"
            self.error_text.visible = True
            if hasattr(self, 'page') and self.page:
                self.page.update()
            elif self.connect_btn.page:
                self.connect_btn.page.update()
    
    def _handle_telegram_disconnect(self, e):
        """Handle Telegram disconnection."""
        self.handlers.handle_telegram_disconnect()
    
    def _handle_otp_submit(self, e):
        """Handle OTP submit button click."""
        if self.handlers:
            self.handlers.handle_otp_submit(e)
    
    def update_accounts_list(self):
        """Update the accounts list display."""
        self.view_model.update_accounts_list()
    
    def _update_account_count(self):
        """Update account count display."""
        self.view_model._update_account_count()
    
    def _handle_phone_change(self, e):
        """Handle phone number input change - remove leading zero."""
        AuthenticateTabUtils.handle_phone_change(self.phone_input, getattr(self, 'page', None))
    
    def _handle_refresh_accounts(self, e):
        """Handle refresh accounts button click."""
        self.update_accounts_list()
    
    def _handle_reconnect_account(self, credential):
        """Handle reconnect account button click for expired accounts."""
        # Extract phone number and remove +855 prefix if present
        phone_number = credential.phone_number
        if phone_number.startswith("+855"):
            phone_number = phone_number[4:]  # Remove "+855" prefix
        
        # Pre-fill phone input field
        self.phone_input.value = phone_number
        
        # Switch to Configuration section
        self._switch_section("configuration")
        
        # Show message to user
        if hasattr(self, 'page') and self.page:
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("phone_number_prefilled") or f"Phone number pre-filled. Click 'Connect to Telegram' to reconnect.",
                bgcolor=ft.Colors.BLUE
            )
            self.page.update()
    
    def _handle_remove_account(self, credential_id: int):
        """Handle remove account button click."""
        if self.handlers and hasattr(self.handlers, 'handle_remove_account'):
            self.handlers.handle_remove_account(credential_id)
            # Refresh accounts list after removal
            self.update_accounts_list()
            # Update account count
            self.view_model._update_account_count()

