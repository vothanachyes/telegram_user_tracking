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
        
        # Template selection
        self.template_dropdown = ft.Dropdown(
            label="Template",
            hint_text="Select a template (optional)",
            options=self._get_template_options(),
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            on_change=self._on_template_changed,
        )
        
        self.load_template_button = ft.ElevatedButton(
            text="Load Template",
            icon=ft.Icons.UPLOAD_FILE,
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
            on_click=self._on_load_template_click,
            disabled=True,
        )
        
        # File picker for browsing HTML/MD files
        self.file_picker = ft.FilePicker(
            on_result=self._on_file_picked,
        )
        
        self.browse_file_button = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            tooltip="Browse for HTML/MD file",
            bgcolor=self.CARD_BG,
            icon_color=self.TEXT_COLOR,
            on_click=self._on_browse_file_click,
        )
        
        self.content_field = ft.TextField(
            label="Content",
            hint_text="HTML/Markdown content (or load from template)",
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
        
        # Template section with better grouping
        template_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.DESCRIPTION, color=self.PRIMARY_COLOR, size=18),
                            ft.Text(
                                "Template & Content",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=self.TEXT_COLOR,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Divider(height=12, color="transparent"),
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=self.template_dropdown,
                                expand=3,
                            ),
                            ft.Container(
                                content=self.load_template_button,
                                expand=1,
                            ),
                            ft.Container(
                                content=self.browse_file_button,
                                width=48,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Divider(height=15, color="transparent"),
                    self.content_field,
                ],
                spacing=0,
            ),
            padding=ft.padding.all(16),
            bgcolor=f"{self.CARD_BG}80",
            border_radius=8,
            border=ft.border.all(1, self.BORDER_COLOR),
        )
        
        # Build form content
        form_controls = [
            self.title_field,
            self.subtitle_field,
            ft.Divider(height=10, color="transparent"),
            template_section,
            ft.Divider(height=15, color="transparent"),
            self.image_url_field,
            self.type_dropdown,
            ft.Divider(height=15, color="transparent"),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.PEOPLE, color=self.PRIMARY_COLOR, size=18),
                                ft.Text(
                                    "Target Audience",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=self.TEXT_COLOR,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Divider(height=12, color="transparent"),
                        self.target_all_users,
                        self.user_selection,
                    ],
                    spacing=0,
                ),
                padding=ft.padding.all(16),
                bgcolor=f"{self.CARD_BG}80",
                border_radius=8,
                border=ft.border.all(1, self.BORDER_COLOR),
            ),
            ft.Divider(height=15, color="transparent"),
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
                    spacing=0,
                    width=700,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=ft.padding.all(20),
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
    
    def _get_template_options(self) -> List[ft.dropdown.Option]:
        """Get available template options."""
        try:
            from admin.utils.template_loader import template_loader
            templates = template_loader.get_available_templates()
            
            options = [ft.dropdown.Option(key="", text="None (Manual Entry)")]
            options.extend([
                ft.dropdown.Option(key=template, text=template)
                for template in templates
            ])
            return options
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"Error loading templates: {e}", exc_info=True)
            return [ft.dropdown.Option(key="", text="None (Manual Entry)")]
    
    def _on_template_changed(self, e: ft.ControlEvent):
        """Handle template selection change."""
        # Enable/disable load button based on selection
        self.load_template_button.disabled = not bool(self.template_dropdown.value)
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _on_load_template_click(self, e: ft.ControlEvent):
        """Handle load template button click."""
        template_filename = self.template_dropdown.value
        if not template_filename:
            self._show_error("Please select a template")
            return
        
        try:
            from admin.utils.template_loader import template_loader
            template_content = template_loader.load_template(template_filename)
            
            # Populate content field with template
            self.content_field.value = template_content
            
            # Show success message
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Template '{template_filename}' loaded successfully. You can edit it below."),
                    bgcolor="#4caf50",
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        except FileNotFoundError:
            self._show_error(f"Template file '{template_filename}' not found")
        except Exception as ex:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"Error loading template: {ex}", exc_info=True)
            self._show_error(f"Failed to load template: {str(ex)}")
    
    def _on_browse_file_click(self, e: ft.ControlEvent):
        """Handle browse file button click."""
        if not self.page:
            return
        
        # Ensure file picker is in overlay
        if not hasattr(self.page, 'overlay') or self.page.overlay is None:
            self.page.overlay = []
        
        if self.file_picker not in self.page.overlay:
            self.page.overlay.append(self.file_picker)
        
        # Set page reference
        self.file_picker.page = self.page
        self.page.update()
        
        # Open file picker dialog
        try:
            self.file_picker.pick_files(
                dialog_title="Select HTML or Markdown file",
                allowed_extensions=["html", "htm", "md", "markdown"],
                file_type=ft.FilePickerFileType.CUSTOM,
            )
        except Exception as ex:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"Error opening file picker: {ex}", exc_info=True)
            self._show_error(f"Failed to open file picker: {str(ex)}")
    
    def _on_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file picker result."""
        if not e.files or len(e.files) == 0:
            return
        
        try:
            file_path = e.files[0].path
            if not file_path:
                return
            
            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
            
            # Populate content field with file content
            self.content_field.value = file_content
            
            # Show success message
            if self.page:
                import os
                filename = os.path.basename(file_path)
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"File '{filename}' loaded successfully. You can edit it below."),
                    bgcolor="#4caf50",
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        except Exception as ex:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"Error loading file: {ex}", exc_info=True)
            if self.page:
                self._show_error(f"Failed to load file: {str(ex)}")
    
    def _show_error(self, message: str):
        """Show error message."""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()

