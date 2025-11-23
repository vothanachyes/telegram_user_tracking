"""
Devices management tab component.
Shows all user's devices and allows revocation.
"""

import flet as ft
import logging
from typing import Optional
from datetime import datetime

from ui.theme import theme_manager
from services.device_manager_service import device_manager_service
from services.auth_service import auth_service
from ui.dialogs.revoke_device_dialog import RevokeDeviceDialog

logger = logging.getLogger(__name__)


class DevicesTab:
    """Devices management tab component."""
    
    def __init__(self):
        self._page: Optional[ft.Page] = None
        self.devices_list: Optional[ft.Column] = None
        self.refresh_button: Optional[ft.ElevatedButton] = None
        self.loading_indicator: Optional[ft.ProgressRing] = None
        self.empty_state: Optional[ft.Container] = None
    
    @property
    def page(self) -> Optional[ft.Page]:
        """Get page reference."""
        return self._page
    
    @page.setter
    def page(self, value: Optional[ft.Page]):
        """Set page reference."""
        self._page = value
    
    def build(self) -> ft.Container:
        """Build the devices tab."""
        self.loading_indicator = ft.ProgressRing(visible=False)
        
        self.refresh_button = theme_manager.create_button(
            text=theme_manager.t("refresh") or "Refresh",
            icon=ft.Icons.REFRESH,
            on_click=self._on_refresh,
            style="primary"
        )
        
        self.devices_list = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        self.empty_state = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.DEVICES, size=64, color=ft.Colors.GREY),
                    ft.Text(
                        theme_manager.t("no_devices") or "No devices found",
                        size=16,
                        color=ft.Colors.GREY
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            ),
            alignment=ft.alignment.center,
            visible=False
        )
        
        header = ft.Row(
            [
                ft.Text(
                    theme_manager.t("devices") or "Devices",
                    size=20,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(expand=True),
                self.loading_indicator,
                self.refresh_button
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    header,
                    ft.Divider(),
                    self.devices_list,
                    self.empty_state
                ],
                spacing=20,
                expand=True
            ),
            padding=20,
            expand=True
        )
    
    def load_devices(self):
        """Load devices from Firebase."""
        if not self._page:
            return
        
        try:
            self._set_loading(True)
            
            current_user = auth_service.get_current_user()
            if not current_user:
                self._show_error("Not logged in")
                return
            
            uid = current_user.get("uid")
            if not uid:
                self._show_error("No user ID")
                return
            
            devices = device_manager_service.get_all_devices(uid)
            current_device_id = auth_service.device_id
            
            # Clear existing devices
            self.devices_list.controls.clear()
            
            if not devices:
                self.empty_state.visible = True
                self.devices_list.visible = False
            else:
                self.empty_state.visible = False
                self.devices_list.visible = True
                
                for device in devices:
                    device_card = self._create_device_card(device, current_device_id)
                    self.devices_list.controls.append(device_card)
            
            if self._page:
                self._page.update()
        except Exception as e:
            logger.error(f"Error loading devices: {e}", exc_info=True)
            self._show_error(f"Error loading devices: {str(e)}")
        finally:
            self._set_loading(False)
    
    def _create_device_card(self, device: dict, current_device_id: str) -> ft.Card:
        """Create a device card UI component."""
        device_id = device.get("device_id", "Unknown")
        device_name = device.get("device_name", "Unknown Device")
        platform = device.get("platform", "Unknown")
        last_login = device.get("last_login", "")
        is_active = device.get("is_active", True)
        revoked_at = device.get("revoked_at")
        
        # Parse last_login timestamp
        last_login_str = "Never"
        if last_login:
            try:
                if isinstance(last_login, str):
                    # Parse ISO timestamp
                    dt = datetime.fromisoformat(last_login.replace("Z", "+00:00"))
                    last_login_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                last_login_str = str(last_login)
        
        # Determine status
        is_current_device = device_id == current_device_id
        is_revoked = revoked_at is not None or not is_active
        status_text = "Current Device" if is_current_device else ("Revoked" if is_revoked else "Active")
        status_color = ft.Colors.GREEN if is_current_device else (ft.Colors.RED if is_revoked else ft.Colors.BLUE)
        
        # Create status badge
        status_badge = ft.Container(
            content=ft.Text(
                status_text,
                size=12,
                weight=ft.FontWeight.BOLD,
                color=status_color
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border=ft.border.all(1, status_color),
            border_radius=4
        )
        
        # Create revoke button (only for non-current devices)
        revoke_button = None
        if not is_current_device:
            revoke_button = theme_manager.create_button(
                text=theme_manager.t("revoke") or "Revoke",
                icon=ft.Icons.DELETE_OUTLINE,
                on_click=lambda e, d=device: self._on_revoke_device(d),
                style="error",
                width=120
            )
        
        card_content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.DEVICES, size=24),
                        ft.Text(device_name, size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        status_badge
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(height=1),
                ft.Row(
                    [
                        ft.Text(f"Platform: {platform}", size=12),
                        ft.Container(expand=True),
                        ft.Text(f"Last Login: {last_login_str}", size=12, color=ft.Colors.GREY)
                    ]
                ),
                ft.Text(f"Device ID: {device_id[:8]}...", size=10, color=ft.Colors.GREY),
                ft.Row(
                    [
                        ft.Container(expand=True),
                        revoke_button
                    ] if revoke_button else [],
                    alignment=ft.MainAxisAlignment.END
                )
            ],
            spacing=10
        )
        
        return ft.Card(
            content=ft.Container(
                content=card_content,
                padding=15
            )
        )
    
    def _on_refresh(self, e):
        """Handle refresh button click."""
        self.load_devices()
    
    def _on_revoke_device(self, device: dict):
        """Handle revoke device action."""
        if not self._page:
            return
        
        try:
            dialog = RevokeDeviceDialog(
                device=device,
                on_confirm=self._handle_revoke_confirm
            )
            dialog.page = self._page
            self._page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening revoke dialog: {ex}", exc_info=True)
            self._show_error(f"Error: {str(ex)}")
    
    def _handle_revoke_confirm(self, device: dict):
        """Handle device revocation confirmation."""
        try:
            device_id = device.get("device_id")
            if not device_id:
                self._show_error("Invalid device")
                return
            
            # Note: Client can only remove from active_devices
            # Actual revocation marking is admin-only
            success = device_manager_service.revoke_device(device_id)
            
            if success:
                self._show_success("Device revoked successfully")
                # Reload devices
                self.load_devices()
            else:
                self._show_error("Failed to revoke device. Please contact admin.")
        except Exception as e:
            logger.error(f"Error revoking device: {e}", exc_info=True)
            self._show_error(f"Error: {str(e)}")
    
    def _set_loading(self, loading: bool):
        """Set loading state."""
        if self.loading_indicator:
            self.loading_indicator.visible = loading
        if self.refresh_button:
            self.refresh_button.disabled = loading
        if self._page:
            self._page.update()
    
    def _show_error(self, message: str):
        """Show error message."""
        if self._page:
            self._page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=ft.Colors.ERROR
            )
            self._page.snack_bar.open = True
            self._page.update()
    
    def _show_success(self, message: str):
        """Show success message."""
        if self._page:
            self._page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=ft.Colors.GREEN
            )
            self._page.snack_bar.open = True
            self._page.update()

