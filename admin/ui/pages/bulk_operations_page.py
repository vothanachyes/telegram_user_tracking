"""
Admin bulk operations page.
"""

import flet as ft
import threading
from datetime import datetime
from pathlib import Path
from admin.services.admin_backup_service import admin_backup_service


class AdminBulkOperationsPage(ft.Container):
    """Admin bulk operations page."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    ERROR_COLOR = "#f44336"
    SUCCESS_COLOR = "#4caf50"
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.file_picker = None
        self.backup_button = None
        self.progress_bar = None
        self.status_text = None
        self.is_backing_up = False
        
        # Initialize file picker
        self._init_file_picker()
        
        # Build UI
        super().__init__(
            content=self._build_content(),
            padding=ft.padding.all(20),
            bgcolor=self.BG_COLOR,
            expand=True,
        )
    
    def _init_file_picker(self):
        """Initialize file picker for saving backup."""
        self.file_picker = ft.FilePicker(
            on_result=self._on_file_picked,
        )
        if self.file_picker not in self.page.overlay:
            self.page.overlay.append(self.file_picker)
        self.file_picker.page = self.page
    
    def _build_content(self) -> ft.Column:
        """Build page content."""
        # Backup section
        backup_section = self._build_backup_section()
        
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            "Bulk Operations",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=self.TEXT_COLOR,
                        ),
                    ],
                ),
                ft.Divider(height=20, color="transparent"),
                backup_section,
            ],
            spacing=10,
            expand=True,
        )
    
    def _build_backup_section(self) -> ft.Container:
        """Build Firebase backup section."""
        # Title
        title = ft.Text(
            "Firebase Backup",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=self.TEXT_COLOR,
        )
        
        # Description
        description = ft.Text(
            "Create a complete backup of all Firebase data including Firestore collections and Firebase Auth users. "
            "The backup will be saved as a ZIP file containing separate JSON files for each collection.",
            size=12,
            color=self.TEXT_SECONDARY,
            width=800,
        )
        
        # Backup button
        self.backup_button = ft.ElevatedButton(
            text="Backup All Data",
            icon=ft.Icons.BACKUP,
            on_click=self._on_backup_clicked,
            disabled=False,
            bgcolor=self.PRIMARY_COLOR,
            color="#ffffff",
        )
        
        # Progress bar
        self.progress_bar = ft.ProgressBar(
            value=0,
            width=800,
            visible=False,
            color=self.PRIMARY_COLOR,
        )
        
        # Status text
        self.status_text = ft.Text(
            "",
            size=12,
            color=self.TEXT_SECONDARY,
            width=800,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    title,
                    ft.Divider(height=10, color="transparent"),
                    description,
                    ft.Divider(height=20, color="transparent"),
                    self.backup_button,
                    ft.Divider(height=10, color="transparent"),
                    self.progress_bar,
                    self.status_text,
                ],
                spacing=5,
            ),
            padding=ft.padding.all(20),
            border=ft.border.all(1, "#333333"),
            border_radius=5,
        )
    
    def _on_backup_clicked(self, e):
        """Handle backup button click."""
        if self.is_backing_up:
            return
        
        # Generate default filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"firebase_backup_{timestamp}.zip"
        
        # Open file save dialog
        self.file_picker.save_file(
            dialog_title="Save Backup File",
            file_name=default_filename,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["zip"],
        )
    
    def _on_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file picker result."""
        if e.path is None:
            # User cancelled
            return
        
        # Start backup in background thread
        self._start_backup(e.path)
    
    def _start_backup(self, output_path: str):
        """Start backup process in background thread."""
        if self.is_backing_up:
            return
        
        self.is_backing_up = True
        self.backup_button.disabled = True
        self.progress_bar.visible = True
        self.progress_bar.value = 0
        self.status_text.value = "Initializing backup..."
        self.status_text.color = self.TEXT_SECONDARY
        self.page.update()
        
        # Run backup in background thread
        thread = threading.Thread(
            target=self._run_backup,
            args=(output_path,),
            daemon=True,
        )
        thread.start()
    
    def _run_backup(self, output_path: str):
        """Run backup process (called from background thread)."""
        try:
            total_collections = 9  # Total number of collections to backup
            current_collection = 0
            
            def progress_callback(collection_name: str, status: str):
                """Progress callback for backup service."""
                nonlocal current_collection
                
                if status == "starting":
                    self.status_text.value = f"Backing up {collection_name}..."
                    self.status_text.color = self.TEXT_SECONDARY
                    self.page.update()
                
                elif status == "completed":
                    current_collection += 1
                    progress = current_collection / total_collections
                    self.progress_bar.value = progress
                    self.status_text.value = f"Completed {collection_name} ({current_collection}/{total_collections})"
                    self.status_text.color = self.TEXT_SECONDARY
                    self.page.update()
                
                elif status == "error":
                    current_collection += 1
                    progress = current_collection / total_collections
                    self.progress_bar.value = progress
                    self.status_text.value = f"Error backing up {collection_name} (continuing...)"
                    self.status_text.color = self.ERROR_COLOR
                    self.page.update()
                
                elif status == "creating_zip":
                    self.status_text.value = "Creating ZIP file..."
                    self.status_text.color = self.TEXT_SECONDARY
                    self.page.update()
            
            # Perform backup
            success, metadata = admin_backup_service.backup_all_collections(
                output_path,
                progress_callback=progress_callback,
            )
            
            # Update UI (Flet's page.update() is thread-safe)
            self._on_backup_complete(success, output_path, metadata)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error during backup: {e}", exc_info=True)
            self._on_backup_error(str(e))
    
    def _on_backup_complete(self, success: bool, output_path: str, metadata: dict):
        """Handle backup completion."""
        self.is_backing_up = False
        self.backup_button.disabled = False
        self.progress_bar.value = 1.0 if success else 0
        
        if success:
            # Show success message
            file_path = Path(output_path)
            self.status_text.value = f"Backup completed successfully! Saved to: {file_path.name}"
            self.status_text.color = self.SUCCESS_COLOR
            
            # Show snackbar
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Backup saved to: {file_path}"),
                bgcolor=self.SUCCESS_COLOR,
            )
            self.page.snack_bar.open = True
            
        else:
            # Show error message
            self.status_text.value = "Backup failed. Check logs for details."
            self.status_text.color = self.ERROR_COLOR
            
            # Show snackbar
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Backup failed. Check logs for details."),
                bgcolor=self.ERROR_COLOR,
            )
            self.page.snack_bar.open = True
        
        self.page.update()
    
    def _on_backup_error(self, error_message: str):
        """Handle backup error."""
        self.is_backing_up = False
        self.backup_button.disabled = False
        self.progress_bar.value = 0
        self.status_text.value = f"Backup error: {error_message}"
        self.status_text.color = self.ERROR_COLOR
        
        # Show snackbar
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Backup error: {error_message}"),
            bgcolor=self.ERROR_COLOR,
        )
        self.page.snack_bar.open = True
        
        self.page.update()

