"""
Reports page with active users and group summary tables.
"""

import flet as ft
from typing import Optional, Callable
from database.db_manager import DatabaseManager
from ui.theme import theme_manager
from ui.components import DataTable, ModernTabs
from utils.helpers import format_datetime, get_telegram_user_link
from ui.pages.telegram.components.filters_bar import FiltersBarComponent


class ReportsPage(ft.Container):
    """Reports page with various report tables."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        on_navigate: Optional[Callable[[str, dict], None]] = None
    ):
        self.db_manager = db_manager
        self.page: Optional[ft.Page] = None
        self.on_navigate = on_navigate
        
        # Get groups and set default selected group
        groups = self.db_manager.get_all_groups()
        default_group_id = groups[0].group_id if groups else None
        
        # Create filters bar for active users (with dates enabled)
        self.active_users_filters_bar = FiltersBarComponent(
            groups=groups,
            on_group_change=self._on_active_users_group_change,
            on_date_change=self._on_active_users_date_change,
            show_dates=True,
            default_group_id=default_group_id
        )
        
        # Create tables
        self.active_users_table = self._create_active_users_table()
        self.group_summary_table = self._create_group_summary_table()
        
        # Create tab definitions
        tabs = [
            {
                'id': 'active_users',
                'label': 'active_users',
                'icon': ft.Icons.PEOPLE,
                'content': self._build_active_users_tab(),
                'enabled': True
            },
            {
                'id': 'group_summary',
                'label': 'group_summary',
                'icon': ft.Icons.GROUP,
                'content': self._build_group_summary_tab(),
                'enabled': True
            }
        ]
        
        # Create modern tabs
        self.modern_tabs = ModernTabs(
            tabs=tabs,
            selected_index=0,
            on_tab_change=self._on_tab_change
        )
        
        # Build layout
        super().__init__(
            content=ft.Column([
                # Header
                ft.Row([
                    ft.Text(
                        theme_manager.t("reports"),
                        size=theme_manager.font_size_page_title,
                        weight=ft.FontWeight.BOLD
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=10),
                theme_manager.spacing_container("md"),
                # Tabs
                self.modern_tabs,
            ], spacing=theme_manager.spacing_sm, expand=True),
            padding=theme_manager.padding_lg,
            expand=True
        )
        
        # Load initial data
        self._refresh_active_users()
        self._refresh_group_summary()
    
    def set_page(self, page: ft.Page):
        """Set page reference."""
        self.page = page
    
    def _on_tab_change(self, index: int):
        """Handle tab change."""
        if self.page:
            self.page.update()
    
    def _on_active_users_group_change(self, group_id: Optional[int]):
        """Handle group change for active users."""
        self._refresh_active_users()
        if self.page:
            self.page.update()
    
    def _on_active_users_date_change(self):
        """Handle date change for active users."""
        self._refresh_active_users()
        if self.page:
            self.page.update()
    
    def _build_active_users_tab(self) -> ft.Container:
        """Build active users tab content."""
        # Get search field and clear filter button from table
        search_field = self.active_users_table.search_field
        clear_filter_btn = self.active_users_table.clear_filter_button
        
        # Export menu
        export_menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            tooltip=theme_manager.t("export"),
            items=[
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_excel"),
                    icon=ft.Icons.TABLE_CHART,
                    on_click=self._export_active_users_excel
                ),
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_pdf"),
                    icon=ft.Icons.PICTURE_AS_PDF,
                    on_click=self._export_active_users_pdf
                ),
            ]
        )
        
        refresh_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip=theme_manager.t("refresh"),
            on_click=lambda e: self._refresh_active_users()
        )
        
        return ft.Container(
            content=ft.Column([
                # Filters row (same layout as Users table)
                ft.Row([
                    clear_filter_btn if clear_filter_btn else ft.Container(),
                    search_field if search_field else ft.Container(),
                    ft.Container(width=20),
                    self.active_users_filters_bar.build(),
                    refresh_btn,
                    export_menu,
                ], spacing=10, wrap=False),
                # Table
                ft.Container(
                    content=self.active_users_table,
                    expand=True,
                    width=None
                ),
            ], spacing=15, expand=True),
            padding=10,
            expand=True
        )
    
    def _build_group_summary_tab(self) -> ft.Container:
        """Build group summary tab content."""
        refresh_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip=theme_manager.t("refresh"),
            on_click=lambda e: self._refresh_group_summary()
        )
        
        return ft.Container(
            content=ft.Column([
                # Controls row
                ft.Row([
                    ft.Container(expand=True),
                    refresh_btn,
                ], spacing=10),
                # Table
                ft.Container(
                    content=self.group_summary_table,
                    expand=True,
                    width=None
                ),
            ], spacing=15, expand=True),
            padding=10,
            expand=True
        )
    
    def _create_active_users_table(self) -> DataTable:
        """Create active users data table."""
        # Check filters before table is created
        has_filters = self.active_users_filters_bar.get_selected_group() is not None
        
        return DataTable(
            columns=["No", "Username", "Full Name", "Phone", "Messages"],
            rows=[],
            on_row_click=None,
            page_size=50,
            column_alignments=["center", "center", "left", "center", "center"],
            row_metadata=[],
            on_clear_filters=self._clear_active_users_filters,
            has_filters=has_filters,
            searchable=True
        )
    
    def _refresh_active_users(self):
        """Refresh active users table."""
        group_id = self.active_users_filters_bar.get_selected_group()
        
        if not group_id:
            self.active_users_table.refresh([], [])
            self.active_users_table.update_filter_state(self._has_active_users_filters())
            return
        
        # Get date range from filters bar
        start_date = self.active_users_filters_bar.get_start_date()
        end_date = self.active_users_filters_bar.get_end_date()
        
        # Get all active users (not just top 10)
        users = self.db_manager.get_top_active_users_by_group(group_id, limit=10000)
        
        # Filter by date range if provided
        if start_date or end_date:
            filtered_users = []
            for user_data in users:
                # Get user messages count for date range
                user_id = user_data['user_id']
                messages = self.db_manager.get_messages(
                    group_id=group_id,
                    user_id=user_id,
                    start_date=start_date,
                    end_date=end_date
                )
                if messages:
                    user_data['message_count'] = len(messages)
                    filtered_users.append(user_data)
            users = filtered_users
            # Re-sort by message count
            users.sort(key=lambda x: x.get('message_count', 0), reverse=True)
        
        rows = []
        row_metadata = []
        for idx, user in enumerate(users, 1):
            username = user.get('username') or "-"
            full_name = user.get('full_name') or "-"
            phone = user.get('phone') or "-"
            message_count = user.get('message_count', 0)
            user_link = get_telegram_user_link(user.get('username'))
            
            rows.append([
                idx,
                username,
                full_name,
                phone,
                str(message_count),
            ])
            
            row_meta = {
                'cells': {}
            }
            if user_link and user.get('username'):
                row_meta['cells'][1] = {'link': user_link}
                row_meta['cells'][2] = {'link': user_link}
            row_metadata.append(row_meta)
        
        self.active_users_table.refresh(rows, row_metadata)
        self.active_users_table.update_filter_state(self._has_active_users_filters())
    
    def _clear_active_users_filters(self):
        """Clear all filters for active users."""
        self.active_users_filters_bar.clear_filters()
        if self.active_users_table.search_field:
            self.active_users_table.search_field.value = ""
        self.active_users_table.search_query = ""
        self._refresh_active_users()
        self.active_users_table.update_filter_state(False)
    
    def _has_active_users_filters(self) -> bool:
        """Check if any filters are active for active users."""
        return (
            self.active_users_filters_bar.get_selected_group() is not None or
            (self.active_users_filters_bar.get_start_date() is not None) or
            (self.active_users_filters_bar.get_end_date() is not None) or
            (self.active_users_table.search_query if hasattr(self.active_users_table, 'search_query') else False)
        )
    
    def _create_group_summary_table(self) -> DataTable:
        """Create group summary table."""
        return DataTable(
            columns=["No", "GroupPic", "GroupName", "History", "Last Export", "Total Messages", "Total Members", "Active Members"],
            rows=[],
            on_row_click=None,
            page_size=50,
            column_alignments=["center", "center", "left", "center", "center", "center", "center", "center"],
            row_metadata=[],
            searchable=False
        )
    
    def _refresh_group_summary(self):
        """Refresh group summary table."""
        summaries = self.db_manager.get_group_summaries()
        
        rows = []
        row_metadata = []
        for idx, summary in enumerate(summaries, 1):
            group_name = summary.get('group_name') or "Unknown"
            group_photo_path = summary.get('group_photo_path')
            history_count = summary.get('export_history_count', 0)
            last_export = summary.get('last_export_date')
            last_export_str = format_datetime(last_export, "%Y-%m-%d") if last_export else "-"
            total_messages = summary.get('total_messages', 0)
            total_members = summary.get('total_members', 0)
            active_members = summary.get('active_members', 0)
            
            # Create group photo display
            if group_photo_path:
                photo_display = ft.Image(
                    src=group_photo_path,
                    width=40,
                    height=40,
                    fit=ft.ImageFit.COVER,
                    border_radius=20
                )
            else:
                photo_display = ft.Icon(ft.Icons.GROUP, size=40, color=theme_manager.primary_color)
            
            rows.append([
                idx,
                "",  # GroupPic - will be handled in row_metadata
                group_name,
                str(history_count),
                last_export_str,
                str(total_messages),
                str(total_members),
                str(active_members),
            ])
            
            row_meta = {
                'cells': {
                    1: {'custom_widget': photo_display}  # Custom widget for group photo
                }
            }
            row_metadata.append(row_meta)
        
        self.group_summary_table.refresh(rows, row_metadata)
    
    def _export_active_users_excel(self, e):
        """Export active users to Excel."""
        group_id = self.active_users_filters_bar.get_selected_group()
        if not self.page or not group_id:
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("select_group_first"),
                bgcolor=ft.Colors.ORANGE
            )
            return
        
        # Get group name
        groups = self.db_manager.get_all_groups()
        group_name = "Unknown"
        for group in groups:
            if group.group_id == group_id:
                group_name = group.group_name
                break
        
        from ui.dialogs.active_users_dialog import ActiveUsersDialog
        dialog = ActiveUsersDialog(
            db_manager=self.db_manager,
            group_id=group_id,
            group_name=group_name
        )
        dialog.set_page(self.page)
        dialog.page = self.page
        # Trigger export directly
        dialog._export_excel(e)
    
    def _export_active_users_pdf(self, e):
        """Export active users to PDF."""
        group_id = self.active_users_filters_bar.get_selected_group()
        if not self.page or not group_id:
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("select_group_first"),
                bgcolor=ft.Colors.ORANGE
            )
            return
        
        # Get group name
        groups = self.db_manager.get_all_groups()
        group_name = "Unknown"
        for group in groups:
            if group.group_id == group_id:
                group_name = group.group_name
                break
        
        from ui.dialogs.active_users_dialog import ActiveUsersDialog
        dialog = ActiveUsersDialog(
            db_manager=self.db_manager,
            group_id=group_id,
            group_name=group_name
        )
        dialog.set_page(self.page)
        dialog.page = self.page
        # Trigger export directly
        dialog._export_pdf(e)

