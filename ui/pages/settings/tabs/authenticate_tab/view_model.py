"""
View model for authenticate tab state management.
"""

import asyncio
import logging
import flet as ft
from database.models import AppSettings
from ui.theme import theme_manager
from ui.pages.settings.tabs.authenticate_tab.utils import AuthenticateTabUtils

logger = logging.getLogger(__name__)


class AuthenticateTabViewModel:
    """View model for managing authenticate tab state."""
    
    def __init__(self, authenticate_tab):
        """Initialize view model with reference to tab."""
        self.tab = authenticate_tab
    
    def update_settings(self, new_settings: AppSettings):
        """Update current settings."""
        self.tab.current_settings = new_settings
        self.tab._reset(None)
    
    def update_status(self):
        """Update status texts."""
        self.tab.api_status_text.value = AuthenticateTabUtils.get_api_status_text(self.tab.current_settings)
        self.tab.account_status_text.value = AuthenticateTabUtils.get_account_status_text(
            self.tab.telegram_service, 
            self.tab.db_manager
        )
        self.update_accounts_list()
        self._update_account_count()
    
    def update_connection_buttons(self):
        """Update connection button states."""
        is_configured = bool(
            self.tab.current_settings.telegram_api_id and 
            self.tab.current_settings.telegram_api_hash
        )
        is_connected = self.tab.telegram_service and self.tab.telegram_service.is_connected()
        
        self.tab.connect_btn.disabled = not is_configured or is_connected
        self.tab.disconnect_btn.visible = is_connected
        self.tab.disconnect_btn.disabled = not is_connected
    
    def _update_account_count(self):
        """Update account count display."""
        # Use async wrapper to respect semaphore for database operations
        async def _update_async():
            try:
                # Use semaphore to prevent database lock conflicts
                async with self.tab._db_semaphore:
                    from services.auth_service import auth_service
                    from services.license_service import LicenseService
                    
                    current_user = auth_service.get_current_user()
                    if not current_user:
                        self.tab.account_count_text.value = ""
                        return
                    
                    user_email = current_user.get('email')
                    uid = current_user.get('uid')
                    
                    if not user_email or not uid:
                        self.tab.account_count_text.value = ""
                        return
                    
                    license_service = LicenseService(self.tab.db_manager, auth_service)
                    status = license_service.check_license_status(user_email, uid)
                    max_accounts = status.get('max_accounts', 1)
                    
                    current_count = self.tab.db_manager.get_account_count()
                    
                    # Format: "2/5 acc"
                    self.tab.account_count_text.value = theme_manager.t("account_count_display").format(
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
                    self.tab.account_count_text.tooltip = tooltip_text
                    
                    # Disable Add Account button if limit reached
                    self.tab.add_account_btn.disabled = current_count >= max_accounts
                    
                    # Update UI if page is available
                    if hasattr(self.tab, 'page') and self.tab.page:
                        self.tab.page.update()
                    
            except Exception as e:
                logger.error(f"Error updating account count: {e}")
                self.tab.account_count_text.value = ""
        
        # Check if we can run async operations
        try:
            # Try to get running event loop
            asyncio.get_running_loop()
            # If we get here, there's a running loop - schedule the task
            if hasattr(self.tab, 'page') and self.tab.page and hasattr(self.tab.page, 'run_task'):
                self.tab.page.run_task(_update_async)
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
                        license_service = LicenseService(self.tab.db_manager, auth_service)
                        status = license_service.check_license_status(user_email, uid)
                        max_accounts = status.get('max_accounts', 1)
                        current_count = self.tab.db_manager.get_account_count()
                        
                        self.tab.account_count_text.value = theme_manager.t("account_count_display").format(
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
                        self.tab.account_count_text.tooltip = tooltip_text
                        self.tab.add_account_btn.disabled = current_count >= max_accounts
            except Exception as e:
                # Silently fail during initialization - will update later when page is set
                pass
    
    def update_accounts_list(self):
        """Update the accounts list display."""
        # Prevent concurrent refreshes to avoid database lock conflicts
        # Check and set flag atomically to prevent race conditions
        if self.tab._refreshing_accounts:
            return
        
        # Set flag immediately to prevent concurrent calls
        self.tab._refreshing_accounts = True
        
        async def _update_async():
            try:
                # Use semaphore to ensure only one database operation at a time
                # This prevents database lock conflicts when multiple operations try to access DB
                # The semaphore protects both the database read AND the status checks
                async with self.tab._db_semaphore:
                    # Small delay to ensure any previous DB operations have completed
                    await asyncio.sleep(0.1)
                accounts_with_status = await self.tab.telegram_service.get_all_accounts_with_status()
                self._render_accounts_list(accounts_with_status)
            except Exception as e:
                logger.error(f"Error updating accounts list: {e}")
            finally:
                # Always reset flag, even on error
                self.tab._refreshing_accounts = False
                # Re-enable button and hide loading
                if hasattr(self.tab, 'refresh_status_btn'):
                    self.tab.refresh_status_btn.disabled = False
                if hasattr(self.tab, 'refresh_loading'):
                    self.tab.refresh_loading.visible = False
                if hasattr(self.tab, 'page') and self.tab.page:
                    self.tab.page.update()
        
        if hasattr(self.tab, 'page') and self.tab.page and hasattr(self.tab.page, 'run_task'):
            self.tab.page.run_task(_update_async)
        else:
            asyncio.create_task(_update_async())
    
    def _render_accounts_list(self, accounts_with_status):
        """Render the list of accounts."""
        self.tab.accounts_list.controls = []
        
        if not accounts_with_status:
            self.tab.accounts_list.controls.append(
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
                status_text = AuthenticateTabUtils.get_status_text(status)
                
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
                        on_click=lambda e, cred=credential: self.tab._handle_reconnect_account(cred),
                        style="primary"
                    )
                    action_buttons.append(reconnect_btn)
                
                # Add Remove button for all accounts
                remove_btn = theme_manager.create_button(
                    text=theme_manager.t("remove_account"),
                    icon=ft.Icons.DELETE,
                    on_click=lambda e, cred_id=credential.id: self.tab._handle_remove_account(cred_id),
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
                                theme_manager.t('account_last_used').format(date=last_used_text) if last_used_text else theme_manager.t("account_last_used").format(date="Never"),
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
                self.tab.accounts_list.controls.append(account_row)
        
        if hasattr(self.tab, 'page') and self.tab.page:
            self.tab.page.update()

