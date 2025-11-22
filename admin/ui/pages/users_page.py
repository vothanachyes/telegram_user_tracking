"""
Admin users management page.
"""

import flet as ft
import logging
from typing import Optional
from admin.services.admin_user_service import admin_user_service
from admin.ui.components.data_table import DataTable
from admin.ui.dialogs import UserFormDialog, DeleteConfirmDialog

logger = logging.getLogger(__name__)


class AdminUsersPage(ft.Container):
    """Admin users management page."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.data_table: Optional[DataTable] = None
        
        self.create_button = ft.ElevatedButton(
            text="Create User",
            icon=ft.Icons.ADD,
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
            on_click=self._on_create_user,
        )
        
        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Users",
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
        
        self._load_users()
    
    def _load_users(self):
        """Load users and populate table."""
        try:
            users = admin_user_service.get_all_users()
            
            columns = [
                {"key": "email", "label": "Email", "width": 200},
                {"key": "display_name", "label": "Display Name", "width": 150},
                {"key": "uid", "label": "UID", "width": 200},
                {"key": "disabled", "label": "Status", "width": 100},
                {"key": "license_tier", "label": "License Tier", "width": 120},
            ]
            
            # Format data for table
            table_data = []
            for user in users:
                table_data.append({
                    "email": user.get("email", ""),
                    "display_name": user.get("display_name", "N/A"),
                    "uid": user.get("uid", ""),
                    "disabled": "Disabled" if user.get("disabled") else "Active",
                    "license_tier": user.get("license_tier", "none").capitalize(),
                    "_user_data": user,  # Store full user data
                })
            
            actions = [
                {
                    "label": "Edit",
                    "icon": ft.Icons.EDIT,
                    "on_click": self._on_edit_user,
                },
                {
                    "label": "Delete",
                    "icon": ft.Icons.DELETE,
                    "on_click": self._on_delete_user,
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
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading users: {e}", exc_info=True)
    
    def _on_create_user(self, e: ft.ControlEvent):
        """Handle create user button click."""
        dialog = UserFormDialog(
            user_data=None,
            on_submit=self._handle_create_user,
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening create user dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_edit_user(self, user_data: dict):
        """Handle edit user action."""
        # Get full user data
        full_user_data = user_data.get("_user_data", user_data)
        dialog = UserFormDialog(
            user_data=full_user_data,
            on_submit=lambda **kwargs: self._handle_update_user(full_user_data.get("uid"), **kwargs),
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening edit user dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_delete_user(self, user_data: dict):
        """Handle delete user action."""
        full_user_data = user_data.get("_user_data", user_data)
        user_email = full_user_data.get("email", "this user")
        user_uid = full_user_data.get("uid")
        
        dialog = DeleteConfirmDialog(
            title="Delete User",
            message=f"Are you sure you want to delete user '{user_email}'? This action cannot be undone.",
            item_name=user_email,
            on_confirm=lambda: self._handle_delete_user(user_uid),
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening delete confirmation dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _handle_create_user(self, email: str, password: str, display_name: Optional[str], disabled: bool):
        """Handle user creation."""
        try:
            uid = admin_user_service.create_user(
                email=email,
                password=password,
                display_name=display_name,
            )
            
            if uid:
                # Update disabled status if needed
                if disabled:
                    admin_user_service.update_user(uid, disabled=True)
                
                # Reload users
                self._reload_users()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"User created successfully: {email}"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to create user. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error creating user: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error creating user: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _handle_update_user(self, uid: str, email: str, password: Optional[str], display_name: Optional[str], disabled: bool):
        """Handle user update."""
        try:
            update_data = {
                "email": email,
                "display_name": display_name,
                "disabled": disabled,
            }
            
            # Only update password if provided
            if password:
                update_data["password"] = password
            
            success = admin_user_service.update_user(uid, **update_data)
            
            if success:
                # Reload users
                self._reload_users()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("User updated successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to update user. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error updating user: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error updating user: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _handle_delete_user(self, uid: str):
        """Handle user deletion."""
        try:
            success = admin_user_service.delete_user(uid)
            
            if success:
                # Reload users
                self._reload_users()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("User deleted successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to delete user. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error deleting user: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error deleting user: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _reload_users(self):
        """Reload users table."""
        # Remove old table
        if self.data_table and self.data_table in self.content.controls:
            self.content.controls.remove(self.data_table)
        
        # Load new data
        self._load_users()

