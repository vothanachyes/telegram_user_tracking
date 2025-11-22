"""
License form dialog for creating and editing licenses.
"""

import flet as ft
from typing import Optional, Callable, Dict, List
from datetime import datetime
from admin.utils.constants import LICENSE_TIERS  # Fallback


class LicenseFormDialog(ft.AlertDialog):
    """Dialog for creating or editing a license."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    CARD_BG = "#252525"
    BORDER_COLOR = "#333333"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    
    def __init__(
        self,
        license_data: Optional[Dict] = None,
        user_uid: Optional[str] = None,
        on_submit: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
    ):
        """
        Initialize license form dialog.
        
        Args:
            license_data: Existing license data for editing (None for create)
            user_uid: User UID (required for create)
            on_submit: Callback with license data dict
            on_cancel: Optional callback when cancelled
        """
        self.is_edit = license_data is not None
        self.license_data = license_data
        self.user_uid = user_uid or (license_data.get("uid") if license_data else None)
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        
        # Form fields
        self.user_uid_field = ft.TextField(
            label="User UID",
            hint_text="Firebase user UID",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            autofocus=not self.is_edit,
            disabled=self.is_edit,  # Can't change UID when editing
        )
        
        # Tier dropdown - load from Firestore or fallback to constants
        tier_options = self._get_tier_options()
        self.tier_dropdown = ft.Dropdown(
            label="Tier",
            options=tier_options,
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        # Expiration date field
        self.expiration_date_field = ft.TextField(
            label="Expiration Date",
            hint_text="YYYY-MM-DD or ISO format (leave empty for no expiration)",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        # Max devices
        self.max_devices_field = ft.TextField(
            label="Max Devices",
            hint_text="Maximum number of devices",
            value="1",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        
        # Max groups
        self.max_groups_field = ft.TextField(
            label="Max Groups",
            hint_text="Maximum number of groups (-1 for unlimited)",
            value="1",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        
        # Max accounts
        self.max_accounts_field = ft.TextField(
            label="Max Accounts",
            hint_text="Maximum number of accounts",
            value="1",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        
        # Notes field
        self.notes_field = ft.TextField(
            label="Notes",
            hint_text="Optional notes",
            multiline=True,
            min_lines=2,
            max_lines=4,
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        # Set initial values if editing
        if self.is_edit:
            self.user_uid_field.value = self.user_uid
            # Get first tier key from options
            first_tier_key = self.tier_dropdown.options[0].key if self.tier_dropdown.options else None
            self.tier_dropdown.value = license_data.get("tier", first_tier_key)
            expiration = license_data.get("expiration_date")
            if expiration:
                # Format date for display
                try:
                    if isinstance(expiration, str):
                        dt = datetime.fromisoformat(expiration.replace("Z", "+00:00"))
                        self.expiration_date_field.value = dt.strftime("%Y-%m-%d")
                    else:
                        self.expiration_date_field.value = str(expiration)
                except Exception:
                    self.expiration_date_field.value = str(expiration)
            
            self.max_devices_field.value = str(license_data.get("max_devices", 1))
            max_groups = license_data.get("max_groups", 1)
            self.max_groups_field.value = str(max_groups) if max_groups != -1 else "-1"
            self.max_accounts_field.value = str(license_data.get("max_accounts", 1))
            self.notes_field.value = license_data.get("notes", "")
        else:
            # Default values for create
            if self.user_uid:
                self.user_uid_field.value = self.user_uid
            # Get first tier key from options
            first_tier_key = self.tier_dropdown.options[0].key if self.tier_dropdown.options else None
            self.tier_dropdown.value = first_tier_key
        
        # Buttons
        cancel_button = ft.TextButton(
            text="Cancel",
            on_click=self._on_cancel_click,
        )
        
        submit_button = ft.ElevatedButton(
            text="Save" if self.is_edit else "Create",
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
            on_click=self._on_submit_click,
        )
        
        # Build form content
        form_controls = [
            self.user_uid_field,
            self.tier_dropdown,
            self.expiration_date_field,
            ft.Row(
                controls=[
                    ft.Container(
                        content=self.max_devices_field,
                        expand=True,
                    ),
                    ft.Container(
                        content=self.max_groups_field,
                        expand=True,
                    ),
                    ft.Container(
                        content=self.max_accounts_field,
                        expand=True,
                    ),
                ],
                spacing=10,
            ),
            self.notes_field,
        ]
        
        super().__init__(
            title=ft.Text(
                "Edit License" if self.is_edit else "Create License",
                color=self.TEXT_COLOR,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=form_controls,
                    spacing=15,
                    width=500,
                ),
                padding=ft.padding.all(10),
            ),
            actions=[
                cancel_button,
                submit_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True,
            bgcolor=self.BG_COLOR,
        )
    
    def _on_submit_click(self, e: ft.ControlEvent):
        """Handle submit button click."""
        # Validate
        user_uid = self.user_uid_field.value.strip()
        if not user_uid:
            self._show_error("User UID is required")
            return
        
        tier = self.tier_dropdown.value
        # Validate tier exists (check against available tiers)
        available_tier_keys = [opt.key for opt in self.tier_dropdown.options]
        if not tier or tier not in available_tier_keys:
            self._show_error("Valid tier is required")
            return
        
        # Parse expiration date
        expiration_date = None
        expiration_str = self.expiration_date_field.value.strip()
        if expiration_str:
            try:
                # Try parsing as YYYY-MM-DD
                dt = datetime.strptime(expiration_str, "%Y-%m-%d")
                expiration_date = dt.isoformat() + "Z"
            except ValueError:
                try:
                    # Try parsing as ISO format
                    dt = datetime.fromisoformat(expiration_str.replace("Z", "+00:00"))
                    expiration_date = dt.isoformat() + "Z"
                except Exception:
                    self._show_error("Invalid expiration date format. Use YYYY-MM-DD")
                    return
        
        # Parse numeric fields
        try:
            max_devices = int(self.max_devices_field.value or "1")
            if max_devices < 1:
                raise ValueError("Max devices must be at least 1")
        except ValueError:
            self._show_error("Max devices must be a positive integer")
            return
        
        try:
            max_groups_str = self.max_groups_field.value or "1"
            max_groups = int(max_groups_str) if max_groups_str != "-1" else -1
            if max_groups < -1 or max_groups == 0:
                raise ValueError("Max groups must be -1 (unlimited) or at least 1")
        except ValueError:
            self._show_error("Max groups must be -1 (unlimited) or a positive integer")
            return
        
        try:
            max_accounts = int(self.max_accounts_field.value or "1")
            if max_accounts < 1:
                raise ValueError("Max accounts must be at least 1")
        except ValueError:
            self._show_error("Max accounts must be a positive integer")
            return
        
        notes = self.notes_field.value.strip() or None
        
        # Build license data
        license_data = {
            "tier": tier,
            "max_devices": max_devices,
            "max_groups": max_groups,
            "max_accounts": max_accounts,
        }
        
        if expiration_date:
            license_data["expiration_date"] = expiration_date
        
        if notes:
            license_data["notes"] = notes
        
        # Close dialog
        if self.page:
            self.page.close(self)
        
        # Call submit callback
        if self.on_submit:
            self.on_submit(user_uid=user_uid, license_data=license_data)
    
    def _on_cancel_click(self, e: ft.ControlEvent):
        """Handle cancel button click."""
        # Close dialog
        if self.page:
            self.page.close(self)
        
        # Call cancel callback
        if self.on_cancel:
            self.on_cancel()
    
    def _show_error(self, message: str):
        """Show error message."""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _get_tier_options(self) -> List[ft.dropdown.Option]:
        """Get tier options from Firestore or fallback to constants."""
        try:
            from admin.services.admin_license_tier_service import admin_license_tier_service
            tiers = admin_license_tier_service.get_all_tiers()
            if tiers:
                return [
                    ft.dropdown.Option(
                        key=tier.get("tier_key", ""),
                        text=tier.get("name", tier.get("tier_key", "")).capitalize()
                    )
                    for tier in tiers
                ]
        except Exception:
            pass
        
        # Fallback to constants
        return [ft.dropdown.Option(key=tier, text=tier.capitalize()) for tier in LICENSE_TIERS]

