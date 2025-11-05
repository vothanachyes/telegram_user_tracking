"""
Telegram page with messages and users tables.
"""

import flet as ft
from typing import Optional
from datetime import datetime, timedelta
from ui.theme import theme_manager
from ui.components import DataTable
from database.db_manager import DatabaseManager
from services.export_service import ExportService
from utils.helpers import format_datetime


class TelegramPage(ft.Container):
    """Telegram page with tabs for messages and users."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.export_service = ExportService(db_manager)
        self.selected_group = None
        
        # Create tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text=theme_manager.t("messages"),
                    icon=ft.icons.MESSAGE,
                    content=self._create_messages_tab()
                ),
                ft.Tab(
                    text=theme_manager.t("users"),
                    icon=ft.icons.PEOPLE,
                    content=self._create_users_tab()
                ),
            ],
            expand=True
        )
        
        super().__init__(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("telegram"),
                    size=32,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(height=10),
                self.tabs,
            ], spacing=10, expand=True),
            padding=20,
            expand=True
        )
    
    def _create_messages_tab(self) -> ft.Container:
        """Create messages tab content."""
        # Group selector
        groups = self.db_manager.get_all_groups()
        group_options = [f"{g.group_name} ({g.group_id})" for g in groups]
        
        self.group_dropdown = theme_manager.create_dropdown(
            label=theme_manager.t("select_group"),
            options=group_options if group_options else ["No groups"],
            on_change=self._on_group_selected
        )
        
        # Date filters (default: current month)
        today = datetime.now()
        first_day = today.replace(day=1)
        
        self.start_date_field = ft.TextField(
            label=theme_manager.t("start_date"),
            value=first_day.strftime("%Y-%m-%d"),
            width=150,
            border_radius=theme_manager.corner_radius
        )
        
        self.end_date_field = ft.TextField(
            label=theme_manager.t("end_date"),
            value=today.strftime("%Y-%m-%d"),
            width=150,
            border_radius=theme_manager.corner_radius
        )
        
        # Export buttons
        export_excel_btn = theme_manager.create_button(
            text=theme_manager.t("export_to_excel"),
            icon=ft.icons.TABLE_CHART,
            on_click=self._export_messages_excel,
            style="success"
        )
        
        export_pdf_btn = theme_manager.create_button(
            text=theme_manager.t("export_to_pdf"),
            icon=ft.icons.PICTURE_AS_PDF,
            on_click=self._export_messages_pdf,
            style="error"
        )
        
        refresh_btn = ft.IconButton(
            icon=ft.icons.REFRESH,
            tooltip=theme_manager.t("refresh"),
            on_click=self._refresh_messages
        )
        
        # Messages table
        self.messages_table = self._create_messages_table()
        
        return ft.Container(
            content=ft.Column([
                # Filters row
                ft.Row([
                    self.group_dropdown,
                    self.start_date_field,
                    self.end_date_field,
                    refresh_btn,
                ], spacing=10, wrap=True),
                
                # Export row
                ft.Row([
                    export_excel_btn,
                    export_pdf_btn,
                ], spacing=10),
                
                # Table
                self.messages_table,
            ], spacing=15, expand=True),
            padding=10,
            expand=True
        )
    
    def _create_messages_table(self) -> DataTable:
        """Create messages data table."""
        messages = self.db_manager.get_messages(limit=100)
        
        rows = []
        for idx, msg in enumerate(messages, 1):
            user = self.db_manager.get_user_by_id(msg.user_id)
            user_name = user.full_name if user else "Unknown"
            
            rows.append([
                idx,
                user_name,
                user.phone if user and user.phone else "-",
                msg.content[:100] + "..." if msg.content and len(msg.content) > 100 else msg.content or "",
                format_datetime(msg.date_sent, "%Y-%m-%d %H:%M"),
                "Yes" if msg.has_media else "No",
                msg.media_type or "-",
            ])
        
        return DataTable(
            columns=["No", "User", "Phone", "Message", "Date", "Media", "Type"],
            rows=rows,
            on_row_click=self._on_message_click,
            page_size=50
        )
    
    def _create_users_tab(self) -> ft.Container:
        """Create users tab content."""
        # Export buttons
        export_excel_btn = theme_manager.create_button(
            text=theme_manager.t("export_to_excel"),
            icon=ft.icons.TABLE_CHART,
            on_click=self._export_users_excel,
            style="success"
        )
        
        export_pdf_btn = theme_manager.create_button(
            text=theme_manager.t("export_to_pdf"),
            icon=ft.icons.PICTURE_AS_PDF,
            on_click=self._export_users_pdf,
            style="error"
        )
        
        refresh_btn = ft.IconButton(
            icon=ft.icons.REFRESH,
            tooltip=theme_manager.t("refresh"),
            on_click=self._refresh_users
        )
        
        # Users table
        self.users_table = self._create_users_table()
        
        return ft.Container(
            content=ft.Column([
                # Export row
                ft.Row([
                    export_excel_btn,
                    export_pdf_btn,
                    refresh_btn,
                ], spacing=10),
                
                # Table
                self.users_table,
            ], spacing=15, expand=True),
            padding=10,
            expand=True
        )
    
    def _create_users_table(self) -> DataTable:
        """Create users data table."""
        users = self.db_manager.get_all_users()
        
        rows = []
        for idx, user in enumerate(users, 1):
            rows.append([
                idx,
                user.username or "-",
                user.full_name,
                user.phone or "-",
                user.bio[:50] + "..." if user.bio and len(user.bio) > 50 else user.bio or "-",
            ])
        
        return DataTable(
            columns=["No", "Username", "Full Name", "Phone", "Bio"],
            rows=rows,
            on_row_click=self._on_user_click,
            page_size=50
        )
    
    def _on_group_selected(self, e):
        """Handle group selection."""
        # Extract group_id from selection
        # Format: "Group Name (group_id)"
        if e.control.value and e.control.value != "No groups":
            group_str = e.control.value
            group_id = int(group_str.split("(")[-1].strip(")"))
            self.selected_group = group_id
            self._refresh_messages(None)
    
    def _refresh_messages(self, e):
        """Refresh messages table."""
        # Get filter values
        group_id = self.selected_group
        
        # Get date range
        try:
            start_date = datetime.strptime(self.start_date_field.value, "%Y-%m-%d") if self.start_date_field.value else None
            end_date = datetime.strptime(self.end_date_field.value, "%Y-%m-%d") if self.end_date_field.value else None
        except:
            start_date = None
            end_date = None
        
        # Fetch messages
        messages = self.db_manager.get_messages(
            group_id=group_id,
            start_date=start_date,
            end_date=end_date,
            limit=100
        )
        
        # Update table
        rows = []
        for idx, msg in enumerate(messages, 1):
            user = self.db_manager.get_user_by_id(msg.user_id)
            user_name = user.full_name if user else "Unknown"
            
            rows.append([
                idx,
                user_name,
                user.phone if user and user.phone else "-",
                msg.content[:100] + "..." if msg.content and len(msg.content) > 100 else msg.content or "",
                format_datetime(msg.date_sent, "%Y-%m-%d %H:%M"),
                "Yes" if msg.has_media else "No",
                msg.media_type or "-",
            ])
        
        self.messages_table.refresh(rows)
    
    def _refresh_users(self, e):
        """Refresh users table."""
        users = self.db_manager.get_all_users()
        
        rows = []
        for idx, user in enumerate(users, 1):
            rows.append([
                idx,
                user.username or "-",
                user.full_name,
                user.phone or "-",
                user.bio[:50] + "..." if user.bio and len(user.bio) > 50 else user.bio or "-",
            ])
        
        self.users_table.refresh(rows)
    
    def _on_message_click(self, row_index: int):
        """Handle message row click."""
        # TODO: Show message detail dialog
        theme_manager.show_snackbar(
            self.page,
            f"Message details for row {row_index}",
            bgcolor=theme_manager.primary_color
        )
    
    def _on_user_click(self, row_index: int):
        """Handle user row click."""
        # TODO: Show user detail dialog
        theme_manager.show_snackbar(
            self.page,
            f"User details for row {row_index}",
            bgcolor=theme_manager.primary_color
        )
    
    def _export_messages_excel(self, e):
        """Export messages to Excel."""
        try:
            messages = self.db_manager.get_messages(group_id=self.selected_group)
            
            output_path = f"messages_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            if self.export_service.export_messages_to_excel(messages, output_path):
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("export_success"),
                    bgcolor=ft.colors.GREEN
                )
            else:
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("export_error"),
                    bgcolor=ft.colors.RED
                )
        except Exception as ex:
            theme_manager.show_snackbar(
                self.page,
                f"{theme_manager.t('export_error')}: {str(ex)}",
                bgcolor=ft.colors.RED
            )
    
    def _export_messages_pdf(self, e):
        """Export messages to PDF."""
        try:
            messages = self.db_manager.get_messages(group_id=self.selected_group)
            
            output_path = f"messages_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            if self.export_service.export_messages_to_pdf(messages, output_path):
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("export_success"),
                    bgcolor=ft.colors.GREEN
                )
            else:
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("export_error"),
                    bgcolor=ft.colors.RED
                )
        except Exception as ex:
            theme_manager.show_snackbar(
                self.page,
                f"{theme_manager.t('export_error')}: {str(ex)}",
                bgcolor=ft.colors.RED
            )
    
    def _export_users_excel(self, e):
        """Export users to Excel."""
        try:
            users = self.db_manager.get_all_users()
            
            output_path = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            if self.export_service.export_users_to_excel(users, output_path):
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("export_success"),
                    bgcolor=ft.colors.GREEN
                )
            else:
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("export_error"),
                    bgcolor=ft.colors.RED
                )
        except Exception as ex:
            theme_manager.show_snackbar(
                self.page,
                f"{theme_manager.t('export_error')}: {str(ex)}",
                bgcolor=ft.colors.RED
            )
    
    def _export_users_pdf(self, e):
        """Export users to PDF."""
        try:
            users = self.db_manager.get_all_users()
            
            output_path = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            if self.export_service.export_users_to_pdf(users, output_path):
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("export_success"),
                    bgcolor=ft.colors.GREEN
                )
            else:
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("export_error"),
                    bgcolor=ft.colors.RED
                )
        except Exception as ex:
            theme_manager.show_snackbar(
                self.page,
                f"{theme_manager.t('export_error')}: {str(ex)}",
                bgcolor=ft.colors.RED
            )

