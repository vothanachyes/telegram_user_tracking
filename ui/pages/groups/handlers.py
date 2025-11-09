"""
Event handlers for groups page.
"""

import logging
import flet as ft
from typing import Optional
from database.db_manager import DatabaseManager
from database.models.telegram import TelegramGroup
from services.telegram import TelegramService
from ui.pages.groups.view_model import GroupsViewModel
from ui.dialogs.add_group_dialog import AddGroupDialog
from ui.dialogs.group_detail_dialog import GroupDetailDialog

logger = logging.getLogger(__name__)


class GroupsHandlers:
    """Handles events for groups page."""
    
    def __init__(
        self,
        page: Optional[ft.Page],
        db_manager: DatabaseManager,
        telegram_service: TelegramService,
        view_model: GroupsViewModel
    ):
        self.page = page
        self.db_manager = db_manager
        self.telegram_service = telegram_service
        self.view_model = view_model
    
    def set_page(self, page: ft.Page):
        """Set page reference."""
        self.page = page
    
    def on_add_group_click(self, e):
        """Handle add group button click."""
        if not self.page:
            return
        
        try:
            dialog = AddGroupDialog(
                db_manager=self.db_manager,
                telegram_service=self.telegram_service,
                on_group_added=self._on_group_added
            )
            dialog.page = self.page
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening add group dialog: {ex}")
            if self.page:
                from ui.theme import theme_manager
                theme_manager.show_snackbar(
                    self.page,
                    f"Error opening dialog: {ex}",
                    bgcolor=ft.Colors.RED
                )
    
    def on_group_click(self, group: TelegramGroup):
        """Handle group card click."""
        if not self.page:
            return
        
        try:
            dialog = GroupDetailDialog(
                db_manager=self.db_manager,
                telegram_service=self.telegram_service,
                group=group
            )
            dialog.page = self.page
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening group detail dialog: {ex}")
            if self.page:
                from ui.theme import theme_manager
                theme_manager.show_snackbar(
                    self.page,
                    f"Error opening dialog: {ex}",
                    bgcolor=ft.Colors.RED
                )
    
    def on_refresh_click(self, e):
        """Handle refresh button click."""
        self.view_model.load_groups()
        if self.page:
            self.page.update()
    
    def _on_group_added(self):
        """Handle group added callback."""
        self.view_model.load_groups()
        if self.page:
            self.page.update()

