"""
License tier form dialog for creating and editing license tier definitions.
"""

import flet as ft
from typing import Optional, Callable, Dict


class LicenseTierFormDialog(ft.AlertDialog):
    """Dialog for creating or editing a license tier definition."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    CARD_BG = "#252525"
    BORDER_COLOR = "#333333"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    
    def __init__(
        self,
        tier_data: Optional[Dict] = None,
        on_submit: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
    ):
        """
        Initialize license tier form dialog.
        
        Args:
            tier_data: Existing tier data for editing (None for create)
            on_submit: Callback with (tier_key, tier_data) tuple
            on_cancel: Optional callback when cancelled
        """
        self.is_edit = tier_data is not None
        self.tier_data = tier_data
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        
        # Form fields
        self.tier_key_field = ft.TextField(
            label="Tier Key",
            hint_text="e.g., bronze, silver, gold (lowercase, alphanumeric, underscores only)",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            autofocus=not self.is_edit,
            disabled=self.is_edit,  # Can't change tier key when editing
        )
        
        self.name_field = ft.TextField(
            label="Name",
            hint_text="Display name (e.g., Bronze, Silver, Gold)",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.price_usd_field = ft.TextField(
            label="Price (USD)",
            hint_text="Price in USD",
            value="0",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.price_khr_field = ft.TextField(
            label="Price (KHR)",
            hint_text="Price in KHR",
            value="0",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.max_groups_field = ft.TextField(
            label="Max Groups",
            hint_text="-1 for unlimited",
            value="1",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.max_devices_field = ft.TextField(
            label="Max Devices",
            hint_text="Maximum number of devices",
            value="1",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.max_accounts_field = ft.TextField(
            label="Max Accounts",
            hint_text="Maximum number of accounts",
            value="1",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.period_field = ft.TextField(
            label="Period (days)",
            hint_text="Subscription period in days",
            value="30",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.features_field = ft.TextField(
            label="Features",
            hint_text="Comma-separated features (e.g., max_groups, max_devices, priority_support)",
            multiline=True,
            min_lines=2,
            max_lines=4,
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.update_existing_checkbox = ft.Checkbox(
            label="Update existing licenses with this tier",
            value=False,
        )
        
        # Populate fields if editing
        if self.is_edit:
            self._populate_fields()
        
        # Buttons
        submit_button = ft.ElevatedButton(
            text="Save" if self.is_edit else "Create",
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
            on_click=self._on_submit_click,
        )
        
        cancel_button = ft.TextButton(
            text="Cancel",
            on_click=self._on_cancel_click,
        )
        
        # Build content
        # Set expand=True for TextFields in Rows to prevent floating out
        self.price_usd_field.expand = True
        self.price_khr_field.expand = True
        self.max_groups_field.expand = True
        self.max_devices_field.expand = True
        self.max_accounts_field.expand = True
        
        content_controls = [
            self.tier_key_field,
            self.name_field,
            ft.Row(
                controls=[
                    self.price_usd_field,
                    self.price_khr_field,
                ],
                spacing=10,
            ),
            ft.Row(
                controls=[
                    self.max_groups_field,
                    self.max_devices_field,
                    self.max_accounts_field,
                ],
                spacing=10,
            ),
            self.period_field,
            self.features_field,
        ]
        
        # Add update existing checkbox only when editing
        if self.is_edit:
            content_controls.append(self.update_existing_checkbox)
        
        super().__init__(
            title=ft.Text(
                "Edit License Tier" if self.is_edit else "Create License Tier",
                color=self.TEXT_COLOR,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=content_controls,
                    spacing=15,
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=ft.padding.all(10),
                width=500,
            ),
            actions=[
                cancel_button,
                submit_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True,
            bgcolor=self.BG_COLOR,
        )
    
    def _populate_fields(self):
        """Populate form fields with existing tier data."""
        if not self.tier_data:
            return
        
        self.tier_key_field.value = self.tier_data.get("tier_key", "")
        self.name_field.value = self.tier_data.get("name", "")
        self.price_usd_field.value = str(self.tier_data.get("price_usd", 0))
        self.price_khr_field.value = str(self.tier_data.get("price_khr", 0))
        self.max_groups_field.value = str(self.tier_data.get("max_groups", 1))
        self.max_devices_field.value = str(self.tier_data.get("max_devices", 1))
        self.max_accounts_field.value = str(self.tier_data.get("max_accounts", 1))
        self.period_field.value = str(self.tier_data.get("period", 30))
        
        # Handle features (list or string)
        features = self.tier_data.get("features", [])
        if isinstance(features, list):
            self.features_field.value = ", ".join(features)
        else:
            self.features_field.value = str(features) if features else ""
    
    def _on_submit_click(self, e: ft.ControlEvent):
        """Handle submit button click."""
        # Validate and collect data
        tier_key = self.tier_key_field.value.strip().lower() if not self.is_edit else self.tier_data.get("tier_key", "")
        
        if not tier_key:
            self._show_error("Tier key is required")
            return
        
        # Validate tier key format
        import re
        if not re.match(r'^[a-z0-9_]+$', tier_key):
            self._show_error("Tier key must be lowercase, alphanumeric with underscores only")
            return
        
        try:
            tier_data = {
                "name": self.name_field.value.strip(),
                "price_usd": float(self.price_usd_field.value or 0),
                "price_khr": float(self.price_khr_field.value or 0),
                "max_groups": int(self.max_groups_field.value or 1),
                "max_devices": int(self.max_devices_field.value or 1),
                "max_accounts": int(self.max_accounts_field.value or 1),
                "period": int(self.period_field.value or 30),
                "features": [f.strip() for f in self.features_field.value.split(",") if f.strip()] if self.features_field.value else [],
            }
            
            # Validation
            if not tier_data["name"]:
                self._show_error("Name is required")
                return
            
            if tier_data["price_usd"] < 0 or tier_data["price_khr"] < 0:
                self._show_error("Prices must be >= 0")
                return
            
            if tier_data["max_groups"] < -1 or tier_data["max_devices"] < -1 or tier_data["max_accounts"] < -1:
                self._show_error("Max values must be >= -1 (where -1 means unlimited)")
                return
            
            if tier_data["period"] <= 0:
                self._show_error("Period must be > 0")
                return
            
            # Close dialog
            if self.page:
                self.page.close(self)
            
            # Call submit callback with tier_key, tier_data, and update_existing flag
            if self.on_submit:
                update_existing = self.update_existing_checkbox.value if self.is_edit else False
                self.on_submit(tier_key, tier_data, update_existing)
                
        except ValueError as ve:
            self._show_error(f"Invalid number format: {str(ve)}")
        except Exception as ex:
            self._show_error(f"Error: {str(ex)}")
    
    def _on_cancel_click(self, e: ft.ControlEvent):
        """Handle cancel button click."""
        # Close dialog
        if self.page:
            self.page.close(self)
        
        # Call cancel callback
        if self.on_cancel:
            self.on_cancel()
    
    def _show_error(self, message: str):
        """Show error message (could use snackbar or inline error)."""
        # For now, we'll just log it - in a real implementation, show in dialog
        import logging
        logger = logging.getLogger(__name__)
        logger.error(message)
        # Could add error text field to dialog

