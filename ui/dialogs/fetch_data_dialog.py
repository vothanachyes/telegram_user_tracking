"""
Fetch data dialog for fetching messages from Telegram.
"""

import flet as ft
from typing import Callable, Optional, Tuple
from datetime import datetime, timedelta
from ui.theme import theme_manager
from .dialog import dialog_manager
from database.db_manager import DatabaseManager
from database.models import TelegramCredential
from services.telegram import TelegramService
from services.license_service import LicenseService
from ui.components.account_selector import AccountSelector
from ui.components.group_selector import GroupSelector
import asyncio
import logging

logger = logging.getLogger(__name__)


class FetchDataDialog(ft.AlertDialog):
    """Dialog for fetching data from Telegram."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        telegram_service: TelegramService,
        on_fetch_complete: Optional[Callable] = None
    ):
        self.db_manager = db_manager
        self.telegram_service = telegram_service
        self.on_fetch_complete_callback = on_fetch_complete
        self.license_service = LicenseService(db_manager)
        self.selected_credential: Optional[TelegramCredential] = None
        
        # Default date range (last 30 days)
        today = datetime.now()
        last_month = today - timedelta(days=30)
        
        # Account selector
        self.account_selector = AccountSelector(
            on_account_selected=self._on_account_selected,
            on_refresh=self._refresh_accounts
        )
        
        # Group selector
        self.group_selector = GroupSelector(
            on_group_selected=self._on_group_selected,
            on_manual_entry=self._on_group_manual_entry
        )
        
        # Initialize groups
        self._update_groups_list()
        
        # Group ID input (kept for backward compatibility, but will be replaced by group_selector)
        self.group_id_field = ft.TextField(
            label=theme_manager.t("group_id"),
            hint_text="e.g., -1001234567890",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=theme_manager.corner_radius,
            expand=True,
            visible=False  # Hidden, using group_selector instead
        )
        
        # Date inputs
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
        
        # Progress indicator
        self.progress_bar = ft.ProgressBar(
            visible=False,
            width=400
        )
        
        self.progress_text = ft.Text(
            "",
            size=14,
            color=theme_manager.text_secondary_color,
            visible=False
        )
        
        # Status text
        self.status_text = ft.Text(
            "",
            size=14,
            color=theme_manager.text_secondary_color,
            visible=False
        )
        
        # Create the dialog content
        super().__init__(
            modal=True,
            title=ft.Text(theme_manager.t("fetch_telegram_data")),
            content=self._build_content(),
            actions=[
                ft.TextButton(
                    theme_manager.t("cancel"),
                    on_click=self._close_dialog
                ),
                ft.ElevatedButton(
                    theme_manager.t("start_fetch"),
                    on_click=self._start_fetch,
                    icon=ft.Icons.PLAY_ARROW,
                    bgcolor=theme_manager.primary_color,
                    color=ft.Colors.WHITE
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def set_page(self, page: ft.Page):
        """Set page reference and initialize accounts."""
        self.page = page
        if self.account_selector:
            self.account_selector.set_page(page)
        if self.group_selector:
            self.group_selector.set_page(page)
            # Disable group selector until account is selected
            self.group_selector.disable()
        
        # Initialize account list
        if page and hasattr(page, 'run_task'):
            page.run_task(self._initialize_accounts)
        else:
            asyncio.create_task(self._initialize_accounts())
    
    async def _initialize_accounts(self):
        """Initialize account list on dialog open."""
        try:
            accounts_with_status = await self.telegram_service.get_all_accounts_with_status()
            if accounts_with_status:
                self.account_selector.update_accounts(accounts_with_status)
            else:
                # No accounts saved - show message
                self.account_selector.update_accounts([])
        except Exception as e:
            logger.error(f"Error initializing accounts: {e}")
            # Handle empty list gracefully
            self.account_selector.update_accounts([])
    
    def _build_content(self) -> ft.Container:
        """Build the dialog content."""
        
        # Info card
        info_card = theme_manager.create_card(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=theme_manager.primary_color, size=20),
                    ft.Text(
                        theme_manager.t("fetch_info"),
                        size=14,
                        color=theme_manager.text_secondary_color,
                    )
                ], spacing=10),
                ft.Text(
                    "• Make sure you're authorized with Telegram\n"
                    "• Enter the group ID (e.g., -1001234567890)\n"
                    "• Select date range to fetch messages",
                    size=12,
                    color=theme_manager.text_secondary_color,
                )
            ], spacing=10)
        )
        
        # Input section
        input_section = ft.Column([
            ft.Text(
                theme_manager.t("fetch_parameters"),
                size=16,
                weight=ft.FontWeight.BOLD
            ),
            ft.Container(height=5),
            self._build_account_selection(),
            self._build_group_selection(),
            ft.Row([
                self.start_date_field,
                self.end_date_field,
            ], spacing=10),
        ], spacing=10)
        
        # Progress section
        progress_section = ft.Column([
            self.progress_bar,
            self.progress_text,
            self.status_text,
        ], spacing=10)
        
        return ft.Container(
            content=ft.Column(
                [
                    info_card,
                    ft.Container(height=10),
                    input_section,
                    ft.Container(height=10),
                    progress_section,
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=550,
            padding=10,
        )
    
    def _validate_inputs(self) -> Tuple[bool, Optional[str]]:
        """Validate user inputs."""
        # Validate group ID (from selector or manual entry)
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
    
    def _build_account_selection(self) -> ft.Column:
        """Build account selection component."""
        return self.account_selector.build()
    
    def _build_group_selection(self) -> ft.Column:
        """Build group selection component."""
        return self.group_selector.build()
    
    def _on_account_selected(self, credential: TelegramCredential):
        """Handle account selection."""
        self.selected_credential = credential
        # Enable group selector when account is selected
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
                # No groups saved - empty list is fine
                self.group_selector.update_groups([])
        except Exception as e:
            logger.error(f"Error updating groups list: {e}")
            # Handle gracefully - empty list
            self.group_selector.update_groups([])
    
    async def _validate_account_group_access(self) -> Tuple[bool, Optional[str]]:
        """
        Validate that selected account can access selected group.
        
        Returns:
            (is_valid, error_message)
        """
        if not self.selected_credential:
            return False, theme_manager.t("select_account_first")
        
        group_id = self.group_selector.get_selected_group_id()
        if not group_id:
            # Try to get from manual entry
            if self.group_id_field.value:
                try:
                    group_id = int(self.group_id_field.value.strip())
                    # Validate group ID format (Telegram group IDs are negative integers)
                    if group_id > 0:
                        return False, theme_manager.t("invalid_group_id") + " (Group IDs are typically negative numbers)"
                except ValueError:
                    return False, theme_manager.t("invalid_group_id")
            else:
                return False, theme_manager.t("group_id_required")
        
        try:
            # Show loading state
            self.status_text.visible = True
            self.status_text.value = theme_manager.t("fetching_group_info")
            self.status_text.color = theme_manager.text_secondary_color
            if self.page:
                self.page.update()
            
            # Validate access using temporary client
            success, group, error, has_access = await self.telegram_service.fetch_and_validate_group(
                self.selected_credential,
                group_id
            )
            
            if not success:
                error_msg = error or theme_manager.t("group_not_found")
                phone = self.selected_credential.phone_number
                group_name = group.group_name if group else str(group_id) if group_id else "group"
                
                # Check for specific error types
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
            
            # Update group info in selector
            if group:
                self.group_selector.set_group_info(group.group_name, group.last_fetch_date)
            
            return True, None
            
        except ConnectionError as e:
            logger.error(f"Network error during validation: {e}")
            return False, theme_manager.t("connection_error")
        except Exception as e:
            logger.error(f"Error validating account group access: {e}")
            # Handle network errors
            error_msg = str(e)
            if "network" in error_msg.lower() or "connection" in error_msg.lower():
                return False, theme_manager.t("connection_error")
            # Handle timeout errors
            if "timeout" in error_msg.lower():
                return False, theme_manager.t("connection_error") + " (Timeout)"
            return False, error_msg
    
    def _close_dialog(self, e):
        """Close the dialog."""
        self.open = False
        if self.page:
            self.page.update()
    
    def _show_upgrade_dialog(self, error_message: str):
        """Show upgrade dialog when group limit is reached."""
        def contact_admin(e):
            self.open = False
            if self.page:
                self.page.update()
                # Navigate to about page (this requires access to app's navigation)
                # For now, just show contact info
                try:
                    from config.settings import settings
                    import webbrowser
                    from urllib.parse import quote
                    email_url = f"mailto:{settings.developer_email}?subject={quote('License Upgrade Request')}&body={quote('I would like to upgrade my subscription.')}"
                    webbrowser.open(email_url)
                except Exception as ex:
                    from config.settings import settings
                    theme_manager.show_snackbar(
                        self.page,
                        f"Please contact admin: {settings.developer_email}",
                        bgcolor=theme_manager.info_color
                    )
        
        # Create custom content
        content = ft.Column([
            ft.Text(error_message, size=14),
            ft.Container(height=10),
            ft.Text(
                theme_manager.t("contact_admin_to_upgrade"),
                size=12,
                color=theme_manager.text_secondary_color
            )
        ], tight=True, scroll=ft.ScrollMode.AUTO)
        
        # Create actions - close button will restore main dialog automatically
        actions = [
            ft.TextButton(theme_manager.t("close")),  # Will restore main dialog on click
            ft.ElevatedButton(
                theme_manager.t("contact_admin"),
                on_click=contact_admin,  # Will restore main dialog then call contact_admin
                bgcolor=theme_manager.primary_color,
                color=ft.Colors.WHITE
            )
        ]
        
        # Show custom dialog using centralized manager
        dialog_manager.show_custom_dialog(
            page=self.page,
            title=theme_manager.t("upgrade_required"),
            content=content,
            actions=actions,
            main_dialog=self  # This is nested, so restore main dialog
        )
    
    def _start_fetch(self, e):
        """Start fetching data from Telegram."""
        logger.info("=== START FETCH CLICKED ===")
        logger.info(f"Page reference available: {self.page is not None}")
        
        # Validate inputs
        is_valid, error_msg = self._validate_inputs()
        if not is_valid:
            logger.warning(f"Validation failed: {error_msg}")
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    error_msg,
                    bgcolor=ft.Colors.RED
                )
            return
        
        # Validate account and group access
        if self.page and hasattr(self.page, 'run_task'):
            self.page.run_task(self._validate_and_fetch)
        else:
            asyncio.create_task(self._validate_and_fetch())
    
    async def _validate_and_fetch(self):
        """Validate account/group access and start fetch."""
        # Validate account-group access
        is_valid, error_msg = await self._validate_account_group_access()
        if not is_valid:
            logger.warning(f"Account-group validation failed: {error_msg}")
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    error_msg,
                    bgcolor=ft.Colors.RED
                )
            return
        
        # Continue with fetch
        await self._proceed_with_fetch()
    
    async def _proceed_with_fetch(self):
        """Proceed with fetch after validation."""
        
        # Check license - can user add more groups?
        can_add, license_error = self.license_service.can_add_group()
        if not can_add:
            logger.warning(f"License check failed: {license_error}")
            if self.page:
                self._show_upgrade_dialog(license_error)
            return
        
        logger.info("Validation passed, starting fetch...")
        
        # Disable inputs during fetch
        self.account_selector.disable()
        self.group_selector.disable()
        self.start_date_field.disabled = True
        self.end_date_field.disabled = True
        
        # Show progress
        self.progress_bar.visible = True
        self.progress_text.visible = True
        self.status_text.visible = True
        self.status_text.value = theme_manager.t("fetching_messages")
        
        # Update UI
        if self.page:
            self.page.update()
        
        # Start async fetch using page's run_task if available
        if self.page and hasattr(self.page, 'run_task'):
            self.page.run_task(self._fetch_messages_async)
        else:
            # Fallback to creating task directly
            asyncio.create_task(self._fetch_messages_async())
    
    async def _fetch_messages_async(self):
        """Async method to fetch messages."""
        try:
            # Get group ID from selector or manual entry
            group_id = self.group_selector.get_selected_group_id()
            if not group_id:
                if self.group_id_field.value:
                    group_id = int(self.group_id_field.value.strip())
                else:
                    error_msg = theme_manager.t("group_id_required")
                    self.status_text.value = error_msg
                    self.status_text.color = ft.Colors.RED
                    self._re_enable_inputs()
                    if self.page:
                        theme_manager.show_snackbar(self.page, error_msg, bgcolor=ft.Colors.RED)
                        self.page.update()
                    return
            
            start_date = datetime.strptime(self.start_date_field.value.strip(), "%Y-%m-%d")
            end_date = datetime.strptime(self.end_date_field.value.strip(), "%Y-%m-%d")
            
            # Progress callback
            def on_progress(current: int, total: int):
                self.progress_text.value = f"{theme_manager.t('messages_fetched')}: {current}"
                if self.page:
                    try:
                        self.page.update()
                    except:
                        pass
            
            # Fetch messages using selected account or default
            if self.selected_credential:
                # Use selected account with temporary client
                success, message_count, error = await self.telegram_service.fetch_messages_with_account(
                    credential=self.selected_credential,
                    group_id=group_id,
                    start_date=start_date,
                    end_date=end_date,
                    progress_callback=on_progress
                )
            else:
                # Use default connected account
                success, message_count, error = await self.telegram_service.fetch_messages(
                    group_id=group_id,
                    start_date=start_date,
                    end_date=end_date,
                    progress_callback=on_progress
                )
            
            if success:
                self.status_text.value = f"{theme_manager.t('fetch_complete')}: {message_count} {theme_manager.t('messages')}"
                self.status_text.color = ft.Colors.GREEN
                
                if self.page:
                    theme_manager.show_snackbar(
                        self.page,
                        f"{theme_manager.t('successfully_fetched')} {message_count} {theme_manager.t('messages')}",
                        bgcolor=ft.Colors.GREEN
                    )
                    
                # Call completion callback
                if self.on_fetch_complete_callback:
                    self.on_fetch_complete_callback()
                
                # Close dialog after a delay
                await asyncio.sleep(2)
                self._close_dialog(None)
            else:
                self.status_text.value = f"{theme_manager.t('fetch_error')}: {error}"
                self.status_text.color = ft.Colors.RED
                
                if self.page:
                    theme_manager.show_snackbar(
                        self.page,
                        f"{theme_manager.t('fetch_error')}: {error}",
                        bgcolor=ft.Colors.RED
                    )
            
            # Re-enable inputs
            self._re_enable_inputs()
            
            if self.page:
                self.page.update()
            
        except Exception as ex:
            logger.error(f"Error in fetch dialog: {ex}")
            self.status_text.value = f"{theme_manager.t('fetch_error')}: {str(ex)}"
            self.status_text.color = ft.Colors.RED
            
            # Re-enable inputs
            self._re_enable_inputs()
            
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    f"{theme_manager.t('fetch_error')}: {str(ex)}",
                    bgcolor=ft.Colors.RED
                )
                self.page.update()
    
    def _re_enable_inputs(self):
        """Re-enable all input fields."""
        self.account_selector.enable()
        self.group_selector.enable()
        self.start_date_field.disabled = False
        self.end_date_field.disabled = False
        self.progress_bar.visible = False

