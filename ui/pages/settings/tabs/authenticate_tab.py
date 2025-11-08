"""
Authenticate settings tab component.
"""

import flet as ft
import asyncio
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
        
        ENABLE_QR_LOGIN = False
        
        qr_radio = ft.Radio(
            value="qr",
            label=theme_manager.t("qr_code_login") + " 🚧",
            disabled=not ENABLE_QR_LOGIN,
            tooltip="QR Code login coming soon! Currently in development. Use phone login for now." if not ENABLE_QR_LOGIN else None
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
        self.accounts_section = self._build_accounts_section()
        
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
        self._update_account_count()
    
    def build(self) -> ft.Container:
        """Build the authenticate tab with left navigation."""
        # Left navigation sidebar
        left_nav = self._build_left_navigation()
        
        # Right content area
        content_area = self._build_content_area()
        
        return ft.Container(
            content=ft.Row([
                left_nav,
                ft.VerticalDivider(width=1),
                content_area,
            ], spacing=0, expand=True),
            padding=10,
            expand=True
        )
    
    def _build_left_navigation(self) -> ft.Container:
        """Build left navigation sidebar."""
        # Store button references for style updates
        self.accounts_nav_btn = ft.ElevatedButton(
            text=theme_manager.t("accounts_section"),
            icon=ft.Icons.ACCOUNT_CIRCLE,
            on_click=lambda e: self._switch_section("accounts"),
            style=ft.ButtonStyle(
                bgcolor=theme_manager.primary_color if self.selected_section == "accounts" else None,
                color=ft.Colors.WHITE if self.selected_section == "accounts" else None
            ),
            width=150,
            height=40
        )
        
        self.config_nav_btn = ft.ElevatedButton(
            text=theme_manager.t("configuration_section"),
            icon=ft.Icons.SETTINGS,
            on_click=lambda e: self._switch_section("configuration"),
            style=ft.ButtonStyle(
                bgcolor=theme_manager.primary_color if self.selected_section == "configuration" else None,
                color=ft.Colors.WHITE if self.selected_section == "configuration" else None
            ),
            width=150,
            height=40
        )
        
        return ft.Container(
            content=ft.Column([
                self.accounts_nav_btn,
                self.config_nav_btn,
            ], spacing=10),
            width=170,
            padding=10,
            bgcolor=theme_manager.surface_color,
            border_radius=theme_manager.corner_radius
        )
    
    def _build_content_area(self) -> ft.Container:
        """Build right content area based on selected section."""
        if self.selected_section == "accounts":
            content = self._build_accounts_section_content()
        else:
            content = self._build_configuration_section_content()
        
        container = ft.Container(
            content=content,
            expand=True,
            padding=10
        )
        self.content_area_container = container
        return container
    
    def _build_accounts_section_content(self) -> ft.Column:
        """Build accounts section content."""
        return ft.Column([
            ft.Row([
                ft.Text(
                    theme_manager.t("accounts_section"),
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    expand=True
                ),
                self.account_count_text,
            ], spacing=10),
            ft.Divider(),
            ft.Row([
                self.add_account_btn,
                self.refresh_status_btn,
            ], spacing=10),
            self.accounts_list,
            self.error_text,
        ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)
    
    def _build_configuration_section_content(self) -> ft.Column:
        """Build configuration section content."""
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
        
        return ft.Column([
            ft.Text(
                theme_manager.t("configuration_section"),
                size=24,
                weight=ft.FontWeight.BOLD
            ),
            ft.Divider(),
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
            self.error_text,
            ft.Row([
                cancel_api_btn,
                save_api_btn,
            ], alignment=ft.MainAxisAlignment.END, spacing=10),
        ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)
    
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
                content = self._build_accounts_section_content()
                # Auto-refresh accounts list when switching to Accounts section
                self.update_accounts_list()
            else:
                content = self._build_configuration_section_content()
            self.content_area_container.content = content
            if hasattr(self, 'page') and self.page:
                self.page.update()
    
    def _update_account_count(self):
        """Update account count display."""
        # Use async wrapper to respect semaphore for database operations
        async def _update_async():
            try:
                # Use semaphore to prevent database lock conflicts
                async with self._db_semaphore:
                    from services.auth_service import auth_service
                    from services.license_service import LicenseService
                    
                    current_user = auth_service.get_current_user()
                    if not current_user:
                        self.account_count_text.value = ""
                        return
                    
                    user_email = current_user.get('email')
                    uid = current_user.get('uid')
                    
                    if not user_email or not uid:
                        self.account_count_text.value = ""
                        return
                    
                    license_service = LicenseService(self.db_manager, auth_service)
                    status = license_service.check_license_status(user_email, uid)
                    max_accounts = status.get('max_accounts', 1)
                    
                    current_count = self.db_manager.get_account_count()
                    
                    # Format: "2/5 acc"
                    self.account_count_text.value = theme_manager.t("account_count_display").format(
                        current=current_count,
                        max=max_accounts
                    )
                    
                    # Update tooltip
                    tier = status.get('tier', 'bronze')
                    tier_name = theme_manager.t(f"{tier}_tier") or tier.capitalize()
                    tooltip_text = theme_manager.t("account_count_tooltip").format(
                        current=current_count,
                        max=max_accounts,
                        tier=tier_name
                    )
                    self.account_count_text.tooltip = tooltip_text
                    
                    # Disable Add Account button if limit reached
                    self.add_account_btn.disabled = current_count >= max_accounts
                    
                    # Update UI if page is available
                    if hasattr(self, 'page') and self.page:
                        self.page.update()
                    
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error updating account count: {e}")
                self.account_count_text.value = ""
        
        # Check if we can run async operations
        try:
            # Try to get running event loop
            asyncio.get_running_loop()
            # If we get here, there's a running loop - schedule the task
            if hasattr(self, 'page') and self.page and hasattr(self.page, 'run_task'):
                self.page.run_task(_update_async)
            else:
                asyncio.create_task(_update_async())
        except RuntimeError:
            # No running event loop - this happens during __init__
            # For initial call, do a simple synchronous read without semaphore
            # (no concurrent operations during initialization)
            try:
                from services.auth_service import auth_service
                from services.license_service import LicenseService
                
                current_user = auth_service.get_current_user()
                if current_user:
                    user_email = current_user.get('email')
                    uid = current_user.get('uid')
                    
                    if user_email and uid:
                        license_service = LicenseService(self.db_manager, auth_service)
                        status = license_service.check_license_status(user_email, uid)
                        max_accounts = status.get('max_accounts', 1)
                        current_count = self.db_manager.get_account_count()
                        
                        self.account_count_text.value = theme_manager.t("account_count_display").format(
                            current=current_count,
                            max=max_accounts
                        )
                        
                        tier = status.get('tier', 'bronze')
                        tier_name = theme_manager.t(f"{tier}_tier") or tier.capitalize()
                        tooltip_text = theme_manager.t("account_count_tooltip").format(
                            current=current_count,
                            max=max_accounts,
                            tier=tier_name
                        )
                        self.account_count_text.tooltip = tooltip_text
                        self.add_account_btn.disabled = current_count >= max_accounts
            except Exception as e:
                # Silently fail during initialization - will update later when page is set
                pass
    
    def _handle_add_account(self, e):
        """Handle add account button click."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("=== _handle_add_account() in authenticate_tab called ===")
        logger.info(f"Event: {e}")
        logger.info(f"Handlers available: {self.handlers is not None}")
        logger.info(f"Has handle_add_account method: {self.handlers and hasattr(self.handlers, 'handle_add_account')}")
        
        if self.handlers and hasattr(self.handlers, 'handle_add_account'):
            logger.info("Calling handlers.handle_add_account()")
            self.handlers.handle_add_account(e)
            # Update account count after addition
            self._update_account_count()
        else:
            logger.error("Handlers not available or handle_add_account method not found")
    
    def update_settings(self, new_settings: AppSettings):
        """Update current settings."""
        self.current_settings = new_settings
        self._reset(None)
    
    def update_status(self):
        """Update status texts."""
        self.api_status_text.value = self._get_api_status_text()
        self.account_status_text.value = self._get_account_status_text()
        self.update_accounts_list()
        self._update_account_count()
    
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
        self.update_connection_buttons()
        self.error_text.visible = False
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _on_login_method_change(self, e):
        """Handle login method change."""
        self.phone_field.visible = True
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _handle_telegram_connect(self, e):
        """Handle Telegram connection."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            if not hasattr(self, 'page') or not self.page:
                if e and hasattr(e, 'control') and e.control.page:
                    self.page = e.control.page
                elif self.connect_btn.page:
                    self.page = self.connect_btn.page
            
            if self.page and not self.handlers.page:
                self.handlers.page = self.page
            
            logger.debug(f"Connect button clicked. Login method: phone (QR disabled)")
            
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
    
    def _build_accounts_section(self) -> ft.Container:
        """Build the saved accounts management section."""
        return theme_manager.create_card(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        theme_manager.t("saved_telegram_accounts"),
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        expand=True
                    ),
                    self.refresh_status_btn,
                ], spacing=10),
                ft.Divider(),
                self.accounts_list,
            ], spacing=15)
        )
    
    def update_accounts_list(self):
        """Update the accounts list display."""
        # Prevent concurrent refreshes to avoid database lock conflicts
        # Check and set flag atomically to prevent race conditions
        if self._refreshing_accounts:
            return
        
        # Set flag immediately to prevent concurrent calls
        self._refreshing_accounts = True
        
        async def _update_async():
            try:
                # Use semaphore to ensure only one database operation at a time
                # This prevents database lock conflicts when multiple operations try to access DB
                # The semaphore protects both the database read AND the status checks
                async with self._db_semaphore:
                    # Small delay to ensure any previous DB operations have completed
                    await asyncio.sleep(0.1)
                accounts_with_status = await self.telegram_service.get_all_accounts_with_status()
                self._render_accounts_list(accounts_with_status)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error updating accounts list: {e}")
            finally:
                # Always reset flag, even on error
                self._refreshing_accounts = False
        
        if hasattr(self, 'page') and self.page and hasattr(self.page, 'run_task'):
            self.page.run_task(_update_async)
        else:
            asyncio.create_task(_update_async())
    
    def _render_accounts_list(self, accounts_with_status):
        """Render the list of accounts."""
        self.accounts_list.controls = []
        
        if not accounts_with_status:
            self.accounts_list.controls.append(
                ft.Text(
                    theme_manager.t("no_accounts_saved"),
                    size=14,
                    color=theme_manager.text_secondary_color,
                    italic=True
                )
            )
        else:
            for item in accounts_with_status:
                credential = item['credential']
                status = item.get('status', 'not_connected')
                
                # Status badge
                status_color = ft.Colors.GREEN if status == 'active' else (
                    ft.Colors.RED if status == 'expired' else ft.Colors.GREY
                )
                status_text = self._get_status_text(status)
                
                # Last used date
                last_used_text = ""
                if credential.last_used:
                    last_used_text = credential.last_used.strftime("%Y-%m-%d %H:%M")
                
                # Action buttons
                action_buttons = []
                
                # Add Reconnect button for expired accounts
                if status == 'expired':
                    reconnect_btn = theme_manager.create_button(
                        text=theme_manager.t("reconnect") or "Reconnect",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda e, cred=credential: self._handle_reconnect_account(cred),
                        style="primary"
                    )
                    action_buttons.append(reconnect_btn)
                
                # Add Remove button for all accounts
                remove_btn = theme_manager.create_button(
                    text=theme_manager.t("remove_account"),
                    icon=ft.Icons.DELETE,
                    on_click=lambda e, cred_id=credential.id: self._handle_remove_account(cred_id),
                    style="error"
                )
                action_buttons.append(remove_btn)
                
                # Account row
                account_row = ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Text(
                                    credential.phone_number,
                                    size=16,
                                    weight=ft.FontWeight.BOLD
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        status_text,
                                        size=12,
                                        color=ft.Colors.WHITE
                                    ),
                                    bgcolor=status_color,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                    border_radius=theme_manager.corner_radius
                                ),
                            ], spacing=10),
                            ft.Text(
                                f"{theme_manager.t('account_last_used')}: {last_used_text}" if last_used_text else theme_manager.t("account_last_used") + ": Never",
                                size=12,
                                color=theme_manager.text_secondary_color
                            ),
                        ], spacing=5, expand=True),
                        ft.Row(action_buttons, spacing=10),
                    ], spacing=10, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10,
                    border=ft.border.all(1, theme_manager.border_color),
                    border_radius=theme_manager.corner_radius,
                    bgcolor=theme_manager.surface_color
                )
                self.accounts_list.controls.append(account_row)
        
        if hasattr(self, 'page') and self.page:
            self.accounts_list.update()
    
    def _get_status_text(self, status: str) -> str:
        """Get localized status text."""
        status_map = {
            'active': theme_manager.t("account_status_active"),
            'expired': theme_manager.t("account_status_expired"),
            'not_connected': theme_manager.t("account_status_not_available"),
            'error': theme_manager.t("account_status_not_available")
        }
        return status_map.get(status, status)
    
    def _handle_phone_change(self, e):
        """Handle phone number input change - remove leading zero."""
        if self.phone_input.value and self.phone_input.value.startswith("0"):
            # Remove leading zero
            self.phone_input.value = self.phone_input.value.lstrip("0")
            if hasattr(self, 'page') and self.page:
                self.page.update()
    
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
            self._update_account_count()

