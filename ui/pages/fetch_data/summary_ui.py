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

