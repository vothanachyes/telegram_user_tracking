"""
Admin devices management page.
"""

import flet as ft
import logging
from typing import Optional
from admin.services.admin_device_service import admin_device_service
from admin.ui.components.data_table import DataTable
from admin.ui.dialogs import DeleteConfirmDialog

logger = logging.getLogger(__name__)


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
            # Only update if control is on the page
            if hasattr(self, 'page') and self.page:
                self.update()
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading devices: {e}", exc_info=True)
    
    def _on_remove_device(self, device_data: dict):
        """Handle remove device action."""
        full_device_data = device_data.get("_device_data", device_data)
        user_uid = full_device_data.get("user_uid", "unknown")
        device_id = full_device_data.get("device_id", "unknown")
        user_email = full_device_data.get("user_email", "unknown")
        
        dialog = DeleteConfirmDialog(
            title="Remove Device",
            message=f"Are you sure you want to remove device '{device_id}' from user '{user_email}'?",
            item_name=device_id,
            require_confirmation_text=False,  # Device removal is less critical
            on_confirm=lambda: self._handle_remove_device(user_uid, device_id),
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening remove device confirmation dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _handle_remove_device(self, user_uid: str, device_id: str):
        """Handle device removal."""
        try:
            success = admin_device_service.remove_device(user_uid, device_id)
            
            if success:
                # Reload devices
                self._reload_devices()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Device removed successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to remove device. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error removing device: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error removing device: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _reload_devices(self):
        """Reload devices table."""
        # Remove old table
        if self.data_table and self.data_table in self.content.controls:
            self.content.controls.remove(self.data_table)
        
        # Load new data
        self._load_devices()

