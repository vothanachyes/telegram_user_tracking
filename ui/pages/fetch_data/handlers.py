"""
Event handlers and fetch logic for fetch data page.
"""

import asyncio
import logging
import flet as ft
from typing import Optional, Tuple, Callable
from datetime import datetime, timedelta
from ui.theme import theme_manager
from database.db_manager import DatabaseManager
from database.models import TelegramCredential
from services.telegram import TelegramService
from services.license_service import LicenseService
from ui.components.account_selector import AccountSelector
from ui.components.group_selector import GroupSelector
from ui.pages.fetch_data.view_model import FetchViewModel

logger = logging.getLogger(__name__)


class FetchHandlers:
    """Handles fetch logic, validation, and error handling."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        telegram_service: TelegramService,
        view_model: FetchViewModel,
        page: Optional['ft.Page'] = None
    ):
        self.db_manager = db_manager
        self.telegram_service = telegram_service
        self.view_model = view_model
        self.page = page
        self.license_service = LicenseService(db_manager)
        self.selected_credential: Optional[TelegramCredential] = None
        
        # Account and group selectors
        self.account_selector = AccountSelector(
            on_account_selected=self._on_account_selected,
            on_refresh=self._refresh_accounts
        )
        
        self.group_selector = GroupSelector(
            on_group_selected=self._on_group_selected,
            on_manual_entry=self._on_group_manual_entry
        )
        
        # Date fields
        today = datetime.now()
        last_month = today - timedelta(days=30)
        
        self.start_date_field = ft.TextField(
            label=theme_manager.t("start_date"),
            hint_text="YYYY-MM-DD",
            value=last_month.strftime("%Y-%m-%d"),
            border_radius=theme_manager.corner_radius,
            expand=True
        )
        
        self.end_date_field = ft.TextField(
            label=theme_manager.t("end_date"),
            hint_text="YYYY-MM-DD",
            value=today.strftime("%Y-%m-%d"),
            border_radius=theme_manager.corner_radius,
            expand=True
        )
        
        # Group ID field (hidden, for backward compatibility)
        self.group_id_field = ft.TextField(
            label=theme_manager.t("group_id"),
            hint_text="e.g., -1001234567890",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=theme_manager.corner_radius,
            expand=True,
            visible=False
        )
        
        # Initialize groups
        self._update_groups_list()
    
    def set_page(self, page: 'ft.Page'):
        """Set page reference and initialize accounts."""
        self.page = page
        if self.account_selector:
            self.account_selector.set_page(page)
        if self.group_selector:
            self.group_selector.set_page(page)
            self.group_selector.disable()
        
        # Initialize account list
        if page and hasattr(page, 'run_task'):
            page.run_task(self._initialize_accounts)
        else:
            asyncio.create_task(self._initialize_accounts())
    
    async def _initialize_accounts(self):
        """Initialize account list."""
        try:
            accounts_with_status = await self.telegram_service.get_all_accounts_with_status()
            if accounts_with_status:
                self.account_selector.update_accounts(accounts_with_status)
            else:
                self.account_selector.update_accounts([])
        except Exception as e:
            logger.error(f"Error initializing accounts: {e}")
            self.account_selector.update_accounts([])
    
    def _on_account_selected(self, credential: TelegramCredential):
        """Handle account selection."""
        self.selected_credential = credential
        self.group_selector.enable()
        if self.page:
            self.page.update()
    
    def _on_group_selected(self, group_id: int):
        """Handle group selection from dropdown."""
        self.group_id_field.value = str(group_id)
        if self.page:
            self.page.update()
    
    def _on_group_manual_entry(self, group_id: int):
        """Handle manual group ID entry."""
        self.group_id_field.value = str(group_id)
        if self.page:
            self.page.update()
    
    async def _refresh_accounts(self):
        """Refresh account list and statuses."""
        try:
            accounts_with_status = await self.telegram_service.get_all_accounts_with_status()
            self.account_selector.update_accounts(accounts_with_status)
        except Exception as e:
            logger.error(f"Error refreshing accounts: {e}")
    
    def _update_groups_list(self):
        """Update groups list in group selector."""
        try:
            groups = self.db_manager.get_all_groups()
            if groups:
                self.group_selector.update_groups(groups)
            else:
                self.group_selector.update_groups([])
        except Exception as e:
            logger.error(f"Error updating groups list: {e}")
            self.group_selector.update_groups([])
    
    def _validate_inputs(self) -> Tuple[bool, Optional[str]]:
        """Validate user inputs."""
        # Validate group ID
        group_id = self.group_selector.get_selected_group_id()
        if not group_id:
            if self.group_id_field.value and self.group_id_field.value.strip():
                try:
                    group_id = int(self.group_id_field.value.strip())
                except ValueError:
                    return False, theme_manager.t("invalid_group_id")
            else:
                return False, theme_manager.t("group_id_required")
        
        # Validate dates
        try:
            start_date_str = self.start_date_field.value.strip()
            end_date_str = self.end_date_field.value.strip()
            
            if not start_date_str or not end_date_str:
                return False, theme_manager.t("dates_required")
            
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            
            if start_date > end_date:
                return False, theme_manager.t("invalid_date_range")
            
        except ValueError:
            return False, theme_manager.t("invalid_date_format")
        
        return True, None
    
    async def _validate_account_group_access(self) -> Tuple[bool, Optional[str]]:
        """Validate that selected account can access selected group."""
        if not self.selected_credential:
            return False, theme_manager.t("select_account_first")
        
        group_id = self.group_selector.get_selected_group_id()
        if not group_id:
            if self.group_id_field.value:
                try:
                    group_id = int(self.group_id_field.value.strip())
                    if group_id > 0:
                        return False, theme_manager.t("invalid_group_id") + " (Group IDs are typically negative numbers)"
                except ValueError:
                    return False, theme_manager.t("invalid_group_id")
            else:
                return False, theme_manager.t("group_id_required")
        
        try:
            success, group, error, has_access = await self.telegram_service.fetch_and_validate_group(
                self.selected_credential,
                group_id
            )
            
            if not success:
                error_msg = error or theme_manager.t("group_not_found")
                phone = self.selected_credential.phone_number
                group_name = group.group_name if group else str(group_id) if group_id else "group"
                
                if error == "permission_denied":
                    return False, theme_manager.t("account_no_permission").format(
                        phone=phone,
                        group_name=group_name
                    )
                elif error == "not_member":
                    return False, theme_manager.t("account_not_member").format(
                        phone=phone,
                        group_name=group_name
                    )
                elif "expired" in error_msg.lower() or "invalid" in error_msg.lower() or "unauthorized" in error_msg.lower():
                    error_msg = theme_manager.t("account_status_expired") + ". " + theme_manager.t("select_account_first")
                
                return False, error_msg
            
            if not has_access:
                phone = self.selected_credential.phone_number
                group_name = group.group_name if group else str(group_id)
                return False, theme_manager.t("account_not_member").format(
                    phone=phone,
                    group_name=group_name
                )
            
            if group:
                self.group_selector.set_group_info(group.group_name, group.last_fetch_date)
            
            return True, None
            
        except ConnectionError as e:
            logger.error(f"Network error during validation: {e}")
            return False, theme_manager.t("connection_error")
        except Exception as e:
            logger.error(f"Error validating account group access: {e}")
            error_msg = str(e)
            if "network" in error_msg.lower() or "connection" in error_msg.lower():
                return False, theme_manager.t("connection_error")
            if "timeout" in error_msg.lower():
                return False, theme_manager.t("connection_error") + " (Timeout)"
            return False, error_msg
    
    async def start_fetch(self, on_progress: Optional[Callable] = None, on_message: Optional[Callable] = None) -> Tuple[bool, int, Optional[str]]:
        """
        Start fetching messages.
        
        Args:
            on_progress: Optional progress callback (current, total)
            on_message: Optional message callback (message, user, error)
        
        Returns:
            (success, message_count, error_message)
        """
        # Validate inputs
        is_valid, error_msg = self._validate_inputs()
        if not is_valid:
            return False, 0, error_msg
        
        # Validate account-group access
        is_valid, error_msg = await self._validate_account_group_access()
        if not is_valid:
            return False, 0, error_msg
        
        # Check license
        can_add, license_error = self.license_service.can_add_group()
        if not can_add:
            return False, 0, license_error
        
        # Get group ID
        group_id = self.group_selector.get_selected_group_id()
        if not group_id:
            if self.group_id_field.value:
                group_id = int(self.group_id_field.value.strip())
            else:
                return False, 0, theme_manager.t("group_id_required")
        
        # Get date range
        start_date = datetime.strptime(self.start_date_field.value.strip(), "%Y-%m-%d")
        end_date = datetime.strptime(self.end_date_field.value.strip(), "%Y-%m-%d")
        
        # Disable inputs
        self.account_selector.disable()
        self.group_selector.disable()
        self.start_date_field.disabled = True
        self.end_date_field.disabled = True
        
        # Set fetching state
        self.view_model.is_fetching = True
        
        try:
            # Message callback wrapper
            def message_callback(message):
                """Wrapper to get user and call on_message."""
                try:
                    user = self.db_manager.get_user_by_id(message.user_id)
                    error = None
                except Exception as e:
                    logger.error(f"Error getting user for message: {e}")
                    user = None
                    error = str(e)
                
                if on_message:
                    on_message(message, user, error)
            
            # Fetch messages
            if self.selected_credential:
                success, message_count, error = await self.telegram_service.fetch_messages_with_account(
                    credential=self.selected_credential,
                    group_id=group_id,
                    start_date=start_date,
                    end_date=end_date,
                    progress_callback=on_progress,
                    message_callback=message_callback
                )
            else:
                success, message_count, error = await self.telegram_service.fetch_messages(
                    group_id=group_id,
                    start_date=start_date,
                    end_date=end_date,
                    progress_callback=on_progress,
                    message_callback=message_callback
                )
            
            # Refresh group selector with updated last_fetch_date after successful fetch
            if success:
                groups = self.db_manager.get_all_groups()
                self.group_selector.refresh_selected_group_info(groups)
            
            return success, message_count, error
            
        except Exception as e:
            logger.error(f"Error in fetch: {e}")
            return False, 0, str(e)
        finally:
            # Re-enable inputs
            self.account_selector.enable()
            self.group_selector.enable()
            self.start_date_field.disabled = False
            self.end_date_field.disabled = False
            self.view_model.is_fetching = False

