"""
Summary UI components for fetch data page.
"""

import flet as ft
import logging
from typing import Optional
from ui.theme import theme_manager
from database.db_manager import DatabaseManager
from ui.pages.fetch_data.view_model import FetchViewModel
from ui.pages.fetch_data.components import SummaryTable

logger = logging.getLogger(__name__)


class SummaryUI:
    """Manages summary table display."""
    
    def __init__(
        self,
        view_model: FetchViewModel,
        db_manager: DatabaseManager,
        page: Optional[ft.Page] = None
    ):
        self.view_model = view_model
        self.db_manager = db_manager
        self.page = page
        
        # Summary table container (hidden initially)
        self.summary_table_container = ft.Container(
            visible=False,
            content=None
        )
        
        # Real-time summary table (scrollable)
        self._summary_table: Optional[ft.DataTable] = None
        self._summary_rows: list = []
        self._user_map: dict = {}
        
        # Finish button (hidden initially)
        self.finish_button = ft.ElevatedButton(
            theme_manager.t("finish") or "Finish",
            icon=ft.Icons.CHECK_CIRCLE,
            on_click=self._on_finish_click,
            bgcolor=theme_manager.primary_color,
            color=ft.Colors.WHITE,
            visible=False
        )
    
    def set_page(self, page: ft.Page):
        """Set page reference."""
        self.page = page
    
    def set_finish_callback(self, callback):
        """Set callback for finish button click."""
        self._finish_callback = callback
    
    def show_summary(self):
        """Show summary table and finish button."""
        self.summary_table_container.visible = True
        self.finish_button.visible = True
    
    def hide_summary(self):
        """Hide summary table and finish button."""
        self.summary_table_container.visible = False
        self.finish_button.visible = False
    
    def show_summary_table_realtime(self):
        """Show summary table for real-time updates during fetch."""
        # Initialize empty table
        self._summary_rows = []
        self._user_map = {}
        
        self._summary_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("No")),
                ft.DataColumn(ft.Text("User Name")),
                ft.DataColumn(ft.Text("Messages Sent")),
                ft.DataColumn(ft.Text("Reactions Given")),
                ft.DataColumn(ft.Text("Media Shared")),
            ],
            rows=[],
            heading_row_color=theme_manager.primary_color,
            heading_text_style=ft.TextStyle(color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        )
        
        # Create scrollable container
        scrollable_content = ft.Column([
            ft.Text(
                "Fetch Summary (Live)",
                size=theme_manager.font_size_subsection_title,
                weight=ft.FontWeight.BOLD
            ),
            ft.Divider(),
            self._summary_table,
        ], spacing=theme_manager.spacing_sm, scroll=ft.ScrollMode.AUTO, expand=True)
        
        self.summary_table_container.content = ft.Container(
            content=scrollable_content,
            height=300,  # Fixed height for scrollable area
            padding=theme_manager.padding_md,
            bgcolor=theme_manager.surface_color,
            border_radius=theme_manager.corner_radius,
            border=ft.border.all(1, theme_manager.border_color),
        )
        self.summary_table_container.visible = True
        
        if self.page:
            self.page.update()
    
    def update_summary_realtime(self):
        """Update summary table in real-time as messages are fetched."""
        try:
            summary_data = self.view_model.get_summary_data()
            
            # Build user map
            for data in summary_data:
                user_id = data['user_id']
                if user_id not in self._user_map:
                    user = self.db_manager.get_user_by_id(user_id)
                    if user:
                        self._user_map[user_id] = user
            
            # Rebuild rows
            self._summary_rows = []
            for idx, data in enumerate(summary_data, 1):
                user = self._user_map.get(data['user_id'])
                user_name = user.full_name if user else f"User {data['user_id']}"
                
                self._summary_rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(idx))),
                            ft.DataCell(ft.Text(user_name)),
                            ft.DataCell(ft.Text(str(data['messages']))),
                            ft.DataCell(ft.Text(str(data['reactions']))),
                            ft.DataCell(ft.Text(str(data['media']))),
                        ]
                    )
                )
            
            # Update table
            if self._summary_table:
                self._summary_table.rows = self._summary_rows
                
                if self.page:
                    try:
                        self.page.update()
                    except:
                        pass
                        
        except Exception as ex:
            logger.error(f"Error updating summary table in real-time: {ex}")
    
    async def display_summary_table(self):
        """Show post-fetch summary table."""
        try:
            summary_data = self.view_model.get_summary_data()
            
            # Build user map
            user_map = {}
            for data in summary_data:
                user_id = data['user_id']
                user = self.db_manager.get_user_by_id(user_id)
                if user:
                    user_map[user_id] = user
            
            # Create summary table
            summary_table = SummaryTable(summary_data, user_map)
            self.summary_table_container.content = summary_table
            self.summary_table_container.visible = True
            
            if self.page:
                self.page.update()
                
        except Exception as ex:
            logger.error(f"Error showing summary table: {ex}")
    
    def _on_finish_click(self, e):
        """Handle finish button click."""
        if hasattr(self, '_finish_callback'):
            self._finish_callback(e)

