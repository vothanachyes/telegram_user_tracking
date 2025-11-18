"""
Active users dialog with full table, search, sort, pagination, and export.
"""

import flet as ft
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime
from ui.theme import theme_manager
from ui.components import DataTable
from database.db_manager import DatabaseManager
from services.export import ExportService
from utils.helpers import get_telegram_user_link


class ActiveUsersDialog(ft.AlertDialog):
    """Dialog for viewing all active users in a group with full features."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        group_id: int,
        group_name: str,
        on_export_excel: Optional[Callable] = None,
        on_export_pdf: Optional[Callable] = None
    ):
        self.db_manager = db_manager
        self.group_id = group_id
        self.group_name = group_name
        self.export_service = ExportService(db_manager)
        self.page: Optional[ft.Page] = None
        
        # File pickers
        self.excel_picker = ft.FilePicker(on_result=self._on_excel_picked)
        self.pdf_picker = ft.FilePicker(on_result=self._on_pdf_picked)
        
        # Page size dropdown
        self.page_size_dropdown = ft.Dropdown(
            label=theme_manager.t("items_per_page"),
            options=[
                ft.dropdown.Option("15", "15"),
                ft.dropdown.Option("25", "25"),
                ft.dropdown.Option("50", "50"),
                ft.dropdown.Option("100", "100"),
            ],
            value="15",
            width=120,
            on_change=self._on_page_size_change
        )
        
        # Create table
        self.users_table = self._create_table()
        
        # Export menu
        export_menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            tooltip=theme_manager.t("export"),
            items=[
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_excel"),
                    icon=ft.Icons.TABLE_CHART,
                    on_click=self._export_excel
                ),
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_pdf"),
                    icon=ft.Icons.PICTURE_AS_PDF,
                    on_click=self._export_pdf
                ),
            ]
        )
        
        # Build content
        super().__init__(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.PEOPLE, color=theme_manager.primary_color),
                ft.Text(
                    f"{theme_manager.t('active_users')} - {group_name}",
                    size=20,
                    weight=ft.FontWeight.BOLD
                )
            ]),
            content=ft.Container(
                content=ft.Column([
                    # Controls row
                    ft.Row([
                        self.page_size_dropdown,
                        ft.Container(expand=True),
                        export_menu,
                    ], spacing=10),
                    # Table
                    ft.Container(
                        content=self.users_table,
                        expand=True,
                        width=None
                    ),
                ], spacing=15, expand=True),
                width=900,
                height=600,
                padding=10
            ),
            actions=[
                ft.TextButton(
                    theme_manager.t("close"),
                    on_click=self._close_dialog
                ),
            ]
        )
        
        # Load data
        self._refresh_table()
    
    def set_page(self, page: ft.Page):
        """Set page reference and add file pickers to overlay."""
        self.page = page
        if not hasattr(page, 'overlay') or page.overlay is None:
            page.overlay = []
        
        pickers = [self.excel_picker, self.pdf_picker]
        for picker in pickers:
            if picker not in page.overlay:
                page.overlay.append(picker)
    
    def _create_table(self) -> DataTable:
        """Create active users data table."""
        return DataTable(
            columns=["No", "Username", "Full Name", "Phone", "Messages"],
            rows=[],
            on_row_click=None,
            page_size=15,
            column_alignments=["center", "center", "left", "center", "center"],
            row_metadata=[],
            searchable=True
        )
    
    def _refresh_table(self):
        """Refresh table with active users data."""
        # Get all active users (not just top 10)
        users = self.db_manager.get_top_active_users_by_group(self.group_id, limit=10000)
        
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
        
        self.users_table.refresh(rows, row_metadata)
    
    def _on_page_size_change(self, e):
        """Handle page size change."""
        new_size = int(self.page_size_dropdown.value)
        self.users_table.page_size = new_size
        self.users_table.current_page = 0
        self.users_table._update_table()
    
    def _export_excel(self, e):
        """Export active users to Excel."""
        if not self.page:
            return
        
        if not hasattr(self.page, 'overlay') or self.page.overlay is None:
            self.page.overlay = []
        if self.excel_picker not in self.page.overlay:
            self.page.overlay.append(self.excel_picker)
        
        default_name = f"active_users_{self.group_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        try:
            self.excel_picker.save_file(
                dialog_title=theme_manager.t("export_to_excel"),
                file_name=default_name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["xlsx"]
            )
        except Exception as ex:
            theme_manager.show_snackbar(
                self.page,
                f"Error: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def _on_excel_picked(self, e: ft.FilePickerResultEvent):
        """Handle Excel file picker result."""
        if not self.page or not e.path:
            return
        
        try:
            users = self.db_manager.get_top_active_users_by_group(self.group_id, limit=10000)
            
            # Convert to TelegramUser objects for export
            from database.models import TelegramUser
            user_objects = []
            for user_data in users:
                user = TelegramUser(
                    user_id=user_data['user_id'],
                    username=user_data.get('username'),
                    first_name=user_data.get('first_name'),
                    last_name=user_data.get('last_name'),
                    full_name=user_data.get('full_name'),
                    phone=user_data.get('phone'),
                    profile_photo_path=user_data.get('profile_photo_path')
                )
                user_objects.append(user)
            
            if self.export_service.export_users_to_excel(user_objects, e.path):
                theme_manager.show_snackbar(
                    self.page,
                    f"{theme_manager.t('export_success')}: {e.path}",
                    bgcolor=ft.Colors.GREEN
                )
            else:
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("export_error"),
                    bgcolor=ft.Colors.RED
                )
        except Exception as ex:
            theme_manager.show_snackbar(
                self.page,
                f"{theme_manager.t('export_error')}: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def _export_pdf(self, e):
        """Export active users to PDF."""
        if not self.page:
            return
        
        if not hasattr(self.page, 'overlay') or self.page.overlay is None:
            self.page.overlay = []
        if self.pdf_picker not in self.page.overlay:
            self.page.overlay.append(self.pdf_picker)
        
        default_name = f"active_users_{self.group_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        try:
            self.pdf_picker.save_file(
                dialog_title=theme_manager.t("export_to_pdf"),
                file_name=default_name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["pdf"]
            )
        except Exception as ex:
            theme_manager.show_snackbar(
                self.page,
                f"Error: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def _on_pdf_picked(self, e: ft.FilePickerResultEvent):
        """Handle PDF file picker result."""
        if not self.page or not e.path:
            return
        
        try:
            users = self.db_manager.get_top_active_users_by_group(self.group_id, limit=10000)
            
            # Convert to TelegramUser objects for export
            from database.models import TelegramUser
            user_objects = []
            for user_data in users:
                user = TelegramUser(
                    user_id=user_data['user_id'],
                    username=user_data.get('username'),
                    first_name=user_data.get('first_name'),
                    last_name=user_data.get('last_name'),
                    full_name=user_data.get('full_name'),
                    phone=user_data.get('phone'),
                    profile_photo_path=user_data.get('profile_photo_path')
                )
                user_objects.append(user)
            
            title = f"Active Users - {self.group_name}"
            if self.export_service.export_users_to_pdf(user_objects, e.path, title):
                theme_manager.show_snackbar(
                    self.page,
                    f"{theme_manager.t('export_success')}: {e.path}",
                    bgcolor=ft.Colors.GREEN
                )
            else:
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("export_error"),
                    bgcolor=ft.Colors.RED
                )
        except Exception as ex:
            theme_manager.show_snackbar(
                self.page,
                f"{theme_manager.t('export_error')}: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def _close_dialog(self, e):
        """Close the dialog."""
        if self.page:
            self.page.close(self)

