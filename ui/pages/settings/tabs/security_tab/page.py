"""
Security settings tab component.
"""

import flet as ft
import logging
from typing import Callable, Optional
from pathlib import Path
from database.models import AppSettings
from ui.theme import theme_manager
from config.settings import settings as app_settings
from utils.constants import DATABASE_PATH
from utils.windows_auth import WindowsAuth
from services.database.encryption_service import DatabaseEncryptionService
from services.database.db_migration_service import DatabaseMigrationService

logger = logging.getLogger(__name__)


class SecurityTab:
    """Security settings tab component with Windows authentication protection."""
    
    def __init__(
        self,
        current_settings: AppSettings,
        db_manager,
        handlers,
        on_settings_changed: Callable[[], None]
    ):
        self.current_settings = current_settings
        self.db_manager = db_manager
        self.handlers = handlers
        self.on_settings_changed = on_settings_changed
        self.page: Optional[ft.Page] = None
        self._authenticated = False
        
        # Get current database path
        current_db_path = current_settings.db_path or DATABASE_PATH
        
        # Database path field
        self.db_path_field = theme_manager.create_text_field(
            label=theme_manager.t("database_path"),
            value=current_db_path,
            read_only=True
        )
        
        # Encryption toggle
        self.encryption_switch = ft.Switch(
            label=theme_manager.t("enable_database_encryption"),
            value=current_settings.encryption_enabled,
            disabled=True  # Disabled until authenticated
        )
        
        # Encryption key display (masked)
        self.encryption_key_field = theme_manager.create_text_field(
            label=theme_manager.t("encryption_key"),
            value="••••••••••••••••",
            read_only=True,
            password=True
        )
        
        # Reveal key button
        self.reveal_key_btn = theme_manager.create_button(
            text=theme_manager.t("reveal_key"),
            icon=ft.Icons.VISIBILITY,
            on_click=self._reveal_key,
            style="secondary"
        )
        self.reveal_key_btn.disabled = True  # Disabled until authenticated
        
        # Change key button
        self.change_key_btn = theme_manager.create_button(
            text=theme_manager.t("change_encryption_key"),
            icon=ft.Icons.KEY,
            on_click=self._change_key,
            style="secondary"
        )
        self.change_key_btn.disabled = True  # Disabled until authenticated
        
        # Change path button
        self.change_path_btn = theme_manager.create_button(
            text=theme_manager.t("change_database_path"),
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._change_path,
            style="primary"
        )
        self.change_path_btn.disabled = True  # Disabled until authenticated
        
        # Error text
        self.error_text = ft.Text("", color=ft.Colors.RED, visible=False)
        self.success_text = ft.Text("", color=ft.Colors.GREEN, visible=False)
        
        # Authentication lock overlay
        self._build_lock_overlay()
        self.lock_overlay_container = None  # Will be set in build()
    
    def _build_lock_overlay(self):
        """Build authentication lock overlay."""
        self.lock_overlay = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.LOCK, size=48, color=theme_manager.text_secondary_color),
                ft.Text(
                    theme_manager.t("security_tab_locked"),
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(
                    theme_manager.t("security_tab_requires_auth"),
                    size=12,
                    color=theme_manager.text_secondary_color
                ),
                ft.ElevatedButton(
                    text=theme_manager.t("authenticate"),
                    icon=ft.Icons.FINGERPRINT,
                    on_click=self._authenticate,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=theme_manager.primary_color
                    )
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor=theme_manager.surface_color,
            border_radius=theme_manager.corner_radius,
            padding=40,
            alignment=ft.alignment.center
        )
    
    def _authenticate(self, e):
        """Handle authentication request."""
        if not WindowsAuth.is_available():
            self._show_error(theme_manager.t("windows_auth_not_available"))
            return
        
        success, error = WindowsAuth.authenticate(
            message=theme_manager.t("authenticate_to_access_security"),
            title=theme_manager.t("security_authentication")
        )
        
        if success:
            self._authenticated = True
            self.encryption_switch.disabled = False
            self._update_ui()
            self._show_success(theme_manager.t("authentication_successful"))
        else:
            self._show_error(error or theme_manager.t("authentication_failed"))
    
    def build(self) -> ft.Container:
        """Build the security tab."""
        # Privacy disclaimer card
        disclaimer_card = theme_manager.create_card(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=theme_manager.primary_color),
                    ft.Text(
                        theme_manager.t("privacy_disclaimer_title"),
                        size=16,
                        weight=ft.FontWeight.BOLD
                    )
                ], spacing=10),
                ft.Divider(),
                ft.Text(
                    theme_manager.t("privacy_disclaimer_text"),
                    size=12,
                    color=theme_manager.text_secondary_color
                )
            ], spacing=10)
        )
        
        # Database path section
        db_path_card = theme_manager.create_card(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("database_path_settings"),
                    size=18,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(),
                self.db_path_field,
                ft.Row([
                    self.change_path_btn
                ], alignment=ft.MainAxisAlignment.END)
            ], spacing=15)
        )
        
        # Encryption section
        encryption_card = theme_manager.create_card(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("database_encryption"),
                    size=18,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(),
                self.encryption_switch,
                ft.Text(
                    theme_manager.t("encryption_key_label"),
                    size=14,
                    weight=ft.FontWeight.BOLD
                ),
                self.encryption_key_field,
                ft.Row([
                    self.reveal_key_btn,
                    self.change_key_btn
                ], spacing=10)
            ], spacing=15)
        )
        
        # Main content
        main_content = ft.Column([
            disclaimer_card,
            db_path_card,
            encryption_card,
            self.error_text,
            self.success_text
        ], scroll=ft.ScrollMode.AUTO, spacing=15)
        
        # Create lock overlay container (we'll control its visibility)
        self.lock_overlay_container = ft.Container(
            content=self.lock_overlay,
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLACK),
            visible=not self._authenticated
        )
        
        # Wrap with lock overlay (visibility controlled dynamically)
        content = ft.Stack([
            main_content,
            self.lock_overlay_container
        ])
        
        return ft.Container(
            content=content,
            padding=10,
            expand=True
        )
    
    def _update_ui(self):
        """Update UI after authentication."""
        # Update lock overlay visibility
        if hasattr(self, 'lock_overlay_container') and self.lock_overlay_container:
            self.lock_overlay_container.visible = not self._authenticated
        
        # Enable/disable controls based on authentication
        if hasattr(self, 'encryption_switch'):
            self.encryption_switch.disabled = not self._authenticated
        if hasattr(self, 'reveal_key_btn'):
            self.reveal_key_btn.disabled = not self._authenticated
        if hasattr(self, 'change_key_btn'):
            self.change_key_btn.disabled = not self._authenticated
        if hasattr(self, 'change_path_btn'):
            self.change_path_btn.disabled = not self._authenticated
        
        # Update the page
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _reveal_key(self, e):
        """Reveal encryption key."""
        if not self._authenticated:
            self._authenticate(e)
            return
        
        # Get encryption key from settings
        if not self.current_settings.encryption_key_hash:
            self._show_error(theme_manager.t("no_encryption_key_set"))
            return
        
        # Decrypt key using DPAPI
        encrypted_key = self.current_settings.encryption_key_hash
        decrypted_key = DatabaseEncryptionService.decrypt_key_with_dpapi(encrypted_key)
        
        if decrypted_key:
            # Show first 8 and last 8 characters
            masked_key = decrypted_key[:8] + "••••••••" + decrypted_key[-8:]
            self.encryption_key_field.value = masked_key
            self.encryption_key_field.password = False
            self._update_ui()
        else:
            self._show_error(theme_manager.t("failed_to_decrypt_key"))
    
    def _change_key(self, e):
        """Change encryption key."""
        if not self._authenticated:
            self._authenticate(e)
            return
        
        # Show dialog to change key
        from ui.dialogs.change_encryption_key_dialog import ChangeEncryptionKeyDialog
        dialog = ChangeEncryptionKeyDialog(
            current_key_hash=self.current_settings.encryption_key_hash,
            on_confirm=self._handle_key_change
        )
        dialog.page = self.page
        if self.page:
            self.page.open(dialog)
    
    def _handle_key_change(self, new_key: str):
        """Handle encryption key change."""
        try:
            # Get current key if exists
            old_key = None
            if self.current_settings.encryption_key_hash:
                old_key = DatabaseEncryptionService.decrypt_key_with_dpapi(
                    self.current_settings.encryption_key_hash
                )
            
            # Encrypt new key with DPAPI
            encrypted_key = DatabaseEncryptionService.encrypt_key_with_dpapi(new_key)
            if not encrypted_key:
                self._show_error(theme_manager.t("failed_to_encrypt_key"))
                return
            
            # Hash the key for storage
            key_hash = DatabaseEncryptionService.hash_key(new_key)
            
            # Re-encrypt database if encryption is enabled
            current_db_path = self.current_settings.db_path or DATABASE_PATH
            if self.current_settings.encryption_enabled and old_key:
                if not DatabaseEncryptionService.rekey_database(
                    old_key, new_key, current_db_path
                ):
                    self._show_error(theme_manager.t("failed_to_rekey_database"))
                    return
            
            # Update settings
            new_settings = AppSettings(
                **{k: v for k, v in self.current_settings.__dict__.items()},
                encryption_key_hash=encrypted_key
            )
            
            if app_settings.save_settings(new_settings):
                self.current_settings = new_settings
                self._show_success(theme_manager.t("encryption_key_changed"))
                self.on_settings_changed()
            else:
                self._show_error(theme_manager.t("failed_to_save_settings"))
                
        except Exception as ex:
            logger.error(f"Failed to change encryption key: {ex}")
            self._show_error(str(ex))
    
    def _change_path(self, e):
        """Change database path."""
        if not self._authenticated:
            self._authenticate(e)
            return
        
        # Show file picker dialog
        from ui.dialogs.change_db_path_dialog import ChangeDbPathDialog
        current_path = self.current_settings.db_path or DATABASE_PATH
        dialog = ChangeDbPathDialog(
            current_path=current_path,
            on_confirm=self._handle_path_change
        )
        dialog.page = self.page
        if self.page:
            self.page.open(dialog)
    
    def _handle_path_change(self, new_path: str):
        """Handle database path change."""
        try:
            current_path = self.current_settings.db_path or DATABASE_PATH
            
            # Get encryption key if database is encrypted
            encryption_key = None
            if self.current_settings.encryption_enabled and self.current_settings.encryption_key_hash:
                encryption_key = DatabaseEncryptionService.decrypt_key_with_dpapi(
                    self.current_settings.encryption_key_hash
                )
            
            # Migrate database
            success, error = DatabaseMigrationService.migrate_database(
                current_path,
                new_path,
                encryption_key
            )
            
            if not success:
                self._show_error(error or theme_manager.t("migration_failed"))
                return
            
            # Update settings
            new_settings = AppSettings(
                **{k: v for k, v in self.current_settings.__dict__.items()},
                db_path=new_path
            )
            
            if app_settings.save_settings(new_settings):
                self.current_settings = new_settings
                self.db_path_field.value = new_path
                self._show_success(theme_manager.t("database_path_changed"))
                self.on_settings_changed()
                
                # Show restart message
                self._show_error(theme_manager.t("restart_required_for_path_change"))
            else:
                self._show_error(theme_manager.t("failed_to_save_settings"))
                
        except Exception as ex:
            logger.error(f"Failed to change database path: {ex}")
            self._show_error(str(ex))
    
    def update_settings(self, new_settings: AppSettings):
        """Update current settings."""
        self.current_settings = new_settings
        current_db_path = new_settings.db_path or DATABASE_PATH
        self.db_path_field.value = current_db_path
        self.encryption_switch.value = new_settings.encryption_enabled
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _show_error(self, message: str):
        """Show error message."""
        self.error_text.value = message
        self.error_text.visible = True
        self.success_text.visible = False
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _show_success(self, message: str):
        """Show success message."""
        self.success_text.value = message
        self.success_text.visible = True
        self.error_text.visible = False
        if hasattr(self, 'page') and self.page:
            self.page.update()

