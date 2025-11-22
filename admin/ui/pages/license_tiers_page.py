"""
Admin license tiers management page.
"""

import flet as ft
import logging
from typing import Optional
from admin.services.admin_license_tier_service import admin_license_tier_service
from admin.ui.components.data_table import DataTable
from admin.ui.dialogs import LicenseTierFormDialog, DeleteConfirmDialog

logger = logging.getLogger(__name__)


class AdminLicenseTiersPage(ft.Container):
    """Admin license tiers management page."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.data_table: Optional[DataTable] = None
        
        self.create_button = ft.ElevatedButton(
            text="Create Tier",
            icon=ft.Icons.ADD,
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
            on_click=self._on_create_tier,
        )
        
        self.sync_button = ft.ElevatedButton(
            text="Sync from Constants",
            icon=ft.Icons.SYNC,
            bgcolor=self.TEXT_SECONDARY,
            color=self.TEXT_COLOR,
            on_click=self._on_sync_from_constants,
        )
        
        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "License Tiers",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color=self.TEXT_COLOR,
                            ),
                            ft.Row(
                                controls=[
                                    self.sync_button,
                                    self.create_button,
                                ],
                                spacing=10,
                            ),
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
        
        self._load_tiers()
    
    def _load_tiers(self):
        """Load license tiers and populate table."""
        try:
            tiers = admin_license_tier_service.get_all_tiers()
            
            columns = [
                {"key": "tier_key", "label": "Tier Key", "width": 120},
                {"key": "name", "label": "Name", "width": 120},
                {"key": "price", "label": "Price", "width": 150},
                {"key": "max_groups", "label": "Max Groups", "width": 100},
                {"key": "max_devices", "label": "Max Devices", "width": 100},
                {"key": "max_accounts", "label": "Max Accounts", "width": 100},
                {"key": "period", "label": "Period (days)", "width": 100},
                {"key": "in_use", "label": "In Use", "width": 80},
            ]
            
            # Format data for table
            table_data = []
            for tier in tiers:
                price_usd = tier.get("price_usd", 0)
                price_khr = tier.get("price_khr", 0)
                price_str = f"${price_usd}"
                if price_khr > 0:
                    price_str += f" / {price_khr:,} KHR"
                
                max_groups = tier.get("max_groups", 1)
                max_groups_str = "Unlimited" if max_groups == -1 else str(max_groups)
                
                # Get count of licenses using this tier
                in_use_count = admin_license_tier_service.get_tiers_in_use_count(tier.get("tier_key", ""))
                
                table_data.append({
                    "tier_key": tier.get("tier_key", ""),
                    "name": tier.get("name", ""),
                    "price": price_str,
                    "max_groups": max_groups_str,
                    "max_devices": str(tier.get("max_devices", 1)),
                    "max_accounts": str(tier.get("max_accounts", 1)),
                    "period": str(tier.get("period", 30)),
                    "in_use": str(in_use_count),
                    "_tier_data": tier,  # Store full tier data
                })
            
            actions = [
                {
                    "label": "Edit",
                    "icon": ft.Icons.EDIT,
                    "on_click": self._on_edit_tier,
                },
                {
                    "label": "Delete",
                    "icon": ft.Icons.DELETE,
                    "on_click": self._on_delete_tier,
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
            logger.error(f"Error loading license tiers: {e}", exc_info=True)
    
    def _on_create_tier(self, e: ft.ControlEvent):
        """Handle create tier button click."""
        dialog = LicenseTierFormDialog(
            tier_data=None,
            on_submit=self._handle_create_tier,
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening create tier dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_edit_tier(self, tier_data: dict):
        """Handle edit tier action."""
        full_tier_data = tier_data.get("_tier_data", tier_data)
        dialog = LicenseTierFormDialog(
            tier_data=full_tier_data,
            on_submit=self._handle_update_tier,
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening edit tier dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_delete_tier(self, tier_data: dict):
        """Handle delete tier action."""
        full_tier_data = tier_data.get("_tier_data", tier_data)
        tier_key = full_tier_data.get("tier_key", "unknown")
        tier_name = full_tier_data.get("name", tier_key)
        in_use_count = admin_license_tier_service.get_tiers_in_use_count(tier_key)
        
        warning_msg = f"Are you sure you want to delete the '{tier_name}' tier?"
        if in_use_count > 0:
            warning_msg += f"\n\n⚠️ WARNING: This tier is currently used by {in_use_count} license(s). Deleting it may cause issues."
        
        dialog = DeleteConfirmDialog(
            title="Delete License Tier",
            message=warning_msg,
            item_name=tier_key,
            on_confirm=lambda: self._handle_delete_tier(tier_key),
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening delete confirmation dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_sync_from_constants(self, e: ft.ControlEvent):
        """Handle sync from constants button click."""
        try:
            # Disable button during sync
            self.sync_button.disabled = True
            self.sync_button.text = "Syncing..."
            self.sync_button.update()
            
            success = admin_license_tier_service.sync_tiers_from_constants()
            
            if success:
                # Reload tiers
                self._reload_tiers()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("License tiers synced from constants successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to sync license tiers. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error syncing tiers from constants: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error syncing tiers: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
        finally:
            self.sync_button.disabled = False
            self.sync_button.text = "Sync from Constants"
            self.sync_button.update()
    
    def _handle_create_tier(self, tier_key: str, tier_data: dict, update_existing: bool):
        """Handle tier creation."""
        try:
            success = admin_license_tier_service.create_tier(tier_key, tier_data)
            
            if success:
                # Reload tiers
                self._reload_tiers()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"License tier '{tier_key}' created successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to create license tier. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error creating license tier: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error creating license tier: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _handle_update_tier(self, tier_key: str, tier_data: dict, update_existing: bool):
        """Handle tier update."""
        try:
            success = admin_license_tier_service.update_tier(tier_key, tier_data)
            
            if success:
                # Update existing licenses if requested
                if update_existing:
                    updated_count = admin_license_tier_service.update_existing_licenses(tier_key, tier_data)
                    if updated_count > 0:
                        logger.info(f"Updated {updated_count} existing licenses for tier {tier_key}")
                
                # Reload tiers
                self._reload_tiers()
                
                update_msg = f"License tier '{tier_key}' updated successfully"
                if update_existing:
                    updated_count = admin_license_tier_service.update_existing_licenses(tier_key, tier_data)
                    update_msg += f" ({updated_count} licenses updated)"
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(update_msg),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to update license tier. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error updating license tier: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error updating license tier: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _handle_delete_tier(self, tier_key: str):
        """Handle tier deletion."""
        try:
            success = admin_license_tier_service.delete_tier(tier_key)
            
            if success:
                # Reload tiers
                self._reload_tiers()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"License tier '{tier_key}' deleted successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to delete license tier. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error deleting license tier: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error deleting license tier: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _reload_tiers(self):
        """Reload tiers table."""
        # Remove old table
        if self.data_table and self.data_table in self.content.controls:
            self.content.controls.remove(self.data_table)
        
        # Load new data
        self._load_tiers()

