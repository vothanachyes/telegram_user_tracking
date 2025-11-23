"""
Security settings tab component.
"""

import flet as ft
import logging
import json
import platform
import threading
import time
from typing import Callable, Optional
from pathlib import Path
from database.models import AppSettings
from ui.theme import theme_manager
from config.settings import settings as app_settings
from utils.constants import DATABASE_PATH
from utils.windows_auth import WindowsAuth
from utils.user_pin_encryption import get_or_create_user_encrypted_pin
from services.database.encryption_service import DatabaseEncryptionService
from services.database.db_migration_service import DatabaseMigrationService
from services.auth_service import auth_service

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
        
        # OS authentication attempt tracking
        self._os_auth_attempts = 0
        self._max_os_auth_attempts = 10
        self._os_auth_delay_seconds = 2
        self._auth_in_progress = False
        
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
            disabled=True,  # Disabled until authenticated
            on_change=self._on_encryption_switch_changed
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
        
        # PIN recovery JSON field (masked)
        self.pin_recovery_json_field = theme_manager.create_text_field(
            label=theme_manager.t("pin_recovery_data") or "PIN Recovery Data",
            value="",
            read_only=True,
            password=True,
            multiline=True,
            min_lines=5,
            max_lines=8
        )
        
        # Copy PIN recovery data button
        self.copy_pin_recovery_btn = theme_manager.create_button(
            text=theme_manager.t("copy_pin_recovery_data") or "Copy to Clipboard",
            icon=ft.Icons.COPY,
            on_click=self._copy_pin_recovery_data,
            style="secondary"
        )
        self.copy_pin_recovery_btn.disabled = True  # Disabled until authenticated
        
        # Store full JSON data for copying
        self._pin_recovery_json_data = None
        
        # Error text
        self.error_text = ft.Text("", color=ft.Colors.RED, visible=False)
        self.success_text = ft.Text("", color=ft.Colors.GREEN, visible=False)
        
        # Authentication lock overlay
        self._build_lock_overlay()
        self.lock_overlay_container = None  # Will be set in build()
    
    def _build_lock_overlay(self):
        """Build authentication lock overlay."""
        # Attempt info text (initially hidden)
        self.attempt_info_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.ORANGE_700,
            weight=ft.FontWeight.BOLD,
            visible=False
        )
        
        # Firebase password button (initially hidden)
        self.firebase_auth_btn = ft.ElevatedButton(
            text=theme_manager.t("use_firebase_password") or "Use Firebase Password",
            icon=ft.Icons.LOCK_OPEN,
            on_click=self._authenticate_with_firebase,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.ORANGE_700
            ),
            visible=False
        )
        
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
                self.attempt_info_text,
                ft.ElevatedButton(
                    text=theme_manager.t("authenticate"),
                    icon=ft.Icons.FINGERPRINT,
                    on_click=self._authenticate,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=theme_manager.primary_color
                    )
                ),
                self.firebase_auth_btn
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
        # Prevent multiple simultaneous authentication attempts
        if self._auth_in_progress:
            return
        
        # Check if max attempts reached
        if self._os_auth_attempts >= self._max_os_auth_attempts:
            # Automatically show Firebase password dialog
            self._authenticate_with_firebase()
            return
        
        if not WindowsAuth.is_available():
            self._show_error(theme_manager.t("windows_auth_not_available"))
            return
        
        # Increment attempt counter
        self._os_auth_attempts += 1
        
        # Add delay before authentication (except for first attempt)
        if self._os_auth_attempts > 1:
            # Run authentication with delay in background thread
            self._auth_in_progress = True
            thread = threading.Thread(
                target=self._authenticate_with_delay,
                daemon=True
            )
            thread.start()
        else:
            # First attempt, no delay
            self._perform_os_authentication()
    
    def _authenticate_with_delay(self):
        """Perform authentication with delay in background thread."""
        try:
            # Wait for delay
            time.sleep(self._os_auth_delay_seconds)
            
            # Perform authentication on main thread
            if self.page:
                self.page.run(self._perform_os_authentication)
            else:
                self._perform_os_authentication()
        except Exception as ex:
            logger.error(f"Error in authentication delay thread: {ex}")
            self._auth_in_progress = False
    
    def _perform_os_authentication(self):
        """Perform OS authentication."""
        try:
            self._auth_in_progress = True
            
            success, error = WindowsAuth.authenticate(
                message=theme_manager.t("authenticate_to_access_security"),
                title=theme_manager.t("security_authentication")
            )
            
            if success:
                # Reset counter on success
                self._os_auth_attempts = 0
                self._authenticated = True
                self.encryption_switch.disabled = False
                self._update_ui()
                self._show_success(theme_manager.t("authentication_successful"))
            else:
                # Show error with remaining attempts
                remaining = self._max_os_auth_attempts - self._os_auth_attempts
                if remaining > 0:
                    error_msg = f"{error or theme_manager.t('authentication_failed')} ({remaining} attempts remaining)"
                    self._show_error(error_msg)
                    self._update_attempt_info()
                else:
                    # Max attempts reached, show Firebase password option
                    self._show_error(theme_manager.t("max_os_auth_attempts_reached") or "Maximum OS authentication attempts reached. Please use Firebase password.")
                    self._update_attempt_info()
                    # Automatically show Firebase password dialog
                    if self.page:
                        self.page.run(lambda _: self._authenticate_with_firebase())
        finally:
            self._auth_in_progress = False
    
    def _update_attempt_info(self):
        """Update attempt info text in lock overlay."""
        if self._os_auth_attempts >= self._max_os_auth_attempts:
            # Show Firebase password button
            if hasattr(self, 'firebase_auth_btn'):
                self.firebase_auth_btn.visible = True
            if hasattr(self, 'attempt_info_text'):
                self.attempt_info_text.value = theme_manager.t("use_firebase_password_fallback") or "OS authentication failed. Please use your Firebase password."
                self.attempt_info_text.visible = True
        elif self._os_auth_attempts > 0:
            # Show remaining attempts
            remaining = self._max_os_auth_attempts - self._os_auth_attempts
            if hasattr(self, 'attempt_info_text'):
                self.attempt_info_text.value = f"{remaining} attempts remaining before Firebase password option"
                self.attempt_info_text.visible = True
            if hasattr(self, 'firebase_auth_btn'):
                self.firebase_auth_btn.visible = False
        else:
            # Hide attempt info
            if hasattr(self, 'attempt_info_text'):
                self.attempt_info_text.visible = False
            if hasattr(self, 'firebase_auth_btn'):
                self.firebase_auth_btn.visible = False
        
        if self.page:
            self.page.update()
    
    def _authenticate_with_firebase(self, e=None):
        """Handle Firebase password authentication fallback."""
        # Get current user email
        current_user = auth_service.get_current_user()
        if not current_user:
            self._show_error(theme_manager.t("user_not_logged_in") or "You must be logged in to use Firebase password authentication.")
            return
        
        email = current_user.get('email')
        if not email:
            self._show_error(theme_manager.t("user_email_not_found") or "User email not found. Please log in again.")
            return
        
        # Show Firebase password dialog
        from ui.dialogs.firebase_password_dialog import FirebasePasswordDialog
        
        message = theme_manager.t("firebase_password_fallback_message") or "OS authentication failed. Please enter your Firebase password to access security settings."
        dialog = FirebasePasswordDialog(
            email=email,
            message=message,
            on_submit=self._handle_firebase_auth,
            on_cancel=self._handle_firebase_auth_cancel
        )
        dialog.page = self.page
        if self.page:
            self.page.open(dialog)
    
    def _handle_firebase_auth(self, password: str):
        """Handle Firebase password authentication."""
        try:
            # Get current user email
            current_user = auth_service.get_current_user()
            if not current_user:
                self._show_error(theme_manager.t("user_not_logged_in") or "You must be logged in to use Firebase password authentication.")
                return
            
            email = current_user.get('email')
            if not email:
                self._show_error(theme_manager.t("user_email_not_found") or "User email not found. Please log in again.")
                return
            
            # Verify password using Firebase REST API
            success, error, token = auth_service.authenticate_with_email_password(email, password)
            
            if success:
                # Reset OS auth attempt counter
                self._os_auth_attempts = 0
                self._authenticated = True
                self.encryption_switch.disabled = False
                self._update_ui()
                self._update_attempt_info()
                self._show_success(theme_manager.t("firebase_authentication_successful") or "Firebase authentication successful")
            else:
                self._show_error(error or theme_manager.t("firebase_authentication_failed") or "Firebase authentication failed")
        except Exception as ex:
            logger.error(f"Firebase authentication error: {ex}")
            self._show_error(f"Authentication error: {str(ex)}")
    
    def _handle_firebase_auth_cancel(self):
        """Handle Firebase authentication cancellation."""
        # Do nothing, user cancelled
        pass
    
    def build(self) -> ft.Container:
        """Build the security tab."""
        # Privacy disclaimer card (always visible, not covered by auth)
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
        
        # PIN Recovery section (only show if PIN is enabled)
        pin_recovery_card = None
        if self.current_settings.pin_enabled and self.current_settings.encrypted_pin:
            masked_json = self._get_masked_json()
            self.pin_recovery_json_field.value = masked_json
            
            pin_recovery_card = theme_manager.create_card(
                content=ft.Column([
                    ft.Text(
                        theme_manager.t("pin_recovery") or "PIN Recovery",
                        size=18,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Divider(),
                    ft.Text(
                        theme_manager.t("pin_recovery_info") or "Export device information and encrypted PIN for PIN recovery",
                        size=12,
                        color=theme_manager.text_secondary_color
                    ),
                    self.pin_recovery_json_field,
                    ft.Row([
                        self.copy_pin_recovery_btn
                    ], alignment=ft.MainAxisAlignment.END)
                ], spacing=15)
            )
        
        # Protected content (covered by auth overlay)
        protected_content_items = [
            db_path_card,
            encryption_card,
            self.error_text,
            self.success_text
        ]
        
        # Add PIN recovery card if available
        if pin_recovery_card:
            protected_content_items.insert(2, pin_recovery_card)  # Insert after encryption_card
        
        protected_content = ft.Column(
            protected_content_items,
            scroll=ft.ScrollMode.AUTO,
            spacing=15,
            expand=True
        )
        
        # Create lock overlay container with visual blur effect
        # Since Flet doesn't support native blur filters, we use a high-opacity
        # overlay with a frosted glass effect to obscure the background
        self.lock_overlay_container = ft.Container(
            content=ft.Stack([
                # Frosted glass effect layer - high opacity overlay
                # This creates a visual "blur" by making background less visible
                ft.Container(
                    expand=True,
                    # Use high opacity to obscure background (creates blur-like effect)
                    bgcolor=ft.Colors.with_opacity(0.92, ft.Colors.BLACK),
                    # Add subtle gradient for depth
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=[
                            ft.Colors.with_opacity(0.95, ft.Colors.BLACK),
                            ft.Colors.with_opacity(0.90, ft.Colors.BLACK),
                            ft.Colors.with_opacity(0.92, ft.Colors.BLACK),
                        ],
                        stops=[0.0, 0.5, 1.0]
                    )
                ),
                # Lock overlay content centered on top
                ft.Container(
                    content=self.lock_overlay,
                    alignment=ft.alignment.center,
                    expand=True
                )
            ]),
            expand=True,
            visible=not self._authenticated
        )
        
        # Stack for protected content with overlay
        protected_stack = ft.Stack([
            protected_content,
            self.lock_overlay_container
        ], expand=True)
        
        # Main content: disclaimer (always visible) + protected content (with overlay)
        main_content = ft.Column([
            disclaimer_card,
            protected_stack
        ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)
        
        return ft.Container(
            content=main_content,
            padding=10,
            expand=True
        )
    
    def _update_ui(self):
        """Update UI after authentication."""
        # Update lock overlay visibility
        if hasattr(self, 'lock_overlay_container') and self.lock_overlay_container:
            self.lock_overlay_container.visible = not self._authenticated
        
        # Reset attempt info if authenticated
        if self._authenticated:
            self._os_auth_attempts = 0
            self._update_attempt_info()
        
        # Enable/disable controls based on authentication
        if hasattr(self, 'encryption_switch'):
            self.encryption_switch.disabled = not self._authenticated
        if hasattr(self, 'reveal_key_btn'):
            self.reveal_key_btn.disabled = not self._authenticated
        if hasattr(self, 'change_key_btn'):
            self.change_key_btn.disabled = not self._authenticated
        if hasattr(self, 'change_path_btn'):
            self.change_path_btn.disabled = not self._authenticated
        if hasattr(self, 'copy_pin_recovery_btn'):
            self.copy_pin_recovery_btn.disabled = not self._authenticated
        
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
        
        # Update PIN recovery field if PIN is enabled
        if hasattr(self, 'pin_recovery_json_field'):
            if new_settings.pin_enabled and new_settings.encrypted_pin:
                masked_json = self._get_masked_json()
                self.pin_recovery_json_field.value = masked_json
            else:
                self.pin_recovery_json_field.value = ""
        
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
    
    def _get_pin_recovery_data(self) -> dict:
        """Generate JSON with device info, user ID, and user-encrypted PIN."""
        # Get or create user-encrypted PIN
        user_encrypted_pin = get_or_create_user_encrypted_pin(self.db_manager)
        
        # Get Firebase user ID
        from services.auth_service import auth_service
        current_user = auth_service.get_current_user()
        user_id = current_user.get('uid') if current_user else ""
        
        return {
            "hostname": platform.node(),
            "machine": platform.machine(),
            "system": platform.system(),
            "user_id": user_id,
            "encrypted_pin": user_encrypted_pin or ""
        }
    
    def _get_masked_json(self) -> str:
        """Return JSON with values masked using asterisks."""
        data = self._get_pin_recovery_data()
        
        # Store full data for copying
        self._pin_recovery_json_data = json.dumps(data, indent=2)
        
        # Create masked version
        masked_data = {
            "hostname": "*" * len(str(data["hostname"])) if data["hostname"] else "",
            "machine": "*" * len(str(data["machine"])) if data["machine"] else "",
            "system": "*" * len(str(data["system"])) if data["system"] else "",
            "user_id": "*" * len(str(data["user_id"])) if data["user_id"] else "",
            "encrypted_pin": "*" * len(str(data["encrypted_pin"])) if data["encrypted_pin"] else ""
        }
        
        return json.dumps(masked_data, indent=2)
    
    def _copy_pin_recovery_data(self, e):
        """Copy full PIN recovery JSON to clipboard."""
        if not self._authenticated:
            self._authenticate(e)
            return
        
        # Check if PIN is enabled
        if not self.current_settings.pin_enabled or not self.current_settings.encrypted_pin:
            self._show_error(theme_manager.t("pin_recovery_not_available") or "PIN recovery is only available when PIN is enabled")
            return
        
        # Get full JSON data
        if not self._pin_recovery_json_data:
            data = self._get_pin_recovery_data()
            self._pin_recovery_json_data = json.dumps(data, indent=2)
        
        # Copy to clipboard
        if self.page:
            try:
                self.page.set_clipboard(self._pin_recovery_json_data)
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("pin_recovery_data_copied") or "PIN recovery data copied to clipboard",
                    bgcolor=ft.Colors.GREEN
                )
            except Exception as ex:
                logger.error(f"Failed to copy PIN recovery data to clipboard: {ex}")
                self._show_error("Failed to copy to clipboard")
    
    def _on_encryption_switch_changed(self, e):
        """Handle encryption switch change."""
        if not self._authenticated:
            # Revert switch if not authenticated
            self.encryption_switch.value = self.current_settings.encryption_enabled
            if self.page:
                self.page.update()
            return
        
        new_value = self.encryption_switch.value
        
        # If switching from False to True (enabling encryption)
        if new_value and not self.current_settings.encryption_enabled:
            self._handle_enable_encryption()
        # If switching from True to False (disabling encryption)
        elif not new_value and self.current_settings.encryption_enabled:
            self._handle_disable_encryption()
    
    def _handle_enable_encryption(self):
        """Handle enabling encryption - show confirmation dialog with statistics."""
        # Check if user is authenticated (required for encryption)
        from services.auth_service import auth_service
        if not auth_service.get_current_user():
            self._show_error(theme_manager.t("user_not_logged_in") or "You must be logged in to enable encryption")
            self.encryption_switch.value = False
            if self.page:
                self.page.update()
            return
        
        # Get database path
        db_path = self._get_database_path()
        
        # Load encryption statistics
        from services.database.encryption_stats_service import EncryptionStatsService
        stats_service = EncryptionStatsService(db_path)
        stats = stats_service.get_encryption_statistics()
        
        # Show enable encryption dialog
        from ui.dialogs.enable_encryption_dialog import EnableEncryptionDialog
        
        def on_start():
            """Handle Start button - run migration."""
            self._run_encryption_migration(db_path)
        
        def on_cancel():
            """Handle Cancel - revert switch."""
            self.encryption_switch.value = False
            if self.page:
                self.page.update()
        
        dialog = EnableEncryptionDialog(
            stats=stats,
            on_start=on_start,
            on_cancel=on_cancel
        )
        dialog.page = self.page
        if self.page:
            self.page.open(dialog)
    
    def _handle_disable_encryption(self):
        """Handle disabling encryption - show confirmation."""
        from ui.dialogs.dialog import DialogManager
        
        def on_confirm(confirm_e=None):
            """Disable encryption."""
            if app_settings.disable_field_encryption():
                self.current_settings.encryption_enabled = False
                self.encryption_switch.value = False
                self._show_success(theme_manager.t("encryption_disabled") or "Encryption disabled")
                self.on_settings_changed()
            else:
                self._show_error(theme_manager.t("failed_to_disable_encryption") or "Failed to disable encryption")
                self.encryption_switch.value = True
                if self.page:
                    self.page.update()
        
        DialogManager.show_confirmation_dialog(
            page=self.page,
            title=theme_manager.t("disable_encryption_title") or "Disable Encryption",
            message=theme_manager.t("disable_encryption_message") or 
                   "Are you sure you want to disable field-level encryption? "
                   "Note: This will not decrypt existing encrypted data.",
            on_confirm=on_confirm,
            on_cancel=lambda: setattr(self.encryption_switch, 'value', True) or self.page.update() if self.page else None
        )
    
    def _run_encryption_migration(self, db_path: str):
        """Run encryption migration with progress dialog."""
        from database.migrations.migrate_to_field_encryption import FieldEncryptionMigration
        from ui.dialogs.encryption_migration_progress_dialog import EncryptionMigrationProgressDialog
        import threading
        
        # Enable encryption in settings first
        if not app_settings.enable_field_encryption():
            self._show_error(theme_manager.t("failed_to_enable_encryption") or "Failed to enable encryption")
            self.encryption_switch.value = False
            if self.page:
                self.page.update()
            return
        
        # Show progress dialog
        progress_dialog = EncryptionMigrationProgressDialog()
        progress_dialog.page = self.page
        if self.page:
            self.page.open(progress_dialog)
        
        # Track total encrypted count
        total_encrypted = [0]
        
        def progress_callback(stage: str, current: int, total: int):
            """Update progress dialog."""
            # Count encrypted records (approximate - just for display)
            if current == total:
                total_encrypted[0] += total
            
            if self.page:
                try:
                    progress_dialog.update_progress(
                        stage, current, total, total_encrypted[0] if current == total else None
                    )
                except Exception:
                    pass  # Dialog might be closed
        
        def run_migration():
            """Run migration in background thread."""
            try:
                migration = FieldEncryptionMigration(db_path)
                success = migration.run(progress_callback=progress_callback)
                
                # Update UI on main thread
                if self.page:
                    # Close progress dialog
                    try:
                        self.page.close(progress_dialog)
                    except Exception:
                        pass
                    
                    if success:
                        # Update settings
                        self.current_settings.encryption_enabled = True
                        self.encryption_switch.value = True
                        self._show_success(
                            theme_manager.t("encryption_migration_complete") or 
                            "Encryption enabled successfully"
                        )
                        self.on_settings_changed()
                    else:
                        # Revert switch and disable encryption
                        app_settings.disable_field_encryption()
                        self.current_settings.encryption_enabled = False
                        self.encryption_switch.value = False
                        self._show_error(
                            theme_manager.t("encryption_migration_failed") or 
                            "Encryption migration failed. Please check logs for details."
                        )
                    
                    # Update page UI
                    self.page.update()
            except Exception as ex:
                logger.error(f"Migration error: {ex}")
                if self.page:
                    try:
                        self.page.close(progress_dialog)
                    except Exception:
                        pass
                    app_settings.disable_field_encryption()
                    self.current_settings.encryption_enabled = False
                    self.encryption_switch.value = False
                    self._show_error(
                        theme_manager.t("encryption_migration_failed") or 
                        f"Migration failed: {str(ex)}"
                    )
                    self.page.update()
        
        # Run migration in background thread
        thread = threading.Thread(target=run_migration, daemon=True)
        thread.start()
    
    def _get_database_path(self) -> str:
        """Get current database path."""
        # Check if user is logged in and use their database path
        try:
            from services.auth_service import auth_service
            user_db_path = auth_service.get_user_database_path()
            if user_db_path:
                return user_db_path
        except Exception:
            pass
        
        # Fallback to settings path or default
        return self.current_settings.db_path or DATABASE_PATH

