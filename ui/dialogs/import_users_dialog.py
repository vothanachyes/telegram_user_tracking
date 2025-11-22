"""
Import Users Dialog for fetching Telegram group members.
"""

import flet as ft
import asyncio
import logging
from typing import Optional, Callable
from datetime import datetime

from ui.theme import theme_manager
from config.settings import settings as app_settings
from ui.components.pie_chart import SimplePieChart

logger = logging.getLogger(__name__)


class ImportUsersDialog(ft.AlertDialog):
    """Dialog for importing users from a Telegram group."""
    
    def __init__(
        self,
        group_id: int,
        group_name: str,
        on_import_complete: Optional[Callable[[], None]] = None
    ):
        # Lazy import to avoid circular dependency
        from ui.pages.telegram.view_models.import_users_view_model import ImportUsersViewModel
        
        self.group_id = group_id
        self.group_name = group_name
        self.on_import_complete = on_import_complete
        self.view_model = ImportUsersViewModel()
        
        # Import task
        self._import_task: Optional[asyncio.Task] = None
        self._cancelled = False
        
        # Settings controls
        self.rate_limit_slider = ft.Slider(
            min=0,
            max=10,
            value=app_settings.settings.fetch_delay_seconds if app_settings.settings else 1.0,
            label="{value}s",
            divisions=20
        )
        
        self.fetch_limit_input = ft.TextField(
            label="Fetch Limit (optional)",
            hint_text="Leave empty for no limit",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=200
        )
        
        self.time_limit_input = ft.TextField(
            label="Time Limit (minutes)",
            hint_text="30",
            value="30",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=200
        )
        
        self.skip_deleted_cb = ft.Checkbox(
            label="Skip Deleted",
            value=True
        )
        
        # Progress UI
        self.progress_text = ft.Text(
            "",
            size=14,
            color=theme_manager.text_secondary_color,
            visible=False
        )
        
        # Pie chart
        self.pie_chart = SimplePieChart(
            data={},
            height=30,
            colors={
                'fetched': ft.Colors.GREEN,
                'skipped_exist': ft.Colors.YELLOW,
                'skipped_deleted': ft.Colors.ORANGE
            }
        )
        
        # Stats text
        self.stats_text = ft.Text(
            "",
            size=12,
            color=theme_manager.text_secondary_color,
            visible=False
        )
        
        # Error text
        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED,
            visible=False
        )
        
        # Buttons
        self.start_button = ft.ElevatedButton(
            "Start Import",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._on_start,
            bgcolor=theme_manager.primary_color,
            color=ft.Colors.WHITE
        )
        
        self.stop_button = ft.ElevatedButton(
            "Stop",
            icon=ft.Icons.STOP,
            on_click=self._on_stop,
            bgcolor=ft.Colors.RED,
            color=ft.Colors.WHITE,
            visible=False
        )
        
        # Create dialog
        super().__init__(
            modal=True,
            title=ft.Text(f"Import Users - {group_name}"),
            content=self._build_content(),
            actions=[
                ft.TextButton(
                    "Close",
                    on_click=self._on_close
                ),
                self.stop_button,
                self.start_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _build_content(self) -> ft.Container:
        """Build dialog content."""
        return ft.Container(
            content=ft.Column([
                # Settings section
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Text(
                            "Settings",
                            size=16,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        ft.Row([
                            ft.Column([
                                ft.Text("Rate Limit (seconds)", size=14),
                                self.rate_limit_slider,
                            ], expand=True),
                        ]),
                        ft.Row([
                            ft.Column([
                                self.skip_deleted_cb,
                            ], expand=True),
                        ]),
                        ft.Row([
                            self.fetch_limit_input,
                            self.time_limit_input,
                        ], spacing=20),
                    ], spacing=15)
                ),
                
                # Progress section
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Text(
                            "Progress",
                            size=16,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        self.progress_text,
                        self.pie_chart,
                        self.stats_text,
                        self.error_text,
                    ], spacing=15)
                ),
            ], scroll=ft.ScrollMode.AUTO, spacing=20),
            width=600,
            height=500
        )
    
    def _on_start(self, e):
        """Handle start button click."""
        # Validate inputs
        rate_limit = self.rate_limit_slider.value
        
        fetch_limit = None
        if self.fetch_limit_input.value and self.fetch_limit_input.value.strip():
            try:
                fetch_limit = int(self.fetch_limit_input.value.strip())
                if fetch_limit <= 0:
                    self._show_error("Fetch limit must be greater than 0")
                    return
            except ValueError:
                self._show_error("Invalid fetch limit")
                return
        
        time_limit = None
        if self.time_limit_input.value and self.time_limit_input.value.strip():
            try:
                time_limit = int(self.time_limit_input.value.strip())
                if time_limit <= 0:
                    self._show_error("Time limit must be greater than 0")
                    return
            except ValueError:
                self._show_error("Invalid time limit")
                return
        
        skip_deleted = self.skip_deleted_cb.value
        
        # Reset state
        self.view_model.reset()
        self._cancelled = False
        self.error_text.visible = False
        
        # Update UI
        self.start_button.visible = False
        self.stop_button.visible = True
        self.progress_text.visible = True
        self.stats_text.visible = True
        self.progress_text.value = "Starting import..."
        self._update_progress_ui()
        
        if self.page:
            self.page.update()
        
        # Start import task
        if self.page and hasattr(self.page, 'run_task'):
            self._import_task = self.page.run_task(
                self._import_users_async,
                rate_limit,
                fetch_limit,
                time_limit,
                skip_deleted
            )
        else:
            # Fallback
            self._import_task = asyncio.create_task(
                self._import_users_async(
                    rate_limit,
                    fetch_limit,
                    time_limit,
                    skip_deleted
                )
            )
    
    def _on_stop(self, e):
        """Handle stop button click."""
        self._cancelled = True
        if self._import_task and not self._import_task.done():
            self._import_task.cancel()
        self.view_model.is_importing = False
        self.progress_text.value = "Import stopped by user"
        self.start_button.visible = True
        self.stop_button.visible = False
        if self.page:
            self.page.update()
    
    def _on_close(self, e):
        """Handle close button click."""
        # Cancel import if running
        if self.view_model.is_importing:
            self._on_stop(None)
        
        # Close dialog
        if self.page:
            self.page.close(self)
    
    async def _import_users_async(
        self,
        rate_limit: float,
        fetch_limit: Optional[int],
        time_limit: Optional[int],
        skip_deleted: bool
    ):
        """Async method to import users."""
        try:
            from services.telegram.member_fetcher import MemberFetcher
            from services.telegram.client_utils import ClientUtils
            from services.telegram.client_manager import ClientManager
            from database.db_manager import DatabaseManager
            
            # Get db_manager from settings (singleton pattern)
            from config.settings import settings
            db_manager = settings.db_manager
            client_manager = ClientManager()
            client_utils = ClientUtils(client_manager)
            member_fetcher = MemberFetcher(db_manager, client_utils)
            
            self.view_model.is_importing = True
            
            # Progress callback
            def on_progress(fetched, skipped_exist, skipped_deleted, total):
                self.view_model.update_progress(fetched, skipped_exist, skipped_deleted, total)
                self._update_progress_ui()
            
            # Member callback
            def on_member(user, status):
                # Update status text
                username = getattr(user, 'username', None) or f"User {getattr(user, 'id', '?')}"
                self.view_model.current_status = f"Processing: {username} ({status})"
                self._update_progress_ui()
            
            # Start fetch
            success, fetched, skipped_exist, skipped_deleted, error = await member_fetcher.fetch_members(
                group_id=self.group_id,
                rate_limit=rate_limit,
                fetch_limit=fetch_limit,
                time_limit_minutes=time_limit,
                skip_deleted=skip_deleted,
                on_progress=on_progress,
                on_member=on_member,
                cancellation_flag=lambda: self._cancelled
            )
            
            # Check if cancelled
            if self._cancelled:
                self.progress_text.value = "Import cancelled"
                self.view_model.is_importing = False
                self.start_button.visible = True
                self.stop_button.visible = False
                if self.page:
                    self.page.update()
                return
            
            # Update final state
            self.view_model.is_importing = False
            self.view_model.update_progress(fetched, skipped_exist, skipped_deleted, fetched + skipped_exist + skipped_deleted)
            
            if success:
                self.progress_text.value = f"Import completed successfully!"
                self.view_model.current_status = f"Fetched: {fetched}, Skipped (exist): {skipped_exist}, Skipped (deleted): {skipped_deleted}"
            else:
                self.progress_text.value = f"Import stopped: {error or 'Unknown error'}"
                self.view_model.error_message = error
                self._show_error(error or "Import failed")
            
            self._update_progress_ui()
            self.start_button.visible = True
            self.stop_button.visible = False
            
            # Call completion callback
            if self.on_import_complete:
                self.on_import_complete()
            
            if self.page:
                self.page.update()
                
        except asyncio.CancelledError:
            self.progress_text.value = "Import cancelled"
            self.view_model.is_importing = False
            self.start_button.visible = True
            self.stop_button.visible = False
            if self.page:
                self.page.update()
        except Exception as e:
            logger.error(f"Error importing users: {e}")
            self.progress_text.value = f"Error: {str(e)}"
            self.view_model.is_importing = False
            self.view_model.error_message = str(e)
            self._show_error(str(e))
            self.start_button.visible = True
            self.stop_button.visible = False
            if self.page:
                self.page.update()
    
    def _update_progress_ui(self):
        """Update progress UI elements."""
        # Update pie chart data
        chart_data = {
            'fetched': self.view_model.fetched_count,
            'skipped_exist': self.view_model.skipped_exist_count,
            'skipped_deleted': self.view_model.skipped_deleted_count
        }
        self.pie_chart.update_data(chart_data)
        
        # Update stats text
        actual_total = self.view_model.get_actual_total()
        stats_lines = [
            f"Total Fetched: {self.view_model.fetched_count}",
            f"Skipped (Already Exist): {self.view_model.skipped_exist_count}",
            f"Skipped (Deleted): {self.view_model.skipped_deleted_count}",
            f"Actual Total: {actual_total}"
        ]
        self.stats_text.value = "\n".join(stats_lines)
        self.stats_text.visible = True
        
        # Update progress text
        if self.view_model.current_status:
            self.progress_text.value = self.view_model.current_status
        elif self.view_model.is_importing:
            self.progress_text.value = f"Importing... ({actual_total} processed)"
        else:
            self.progress_text.value = "Ready to import"
    
    def _show_error(self, message: str):
        """Show error message."""
        self.error_text.value = message
        self.error_text.visible = True
        if self.page:
            self.page.update()

