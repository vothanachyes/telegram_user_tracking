"""
Admin notifications management page.
"""

import flet as ft
import logging
from typing import Optional
from datetime import datetime
from admin.services.admin_notification_service import admin_notification_service
from admin.ui.components.data_table import DataTable
from admin.ui.dialogs.notification_form_dialog import NotificationFormDialog
from admin.ui.dialogs import DeleteConfirmDialog

logger = logging.getLogger(__name__)


class AdminNotificationsPage(ft.Container):
    """Admin notifications management page."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.data_table: Optional[DataTable] = None
        
        self.create_button = ft.ElevatedButton(
            text="Create Notification",
            icon=ft.Icons.ADD,
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
            on_click=self._on_create_notification,
        )
        
        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Notifications",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color=self.TEXT_COLOR,
                            ),
                            self.create_button,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=20, color="transparent"),
                ],
                spacing=10,
                expand=True,
            ),
            padding=ft.padding.all(20),
            bgcolor=self.BG_COLOR,
            expand=True,
        )
        
        self._load_notifications()
    
    def _load_notifications(self):
        """Load notifications and populate table."""
        try:
            notifications = admin_notification_service.get_all_notifications()
            
            columns = [
                {"key": "title", "label": "Title", "width": 200},
                {"key": "subtitle", "label": "Subtitle", "width": 150},
                {"key": "type", "label": "Type", "width": 100},
                {"key": "target", "label": "Target", "width": 150},
                {"key": "created_at", "label": "Created At", "width": 150},
            ]
            
            # Format data for table
            table_data = []
            for notification_data in notifications:
                target_users = notification_data.get("target_users")
                if target_users is None:
                    target = "All Users"
                else:
                    count = len(target_users) if isinstance(target_users, list) else 0
                    target = f"{count} User(s)"
                
                created_at = notification_data.get("created_at", "")
                if created_at:
                    try:
                        if isinstance(created_at, str):
                            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                            created_at = dt.strftime("%Y-%m-%d %H:%M")
                        elif hasattr(created_at, "strftime"):
                            created_at = created_at.strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        created_at = str(created_at)
                
                table_data.append({
                    "title": notification_data.get("title", ""),
                    "subtitle": notification_data.get("subtitle", "N/A"),
                    "type": notification_data.get("type", "info").capitalize(),
                    "target": target,
                    "created_at": created_at or "N/A",
                    "_notification_data": notification_data,  # Store full notification data
                })
            
            actions = [
                {
                    "label": "Edit",
                    "icon": ft.Icons.EDIT,
                    "on_click": self._on_edit_notification,
                },
                {
                    "label": "Delete",
                    "icon": ft.Icons.DELETE,
                    "on_click": self._on_delete_notification,
                },
            ]
            
            self.data_table = DataTable(
                columns=columns,
                data=table_data,
                actions=actions,
            )
            
            self.content.controls.append(self.data_table)
            # Only update if control is on the page
            if hasattr(self, 'page') and self.page:
                self.update()
            
        except Exception as e:
            logger.error(f"Error loading notifications: {e}", exc_info=True)
    
    def _on_create_notification(self, e: ft.ControlEvent):
        """Handle create notification button click."""
        dialog = NotificationFormDialog(
            notification_data=None,
            on_submit=self._handle_create_notification,
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening create notification dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_edit_notification(self, notification_data: dict):
        """Handle edit notification action."""
        full_notification_data = notification_data.get("_notification_data", notification_data)
        dialog = NotificationFormDialog(
            notification_data=full_notification_data,
            on_submit=lambda notification_data_param: self._handle_update_notification(
                full_notification_data.get("notification_id"), notification_data_param
            ),
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening edit notification dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_delete_notification(self, notification_data: dict):
        """Handle delete notification action."""
        full_notification_data = notification_data.get("_notification_data", notification_data)
        notification_id = full_notification_data.get("notification_id", "unknown")
        title = full_notification_data.get("title", "Unknown")
        
        dialog = DeleteConfirmDialog(
            title="Delete Notification",
            message=f"Are you sure you want to delete the notification '{title}'? This action cannot be undone.",
            item_name=title,
            on_confirm=lambda: self._handle_delete_notification(notification_id),
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening delete confirmation dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _handle_create_notification(self, notification_data: dict):
        """Handle notification creation."""
        try:
            success = admin_notification_service.create_notification(notification_data)
            
            if success:
                # Reload notifications
                self._reload_notifications()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Notification created successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to create notification. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error creating notification: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _handle_update_notification(self, notification_id: str, notification_data: dict):
        """Handle notification update."""
        try:
            success = admin_notification_service.update_notification(notification_id, notification_data)
            
            if success:
                # Reload notifications
                self._reload_notifications()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Notification updated successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to update notification. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error updating notification: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error updating notification: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _handle_delete_notification(self, notification_id: str):
        """Handle notification deletion."""
        try:
            success = admin_notification_service.delete_notification(notification_id)
            
            if success:
                # Reload notifications
                self._reload_notifications()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Notification deleted successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to delete notification. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error deleting notification: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error deleting notification: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _reload_notifications(self):
        """Reload notifications table."""
        # Remove old table
        if self.data_table and self.data_table in self.content.controls:
            self.content.controls.remove(self.data_table)
        
        # Load new data
        self._load_notifications()

