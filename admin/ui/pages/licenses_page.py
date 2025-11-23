"""
Admin licenses management page.
"""

import flet as ft
import logging
from typing import Optional
from admin.services.admin_license_service import admin_license_service
from admin.ui.components.data_table import DataTable
from admin.ui.dialogs import LicenseFormDialog, DeleteConfirmDialog

logger = logging.getLogger(__name__)


class AdminLicensesPage(ft.Container):
    """Admin licenses management page."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.data_table: Optional[DataTable] = None
        
        self.create_button = ft.ElevatedButton(
            text="Create License",
            icon=ft.Icons.ADD,
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
            on_click=self._on_create_license,
        )
        
        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Licenses",
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
        
        self._load_licenses()
    
    def _load_licenses(self):
        """Load licenses and populate table."""
        try:
            licenses = admin_license_service.get_all_licenses()
            
            # Get user emails (would need to fetch from users service)
            # For now, just show UID
            columns = [
                {"key": "uid", "label": "User UID", "width": 200},
                {"key": "tier", "label": "Tier", "width": 100},
                {"key": "expiration_date", "label": "Expiration", "width": 150},
                {"key": "max_devices", "label": "Max Devices", "width": 100},
                {"key": "max_groups", "label": "Max Groups", "width": 100},
                {"key": "status", "label": "Status", "width": 100},
            ]
            
            # Format data for table
            from datetime import datetime
            table_data = []
            for license_data in licenses:
                expiration = license_data.get("expiration_date", "")
                now = datetime.utcnow()
                status = "Active"
                
                if expiration:
                    try:
                        if isinstance(expiration, str):
                            exp_date = datetime.fromisoformat(expiration.replace("Z", "+00:00"))
                        else:
                            exp_date = expiration
                        if exp_date < now:
                            status = "Expired"
                    except Exception:
                        pass
                
                table_data.append({
                    "uid": license_data.get("uid", ""),
                    "tier": license_data.get("tier", "none").capitalize(),
                    "expiration_date": expiration or "N/A",
                    "max_devices": str(license_data.get("max_devices", 0)),
                    "max_groups": str(license_data.get("max_groups", 0)) if license_data.get("max_groups", 0) != -1 else "Unlimited",
                    "status": status,
                    "_license_data": license_data,  # Store full license data
                })
            
            actions = [
                {
                    "label": "Edit",
                    "icon": ft.Icons.EDIT,
                    "on_click": self._on_edit_license,
                },
                {
                    "label": "Delete",
                    "icon": ft.Icons.DELETE,
                    "on_click": self._on_delete_license,
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
            logger.error(f"Error loading licenses: {e}", exc_info=True)
    
    def _on_create_license(self, e: ft.ControlEvent):
        """Handle create license button click."""
        dialog = LicenseFormDialog(
            license_data=None,
            user_uid=None,
            on_submit=self._handle_create_license,
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening create license dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_edit_license(self, license_data: dict):
        """Handle edit license action."""
        full_license_data = license_data.get("_license_data", license_data)
        user_uid = full_license_data.get("uid")
        dialog = LicenseFormDialog(
            license_data=full_license_data,
            user_uid=user_uid,
            on_submit=lambda user_uid=None, license_data=None: self._handle_update_license(user_uid, license_data),
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening edit license dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_delete_license(self, license_data: dict):
        """Handle delete license action."""
        full_license_data = license_data.get("_license_data", license_data)
        user_uid = full_license_data.get("uid", "unknown")
        tier = full_license_data.get("tier", "unknown").capitalize()
        
        dialog = DeleteConfirmDialog(
            title="Delete License",
            message=f"Are you sure you want to delete the {tier} license for user '{user_uid}'? This action cannot be undone.",
            item_name=user_uid,
            on_confirm=lambda: self._handle_delete_license(user_uid),
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening delete confirmation dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _handle_create_license(self, user_uid: str, license_data: dict):
        """Handle license creation."""
        try:
            success = admin_license_service.create_license(user_uid, license_data)
            
            if success:
                # Reload licenses
                self._reload_licenses()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"License created successfully for user: {user_uid}"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to create license. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error creating license: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error creating license: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _handle_update_license(self, user_uid: str, license_data: dict):
        """Handle license update."""
        try:
            success = admin_license_service.update_license(user_uid, license_data)
            
            if success:
                # Reload licenses
                self._reload_licenses()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("License updated successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to update license. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error updating license: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error updating license: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _handle_delete_license(self, user_uid: str):
        """Handle license deletion."""
        try:
            success = admin_license_service.delete_license(user_uid)
            
            if success:
                # Reload licenses
                self._reload_licenses()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("License deleted successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to delete license. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error deleting license: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error deleting license: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _reload_licenses(self):
        """Reload licenses table."""
        # Remove old table
        if self.data_table and self.data_table in self.content.controls:
            self.content.controls.remove(self.data_table)
        
        # Load new data
        self._load_licenses()

