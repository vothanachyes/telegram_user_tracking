"""
License form dialog for creating and editing licenses.
"""

import flet as ft
from typing import Optional, Callable, Dict, List
from datetime import datetime, timedelta
from admin.utils.constants import LICENSE_TIERS  # Fallback
from admin.services.admin_user_service import admin_user_service


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
        
        # Form fields - User UID field
        # Use dropdown for create mode, TextField for edit mode (read-only)
        if self.is_edit:
            # Edit mode: Use TextField (read-only)
            self.user_uid_field = ft.TextField(
                label="User UID",
                hint_text="Firebase user UID",
                bgcolor=self.CARD_BG,
                color=self.TEXT_COLOR,
                border_color=self.BORDER_COLOR,
                disabled=True,  # Can't change UID when editing
            )
        else:
            # Create mode: Use Dropdown with users list
            user_options = self._get_user_options()
            self.user_uid_field = ft.Dropdown(
                label="User UID",
                hint_text="Select a user",
                options=user_options,
                bgcolor=self.CARD_BG,
                color=self.TEXT_COLOR,
                border_color=self.BORDER_COLOR,
                autofocus=True,
            )
        
        # Tier dropdown - load from Firestore or fallback to constants
        tier_options = self._get_tier_options()
        self.tier_dropdown = ft.Dropdown(
            label="Tier",
            options=tier_options,
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            on_change=self._on_tier_change,  # Update fields when tier changes
        )
        
        # Expiration date field - read-only in edit mode
        self.expiration_date_field = ft.TextField(
            label="Expiration Date",
            hint_text="YYYY-MM-DD or ISO format (leave empty for no expiration)",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            disabled=self.is_edit,  # Read-only in edit mode
        )
        
        # Max devices - read-only in edit mode
        self.max_devices_field = ft.TextField(
            label="Max Devices",
            hint_text="Maximum number of devices",
            value="1",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            keyboard_type=ft.KeyboardType.NUMBER,
            disabled=self.is_edit,  # Read-only in edit mode
        )
        
        # Max groups - read-only in edit mode
        self.max_groups_field = ft.TextField(
            label="Max Groups",
            hint_text="Maximum number of groups (-1 for unlimited)",
            value="1",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            keyboard_type=ft.KeyboardType.NUMBER,
            disabled=self.is_edit,  # Read-only in edit mode
        )
        
        # Max accounts - read-only in edit mode
        self.max_accounts_field = ft.TextField(
            label="Max Accounts",
            hint_text="Maximum number of accounts",
            value="1",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            keyboard_type=ft.KeyboardType.NUMBER,
            disabled=self.is_edit,  # Read-only in edit mode
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
            current_tier = license_data.get("tier", first_tier_key)
            self.tier_dropdown.value = current_tier
            
            # If custom tier, enable all fields
            if current_tier == "custom":
                self.max_devices_field.disabled = False
                self.max_groups_field.disabled = False
                self.max_accounts_field.disabled = False
                self.expiration_date_field.disabled = False
            
            # Load tier definition and update fields
            self._update_fields_from_tier(current_tier, license_data)
            
            self.notes_field.value = license_data.get("notes", "")
        else:
            # Default values for create
            if self.user_uid:
                # If user_uid is provided, set it in dropdown
                if isinstance(self.user_uid_field, ft.Dropdown):
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
        # Validate - handle both TextField and Dropdown
        if isinstance(self.user_uid_field, ft.Dropdown):
            user_uid = self.user_uid_field.value
        else:
            user_uid = self.user_uid_field.value.strip() if self.user_uid_field.value else ""
        
        if not user_uid:
            self._show_error("User UID is required")
            return
        
        tier = self.tier_dropdown.value
        # Validate tier exists (check against available tiers)
        available_tier_keys = [opt.key for opt in self.tier_dropdown.options]
        if not tier or tier not in available_tier_keys:
            self._show_error("Valid tier is required")
            return
        
        # Handle "custom" tier - use form field values directly
        if tier == "custom":
            # Parse from form fields (all fields are editable for custom tier)
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
        else:
            # For non-custom tiers, get tier definition
            from admin.services.admin_license_service import admin_license_service
            tier_definition = admin_license_service.get_tier_definition(tier)
            if not tier_definition:
                self._show_error(f"Invalid tier: {tier}")
                return
            
            # In edit mode, use tier definition values; in create mode, allow manual input
            if self.is_edit:
                # Use tier definition values (fields are read-only)
                max_devices = tier_definition.get("max_devices", 1)
                max_groups = tier_definition.get("max_groups", 1)
                max_accounts = tier_definition.get("max_accounts", 1)
                # Keep existing expiration date (read-only field)
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
                            # If parsing fails, keep original value
                            expiration_date = expiration_str if expiration_str else None
            else:
                # Create mode: parse from form fields
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
                
                # Parse expiration date for create mode
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
        
        notes = self.notes_field.value.strip() or None
        
        # Build license data
        license_data = {
            "tier": tier,
            "max_devices": max_devices,
            "max_groups": max_groups,
            "max_accounts": max_accounts,
        }
        
        # Always include expiration_date (None means delete field for lifetime license)
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
        options = []
        
        try:
            from admin.services.admin_license_tier_service import admin_license_tier_service
            tiers = admin_license_tier_service.get_all_tiers()
            if tiers:
                options = [
                    ft.dropdown.Option(
                        key=tier.get("tier_key", ""),
                        text=tier.get("name", tier.get("tier_key", "")).capitalize()
                    )
                    for tier in tiers
                ]
        except Exception:
            pass
        
        # Fallback to constants if no tiers from Firestore
        if not options:
            options = [ft.dropdown.Option(key=tier, text=tier.capitalize()) for tier in LICENSE_TIERS]
        
        # Add "Custom" option at the end
        options.append(ft.dropdown.Option(key="custom", text="Custom"))
        
        return options
    
    def _on_tier_change(self, e: ft.ControlEvent):
        """Handle tier dropdown change - update fields from tier definition."""
        tier_key = self.tier_dropdown.value
        if not tier_key:
            return
        
        # Handle "custom" tier - enable all fields and set Bronze defaults
        if tier_key == "custom":
            # Enable all fields
            self.max_devices_field.disabled = False
            self.max_groups_field.disabled = False
            self.max_accounts_field.disabled = False
            self.expiration_date_field.disabled = False
            
            # Set Bronze tier defaults (1 device, 1 group, 1 account) if fields are empty
            if not self.max_devices_field.value or self.max_devices_field.value == "1":
                self.max_devices_field.value = "1"
            if not self.max_groups_field.value or self.max_groups_field.value == "1":
                self.max_groups_field.value = "1"
            if not self.max_accounts_field.value or self.max_accounts_field.value == "1":
                self.max_accounts_field.value = "1"
            
            # Update UI
            if self.page:
                self.page.update()
            return
        
        # For non-custom tiers, disable fields in edit mode
        if self.is_edit:
            self.max_devices_field.disabled = True
            self.max_groups_field.disabled = True
            self.max_accounts_field.disabled = True
            self.expiration_date_field.disabled = True
        else:
            # In create mode, fields are already enabled
            pass
        
        # Get tier definition
        from admin.services.admin_license_service import admin_license_service
        tier_definition = admin_license_service.get_tier_definition(tier_key)
        if not tier_definition:
            return
        
        # Update fields from tier definition
        self.max_devices_field.value = str(tier_definition.get("max_devices", 1))
        max_groups = tier_definition.get("max_groups", 1)
        self.max_groups_field.value = str(max_groups) if max_groups != -1 else "-1"
        self.max_accounts_field.value = str(tier_definition.get("max_accounts", 1))
        
        # Update expiration date if in create mode (calculate from period)
        if not self.is_edit:
            period_days = tier_definition.get("period", 30)
            if self.expiration_date_field.value:
                # If expiration date exists, extend it by period
                try:
                    current_date = datetime.strptime(self.expiration_date_field.value, "%Y-%m-%d")
                    new_date = current_date
                except ValueError:
                    new_date = datetime.utcnow()
            else:
                new_date = datetime.utcnow()
            
            # Only update if field is empty or we're in create mode
            if not self.expiration_date_field.value or not self.is_edit:
                expiration_date = (new_date + timedelta(days=period_days)).strftime("%Y-%m-%d")
                self.expiration_date_field.value = expiration_date
        
        # Update UI
        if self.page:
            self.page.update()
    
    def _update_fields_from_tier(self, tier_key: str, license_data: Optional[Dict] = None):
        """Update form fields from tier definition."""
        # Skip auto-update for "custom" tier - use license data values directly
        if tier_key == "custom":
            if license_data:
                self.max_devices_field.value = str(license_data.get("max_devices", 1))
                max_groups = license_data.get("max_groups", 1)
                self.max_groups_field.value = str(max_groups) if max_groups != -1 else "-1"
                self.max_accounts_field.value = str(license_data.get("max_accounts", 1))
                
                # Set expiration date from license data
                expiration = license_data.get("expiration_date")
                if expiration:
                    try:
                        if isinstance(expiration, str):
                            dt = datetime.fromisoformat(expiration.replace("Z", "+00:00"))
                            self.expiration_date_field.value = dt.strftime("%Y-%m-%d")
                        else:
                            self.expiration_date_field.value = str(expiration)
                    except Exception:
                        self.expiration_date_field.value = str(expiration)
            return
        
        # For non-custom tiers, get tier definition
        from admin.services.admin_license_service import admin_license_service
        tier_definition = admin_license_service.get_tier_definition(tier_key)
        
        if tier_definition:
            # Update from tier definition
            self.max_devices_field.value = str(tier_definition.get("max_devices", 1))
            max_groups = tier_definition.get("max_groups", 1)
            self.max_groups_field.value = str(max_groups) if max_groups != -1 else "-1"
            self.max_accounts_field.value = str(tier_definition.get("max_accounts", 1))
        else:
            # Fallback to license data if tier definition not found
            if license_data:
                self.max_devices_field.value = str(license_data.get("max_devices", 1))
                max_groups = license_data.get("max_groups", 1)
                self.max_groups_field.value = str(max_groups) if max_groups != -1 else "-1"
                self.max_accounts_field.value = str(license_data.get("max_accounts", 1))
        
        # Set expiration date from license data (keep existing)
        if license_data:
            expiration = license_data.get("expiration_date")
            if expiration:
                try:
                    if isinstance(expiration, str):
                        dt = datetime.fromisoformat(expiration.replace("Z", "+00:00"))
                        self.expiration_date_field.value = dt.strftime("%Y-%m-%d")
                    else:
                        self.expiration_date_field.value = str(expiration)
                except Exception:
                    self.expiration_date_field.value = str(expiration)
    
    def _get_user_options(self) -> List[ft.dropdown.Option]:
        """Get user options from Firebase for dropdown."""
        try:
            users = admin_user_service.get_all_users()
            if not users:
                return []
            
            options = []
            for user in users:
                uid = user.get("uid", "")
                email = user.get("email", "No email")
                display_name = user.get("display_name", "")
                
                # Format display text: "Email (Display Name)" or just "Email"
                if display_name:
                    display_text = f"{email} ({display_name})"
                else:
                    display_text = email
                
                options.append(
                    ft.dropdown.Option(
                        key=uid,
                        text=display_text
                    )
                )
            
            return options
            
        except Exception as e:
            # Log error but return empty list to allow manual entry if needed
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading users for dropdown: {e}", exc_info=True)
            return []

