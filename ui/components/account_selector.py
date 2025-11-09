"""
Account selector component for selecting Telegram accounts.
"""

import flet as ft
import logging
from typing import Optional, Callable, List, Dict
from datetime import datetime
from database.models import TelegramCredential
from ui.theme import theme_manager

logger = logging.getLogger(__name__)


class AccountSelector:
    """Component for selecting Telegram accounts with status badges."""
    
    def __init__(
        self,
        on_account_selected: Optional[Callable[[TelegramCredential], None]] = None,
        on_refresh: Optional[Callable[[], None]] = None,
        width: Optional[int] = None
    ):
        """
        Initialize account selector.
        
        Args:
            on_account_selected: Callback when an account is selected
            on_refresh: Callback when refresh button is clicked
            width: Optional width for the dropdown
        """
        self.on_account_selected = on_account_selected
        self.on_refresh = on_refresh
        self.page: Optional[ft.Page] = None
        self.selected_credential_id: Optional[int] = None
        self.accounts_with_status: List[Dict] = []
        
        # Account dropdown (create manually to support Option objects with keys)
        self.account_dropdown = ft.Dropdown(
            label=theme_manager.t("select_account"),
            options=[],
            value=None,
            on_change=self._on_account_change,
            border_radius=theme_manager.corner_radius,
            border_color=theme_manager.border_color,
            focused_border_color=theme_manager.primary_color,
            expand=True if width is None else False,
            width=width
        )
        
        # Refresh button
        self.refresh_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip=theme_manager.t("refresh_account_status"),
            on_click=self._on_refresh_click
        )
        
        # Account count text
        self.account_count_text = ft.Text(
            "",
            size=12,
            color=theme_manager.text_secondary_color
        )
    
    def build(self) -> ft.Column:
        """Build the account selector component."""
        return ft.Column([
            ft.Row([
                self.account_dropdown,
                self.refresh_btn,
            ], spacing=10, expand=True),
            self.account_count_text,
        ], spacing=5, tight=True)
    
    def set_page(self, page: ft.Page):
        """Set the Flet page instance for updates."""
        self.page = page
    
    def update_accounts(self, accounts_with_status: List[Dict]):
        """
        Update dropdown with accounts and their statuses.
        
        Args:
            accounts_with_status: List of dicts with 'credential' and 'status' keys
        """
        self.accounts_with_status = accounts_with_status
        
        options = []
        for item in accounts_with_status:
            credential: TelegramCredential = item['credential']
            status = item.get('status', 'not_connected')
            
            # Format display text
            phone = credential.phone_number
            last_used = ""
            if credential.last_used:
                last_used = credential.last_used.strftime("%Y-%m-%d")
            
            # Status badge text
            status_text = self._get_status_text(status)
            
            # Build option text
            if last_used:
                option_text = f"{phone} ({status_text}) - {theme_manager.t('account_last_used').format(date=last_used)}"
            else:
                option_text = f"{phone} ({status_text})"
            
            options.append(ft.dropdown.Option(
                key=str(credential.id),
                text=option_text,
                disabled=(status in ('expired', 'error'))
            ))
        
        self.account_dropdown.options = options
        
        # Update account count
        total = len(accounts_with_status)
        active = sum(1 for item in accounts_with_status if item.get('status') == 'active')
        self.account_count_text.value = theme_manager.t("account_count").format(
            current=active,
            total=total
        )
        
        # Set default selection if not already set
        if not self.selected_credential_id and accounts_with_status:
            # Try to find default or first active account
            default_account = None
            for item in accounts_with_status:
                cred = item['credential']
                if cred.is_default and item.get('status') == 'active':
                    default_account = cred
                    break
            
            if not default_account:
                # Find first active account
                for item in accounts_with_status:
                    if item.get('status') == 'active':
                        default_account = item['credential']
                        break
            
            if default_account:
                self.set_selected_account(default_account.id)
        
        if self.page:
            self.account_dropdown.update()
            self.account_count_text.update()
    
    def set_selected_account(self, credential_id: int):
        """Set the selected account by credential ID."""
        self.selected_credential_id = credential_id
        self.account_dropdown.value = str(credential_id)
        if self.page:
            self.account_dropdown.update()
    
    def get_selected_account(self) -> Optional[TelegramCredential]:
        """Get the currently selected account credential."""
        if not self.selected_credential_id:
            return None
        
        for item in self.accounts_with_status:
            if item['credential'].id == self.selected_credential_id:
                return item['credential']
        return None
    
    def get_selected_account_status(self) -> Optional[str]:
        """Get the status of the currently selected account."""
        if not self.selected_credential_id:
            return None
        
        for item in self.accounts_with_status:
            if item['credential'].id == self.selected_credential_id:
                return item.get('status', 'not_connected')
        return None
    
    def _get_status_text(self, status: str) -> str:
        """Get localized status text."""
        status_map = {
            'active': theme_manager.t("account_status_active"),
            'expired': theme_manager.t("account_status_expired"),
            'not_connected': theme_manager.t("account_status_not_available"),
            'error': theme_manager.t("account_status_not_available")
        }
        return status_map.get(status, status)
    
    def _on_account_change(self, e):
        """Handle account selection change."""
        if not e.control.value:
            self.selected_credential_id = None
            return
        
        try:
            credential_id = int(e.control.value)
            self.selected_credential_id = credential_id
            
            # Find selected credential
            for item in self.accounts_with_status:
                if item['credential'].id == credential_id:
                    if self.on_account_selected:
                        self.on_account_selected(item['credential'])
                    break
        except (ValueError, TypeError):
            logger.error(f"Invalid credential ID: {e.control.value}")
    
    def _on_refresh_click(self, e):
        """Handle refresh button click."""
        if self.on_refresh:
            import asyncio
            if asyncio.iscoroutinefunction(self.on_refresh):
                if self.page and hasattr(self.page, 'run_task'):
                    self.page.run_task(self.on_refresh)
                else:
                    asyncio.create_task(self.on_refresh())
            else:
                self.on_refresh()
    
    def disable(self):
        """Disable the account selector."""
        self.account_dropdown.disabled = True
        self.refresh_btn.disabled = True
        if self.page:
            try:
                self.account_dropdown.update()
                self.refresh_btn.update()
            except AssertionError:
                # Control not added to page yet - disabled state will be applied when added
                pass
    
    def enable(self):
        """Enable the account selector."""
        self.account_dropdown.disabled = False
        self.refresh_btn.disabled = False
        if self.page:
            try:
                self.account_dropdown.update()
                self.refresh_btn.update()
            except AssertionError:
                # Control not added to page yet - enabled state will be applied when added
                pass

