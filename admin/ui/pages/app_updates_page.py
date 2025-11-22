"""
Admin app updates management page.
"""

import flet as ft
from datetime import datetime
from admin.services.admin_app_update_service import admin_app_update_service


class AdminAppUpdatesPage(ft.Container):
    """Admin app updates management page."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    CARD_BG = "#252525"
    BORDER_COLOR = "#333333"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    
    def __init__(self, page: ft.Page):
        self.page = page
        
        # Form fields
        self.version_field = ft.TextField(
            label="Version",
            hint_text="e.g., 1.0.1",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            expand=True,
        )
        self.windows_url_field = ft.TextField(
            label="Windows Download URL",
            hint_text="GitHub release URL for Windows",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            expand=True,
        )
        self.macos_url_field = ft.TextField(
            label="macOS Download URL",
            hint_text="GitHub release URL for macOS",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            expand=True,
        )
        self.linux_url_field = ft.TextField(
            label="Linux Download URL",
            hint_text="GitHub release URL for Linux",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            expand=True,
        )
        self.release_notes_field = ft.TextField(
            label="Release Notes",
            hint_text="Release notes (markdown supported)",
            multiline=True,
            min_lines=5,
            max_lines=10,
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            expand=True,
        )
        self.is_available_switch = ft.Switch(
            label="Update Available",
            value=True,
        )
        
        self.save_button = ft.ElevatedButton(
            text="Save Update Info",
            icon=ft.Icons.SAVE,
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
            on_click=self._on_save,
        )
        
        self.current_info_text = ft.Text(
            "",
            color=self.TEXT_SECONDARY,
            size=12,
        )
        
        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "App Updates",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color=self.TEXT_COLOR,
                            ),
                        ],
                    ),
                    ft.Divider(height=20, color="transparent"),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self.version_field,
                                self.windows_url_field,
                                self.macos_url_field,
                                self.linux_url_field,
                                self.release_notes_field,
                                ft.Row(
                                    controls=[self.is_available_switch],
                                ),
                                self.current_info_text,
                                ft.Divider(height=10, color="transparent"),
                                self.save_button,
                            ],
                            spacing=15,
                        ),
                        padding=ft.padding.all(20),
                        bgcolor=self.CARD_BG,
                        border=ft.border.all(1, self.BORDER_COLOR),
                        border_radius=8,
                    ),
                ],
                spacing=10,
                expand=True,
            ),
            padding=ft.padding.all(20),
            bgcolor=self.BG_COLOR,
            expand=True,
        )
        
        self._load_current_info()
    
    def _load_current_info(self):
        """Load current app update info."""
        try:
            update_info = admin_app_update_service.get_app_update_info()
            
            if update_info:
                self.version_field.value = update_info.get("version", "")
                self.windows_url_field.value = update_info.get("download_url_windows", "")
                self.macos_url_field.value = update_info.get("download_url_macos", "")
                self.linux_url_field.value = update_info.get("download_url_linux", "")
                self.release_notes_field.value = update_info.get("release_notes", "")
                self.is_available_switch.value = update_info.get("is_available", True)
                
                release_date = update_info.get("release_date", "")
                self.current_info_text.value = f"Current version: {update_info.get('version', 'N/A')} (Last updated: {release_date})"
            else:
                self.current_info_text.value = "No update info found. Create new update info."
            
            self.update()
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading app update info: {e}", exc_info=True)
    
    def _on_save(self, e: ft.ControlEvent):
        """Handle save button click."""
        try:
            update_data = {
                "version": self.version_field.value,
                "download_url_windows": self.windows_url_field.value,
                "download_url_macos": self.macos_url_field.value,
                "download_url_linux": self.linux_url_field.value,
                "release_notes": self.release_notes_field.value,
                "is_available": self.is_available_switch.value,
                "release_date": datetime.utcnow().isoformat() + "Z",
            }
            
            # Validate
            if not update_data["version"]:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Version is required"),
                    bgcolor="#f44336",
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            # Save
            success = admin_app_update_service.update_app_update_info(update_data)
            
            if success:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("App update info saved successfully"),
                    bgcolor="#4caf50",
                )
                self._load_current_info()
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to save app update info"),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving app update info: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()

