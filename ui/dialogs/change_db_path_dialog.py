"""
Dialog for changing database path.
"""

import flet as ft
from pathlib import Path
from typing import Optional, Callable
from ui.theme import theme_manager
from services.database.db_migration_service import DatabaseMigrationService


class ChangeDbPathDialog(ft.AlertDialog):
    """Dialog for changing database path."""
    
    def __init__(
        self,
        current_path: str,
        on_confirm: Optional[Callable[[str], None]] = None
    ):
        self.current_path = current_path
        self.on_confirm_callback = on_confirm
        self.selected_path: Optional[str] = None
        
        # Path display
        self.path_display = ft.Text(
            current_path,
            size=12,
            color=theme_manager.text_secondary_color,
            selectable=True
        )
        
        # Browse button
        self.browse_btn = ft.ElevatedButton(
            text=theme_manager.t("browse"),
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._browse_path
        )
        
        # New path field
        self.new_path_field = theme_manager.create_text_field(
            label=theme_manager.t("new_database_path"),
            hint_text=theme_manager.t("enter_path_or_browse"),
            value=current_path
        )
        
        # Migration info
        self.migration_info = ft.Text(
            theme_manager.t("database_migration_info"),
            size=12,
            color=theme_manager.text_secondary_color
        )
        
        # Error text
        self.error_text = ft.Text("", color=ft.Colors.RED, visible=False)
        
        super().__init__(
            title=ft.Text(theme_manager.t("change_database_path")),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        theme_manager.t("current_database_path"),
                        size=14,
                        weight=ft.FontWeight.BOLD
                    ),
                    self.path_display,
                    ft.Divider(),
                    ft.Text(
                        theme_manager.t("new_database_path"),
                        size=14,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Row([
                        self.new_path_field,
                        self.browse_btn
                    ], spacing=10),
                    self.migration_info,
                    self.error_text
                ], spacing=15, tight=True),
                width=500,
                padding=10
            ),
            actions=[
                ft.TextButton(
                    text=theme_manager.t("cancel"),
                    on_click=self._on_cancel
                ),
                ft.TextButton(
                    text=theme_manager.t("confirm"),
                    on_click=self._on_confirm
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True
        )
    
    def _browse_path(self, e):
        """Browse for directory."""
        # Note: Flet doesn't have native directory picker in all platforms
        # This is a placeholder - in production, you might need platform-specific implementation
        if self.page:
            # For now, just show a message
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("enter_path_manually"),
                bgcolor=ft.Colors.ORANGE
            )
    
    def _on_confirm(self, e):
        """Handle confirm button click."""
        new_path = self.new_path_field.value or ""
        
        if not new_path:
            self._show_error(theme_manager.t("database_path_required"))
            return
        
        # Validate path
        is_valid, error = DatabaseMigrationService.validate_path(new_path)
        if not is_valid:
            self._show_error(error or theme_manager.t("invalid_database_path"))
            return
        
        # Check if path is different
        if new_path == self.current_path:
            self._show_error(theme_manager.t("path_unchanged"))
            return
        
        # Call callback
        if self.on_confirm_callback:
            self.on_confirm_callback(new_path)
        
        # Close dialog
        if self.page:
            self.page.close(self)
    
    def _on_cancel(self, e):
        """Handle cancel button click."""
        if self.page:
            self.page.close(self)
    
    def _show_error(self, message: str):
        """Show error message."""
        self.error_text.value = message
        self.error_text.visible = True
        if self.page:
            self.page.update()

