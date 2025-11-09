"""
Add Group dialog for adding new Telegram groups.
"""

import flet as ft
import asyncio
import logging
from typing import Optional, Callable
from database.db_manager import DatabaseManager
from database.models import TelegramCredential, TelegramGroup
from services.telegram import TelegramService
from services.license_service import LicenseService
from ui.components.account_selector import AccountSelector
from ui.theme import theme_manager
from utils.group_parser import parse_group_input

logger = logging.getLogger(__name__)


class AddGroupDialog(ft.AlertDialog):
    """Dialog for adding new Telegram groups."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        telegram_service: TelegramService,
        on_group_added: Optional[Callable[[], None]] = None
    ):
        self.db_manager = db_manager
        self.telegram_service = telegram_service
        self.license_service = LicenseService(db_manager)
        self.on_group_added = on_group_added
        self.page: Optional[ft.Page] = None
        self.selected_credential: Optional[TelegramCredential] = None
        self.preview_group: Optional[TelegramGroup] = None
        
        # Group input field
        self.group_input = ft.TextField(
            label="Group Link, ID, or Username",
            hint_text="e.g., https://t.me/groupname, https://t.me/+..., -1001234567890, or @groupname",
            border_radius=theme_manager.corner_radius,
            expand=True
        )
        
        # Preview button
        self.preview_button = ft.ElevatedButton(
            "Preview",
            icon=ft.Icons.SEARCH,
            on_click=self._on_preview_click,
            disabled=True
        )
        
        # Account selector
        self.account_selector = AccountSelector(
            on_account_selected=self._on_account_selected,
            on_refresh=self._refresh_accounts
        )
        
        # License warning
        self.license_warning = ft.Container(
            visible=False,
            content=ft.Row([
                ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE, size=20),
                ft.Text("", size=12, color=ft.Colors.ORANGE, expand=True)
            ], spacing=10)
        )
        
        # Preview section
        self.preview_container = ft.Container(visible=False)
        
        # Error info
        self.error_info = ft.Container(
            visible=False,
            content=ft.Row([
                ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED, size=20),
                ft.Text("", size=12, color=ft.Colors.RED, expand=True)
            ], spacing=10)
        )
        
        # Loading indicator
        self.loading_indicator = ft.ProgressRing(visible=False)
        
        super().__init__(
            modal=True,
            title=ft.Text(theme_manager.t("add_group") or "Add Group"),
            content=self._build_content(),
            actions=[
                ft.TextButton(
                    theme_manager.t("cancel"),
                    on_click=self._close_dialog
                ),
                ft.ElevatedButton(
                    theme_manager.t("add_group") or "Add",
                    on_click=self._on_add_click,
                    icon=ft.Icons.ADD,
                    bgcolor=theme_manager.primary_color,
                    color=ft.Colors.WHITE,
                    disabled=True
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def set_page(self, page: ft.Page):
        """Set page reference."""
        self.page = page
        if self.account_selector:
            self.account_selector.set_page(page)
        if page:
            try:
                page.run_task(self._initialize_accounts)
            except Exception as ex:
                logger.error(f"Error running initialize accounts task: {ex}", exc_info=True)
        else:
            logger.warning("Page not available, cannot initialize accounts")
    
    async def _initialize_accounts(self):
        """Initialize account list."""
        try:
            accounts_with_status = await self.telegram_service.get_all_accounts_with_status()
            if accounts_with_status:
                self.account_selector.update_accounts(accounts_with_status)
                logger.debug(f"Initialized {len(accounts_with_status)} accounts in add group dialog")
            else:
                self.account_selector.update_accounts([])
                logger.warning("No accounts found for add group dialog")
            # Update the page to show the dropdown options
            if self.page:
                self.page.update()
        except Exception as e:
            logger.error(f"Error initializing accounts: {e}", exc_info=True)
            self.account_selector.update_accounts([])
            if self.page:
                self.page.update()
    
    async def _refresh_accounts(self):
        """Refresh account list."""
        await self._initialize_accounts()
    
    def _on_account_selected(self, credential: TelegramCredential):
        """Handle account selection."""
        self.selected_credential = credential
        self._update_license_warning()
        # Enable preview button if we have input
        self.preview_button.disabled = not (self.group_input.value.strip() and self.selected_credential)
        self._check_input()
        if self.page:
            self.page.update()
    
    def _on_input_change(self, e):
        """Handle input change."""
        self._hide_preview()
        self._hide_error()
        # Enable preview button if we have input and account
        self.preview_button.disabled = not (self.group_input.value.strip() and self.selected_credential)
        self._check_input()
        if self.page:
            self.page.update()
    
    def _on_preview_click(self, e):
        """Handle preview button click."""
        if self.page:
            try:
                self.page.run_task(self._fetch_preview)
            except Exception as ex:
                logger.error(f"Error running fetch preview task: {ex}", exc_info=True)
        else:
            logger.warning("Page not available, cannot fetch preview")
    
    def _check_input(self):
        """Check if input is valid and enable/disable add button."""
        input_text = self.group_input.value.strip() if self.group_input.value else ""
        has_account = self.selected_credential is not None
        has_preview = self.preview_group is not None
        
        # Enable add button if we have account, input, and preview
        add_button = self.actions[1] if len(self.actions) > 1 else None
        if add_button:
            add_button.disabled = not (has_account and input_text and has_preview)
    
    def _update_license_warning(self):
        """Update license warning display."""
        try:
            license_info = self.license_service.get_license_info()
            current = license_info.get('current_groups', 0)
            max_groups = license_info.get('max_groups', 0)
            
            if max_groups == -1:  # Unlimited
                self.license_warning.visible = False
            else:
                warning_text = theme_manager.t("license_group_limit_warning") or f"You have {current}/{max_groups} groups. Your license allows up to {max_groups} groups."
                self.license_warning.content.controls[1].value = warning_text.format(current=current, max=max_groups)
                self.license_warning.visible = True
        except Exception as e:
            logger.error(f"Error updating license warning: {e}")
            self.license_warning.visible = False
    
    def _build_content(self) -> ft.Container:
        """Build dialog content."""
        self.group_input.on_change = self._on_input_change
        
        return ft.Container(
            content=ft.Column([
                self.group_input,
                ft.Row([self.preview_button], alignment=ft.MainAxisAlignment.END),
                ft.Container(height=10),
                self.account_selector.build(),
                ft.Container(height=10),
                self.license_warning,
                ft.Container(height=10),
                self.loading_indicator,
                self.error_info,
                self.preview_container,
            ], spacing=5, width=500, height=400, scroll=ft.ScrollMode.AUTO),
            padding=10
        )
    
    def _hide_preview(self):
        """Hide preview section."""
        self.preview_container.visible = False
        self.preview_group = None
    
    def _hide_error(self):
        """Hide error info."""
        self.error_info.visible = False
    
    def _show_error(self, message: str):
        """Show error message."""
        self.error_info.content.controls[1].value = message
        self.error_info.visible = True
        self._hide_preview()
    
    async def _fetch_preview(self):
        """Fetch group preview."""
        if not self.selected_credential:
            return
        
        input_text = self.group_input.value.strip() if self.group_input.value else ""
        if not input_text:
            return
        
        # Parse input
        group_id, username, invite_link, error = parse_group_input(input_text)
        if error:
            self._show_error(error)
            if self.page:
                self.page.update()
            return
        
        # Show loading
        self.loading_indicator.visible = True
        self._hide_error()
        self._hide_preview()
        if self.page:
            self.page.update()
        
        try:
            # Fetch group info
            if group_id:
                success, group, error_msg, has_access = await self.telegram_service.fetch_and_validate_group(
                    self.selected_credential,
                    group_id=group_id
                )
            elif invite_link:
                # Handle invite links - Telethon can resolve them directly
                success, group, error_msg, has_access = await self.telegram_service.fetch_and_validate_group(
                    self.selected_credential,
                    invite_link=invite_link
                )
            elif username:
                # Resolve username using Telethon - it can handle usernames directly
                success, group, error_msg, has_access = await self.telegram_service.fetch_and_validate_group(
                    self.selected_credential,
                    username=username
                )
            else:
                self._show_error("Could not parse input")
                if self.page:
                    self.page.update()
                return
            
            self.loading_indicator.visible = False
            
            if not success:
                if error_msg == "permission_denied":
                    self._show_error("Permission denied. This account does not have access to this group.")
                elif error_msg == "not_member":
                    self._show_error("Account is not a member of this group.")
                else:
                    self._show_error(error_msg or "Failed to fetch group information")
                if self.page:
                    self.page.update()
                return
            
            if group:
                self.preview_group = group
                self._show_preview(group)
                self._check_input()
                if self.page:
                    self.page.update()
        
        except Exception as e:
            logger.error(f"Error fetching group preview: {e}")
            self.loading_indicator.visible = False
            self._show_error(f"Error: {str(e)}")
            if self.page:
                self.page.update()
    
    def _show_preview(self, group: TelegramGroup):
        """Show group preview."""
        # Group photo or icon
        photo_content = ft.Icon(ft.Icons.GROUP, size=48, color=theme_manager.primary_color)
        if group.group_photo_path:
            try:
                photo_content = ft.Image(
                    src=group.group_photo_path,
                    width=48,
                    height=48,
                    fit=ft.ImageFit.COVER,
                    border_radius=theme_manager.corner_radius
                )
            except:
                pass
        
        # Copy button for group ID
        copy_button = ft.IconButton(
            icon=ft.Icons.COPY,
            icon_size=16,
            tooltip="Copy Group ID",
            on_click=lambda e: self._copy_group_id(group.group_id),
            data=group.group_id
        )
        
        self.preview_container.content = ft.Column([
            ft.Text("Preview:", size=14, weight=ft.FontWeight.BOLD),
            ft.Row([
                photo_content,
                ft.Column([
                    ft.Text(group.group_name, size=16, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Text(f"ID: {group.group_id}", size=12, color=theme_manager.text_secondary_color),
                        copy_button
                    ], spacing=5, tight=True),
                    ft.Text(f"Username: {group.group_username or 'N/A'}", size=12, color=theme_manager.text_secondary_color),
                ], spacing=5, expand=True)
            ], spacing=10)
        ], spacing=10)
        self.preview_container.visible = True
    
    def _copy_group_id(self, group_id: str):
        """Copy group ID to clipboard."""
        if self.page:
            try:
                self.page.set_clipboard(str(group_id))
                theme_manager.show_snackbar(
                    self.page,
                    f"Group ID copied: {group_id}",
                    bgcolor=ft.Colors.GREEN
                )
            except Exception as e:
                logger.error(f"Error copying group ID to clipboard: {e}")
                theme_manager.show_snackbar(
                    self.page,
                    "Failed to copy group ID",
                    bgcolor=ft.Colors.RED
                )
    
    def _close_dialog(self, e):
        """Close dialog."""
        if self.page:
            self.page.close(self)
    
    async def _on_add_click(self, e):
        """Handle add button click."""
        if not self.preview_group or not self.selected_credential:
            return
        
        try:
            # Check license limits
            can_add, error_msg = self.license_service.enforcer.can_add_group()
            if not can_add:
                if self.page:
                    theme_manager.show_snackbar(
                        self.page,
                        error_msg or "Cannot add group",
                        bgcolor=ft.Colors.RED
                    )
                return
            
            # Save group
            self.db_manager.save_group(self.preview_group)
            
            # Callback
            if self.on_group_added:
                self.on_group_added()
            
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("group_added_successfully") or "Group added successfully",
                    bgcolor=ft.Colors.GREEN
                )
                self.page.close(self)
        
        except Exception as ex:
            logger.error(f"Error adding group: {ex}")
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    f"Error adding group: {ex}",
                    bgcolor=ft.Colors.RED
                )

