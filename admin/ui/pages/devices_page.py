"""
Admin devices management page with grouped tree view.
"""

import flet as ft
import logging
from typing import Optional, Dict, List
from collections import defaultdict
from admin.services.admin_device_service import admin_device_service
from admin.ui.dialogs import DeleteConfirmDialog

logger = logging.getLogger(__name__)


class AdminDevicesPage(ft.Container):
    """Admin devices management page with grouped tree view."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    SUCCESS_COLOR = "#4caf50"
    ERROR_COLOR = "#f44336"
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.devices_container_ref = ft.Ref[ft.Container]()
        self.expanded_users: Dict[str, bool] = {}  # Track which users are expanded
        
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
                            ft.Container(expand=True),
                            ft.ElevatedButton(
                                "Refresh",
                                icon=ft.Icons.REFRESH,
                                on_click=self._on_refresh,
                            ),
                        ],
                    ),
                    ft.Divider(height=20, color="transparent"),
                    ft.Container(
                        content=ft.Column(
                            controls=[],
                            spacing=0,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        expand=True,
                        ref=self.devices_container_ref,
                    ),
                ],
                spacing=10,
                expand=True,
            ),
            padding=ft.padding.all(20),
            bgcolor=self.BG_COLOR,
            expand=True,
        )
        
        self._load_devices()
    
    def _on_refresh(self, e):
        """Handle refresh button click."""
        self._load_devices()
    
    def _load_devices(self):
        """Load devices and create grouped tree view."""
        if not self.devices_container_ref.current:
            return
        
        devices_container = self.devices_container_ref.current
        if not devices_container.content:
            return
        
        devices_column = devices_container.content
        
        try:
            # Clear existing content
            devices_column.controls.clear()
            
            # Get all devices
            all_devices = admin_device_service.get_all_devices()
            
            # Filter out revoked devices
            active_devices = [
                d for d in all_devices 
                if not d.get("revoked_at") and d.get("is_active", True)
            ]
            
            if not active_devices:
                # Show empty state
                devices_column.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.DEVICES, size=64, color=self.TEXT_SECONDARY),
                                ft.Text(
                                    "No active devices found",
                                    size=16,
                                    color=self.TEXT_SECONDARY,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        alignment=ft.alignment.center,
                        padding=40,
                    )
                )
                if self.page:
                    self.page.update()
                return
            
            # Group devices by user_email
            devices_by_user = defaultdict(list)
            for device in active_devices:
                user_email = device.get("user_email", "Unknown")
                devices_by_user[user_email].append(device)
            
            # Create tree view for each user
            for user_email, devices in sorted(devices_by_user.items()):
                user_group = self._create_user_group(user_email, devices)
                devices_column.controls.append(user_group)
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            logger.error(f"Error loading devices: {e}", exc_info=True)
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error loading devices: {str(e)}"),
                    bgcolor=self.ERROR_COLOR,
                )
                self.page.snack_bar.open = True
                self.page.update()
    
    def _create_user_group(self, user_email: str, devices: List[dict]) -> ft.Container:
        """Create a collapsible user group with devices."""
        is_expanded = self.expanded_users.get(user_email, True)  # Default to expanded
        
        # Create expand/collapse icon
        expand_icon = ft.Icons.EXPAND_MORE if is_expanded else ft.Icons.CHEVRON_RIGHT
        
        # Create header row
        header_row = ft.Row(
            controls=[
                ft.Icon(expand_icon, size=20, color=self.PRIMARY_COLOR),
                ft.Text(
                    user_email,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=self.TEXT_COLOR,
                ),
                ft.Container(expand=True),
                ft.Text(
                    f"{len(devices)} device(s)",
                    size=12,
                    color=self.TEXT_SECONDARY,
                ),
            ],
            spacing=10,
        )
        
        # Create devices list (visible if expanded)
        devices_list = ft.Column(
            controls=[
                self._create_device_row(device) for device in devices
            ],
            spacing=5,
            visible=is_expanded,
        )
        
        # Create group container
        group_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=header_row,
                        on_click=lambda e, email=user_email: self._toggle_user_group(email),
                        padding=ft.padding.symmetric(horizontal=10, vertical=8),
                        bgcolor="#2a2a2a",
                        border_radius=5,
                    ),
                    ft.Container(
                        content=devices_list,
                        padding=ft.padding.only(left=30, top=5, bottom=5),
                    ),
                ],
                spacing=0,
            ),
            margin=ft.margin.only(bottom=10),
        )
        
        return group_container
    
    def _create_device_row(self, device: dict) -> ft.Container:
        """Create a device row with details."""
        device_name = device.get("device_name", "Unknown Device")
        platform = device.get("platform", "Unknown")
        device_id = device.get("device_id", "")
        last_login = device.get("last_login", "")
        user_uid = device.get("user_uid", "")
        
        # Format last login
        last_login_str = self._format_last_login(last_login)
        
        # Create device row
        device_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PHONE_ANDROID, size=20, color=self.TEXT_SECONDARY),
                    ft.Column(
                        controls=[
                            ft.Text(
                                device_name,
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=self.TEXT_COLOR,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text(f"Platform: {platform}", size=12, color=self.TEXT_SECONDARY),
                                    ft.Text(" • ", size=12, color=self.TEXT_SECONDARY),
                                    ft.Text(f"Last Login: {last_login_str}", size=12, color=self.TEXT_SECONDARY),
                                    ft.Text(" • ", size=12, color=self.TEXT_SECONDARY),
                                    ft.Text(f"ID: {device_id[:12]}...", size=12, color=self.TEXT_SECONDARY),
                                ],
                                spacing=5,
                            ),
                        ],
                        spacing=5,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=self.ERROR_COLOR,
                        tooltip="Remove Device",
                        on_click=lambda e, d=device: self._on_remove_device(d),
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            bgcolor="#252525",
            border_radius=5,
            margin=ft.margin.only(bottom=5),
        )
        
        return device_row
    
    def _format_last_login(self, last_login) -> str:
        """Format last login timestamp."""
        if not last_login:
            return "Never"
        try:
            if isinstance(last_login, str):
                from datetime import datetime
                dt = datetime.fromisoformat(last_login.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            return str(last_login)
        except Exception:
            return str(last_login)
    
    def _toggle_user_group(self, user_email: str):
        """Toggle expand/collapse of user group."""
        self.expanded_users[user_email] = not self.expanded_users.get(user_email, True)
        self._load_devices()  # Reload to update UI
    
    def _on_remove_device(self, device: dict):
        """Handle remove device action."""
        user_uid = device.get("user_uid", "unknown")
        device_id = device.get("device_id", "unknown")
        user_email = device.get("user_email", "unknown")
        device_name = device.get("device_name", "Unknown Device")
        
        dialog = DeleteConfirmDialog(
            title="Remove Device",
            message=f"Are you sure you want to remove device '{device_name}' from user '{user_email}'? This will revoke the device.",
            item_name=device_id,
            require_confirmation_text=False,
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
                # Reload devices (revoked device will be hidden)
                self._load_devices()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Device removed successfully"),
                    bgcolor=self.SUCCESS_COLOR,
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to remove device. Please check logs."),
                    bgcolor=self.ERROR_COLOR,
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error removing device: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error removing device: {str(e)}"),
                bgcolor=self.ERROR_COLOR,
            )
            self.page.snack_bar.open = True
            self.page.update()
