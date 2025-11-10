"""
Groups page for managing Telegram groups.
"""

import flet as ft
from typing import Optional
from database.db_manager import DatabaseManager
from services.telegram import TelegramService
from ui.theme import theme_manager
from ui.pages.groups.view_model import GroupsViewModel
from ui.pages.groups.components import GroupsComponents
from ui.pages.groups.handlers import GroupsHandlers


class GroupsPage(ft.Container):
    """Groups page for listing and managing Telegram groups."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        telegram_service: Optional[TelegramService] = None
    ):
        self.db_manager = db_manager
        self.telegram_service = telegram_service
        self.page: Optional[ft.Page] = None
        
        # Initialize view model
        self.view_model = GroupsViewModel(db_manager)
        self.view_model.load_groups()
        
        # Initialize components
        self.components = GroupsComponents(
            on_group_click=self._on_group_click
        )
        
        # Initialize handlers
        self.handlers = GroupsHandlers(
            page=None,  # Will be set in set_page
            db_manager=db_manager,
            telegram_service=telegram_service,
            view_model=self.view_model
        )
        # Pass reference to this page for refresh callback
        self.handlers.groups_page = self
        
        # Build UI
        super().__init__(
            content=self._build_content(),
            padding=theme_manager.padding_lg,
            expand=True
        )
    
    def set_page(self, page: ft.Page):
        """Set page reference."""
        self.page = page
        self.handlers.set_page(page)
    
    def _build_content(self) -> ft.Column:
        """Build page content."""
        # Store reference to groups list container for updates
        self.groups_list_container = self.components.build_group_list(self.view_model.get_all_groups())
        
        return ft.Column([
            # Header
            ft.Row([
                ft.Icon(ft.Icons.GROUP, size=theme_manager.font_size_page_title, color=theme_manager.primary_color),
                ft.Text(
                    theme_manager.t("groups") or "Groups",
                    size=theme_manager.font_size_page_title,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.ADD,
                    tooltip=theme_manager.t("add_group") or "Add Group",
                    on_click=self.handlers.on_add_group_click,
                    bgcolor=theme_manager.primary_color,
                    icon_color=ft.Colors.WHITE
                ),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip=theme_manager.t("refresh") or "Refresh",
                    on_click=self.handlers.on_refresh_click
                )
            ], spacing=10),
            
            ft.Container(height=20),
            
            # Groups list
            self.groups_list_container
            
        ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def refresh_groups_list(self):
        """Refresh the groups list UI."""
        # Reload groups from database
        self.view_model.load_groups()
        
        # Rebuild the groups list
        new_groups_list = self.components.build_group_list(self.view_model.get_all_groups())
        
        # Find and replace the groups list in the content
        if hasattr(self, 'content') and isinstance(self.content, ft.Column):
            # Find the groups list container in the content
            for i, control in enumerate(self.content.controls):
                if control == self.groups_list_container:
                    # Replace with new list
                    self.content.controls[i] = new_groups_list
                    self.groups_list_container = new_groups_list
                    break
        
        # Update the page
        if self.page:
            self.page.update()
    
    def _on_group_click(self, group):
        """Handle group click."""
        self.handlers.on_group_click(group)

