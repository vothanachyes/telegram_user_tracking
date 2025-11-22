"""
Notification form dialog for creating and editing notifications.
"""

import flet as ft
from typing import Optional, Callable, Dict, List
from datetime import datetime


class NotificationFormDialog(ft.AlertDialog):
    """Dialog for creating or editing a notification."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    CARD_BG = "#252525"
    BORDER_COLOR = "#333333"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    
    def __init__(
        self,
        notification_data: Optional[Dict] = None,
        on_submit: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
    ):
        """
        Initialize notification form dialog.
        
        Args:
            notification_data: Existing notification data for editing (None for create)
            on_submit: Callback with notification data dict
            on_cancel: Optional callback when cancelled
        """
        self.is_edit = notification_data is not None
        self.notification_data = notification_data
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        
        # Form fields
        self.title_field = ft.TextField(
            label="Title",
            hint_text="Notification title",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            autofocus=True,
        )
        
        self.subtitle_field = ft.TextField(
            label="Subtitle",
            hint_text="Optional subtitle",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.content_field = ft.TextField(
            label="Content",
            hint_text="HTML/Markdown content",
            multiline=True,
            min_lines=5,
            max_lines=10,
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.image_url_field = ft.TextField(
            label="Image URL",
            hint_text="Optional image URL",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        # Type dropdown
        self.type_dropdown = ft.Dropdown(
            label="Type",
            options=[
                ft.dropdown.Option(key="info", text="Info"),
                ft.dropdown.Option(key="warning", text="Warning"),
                ft.dropdown.Option(key="announcement", text="Announcement"),
                ft.dropdown.Option(key="update", text="Update"),
            ],
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        # Target users - multi-select with "All Users" option
        self.target_all_users = ft.Checkbox(
            label="All Users",
            value=True,
            on_change=self._on_target_all_changed,
        )
        
        # User selection (will be populated from service)
        self.user_selection = ft.Column(
            controls=[],
            spacing=5,
            visible=False,
        )
        
        self.selected_user_ids = set()
        
        # Expiration date field
        self.expires_at_field = ft.TextField(
            label="Expires At",
            hint_text="YYYY-MM-DD or ISO format (optional)",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        # Set initial values if editing
        if self.is_edit:
            self.title_field.value = notification_data.get("title", "")
            self.subtitle_field.value = notification_data.get("subtitle", "")
            self.content_field.value = notification_data.get("content", "")
            self.image_url_field.value = notification_data.get("image_url", "")
            self.type_dropdown.value = notification_data.get("type", "info")
            
            target_users = notification_data.get("target_users")
            if target_users is None:
                self.target_all_users.value = True
            else:
                self.target_all_users.value = False
                self.selected_user_ids = set(target_users)
                self.user_selection.visible = True
            
            expires_at = notification_data.get("expires_at")
            if expires_at:
                try:
                    if isinstance(expires_at, str):
                        dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                        self.expires_at_field.value = dt.strftime("%Y-%m-%d")
                    else:
                        self.expires_at_field.value = str(expires_at)
                except Exception:
                    self.expires_at_field.value = str(expires_at)
        else:
            # Default values for create
            self.type_dropdown.value = "info"
            self.target_all_users.value = True
        
        # Load users for selection
        self._load_users()
        
        # Buttons
        cancel_button = ft.TextButton(
            text="Cancel",
            on_click=self._on_cancel_click,
        )
        
        submit_button = ft.ElevatedButton(
            text="Save" if self.is_edit else "Create",
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
            on_click=self._on_submit_click,
        )
        
        # Build form content
        form_controls = [
            self.title_field,
            self.subtitle_field,
            self.content_field,
            self.image_url_field,
            self.type_dropdown,
            self.target_all_users,
            self.user_selection,
            self.expires_at_field,
        ]
        
        super().__init__(
            title=ft.Text(
                "Edit Notification" if self.is_edit else "Create Notification",
                color=self.TEXT_COLOR,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=form_controls,
                    spacing=15,
                    width=600,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=ft.padding.all(10),
            ),
            actions=[
                cancel_button,
                submit_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True,
            bgcolor=self.BG_COLOR,
        )
    
    def _on_target_all_changed(self, e: ft.ControlEvent):
        """Handle target all users checkbox change."""
        self.user_selection.visible = not self.target_all_users.value
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _load_users(self):
        """Load users for selection."""
        try:
            from admin.services.admin_notification_service import admin_notification_service
            users = admin_notification_service.get_all_users()
            
            # Create checkboxes for each user
            user_controls = []
            for user in users:
                uid = user.get("uid")
                email = user.get("email", "")
                display_name = user.get("display_name", "")
                label = f"{display_name} ({email})" if display_name else email
                
                checkbox = ft.Checkbox(
                    label=label,
                    value=uid in self.selected_user_ids,
                    on_change=lambda e, u=uid: self._on_user_selection_changed(u, e.control.value),
                )
                user_controls.append(checkbox)
            
            self.user_selection.controls = user_controls
            
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"Error loading users: {e}", exc_info=True)
    
    def _on_user_selection_changed(self, user_id: str, is_selected: bool):
        """Handle user selection change."""
        if is_selected:
            self.selected_user_ids.add(user_id)
        else:
            self.selected_user_ids.discard(user_id)
    
    def _on_submit_click(self, e: ft.ControlEvent):
        """Handle submit button click."""
        # Validate
        title = self.title_field.value.strip()
        if not title:
            self._show_error("Title is required")
            return
        
        content = self.content_field.value.strip()
        if not content:
            self._show_error("Content is required")
            return
        
        notification_type = self.type_dropdown.value
        if not notification_type:
            self._show_error("Type is required")
            return
        
        # Build notification data
        notification_data = {
            "title": title,
            "content": content,
            "type": notification_type,
        }
        
        # Optional fields
        subtitle = self.subtitle_field.value.strip()
        if subtitle:
            notification_data["subtitle"] = subtitle
        
        image_url = self.image_url_field.value.strip()
        if image_url:
            notification_data["image_url"] = image_url
        
        # Target users
        if self.target_all_users.value:
            notification_data["target_users"] = None
        else:
            notification_data["target_users"] = list(self.selected_user_ids)
            if not notification_data["target_users"]:
                self._show_error("Please select at least one user or select 'All Users'")
                return
        
        # Expiration date
        expires_at_str = self.expires_at_field.value.strip()
        if expires_at_str:
            try:
                dt = datetime.strptime(expires_at_str, "%Y-%m-%d")
                notification_data["expires_at"] = dt.isoformat() + "Z"
            except ValueError:
                try:
                    dt = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                    notification_data["expires_at"] = dt.isoformat() + "Z"
                except Exception:
                    self._show_error("Invalid expiration date format. Use YYYY-MM-DD")
                    return
        
        # Close dialog
        if self.page:
            self.page.close(self)
        
        # Call submit callback
        if self.on_submit:
            self.on_submit(notification_data=notification_data)
    
    def _on_cancel_click(self, e: ft.ControlEvent):
        """Handle cancel button click."""
        # Close dialog
        if self.page:
            self.page.close(self)
        
        # Call cancel callback
        if self.on_cancel:
            self.on_cancel()
    
    def _show_error(self, message: str):
        """Show error message."""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()

