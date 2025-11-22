"""
Data settings tab component for sample database management.
"""

import flet as ft
import logging
from typing import Optional, Callable
from database.db_manager import DatabaseManager
from ui.theme import theme_manager
from config.app_config import app_config
from ui.dialogs.sample_db_warning_dialog import SampleDbWarningDialog
from ui.dialogs import dialog_manager

logger = logging.getLogger(__name__)


class DataTab:
    """Data settings tab component for sample database management."""
    
    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        page: Optional[ft.Page] = None
    ):
        self.db_manager = db_manager
        self._page = page
        
        # Update UI based on current mode
        self._update_ui()
    
    @property
    def page(self) -> Optional[ft.Page]:
        """Get page reference."""
        return self._page
    
    @page.setter
    def page(self, value: Optional[ft.Page]):
        """Set page reference."""
        self._page = value
    
    def _update_ui(self):
        """Update UI components based on current sample_db mode."""
        is_sample_mode = app_config.is_sample_db_mode()
        
        # Current mode display
        self.mode_text = ft.Text(
            theme_manager.t("current_database_mode") or "Current Database Mode",
            size=16,
            weight=ft.FontWeight.BOLD
        )
        
        self.mode_status = ft.Text(
            theme_manager.t("sample_database") if is_sample_mode else theme_manager.t("production_database"),
            size=14,
            color=ft.Colors.GREEN if is_sample_mode else ft.Colors.BLUE
        )
        
        # Switch button
        self.switch_button = theme_manager.create_button(
            text=theme_manager.t("switch_to_sample_db") if not is_sample_mode else theme_manager.t("switch_to_production_db"),
            icon=ft.Icons.SWAP_HORIZ,
            on_click=self._on_switch_click,
            style="primary"
        )
        
        # Generate data button (only visible in sample_db mode)
        self.generate_button = theme_manager.create_button(
            text=theme_manager.t("generate_test_data") or "Generate Test Data",
            icon=ft.Icons.DATA_OBJECT,
            on_click=self._on_generate_click,
            style="success",
            visible=is_sample_mode
        )
        
        # Info message
        self.info_text = ft.Text(
            theme_manager.t("sample_db_warning_message") or 
            "Warning: Switching to sample database mode will disable real account login, logout functionality, and hide the Security tab. This mode is for testing data generation only.",
            size=12,
            color=theme_manager.text_secondary_color,
            visible=is_sample_mode
        )
    
    def build(self) -> ft.Container:
        """Build the data tab."""
        return ft.Container(
            content=ft.Column([
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Text(
                            theme_manager.t("sample_db_mode") or "Sample Database Mode",
                            size=20,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        self.mode_text,
                        self.mode_status,
                        ft.Divider(),
                        self.switch_button,
                        ft.Divider() if app_config.is_sample_db_mode() else ft.Container(),
                        self.generate_button,
                        self.info_text,
                    ], spacing=20)
                ),
            ], scroll=ft.ScrollMode.AUTO, spacing=20),
            padding=10,
            expand=True
        )
    
    def _on_switch_click(self, e):
        """Handle switch button click."""
        is_sample_mode = app_config.is_sample_db_mode()
        
        if not is_sample_mode:
            # Switching to sample_db mode - show warning
            self._show_switch_warning()
        else:
            # Switching back to production mode - show warning
            self._show_switch_back_warning()
    
    def _show_switch_warning(self):
        """Show warning dialog when switching to sample_db mode."""
        if not self.page:
            logger.error("No page available for warning dialog")
            return
        
        def on_confirm():
            """Handle confirmation - switch to sample_db mode."""
            try:
                app_config.set_sample_db_mode(True)
                # Show restart message
                dialog_manager.show_simple_dialog(
                    page=self.page,
                    title=theme_manager.t("sample_db_restart_required") or "Restart Required",
                    message=theme_manager.t("sample_db_restart_required") or 
                    "Please restart the application to complete the database switch.",
                    actions=[ft.TextButton(theme_manager.t("close") or "Close")]
                )
                # Update UI
                self._update_ui()
                if self.page:
                    self.page.update()
            except Exception as ex:
                logger.error(f"Error switching to sample_db mode: {ex}")
                theme_manager.show_snackbar(
                    self.page,
                    f"Error: {str(ex)}",
                    bgcolor=ft.Colors.RED
                )
        
        dialog = SampleDbWarningDialog(on_confirm=on_confirm)
        dialog.page = self.page
        
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening warning dialog: {ex}")
            # Fallback
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _show_switch_back_warning(self):
        """Show warning when switching back to production mode."""
        if not self.page:
            logger.error("No page available for warning dialog")
            return
        
        def on_confirm():
            """Handle confirmation - switch back to production mode and close app."""
            try:
                app_config.set_sample_db_mode(False)
                # Update UI before closing
                self._update_ui()
                if self.page:
                    self.page.update()
            except Exception as ex:
                logger.error(f"Error switching back to production mode: {ex}")
                theme_manager.show_snackbar(
                    self.page,
                    f"Error: {str(ex)}",
                    bgcolor=ft.Colors.RED
                )
                return
            
            # Close the application after saving settings
            self._close_application()
        
        # Use the same dialog pattern as switch-to-sample (with only Close App button)
        dialog = SampleDbWarningDialog(
            on_confirm=on_confirm,
            on_cancel=None
        )
        dialog.page = self.page
        
        # Update dialog title and message for switch-back context
        dialog.title = ft.Text(theme_manager.t("switch_to_production_db") or "Close Application?")
        dialog.content = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE, size=24),
                    ft.Text(
                        theme_manager.t("sample_db_switch_back_warning") or 
                        "Switching back to production database will restore all functionality. You need to close and restart the application for changes to take effect.",
                        size=14,
                        expand=True
                    )
                ], spacing=10)
            ], spacing=10, width=500),
            padding=10
        )
        
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening switch-back warning dialog: {ex}")
            # Fallback
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _close_application(self):
        """
        Close the application cross-platform.
        Works on Windows, macOS, and Linux.
        """
        if not self.page:
            return
        
        try:
            # Method 1: Try to close the window (cross-platform Flet method)
            if hasattr(self.page, 'window') and hasattr(self.page.window, 'close'):
                self.page.window.close()
                return
        except Exception as e:
            logger.debug(f"Could not close window via page.window.close(): {e}")
        
        # Method 2: Fallback - exit the application process
        try:
            import sys
            sys.exit(0)
        except Exception:
            # Final fallback - force exit
            try:
                import os
                os._exit(0)
            except Exception:
                pass
    
    def _on_generate_click(self, e):
        """Handle generate data button click."""
        if not self.page:
            logger.error("No page available for data generator")
            return
        
        try:
            # Import here to avoid circular imports
            from ui.data_generator import DataGeneratorApp
            from utils.constants import SAMPLE_DATABASE_PATH
            from ui.dialogs import dialog_manager
            
            # Create a temporary page for the data generator
            # We'll embed it in a dialog
            import flet as ft
            
            # Create a temporary page-like object for the data generator
            # We need to create the UI components first
            temp_page = self.page  # Use current page for overlay and updates
            
            # Create data generator instance (don't build UI automatically)
            data_gen = DataGeneratorApp(temp_page, db_path=SAMPLE_DATABASE_PATH, build_ui=False)
            
            # Build the content for the dialog
            dialog_content = data_gen.build_content()
            
            # Add date pickers to page overlay if not already added
            if data_gen.start_date_picker not in temp_page.overlay:
                temp_page.overlay.extend([data_gen.start_date_picker, data_gen.end_date_picker])
                temp_page.update()
            
            # Create close button
            def close_dialog(e):
                """Close the data generator dialog."""
                try:
                    if hasattr(self, '_data_generator_dialog') and self._data_generator_dialog:
                        self.page.close(self._data_generator_dialog)
                except Exception:
                    # Fallback
                    if hasattr(self, '_data_generator_dialog'):
                        self._data_generator_dialog.open = False
                        if self.page:
                            self.page.update()
            
            close_btn = ft.TextButton(
                theme_manager.t("close") or "Close",
                on_click=close_dialog
            )
            
            # Create dialog with data generator content
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(theme_manager.t("generate_test_data") or "Generate Test Data"),
                content=dialog_content,
                actions=[close_btn],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            # Store dialog reference for closing
            self._data_generator_dialog = dialog
            self._data_generator_app = data_gen
            
            # Open dialog using page.open()
            try:
                dialog.page = self.page
                self.page.open(dialog)
            except Exception as ex:
                logger.error(f"Error opening data generator dialog: {ex}")
                # Fallback
                self.page.dialog = dialog
                dialog.open = True
                self.page.update()
            
        except Exception as ex:
            logger.error(f"Error opening data generator: {ex}", exc_info=True)
            theme_manager.show_snackbar(
                self.page,
                f"Error opening data generator: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    

