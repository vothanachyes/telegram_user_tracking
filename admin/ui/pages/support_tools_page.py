"""
Admin support tools page for decryption operations.
"""

import flet as ft
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
from admin.services.admin_decryption_service import admin_decryption_service

logger = logging.getLogger(__name__)


class AdminSupportToolsPage(ft.Container):
    """Admin support tools page for database and PIN decryption."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    CARD_BG = "#252525"
    BORDER_COLOR = "#333333"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    ERROR_COLOR = "#f44336"
    SUCCESS_COLOR = "#4caf50"
    
    def __init__(self, page: ft.Page):
        self.page = page
        
        # File pickers
        self.db_file_picker = ft.FilePicker(
            on_result=self._on_db_file_picked
        )
        self.output_dir_picker = ft.FilePicker(
            on_result=self._on_output_dir_picked
        )
        
        # Add file pickers to page overlay
        if not hasattr(self.page, 'overlay') or self.page.overlay is None:
            self.page.overlay = []
        self.page.overlay.append(self.db_file_picker)
        self.page.overlay.append(self.output_dir_picker)
        
        # Database decryption section
        self._build_database_section()
        
        # PIN decryption section
        self._build_pin_section()
        
        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Support Tools",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=self.TEXT_COLOR,
                    ),
                    ft.Divider(height=20, color="transparent"),
                    self.database_section,
                    ft.Divider(height=30, color="transparent"),
                    self.pin_section,
                ],
                spacing=10,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=ft.padding.all(20),
            bgcolor=self.BG_COLOR,
            expand=True,
        )
    
    def _build_database_section(self):
        """Build database decryption section."""
        # Input database file
        self.db_file_path_field = ft.TextField(
            label="Input Database File",
            hint_text="Select encrypted database file",
            read_only=True,
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            expand=True,
        )
        
        self.db_file_picker_btn = ft.ElevatedButton(
            text="Browse",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._on_browse_db_file,
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
        )
        
        # Device info - JSON input
        self.device_info_json_field = ft.TextField(
            label="Device Information (JSON)",
            hint_text='{"hostname": "DESKTOP-ABC", "machine": "AMD64", "system": "Windows"}',
            multiline=True,
            min_lines=3,
            max_lines=5,
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        # Device info - Individual fields
        self.hostname_field = ft.TextField(
            label="Hostname",
            hint_text="platform.node()",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.machine_field = ft.TextField(
            label="Machine Type",
            hint_text="platform.machine()",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.system_field = ft.TextField(
            label="Operating System",
            hint_text="platform.system()",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        # Toggle between JSON and fields
        self.use_json_switch = ft.Switch(
            label="Use JSON input",
            value=True,
            on_change=self._on_toggle_json_input,
        )
        
        # Output directory
        self.output_dir_field = ft.TextField(
            label="Output Directory",
            hint_text="Select or enter output directory for decrypted database",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            expand=True,
            on_change=lambda e: self._update_decrypt_button_state(),
        )
        
        self.output_dir_picker_btn = ft.ElevatedButton(
            text="Browse",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._on_browse_output_dir,
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
        )
        
        # Output filename
        self.output_filename_field = ft.TextField(
            label="Output Filename",
            hint_text="decrypted_database.db",
            value=f"decrypted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            on_change=lambda e: self._update_decrypt_button_state(),
        )
        
        # Decrypt button
        self.decrypt_db_btn = ft.ElevatedButton(
            text="Decrypt Database",
            icon=ft.Icons.LOCK_OPEN,
            on_click=self._on_decrypt_database,
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
            disabled=True,
        )
        
        # Progress indicator
        self.db_progress = ft.ProgressBar(
            width=400,
            visible=False,
        )
        
        self.db_status_text = ft.Text(
            "",
            color=self.TEXT_SECONDARY,
            visible=False,
        )
        
        # Device info container (JSON or fields)
        self.device_info_container = ft.Container(
            content=self.device_info_json_field,
        )
        
        self.database_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Database Decryption",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=self.TEXT_COLOR,
                    ),
                    ft.Divider(),
                    ft.Row(
                        controls=[
                            self.db_file_path_field,
                            self.db_file_picker_btn,
                        ],
                        spacing=10,
                    ),
                    ft.Divider(height=10, color="transparent"),
                    self.use_json_switch,
                    self.device_info_container,
                    ft.Divider(height=10, color="transparent"),
                    ft.Row(
                        controls=[
                            self.output_dir_field,
                            self.output_dir_picker_btn,
                        ],
                        spacing=10,
                    ),
                    self.output_filename_field,
                    ft.Divider(height=10, color="transparent"),
                    self.decrypt_db_btn,
                    self.db_progress,
                    self.db_status_text,
                ],
                spacing=10,
            ),
            bgcolor=self.CARD_BG,
            padding=20,
            border_radius=8,
        )
    
    def _build_pin_section(self):
        """Build PIN decryption section."""
        # PIN recovery data - JSON input
        self.pin_json_field = ft.TextField(
            label="PIN Recovery Data (JSON)",
            hint_text='{"hostname": "...", "machine": "...", "system": "...", "user_id": "...", "encrypted_pin": "..."}',
            multiline=True,
            min_lines=5,
            max_lines=8,
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        # Individual fields for PIN
        self.pin_hostname_field = ft.TextField(
            label="Hostname",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.pin_machine_field = ft.TextField(
            label="Machine Type",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.pin_system_field = ft.TextField(
            label="Operating System",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.pin_user_id_field = ft.TextField(
            label="User ID (Firebase UID)",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        self.pin_encrypted_field = ft.TextField(
            label="Encrypted PIN",
            multiline=True,
            min_lines=2,
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
        )
        
        # Toggle for PIN
        self.pin_use_json_switch = ft.Switch(
            label="Use JSON input",
            value=True,
            on_change=self._on_toggle_pin_json_input,
        )
        
        # Decrypt PIN button
        self.decrypt_pin_btn = ft.ElevatedButton(
            text="Decrypt PIN",
            icon=ft.Icons.LOCK_OPEN,
            on_click=self._on_decrypt_pin,
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
        )
        
        # PIN result
        self.pin_result_field = ft.TextField(
            label="Decrypted PIN",
            read_only=True,
            bgcolor=self.CARD_BG,
            color=self.SUCCESS_COLOR,
            border_color=self.BORDER_COLOR,
            visible=False,
        )
        
        # PIN info container
        self.pin_info_container = ft.Container(
            content=self.pin_json_field,
        )
        
        self.pin_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "PIN Decryption",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=self.TEXT_COLOR,
                    ),
                    ft.Divider(),
                    self.pin_use_json_switch,
                    self.pin_info_container,
                    ft.Divider(height=10, color="transparent"),
                    self.decrypt_pin_btn,
                    self.pin_result_field,
                ],
                spacing=10,
            ),
            bgcolor=self.CARD_BG,
            padding=20,
            border_radius=8,
        )
    
    def _on_toggle_json_input(self, e):
        """Toggle between JSON and individual fields for device info."""
        if self.use_json_switch.value:
            self.device_info_container.content = self.device_info_json_field
        else:
            self.device_info_container.content = ft.Column(
                controls=[
                    self.hostname_field,
                    self.machine_field,
                    self.system_field,
                ],
                spacing=10,
            )
        self.page.update()
    
    def _on_toggle_pin_json_input(self, e):
        """Toggle between JSON and individual fields for PIN."""
        if self.pin_use_json_switch.value:
            self.pin_info_container.content = self.pin_json_field
        else:
            self.pin_info_container.content = ft.Column(
                controls=[
                    self.pin_hostname_field,
                    self.pin_machine_field,
                    self.pin_system_field,
                    self.pin_user_id_field,
                    self.pin_encrypted_field,
                ],
                spacing=10,
            )
        self.page.update()
    
    def _on_browse_db_file(self, e):
        """Handle browse database file button click."""
        try:
            self.db_file_picker.pick_files(
                dialog_title="Select Encrypted Database File",
                allowed_extensions=["db"],
                file_type=ft.FilePickerFileType.CUSTOM,
            )
        except Exception as ex:
            logger.error(f"Error opening file picker: {ex}")
            self._show_error(f"Failed to open file picker: {str(ex)}")
    
    def _on_db_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle database file picker result."""
        if e.files and len(e.files) > 0:
            self.db_file_path_field.value = e.files[0].path
            self._update_decrypt_button_state()
            self.page.update()
    
    def _on_browse_output_dir(self, e):
        """Handle browse output directory button click."""
        try:
            # Flet doesn't have native directory picker on all platforms
            # Use file picker to select a file, then use its directory
            self.output_dir_picker.pick_files(
                dialog_title="Select any file in the output directory (directory will be used)",
                allowed_extensions=["*"],
                file_type=ft.FilePickerFileType.ANY,
            )
        except Exception as ex:
            logger.error(f"Error opening file picker: {ex}")
            self._show_error("Please enter the output directory path manually in the text field.")
    
    def _on_output_dir_picked(self, e: ft.FilePickerResultEvent):
        """Handle output directory picker result."""
        # Use selected file's directory as output directory
        if e.files and len(e.files) > 0:
            file_path = Path(e.files[0].path)
            self.output_dir_field.value = str(file_path.parent)
            self._update_decrypt_button_state()
            self.page.update()
    
    def _update_decrypt_button_state(self):
        """Update decrypt button enabled state."""
        has_db_file = bool(self.db_file_path_field.value)
        has_output_dir = bool(self.output_dir_field.value and self.output_dir_field.value.strip())
        has_output_filename = bool(self.output_filename_field.value and self.output_filename_field.value.strip())
        self.decrypt_db_btn.disabled = not (has_db_file and has_output_dir and has_output_filename)
    
    def _get_device_info(self) -> tuple:
        """Get device info from JSON or individual fields."""
        if self.use_json_switch.value:
            # Parse JSON
            json_text = self.device_info_json_field.value or ""
            if not json_text.strip():
                raise ValueError("Device information JSON is required")
            
            try:
                data = json.loads(json_text)
                hostname = data.get("hostname", "").strip()
                machine = data.get("machine", "").strip()
                system = data.get("system", "").strip()
                
                if not all([hostname, machine, system]):
                    raise ValueError("JSON must contain 'hostname', 'machine', and 'system' fields")
                
                return hostname, machine, system
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {e}")
        else:
            # Get from individual fields
            hostname = (self.hostname_field.value or "").strip()
            machine = (self.machine_field.value or "").strip()
            system = (self.system_field.value or "").strip()
            
            if not all([hostname, machine, system]):
                raise ValueError("All device information fields are required")
            
            return hostname, machine, system
    
    def _on_decrypt_database(self, e):
        """Handle decrypt database button click."""
        try:
            # Validate inputs
            if not self.db_file_path_field.value:
                self._show_error("Please select an input database file")
                return
            
            if not self.output_dir_field.value:
                self._show_error("Please select an output directory")
                return
            
            if not self.output_filename_field.value:
                self._show_error("Please enter an output filename")
                return
            
            # Get device info
            try:
                hostname, machine, system = self._get_device_info()
            except ValueError as ve:
                self._show_error(str(ve))
                return
            
            # Build output path
            output_dir = Path(self.output_dir_field.value)
            output_filename = self.output_filename_field.value
            if not output_filename.endswith('.db'):
                output_filename += '.db'
            output_path = output_dir / output_filename
            
            # Disable button and show progress
            self.decrypt_db_btn.disabled = True
            self.db_progress.visible = True
            self.db_status_text.value = "Decrypting database..."
            self.db_status_text.visible = True
            self.db_status_text.color = self.TEXT_SECONDARY
            self.page.update()
            
            # Run decryption in background thread
            def decrypt_thread():
                try:
                    success, error = admin_decryption_service.decrypt_database(
                        self.db_file_path_field.value,
                        str(output_path),
                        hostname,
                        machine,
                        system
                    )
                    
                    # Update UI on main thread
                    def update_ui():
                        self.decrypt_db_btn.disabled = False
                        self.db_progress.visible = False
                        
                        if success:
                            self.db_status_text.value = f"✓ Database decrypted successfully!\nSaved to: {output_path}"
                            self.db_status_text.color = self.SUCCESS_COLOR
                            self._show_success(f"Database decrypted successfully!\nSaved to: {output_path}")
                        else:
                            self.db_status_text.value = f"✗ Decryption failed: {error}"
                            self.db_status_text.color = self.ERROR_COLOR
                            self._show_error(f"Decryption failed: {error}")
                        
                        self.db_status_text.visible = True
                        self.page.update()
                    
                    self.page.run(update_ui)
                except Exception as ex:
                    logger.error(f"Error in decrypt thread: {ex}", exc_info=True)
                    def update_error():
                        self.decrypt_db_btn.disabled = False
                        self.db_progress.visible = False
                        self.db_status_text.value = f"✗ Error: {str(ex)}"
                        self.db_status_text.color = self.ERROR_COLOR
                        self.db_status_text.visible = True
                        self._show_error(f"Error: {str(ex)}")
                        self.page.update()
                    self.page.run(update_error)
            
            thread = threading.Thread(target=decrypt_thread, daemon=True)
            thread.start()
            
        except Exception as ex:
            logger.error(f"Error decrypting database: {ex}", exc_info=True)
            self._show_error(f"Error: {str(ex)}")
            self.decrypt_db_btn.disabled = False
            self.db_progress.visible = False
            self.page.update()
    
    def _get_pin_data(self) -> tuple:
        """Get PIN data from JSON or individual fields."""
        if self.pin_use_json_switch.value:
            json_text = self.pin_json_field.value or ""
            if not json_text.strip():
                raise ValueError("PIN recovery data JSON is required")
            
            try:
                data = json.loads(json_text)
                hostname = data.get("hostname", "").strip()
                machine = data.get("machine", "").strip()
                system = data.get("system", "").strip()
                user_id = data.get("user_id", "").strip()
                encrypted_pin = data.get("encrypted_pin", "").strip()
                
                if not all([hostname, machine, system, user_id, encrypted_pin]):
                    raise ValueError("JSON must contain 'hostname', 'machine', 'system', 'user_id', and 'encrypted_pin' fields")
                
                return hostname, machine, system, user_id, encrypted_pin
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {e}")
        else:
            hostname = (self.pin_hostname_field.value or "").strip()
            machine = (self.pin_machine_field.value or "").strip()
            system = (self.pin_system_field.value or "").strip()
            user_id = (self.pin_user_id_field.value or "").strip()
            encrypted_pin = (self.pin_encrypted_field.value or "").strip()
            
            if not all([hostname, machine, system, user_id, encrypted_pin]):
                raise ValueError("All PIN recovery data fields are required")
            
            return hostname, machine, system, user_id, encrypted_pin
    
    def _on_decrypt_pin(self, e):
        """Handle decrypt PIN button click."""
        try:
            # Get PIN data
            try:
                hostname, machine, system, user_id, encrypted_pin = self._get_pin_data()
            except ValueError as ve:
                self._show_error(str(ve))
                return
            
            # Decrypt PIN
            try:
                decrypted_pin = admin_decryption_service.decrypt_pin(
                    hostname, machine, system, user_id, encrypted_pin
                )
                
                # Show result
                self.pin_result_field.value = decrypted_pin
                self.pin_result_field.visible = True
                self._show_success(f"PIN decrypted successfully: {decrypted_pin}")
                self.page.update()
            except ValueError as ve:
                self._show_error(f"Decryption failed: {str(ve)}")
            except Exception as ex:
                logger.error(f"Error decrypting PIN: {ex}", exc_info=True)
                self._show_error(f"Error: {str(ex)}")
                
        except Exception as ex:
            logger.error(f"Error in decrypt PIN: {ex}", exc_info=True)
            self._show_error(f"Error: {str(ex)}")
    
    def _show_error(self, message: str):
        """Show error message."""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=self.ERROR_COLOR,
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _show_success(self, message: str):
        """Show success message."""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=self.SUCCESS_COLOR,
            )
            self.page.snack_bar.open = True
            self.page.update()

