"""
Groups page for managing Telegram groups.
"""

import flet as ft
import asyncio
import logging
from typing import Optional
from database.db_manager import DatabaseManager
from database.async_query_executor import async_query_executor
from services.page_cache_service import page_cache_service
from services.telegram import TelegramService
from ui.theme import theme_manager
from ui.components.skeleton_loaders.groups_skeleton import GroupsSkeleton
from ui.pages.groups.view_model import GroupsViewModel
from ui.pages.groups.components import GroupsComponents
from ui.pages.groups.handlers import GroupsHandlers

logger = logging.getLogger(__name__)


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
        self.is_loading = True
        
        # Initialize view model (don't load groups yet)
        self.view_model = GroupsViewModel(db_manager)
        
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
        
        # Build UI with skeleton loader
        super().__init__(
            content=self._build_content(),
            padding=theme_manager.padding_lg,
            expand=True
        )
    
    def set_page(self, page: ft.Page):
        """Set page reference and load data asynchronously."""
        self.page = page
        self.handlers.set_page(page)
        
        # Load groups asynchronously
        if page and hasattr(page, 'run_task'):
            page.run_task(self._load_groups_async)
        else:
            asyncio.create_task(self._load_groups_async())
    
    async def _load_groups_async(self):
        """Load groups asynchronously."""
        try:
            self.is_loading = True
            
            # Check cache first
            cache_key = page_cache_service.generate_key("groups")
            groups = page_cache_service.get(cache_key)
            
            if not groups:
                # Load from database
                groups = await async_query_executor.execute(self.db_manager.get_all_groups)
                # Cache groups for 10 minutes (they don't change often)
                if page_cache_service.is_enabled():
                    page_cache_service.set(cache_key, groups, ttl=600)
            
            # Update view model
            self.view_model.groups = groups
            
            # Update UI
            new_groups_list = self.components.build_group_list(groups)
            self.groups_list_container.content = new_groups_list
            
            self.is_loading = False
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            logger.error(f"Error loading groups: {e}", exc_info=True)
            self.is_loading = False
            if self.page:
                self.page.update()
    
    def _build_content(self) -> ft.Column:
        """Build page content."""
        # Show skeleton loader initially
        skeleton = GroupsSkeleton.create()
        
        # Store reference to groups list container for updates
        self.groups_list_container = ft.Container(
            content=skeleton,
            expand=True
        )
        
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
            
            # Groups list - wrapped in container to ensure it expands
            self.groups_list_container
            
        ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def refresh_groups_list(self):
        """Refresh the groups list UI."""
        # Invalidate cache
        page_cache_service.invalidate("page:groups")
        
        # Reload groups asynchronously
        if self.page and hasattr(self.page, 'run_task'):
            self.page.run_task(self._load_groups_async)
        else:
            asyncio.create_task(self._load_groups_async())
    
    def _on_group_click(self, group):
        """Handle group click."""
        self.handlers.on_group_click(group)

