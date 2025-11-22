"""
Handler for import users functionality.
"""

import flet as ft
import logging
from typing import Optional

from ui.dialogs.import_users_dialog import ImportUsersDialog

logger = logging.getLogger(__name__)


class ImportUsersHandler:
    """Handles import users operations."""
    
    def __init__(self, page: Optional[ft.Page], view_model):
        self.page = page
        self.view_model = view_model
    
    def handle_import_users(self, group_id: Optional[int], group_name: Optional[str] = None):
        """
        Handle import users button click.
        
        Args:
            group_id: Selected group ID
            group_name: Group name (optional, will be fetched if not provided)
        """
        if not self.page:
            logger.error("Page not set in ImportUsersHandler")
            return
        
        # Check if Telegram account is configured
        credential = self.view_model.db_manager.get_default_credential()
        if not credential:
            from ui.theme import theme_manager
            theme_manager.show_snackbar(
                self.page,
                "Please login to Telegram first. Go to Settings > Authenticate to add a Telegram account.",
                bgcolor=ft.Colors.ORANGE
            )
            return
        
        if not group_id:
            from ui.theme import theme_manager
            theme_manager.show_snackbar(
                self.page,
                "Please select a group first",
                bgcolor=ft.Colors.ORANGE
            )
            return
        
        # Get group name if not provided
        if not group_name:
            group = self.view_model.db_manager.get_group_by_id(group_id)
            if group:
                group_name = group.group_name
            else:
                group_name = f"Group {group_id}"
        
        # Create and open dialog
        def on_complete():
            # Refresh users table after import
            if hasattr(self.view_model, 'refresh_users'):
                self.view_model.refresh_users()
        
        dialog = ImportUsersDialog(
            group_id=group_id,
            group_name=group_name,
            on_import_complete=on_complete
        )
        dialog.page = self.page
        self.page.open(dialog)

