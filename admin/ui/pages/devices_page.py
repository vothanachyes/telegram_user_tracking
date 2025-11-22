"""
Admin devices management page.
"""

import flet as ft
from typing import Optional
from admin.services.admin_device_service import admin_device_service
from admin.ui.components.data_table import DataTable


class AdminDevicesPage(ft.Container):
    """Admin devices management page."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    TEXT_COLOR = "#ffffff"
    PRIMARY_COLOR = "#0078d4"
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.data_table: Optional[DataTable] = None
        
        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Devices",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color=self.TEXT_COLOR,
                            ),
                        ],
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
        
        self._load_devices()
    
    def _load_devices(self):
        """Load devices and populate table."""
        try:
            devices = admin_device_service.get_all_devices()
            
            columns = [
                {"key": "user_email", "label": "User Email", "width": 200},
                {"key": "device_id", "label": "Device ID", "width": 300},
            ]
            
            table_data = [
                {
                    "user_email": d.get("user_email", ""),
                    "device_id": d.get("device_id", ""),
                    "_device_data": d,
                }
                for d in devices
            ]
            
            actions = [
                {
                    "label": "Remove",
                    "icon": ft.Icons.DELETE,
                    "on_click": self._on_remove_device,
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
            logger.error(f"Error loading devices: {e}", exc_info=True)
    
    def _on_remove_device(self, device_data: dict):
        """Handle remove device action."""
        # TODO: Open confirmation dialog
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Remove device: {device_data.get('device_id')} - to be implemented"),
            bgcolor="#333333",
        )
        self.page.snack_bar.open = True
        self.page.update()

