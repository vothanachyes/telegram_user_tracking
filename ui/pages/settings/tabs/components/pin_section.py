"""
PIN section component for general settings tab.
"""

import flet as ft
import logging
from typing import Callable, Optional
from database.models import AppSettings
from ui.theme import theme_manager
from config.settings import settings as app_settings
from utils.pin_validator import encrypt_pin, verify_pin
from utils.user_pin_encryption import get_or_create_user_encrypted_pin, update_user_encrypted_pin

logger = logging.getLogger(__name__)


class PinSection:
    """PIN code section component."""
    
    def __init__(
        self,
        current_settings: AppSettings,
        on_settings_changed: Callable[[], None],
        on_error: Callable[[str], None]
    ):
        self.current_settings = current_settings
        self.on_settings_changed = on_settings_changed
        self.on_error = on_error
        self.page: Optional[ft.Page] = None
        
        # Initialize PIN controls
        self._init_pin_controls()
    
    def _init_pin_controls(self):
        """Initialize PIN-related UI controls."""
        has_pin = bool(self.current_settings.encrypted_pin)
        
        # PIN enabled switch
        self.pin_enabled_switch = ft.Switch(
            label=theme_manager.t("enable_pin_code"),
            value=self.current_settings.pin_enabled,
            on_change=self._on_pin_enabled_change
        )
        
        # PIN warning text
        self.pin_warning_text = ft.Text(
            theme_manager.t("pin_warning_local_only"),
            size=12,
            color=ft.Colors.ORANGE_700,
            visible=self.current_settings.pin_enabled,
            weight=ft.FontWeight.BOLD
        )
        
        # Encrypted PIN display (show user-encrypted PIN)
        self.encrypted_pin_visible = False
        # Get user-encrypted PIN (will be created if needed)
        user_encrypted_pin = get_or_create_user_encrypted_pin(app_settings.db_manager) if has_pin else None
        encrypted_pin_value = user_encrypted_pin or ""
        self.encrypted_pin_text = ft.Text(
            "••••••••••••••••" if encrypted_pin_value else "",
            size=11,
            color=theme_manager.text_secondary_color,
            font_family="monospace",
            visible=True,
            selectable=True
        )
        # Store the actual value for copying
        self._user_encrypted_pin_value = user_encrypted_pin
        
        # Peek button (eye icon)
        self.peek_pin_btn = ft.IconButton(
            icon=ft.Icons.VISIBILITY_OFF,
            tooltip=theme_manager.t("show_encrypted_pin") or "Show encrypted PIN",
            on_click=self._toggle_pin_visibility,
            icon_size=18,
            visible=has_pin and self.current_settings.pin_enabled
        )
        
        # Copy button
        self.copy_pin_btn = ft.IconButton(
            icon=ft.Icons.COPY,
            tooltip=theme_manager.t("copy_encrypted_pin") or "Copy encrypted PIN",
            on_click=self._copy_encrypted_pin,
            icon_size=18,
            visible=has_pin and self.current_settings.pin_enabled
        )
        
        # Encrypted PIN container
        self.encrypted_pin_container = ft.Container(
            content=ft.Row([
                ft.Text(
                    theme_manager.t("encrypted_pin") or "Encrypted PIN:",
                    size=11,
                    color=theme_manager.text_secondary_color
                ),
                self.encrypted_pin_text,
                self.peek_pin_btn,
                self.copy_pin_btn
            ], spacing=8, tight=True),
            visible=has_pin and self.current_settings.pin_enabled,
            padding=ft.padding.only(top=5)
        )
        
        # PIN action buttons
        self.set_pin_btn = theme_manager.create_button(
            text=theme_manager.t("set_pin"),
            icon=ft.Icons.LOCK,
            on_click=self._handle_set_pin,
            style="secondary",
            visible=self.current_settings.pin_enabled and not has_pin
        )
        
        self.change_pin_btn = theme_manager.create_button(
            text=theme_manager.t("change_pin"),
            icon=ft.Icons.EDIT,
            on_click=self._handle_change_pin,
            style="secondary",
            visible=self.current_settings.pin_enabled and has_pin
        )
        
        self.remove_pin_btn = theme_manager.create_button(
            text=theme_manager.t("remove_pin"),
            icon=ft.Icons.DELETE,
            on_click=self._handle_remove_pin,
            style="error",
            visible=self.current_settings.pin_enabled and has_pin
        )
    
    def build(self) -> ft.Container:
        """Build the PIN section card."""
        return theme_manager.create_card(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("pin_code"),
                    size=20,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(),
                self.pin_enabled_switch,
                self.pin_warning_text,
                self.encrypted_pin_container,
                ft.Row([
                    self.set_pin_btn,
                    self.change_pin_btn,
                    self.remove_pin_btn,
                ], spacing=10, wrap=False) if (self.set_pin_btn.visible or self.change_pin_btn.visible or self.remove_pin_btn.visible) else ft.Container(height=0),
            ], spacing=15)
        )
    
    def update_settings(self, new_settings: AppSettings):
        """Update with new settings."""
        self.current_settings = new_settings
        self._update_ui_state()
    
    def _update_ui_state(self):
        """Update UI state based on current settings."""
        has_pin = bool(self.current_settings.encrypted_pin)
        
        self.pin_enabled_switch.value = self.current_settings.pin_enabled
        self.pin_warning_text.visible = self.current_settings.pin_enabled
        self.set_pin_btn.visible = self.current_settings.pin_enabled and not has_pin
        self.change_pin_btn.visible = self.current_settings.pin_enabled and has_pin
        self.remove_pin_btn.visible = self.current_settings.pin_enabled and has_pin
        
        # Update encrypted PIN display
        if has_pin and self.current_settings.encrypted_pin:
            self.encrypted_pin_container.visible = self.current_settings.pin_enabled
            self.peek_pin_btn.visible = self.current_settings.pin_enabled
            self.copy_pin_btn.visible = self.current_settings.pin_enabled
            self.encrypted_pin_visible = False
            self.peek_pin_btn.icon = ft.Icons.VISIBILITY_OFF
            self.encrypted_pin_text.value = "••••••••••••••••"
        else:
            self.encrypted_pin_container.visible = False
            self.peek_pin_btn.visible = False
            self.copy_pin_btn.visible = False
    
    def _on_pin_enabled_change(self, e):
        """Handle PIN enabled toggle change."""
        pin_enabled = e.control.value
        has_pin = bool(self.current_settings.encrypted_pin)
        
        # If disabling PIN and PIN is set, require current PIN verification
        if not pin_enabled and has_pin:
            # Revert switch
            self.pin_enabled_switch.value = True
            if self.page:
                self.page.update()
            
            # Show PIN verification dialog
            self._verify_pin_for_disable()
            return
        
        # Update warning visibility
        self.pin_warning_text.visible = pin_enabled
        
        # Update button visibility
        self.set_pin_btn.visible = pin_enabled and not has_pin
        self.change_pin_btn.visible = pin_enabled and has_pin
        self.remove_pin_btn.visible = pin_enabled and has_pin
        
        # Update encrypted PIN display
        if has_pin and self.current_settings.encrypted_pin:
            self.encrypted_pin_container.visible = pin_enabled
            self.peek_pin_btn.visible = pin_enabled
            self.copy_pin_btn.visible = pin_enabled
        else:
            self.encrypted_pin_container.visible = False
            self.peek_pin_btn.visible = False
            self.copy_pin_btn.visible = False
        
        # If disabling PIN, clear encrypted PIN
        if not pin_enabled:
            self.current_settings.encrypted_pin = None
        
        # Update PIN enabled state
        self.current_settings.pin_enabled = pin_enabled
        
        # Save immediately when toggling
        if app_settings.save_settings(self.current_settings):
            self.on_settings_changed()
        
        if self.page:
            self.page.update()
    
    def _handle_set_pin(self, e):
        """Handle set PIN button click."""
        from ui.dialogs.pin_dialog import PinSetupDialog
        
        def on_pin_set(pin: str):
            """Handle PIN setup completion."""
            try:
                # Encrypt PIN
                encrypted_pin = encrypt_pin(pin)
                
                # Update settings
                self.current_settings.pin_enabled = True
                self.current_settings.encrypted_pin = encrypted_pin
                
                if app_settings.save_settings(self.current_settings):
                    # Update user-encrypted PIN
                    update_user_encrypted_pin(app_settings.db_manager)
                    
                    # Refresh settings to get updated user-encrypted PIN
                    self.current_settings = app_settings.db_manager.get_settings()
                    user_encrypted_pin = get_or_create_user_encrypted_pin(app_settings.db_manager)
                    self._user_encrypted_pin_value = user_encrypted_pin
                    
                    # Update UI
                    self._update_ui_state()
                    
                    theme_manager.show_snackbar(
                        self.page,
                        theme_manager.t("settings_saved"),
                        bgcolor=ft.Colors.GREEN
                    )
                    self.on_settings_changed()
                    
                    if self.page:
                        self.page.update()
                else:
                    self.on_error("Failed to save PIN")
            except Exception as ex:
                logger.error(f"Error setting PIN: {ex}")
                self.on_error(f"Failed to set PIN: {str(ex)}")
        
        # Create and show PIN setup dialog
        dialog = PinSetupDialog(
            title=theme_manager.t("set_pin"),
            on_submit=on_pin_set,
            on_cancel=None
        )
        dialog.page = self.page
        
        if self.page:
            try:
                self.page.open(dialog)
            except Exception as ex:
                logger.error(f"page.open() failed: {ex}")
                self.page.dialog = dialog
                dialog.open = True
                self.page.update()
    
    def _handle_change_pin(self, e):
        """Handle change PIN button click."""
        # First verify current PIN
        self._verify_pin_for_change()
    
    def _handle_remove_pin(self, e):
        """Handle remove PIN button click."""
        # First verify current PIN
        self._verify_pin_for_remove()
    
    def _verify_pin_for_disable(self):
        """Verify current PIN before disabling PIN."""
        from ui.dialogs.pin_dialog import PinEntryDialog
        
        if not self.current_settings.encrypted_pin:
            return
        
        def on_pin_verified(pin: str):
            """Handle PIN verification for disable."""
            try:
                if verify_pin(pin, self.current_settings.encrypted_pin):
                    # PIN verified, disable PIN
                    self.current_settings.encrypted_pin = None
                    self.current_settings.pin_enabled = False
                    self.current_settings.user_encrypted_pin = None  # Clear user-encrypted PIN
                    
                    if app_settings.save_settings(self.current_settings):
                        # Update UI
                        self._update_ui_state()
                        
                        theme_manager.show_snackbar(
                            self.page,
                            theme_manager.t("pin_disabled") or "PIN disabled successfully",
                            bgcolor=ft.Colors.GREEN
                        )
                        self.on_settings_changed()
                        
                        if self.page:
                            self.page.update()
                    else:
                        self.on_error("Failed to disable PIN")
                else:
                    # Incorrect PIN
                    pin_dialog.show_error(theme_manager.t("pin_incorrect"))
            except Exception as ex:
                logger.error(f"Error verifying PIN for disable: {ex}")
                pin_dialog.show_error(theme_manager.t("pin_incorrect"))
        
        def on_cancel():
            """Handle cancellation."""
            # Switch is already reverted, just close dialog
            pass
        
        # Create and show PIN verification dialog
        pin_dialog = PinEntryDialog(
            title=theme_manager.t("verify_current_pin") or "Verify Current PIN",
            message=theme_manager.t("enter_current_pin_to_disable") or "Enter your current PIN to disable PIN protection.",
            on_submit=on_pin_verified,
            on_cancel=on_cancel,
            allow_cancel=True
        )
        pin_dialog.page = self.page
        
        if self.page:
            try:
                self.page.open(pin_dialog)
            except Exception as ex:
                logger.error(f"page.open() failed: {ex}")
                self.page.dialog = pin_dialog
                pin_dialog.open = True
                self.page.update()
    
    def _verify_pin_for_change(self):
        """Verify current PIN before changing PIN."""
        from ui.dialogs.pin_dialog import PinEntryDialog, PinSetupDialog
        
        if not self.current_settings.encrypted_pin:
            return
        
        def on_pin_verified(pin: str):
            """Handle PIN verification for change."""
            try:
                if verify_pin(pin, self.current_settings.encrypted_pin):
                    # PIN verified, show change PIN dialog
                    def on_pin_change(new_pin: str):
                        """Handle PIN change completion."""
                        try:
                            # Encrypt new PIN
                            encrypted_pin = encrypt_pin(new_pin)
                            
                            # Update settings
                            self.current_settings.encrypted_pin = encrypted_pin
                            
                            if app_settings.save_settings(self.current_settings):
                                # Update user-encrypted PIN
                                update_user_encrypted_pin(app_settings.db_manager)
                                
                                # Refresh settings to get updated user-encrypted PIN
                                self.current_settings = app_settings.db_manager.get_settings()
                                user_encrypted_pin = get_or_create_user_encrypted_pin(app_settings.db_manager)
                                self._user_encrypted_pin_value = user_encrypted_pin
                                
                                # Update encrypted PIN display
                                self.encrypted_pin_text.value = "••••••••••••••••"
                                self.encrypted_pin_visible = False
                                self.peek_pin_btn.icon = ft.Icons.VISIBILITY_OFF
                                
                                theme_manager.show_snackbar(
                                    self.page,
                                    theme_manager.t("settings_saved"),
                                    bgcolor=ft.Colors.GREEN
                                )
                                self.on_settings_changed()
                                
                                if self.page:
                                    self.page.update()
                            else:
                                self.on_error("Failed to save PIN")
                        except Exception as ex:
                            logger.error(f"Error changing PIN: {ex}")
                            self.on_error(f"Failed to change PIN: {str(ex)}")
                    
                    # Create and show PIN setup dialog
                    change_dialog = PinSetupDialog(
                        title=theme_manager.t("change_pin"),
                        on_submit=on_pin_change,
                        on_cancel=None
                    )
                    change_dialog.page = self.page
                    
                    if self.page:
                        try:
                            self.page.open(change_dialog)
                        except Exception as ex:
                            logger.error(f"page.open() failed: {ex}")
                            self.page.dialog = change_dialog
                            change_dialog.open = True
                            self.page.update()
                else:
                    # Incorrect PIN
                    pin_dialog.show_error(theme_manager.t("pin_incorrect"))
            except Exception as ex:
                logger.error(f"Error verifying PIN for change: {ex}")
                pin_dialog.show_error(theme_manager.t("pin_incorrect"))
        
        def on_cancel():
            """Handle cancellation."""
            pass
        
        # Create and show PIN verification dialog
        pin_dialog = PinEntryDialog(
            title=theme_manager.t("verify_current_pin") or "Verify Current PIN",
            message=theme_manager.t("enter_current_pin_to_change") or "Enter your current PIN to change it.",
            on_submit=on_pin_verified,
            on_cancel=on_cancel,
            allow_cancel=True
        )
        pin_dialog.page = self.page
        
        if self.page:
            try:
                self.page.open(pin_dialog)
            except Exception as ex:
                logger.error(f"page.open() failed: {ex}")
                self.page.dialog = pin_dialog
                pin_dialog.open = True
                self.page.update()
    
    def _verify_pin_for_remove(self):
        """Verify current PIN before removing PIN."""
        from ui.dialogs.pin_dialog import PinEntryDialog
        
        if not self.current_settings.encrypted_pin:
            return
        
        def on_pin_verified(pin: str):
            """Handle PIN verification for remove."""
            try:
                if verify_pin(pin, self.current_settings.encrypted_pin):
                    # PIN verified, remove PIN
                    self.current_settings.encrypted_pin = None
                    self.current_settings.pin_enabled = False
                    self.current_settings.user_encrypted_pin = None  # Clear user-encrypted PIN
                    
                    if app_settings.save_settings(self.current_settings):
                        # Update UI
                        self._update_ui_state()
                        
                        theme_manager.show_snackbar(
                            self.page,
                            theme_manager.t("settings_saved"),
                            bgcolor=ft.Colors.GREEN
                        )
                        self.on_settings_changed()
                        
                        if self.page:
                            self.page.update()
                    else:
                        self.on_error("Failed to remove PIN")
                else:
                    # Incorrect PIN
                    pin_dialog.show_error(theme_manager.t("pin_incorrect"))
            except Exception as ex:
                logger.error(f"Error verifying PIN for remove: {ex}")
                pin_dialog.show_error(theme_manager.t("pin_incorrect"))
        
        def on_cancel():
            """Handle cancellation."""
            pass
        
        # Create and show PIN verification dialog
        pin_dialog = PinEntryDialog(
            title=theme_manager.t("verify_current_pin") or "Verify Current PIN",
            message=theme_manager.t("enter_current_pin_to_remove") or "Enter your current PIN to remove it.",
            on_submit=on_pin_verified,
            on_cancel=on_cancel,
            allow_cancel=True
        )
        pin_dialog.page = self.page
        
        if self.page:
            try:
                self.page.open(pin_dialog)
            except Exception as ex:
                logger.error(f"page.open() failed: {ex}")
                self.page.dialog = pin_dialog
                pin_dialog.open = True
                self.page.update()
    
    def _toggle_pin_visibility(self, e):
        """Toggle encrypted PIN visibility."""
        if not self.current_settings.encrypted_pin:
            return
        
        self.encrypted_pin_visible = not self.encrypted_pin_visible
        
        if self.encrypted_pin_visible:
            # Show user-encrypted PIN
            user_encrypted_pin = get_or_create_user_encrypted_pin(app_settings.db_manager)
            self._user_encrypted_pin_value = user_encrypted_pin
            self.encrypted_pin_text.value = user_encrypted_pin or "••••••••••••••••"
            self.peek_pin_btn.icon = ft.Icons.VISIBILITY
            self.peek_pin_btn.tooltip = theme_manager.t("hide_encrypted_pin") or "Hide encrypted PIN"
        else:
            self.encrypted_pin_text.value = "••••••••••••••••"
            self.peek_pin_btn.icon = ft.Icons.VISIBILITY_OFF
            self.peek_pin_btn.tooltip = theme_manager.t("show_encrypted_pin") or "Show encrypted PIN"
        
        if self.page:
            self.page.update()
    
    def _copy_encrypted_pin(self, e):
        """Copy user-encrypted PIN to clipboard."""
        if not self.current_settings.encrypted_pin:
            return
        
        # Get user-encrypted PIN
        user_encrypted_pin = get_or_create_user_encrypted_pin(app_settings.db_manager)
        if not user_encrypted_pin:
            return
        
        if self.page:
            self.page.set_clipboard(user_encrypted_pin)
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("encrypted_pin_copied") or "Encrypted PIN copied to clipboard",
                bgcolor=ft.Colors.GREEN
            )

