"""
User filter dialog for selecting users in notifications filter.
"""

import flet as ft
import logging
from typing import Optional, Callable, Set, List, Dict
from admin.services.admin_notification_service import admin_notification_service

logger = logging.getLogger(__name__)


class UserFilterDialog(ft.AlertDialog):
    """Dialog for selecting users to filter notifications."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    CARD_BG = "#252525"
    BORDER_COLOR = "#333333"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    
    def __init__(
        self,
        selected_user_ids: Set[str],
        on_confirm: Optional[Callable[[Set[str]], None]] = None,
        on_cancel: Optional[Callable] = None,
    ):
        """
        Initialize user filter dialog.
        
        Args:
            selected_user_ids: Currently selected user IDs
            on_confirm: Callback when confirmed (receives set of user IDs)
            on_cancel: Optional callback when cancelled
        """
        self.selected_user_ids = selected_user_ids.copy()
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.all_users: List[Dict] = []
        self.filtered_users: List[Dict] = []
        
        # Search field
        self.search_field = ft.TextField(
            hint_text="Search users...",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            on_change=self._on_search_changed,
            prefix_icon=ft.Icons.SEARCH,
            autofocus=True,
        )
        
        # User list container
        self.user_list_container = ft.Container(
            content=ft.Column(
                controls=[],
                spacing=5,
                scroll=ft.ScrollMode.AUTO,
            ),
            height=400,
            padding=ft.padding.all(10),
            bgcolor=self.CARD_BG,
            border=ft.border.all(1, self.BORDER_COLOR),
            border_radius=5,
        )
        
        # Select all / Clear all buttons
        self.select_all_button = ft.TextButton(
            text="Select All",
            icon=ft.Icons.CHECK_BOX,
            on_click=self._on_select_all,
        )
        
        self.clear_all_button = ft.TextButton(
            text="Clear All",
            icon=ft.Icons.CHECK_BOX_OUTLINE_BLANK,
            on_click=self._on_clear_all,
        )
        
        # Selected count display
        self.selected_count_text = ft.Text(
            "0 users selected",
            size=12,
            color=self.TEXT_SECONDARY,
        )
        
        # Dialog content
        dialog_content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self.search_field,
                    ],
                    spacing=10,
                ),
                ft.Divider(height=10, color="transparent"),
                ft.Row(
                    controls=[
                        self.select_all_button,
                        self.clear_all_button,
                        ft.Container(expand=True),
                        self.selected_count_text,
                    ],
                    spacing=10,
                ),
                self.user_list_container,
            ],
            spacing=5,
            width=500,
            height=500,
        )
        
        super().__init__(
            modal=True,
            title=ft.Text("Select Users", color=self.TEXT_COLOR),
            content=dialog_content,
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=self._on_cancel_click,
                ),
                ft.ElevatedButton(
                    "Apply",
                    bgcolor=self.PRIMARY_COLOR,
                    color=self.TEXT_COLOR,
                    on_click=self._on_confirm_click,
                ),
            ],
            bgcolor=self.BG_COLOR,
        )
        
        # Load users
        self._load_users()
    
    def _load_users(self):
        """Load users from service."""
        try:
            self.all_users = admin_notification_service.get_all_users()
            self.filtered_users = self.all_users.copy()
            self._update_user_list()
            self._update_selected_count()
        except Exception as e:
            logger.error(f"Error loading users: {e}", exc_info=True)
            self.all_users = []
            self.filtered_users = []
    
    def _on_search_changed(self, e: ft.ControlEvent):
        """Handle search field change."""
        query = e.control.value.lower().strip()
        
        if not query:
            self.filtered_users = self.all_users.copy()
        else:
            self.filtered_users = [
                user for user in self.all_users
                if query in user.get("email", "").lower()
                or query in (user.get("display_name", "") or "").lower()
            ]
        
        self._update_user_list()
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _update_user_list(self):
        """Update the user list display."""
        # Create checkboxes for filtered users
        checkboxes = []
        for user in self.filtered_users:
            uid = user.get("uid", "")
            email = user.get("email", "")
            display_name = user.get("display_name", "")
            label = f"{display_name} ({email})" if display_name else email
            
            checkbox = ft.Checkbox(
                label=label,
                value=uid in self.selected_user_ids,
                on_change=lambda e, u=uid: self._on_user_toggled(u, e.control.value),
            )
            checkboxes.append(checkbox)
        
        self.user_list_container.content.controls = checkboxes
        self._update_selected_count()
    
    def _on_user_toggled(self, user_id: str, is_selected: bool):
        """Handle user checkbox toggle."""
        if is_selected:
            self.selected_user_ids.add(user_id)
        else:
            self.selected_user_ids.discard(user_id)
        
        self._update_selected_count()
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _on_select_all(self, e: ft.ControlEvent):
        """Select all filtered users."""
        for user in self.filtered_users:
            uid = user.get("uid", "")
            if uid:
                self.selected_user_ids.add(uid)
        
        self._update_user_list()
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _on_clear_all(self, e: ft.ControlEvent):
        """Clear all selections."""
        # Remove only the filtered users from selection
        filtered_uids = {user.get("uid") for user in self.filtered_users if user.get("uid")}
        self.selected_user_ids -= filtered_uids
        
        self._update_user_list()
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _update_selected_count(self):
        """Update the selected count display."""
        count = len(self.selected_user_ids)
        if count == 0:
            self.selected_count_text.value = "0 users selected"
        elif count == 1:
            self.selected_count_text.value = "1 user selected"
        else:
            self.selected_count_text.value = f"{count} users selected"
    
    def _on_confirm_click(self, e: ft.ControlEvent):
        """Handle confirm button click."""
        # Close dialog
        if self.page:
            self.page.close(self)
        
        # Call confirm callback
        if self.on_confirm:
            self.on_confirm(self.selected_user_ids.copy())
    
    def _on_cancel_click(self, e: ft.ControlEvent):
        """Handle cancel button click."""
        # Close dialog
        if self.page:
            self.page.close(self)
        
        # Call cancel callback
        if self.on_cancel:
            self.on_cancel()

