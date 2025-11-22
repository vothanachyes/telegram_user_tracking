"""
Admin users management page.
"""

import flet as ft
from typing import Optional
from admin.services.admin_user_service import admin_user_service
from admin.ui.components.data_table import DataTable


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
            self.update()
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading users: {e}", exc_info=True)
    
    def _on_create_user(self, e: ft.ControlEvent):
        """Handle create user button click."""
        # TODO: Open create user dialog
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Create user dialog - to be implemented"),
            bgcolor="#333333",
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _on_edit_user(self, user_data: dict):
        """Handle edit user action."""
        # TODO: Open edit user dialog
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Edit user: {user_data.get('email')} - to be implemented"),
            bgcolor="#333333",
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _on_delete_user(self, user_data: dict):
        """Handle delete user action."""
        # TODO: Open delete confirmation dialog
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Delete user: {user_data.get('email')} - to be implemented"),
            bgcolor="#333333",
        )
        self.page.snack_bar.open = True
        self.page.update()

