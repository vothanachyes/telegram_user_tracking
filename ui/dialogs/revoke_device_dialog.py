"""
Revoke device confirmation dialog.
"""

import flet as ft
import logging
from typing import Callable, Optional

from ui.theme import theme_manager

logger = logging.getLogger(__name__)


class RevokeDeviceDialog(ft.AlertDialog):
    """Dialog for confirming device revocation."""
    
    def __init__(
        self,
        device: dict,
        on_confirm: Optional[Callable[[dict], None]] = None
    ):
        self.device = device
        self.on_confirm = on_confirm
        
        device_name = device.get("device_name", "Unknown Device")
        platform = device.get("platform", "Unknown")
        device_id = device.get("device_id", "Unknown")
        
        super().__init__(
            modal=True,
            title=ft.Text(theme_manager.t("revoke_device") or "Revoke Device"),
            content=ft.Column(
                [
                    ft.Text(
                        theme_manager.t("revoke_device_confirmation") or 
                        "Are you sure you want to revoke this device?",
                        size=14
                    ),
                    ft.Divider(height=20, color="transparent"),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text("Device:", size=12, weight=ft.FontWeight.BOLD),
                                        ft.Text(device_name, size=12)
                                    ]
                                ),
                                ft.Row(
                                    [
                                        ft.Text("Platform:", size=12, weight=ft.FontWeight.BOLD),
                                        ft.Text(platform, size=12)
                                    ]
                                ),
                                ft.Row(
                                    [
                                        ft.Text("Device ID:", size=12, weight=ft.FontWeight.BOLD),
                                        ft.Text(device_id[:16] + "...", size=12, color=ft.Colors.GREY)
                                    ]
                                )
                            ],
                            spacing=8
                        ),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.GREY),
                        border_radius=5
                    ),
                    ft.Text(
                        theme_manager.t("revoke_device_warning") or 
                        "You will be logged out from this device. You can add it again later.",
                        size=12,
                        color=ft.Colors.ORANGE
                    )
                ],
                tight=True,
                scroll=ft.ScrollMode.AUTO
            ),
            actions=[
                ft.TextButton(
                    text=theme_manager.t("cancel") or "Cancel",
                    on_click=self._on_cancel
                ),
                ft.TextButton(
                    text=theme_manager.t("revoke") or "Revoke",
                    on_click=self._on_confirm,
                    style=ft.ButtonStyle(color=ft.Colors.RED)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
    
    def _on_cancel(self, e):
        """Handle cancel button click."""
        self.open = False
        if self.page:
            self.page.update()
    
    def _on_confirm(self, e):
        """Handle confirm button click."""
        self.open = False
        if self.page:
            self.page.update()
        
        if self.on_confirm:
            try:
                self.on_confirm(self.device)
            except Exception as ex:
                logger.error(f"Error in revoke confirm callback: {ex}", exc_info=True)

