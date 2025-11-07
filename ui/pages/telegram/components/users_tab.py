"""
Users tab component for Telegram page.
"""

import flet as ft
from typing import Optional, Callable, List
from ui.theme import theme_manager
from ui.components import DataTable
from utils.helpers import get_telegram_user_link
from ui.pages.telegram.components.filters_bar import FiltersBarComponent


class UsersTabComponent:
    """Users tab component."""
    
    def __init__(
        self,
        view_model,
        on_user_click: Callable[[int], None],
        on_refresh: Optional[Callable[[], None]] = None,
        on_export_excel: Optional[Callable[[], None]] = None,
        on_export_pdf: Optional[Callable[[], None]] = None
    ):
        self.view_model = view_model
        self.on_user_click = on_user_click
        self.on_refresh = on_refresh
        self.on_export_excel = on_export_excel
        self.on_export_pdf = on_export_pdf
        
        # Filters bar (no dates for users tab)
        groups = view_model.get_all_groups()
        self.filters_bar = FiltersBarComponent(
            groups=groups,
            on_group_change=self._on_group_change,
            show_dates=False
        )
        
        # Users table
        self.users_table = self._create_users_table()
        
        # Export menu
        self.export_menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            tooltip=theme_manager.t("export"),
            items=[
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_excel"),
                    icon=ft.Icons.TABLE_CHART,
                    on_click=lambda e: self.on_export_excel() if self.on_export_excel else None
                ),
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_pdf"),
                    icon=ft.Icons.PICTURE_AS_PDF,
                    on_click=lambda e: self.on_export_pdf() if self.on_export_pdf else None
                ),
            ]
        )
        
        # Refresh button
        self.refresh_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip=theme_manager.t("refresh"),
            on_click=self._refresh_users
        )
    
    def build(self) -> ft.Container:
        """Build the users tab."""
        # Get search field and clear filter button from table
        search_field = self.users_table.search_field
        clear_filter_btn = self.users_table.clear_filter_button
        
        return ft.Container(
            content=ft.Column([
                # Filters row
                ft.Row([
                    clear_filter_btn if clear_filter_btn else ft.Container(),
                    search_field if search_field else ft.Container(),
                    ft.Container(width=20),
                    self.filters_bar.build(),
                    self.refresh_btn,
                    self.export_menu,
                ], spacing=10, wrap=False),
                
                # Table
                ft.Container(
                    content=self.users_table,
                    expand=True,
                    width=None
                ),
            ], spacing=15, expand=True),
            padding=10,
            expand=True
        )
    
    def refresh_users(self):
        """Refresh users table."""
        group_id = self.filters_bar.get_selected_group()
        
        if not group_id:
            self.users_table.refresh([], [])
            self.users_table.update_filter_state(self._has_filters())
            return
        
        users = self.view_model.get_users_by_group(group_id)
        
        rows = []
        row_metadata = []
        for idx, user in enumerate(users, 1):
            username = user.username or "-"
            full_name = user.full_name
            user_link = get_telegram_user_link(user.username)
            
            rows.append([
                idx,
                username,
                full_name,
                user.phone or "-",
                user.bio[:50] + "..." if user.bio and len(user.bio) > 50 else user.bio or "-",
            ])
            
            row_meta = {
                'cells': {}
            }
            if user_link and user.username:
                row_meta['cells'][1] = {'link': user_link}
                row_meta['cells'][2] = {'link': user_link}
            row_metadata.append(row_meta)
        
        self.users_table.refresh(rows, row_metadata)
        self.users_table.update_filter_state(self._has_filters())
    
    def clear_filters(self):
        """Clear all filters."""
        self.filters_bar.clear_filters()
        if self.users_table.search_field:
            self.users_table.search_field.value = ""
        self.users_table.search_query = ""
        self.refresh_users()
        self.users_table.update_filter_state(False)
    
    def get_selected_group(self) -> Optional[int]:
        """Get selected group ID."""
        return self.filters_bar.get_selected_group()
    
    def get_users(self) -> List:
        """Get current filtered users."""
        group_id = self.filters_bar.get_selected_group()
        if not group_id:
            return []
        return self.view_model.get_users_by_group(group_id)
    
    def _create_users_table(self) -> DataTable:
        """Create users data table."""
        column_alignments = ["center", "center", "center", "center", "left"]
        
        # Check filters before table is created (only group filter at this point)
        has_filters = self.filters_bar.get_selected_group() is not None
        
        return DataTable(
            columns=["No", "Username", "Full Name", "Phone", "Bio"],
            rows=[],
            on_row_click=self.on_user_click,
            page_size=50,
            column_alignments=column_alignments,
            row_metadata=[],
            on_clear_filters=self.clear_filters,
            has_filters=has_filters
        )
    
    def _has_filters(self) -> bool:
        """Check if any filters are active."""
        return (
            self.filters_bar.get_selected_group() is not None or
            (self.users_table.search_query if hasattr(self.users_table, 'search_query') else False)
        )
    
    def _on_group_change(self, group_id: Optional[int]):
        """Handle group change."""
        if self.on_refresh:
            self.on_refresh()
    
    def _refresh_users(self, e):
        """Handle refresh button click."""
        if self.on_refresh:
            self.on_refresh()

