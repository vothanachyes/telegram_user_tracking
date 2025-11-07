"""
Telegram page with messages and users tables.
"""

import flet as ft
from typing import Optional
from datetime import datetime, timedelta
from ui.theme import theme_manager
from ui.components import DataTable
from ui.dialogs import MessageDetailDialog, UserDetailDialog
from database.db_manager import DatabaseManager
from services.export import ExportService
from utils.helpers import format_datetime, get_telegram_user_link


class TelegramPage(ft.Container):
    """Telegram page with tabs for messages and users."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.export_service = ExportService(db_manager)
        self.selected_group = None
        self.selected_users_group = None  # For users tab
        self.page: Optional[ft.Page] = None
        
        # File pickers for export
        self.messages_excel_picker = ft.FilePicker(
            on_result=self._on_messages_excel_picked
        )
        self.messages_pdf_picker = ft.FilePicker(
            on_result=self._on_messages_pdf_picked
        )
        self.users_excel_picker = ft.FilePicker(
            on_result=self._on_users_excel_picked
        )
        self.users_pdf_picker = ft.FilePicker(
            on_result=self._on_users_pdf_picked
        )
        
        # Create tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text=theme_manager.t("messages"),
                    icon=ft.Icons.MESSAGE,
                    content=self._create_messages_tab()
                ),
                ft.Tab(
                    text=theme_manager.t("users"),
                    icon=ft.Icons.PEOPLE,
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
    
    def set_page(self, page: ft.Page):
        """Set page reference and add file pickers to overlay."""
        self.page = page
        # Ensure overlay exists
        if not hasattr(page, 'overlay') or page.overlay is None:
            page.overlay = []
        
        # Add file pickers to page overlay (avoid duplicates)
        pickers = [
            self.messages_excel_picker,
            self.messages_pdf_picker,
            self.users_excel_picker,
            self.users_pdf_picker,
        ]
        for picker in pickers:
            if picker not in page.overlay:
                page.overlay.append(picker)
        page.update()
    
    def _ensure_picker_in_overlay(self, picker: ft.FilePicker):
        """Ensure file picker is in page overlay."""
        if not self.page:
            return False
        if not hasattr(self.page, 'overlay') or self.page.overlay is None:
            self.page.overlay = []
        if picker not in self.page.overlay:
            self.page.overlay.append(picker)
            self.page.update()
        return True
    
    def _create_messages_tab(self) -> ft.Container:
        """Create messages tab content."""
        # Group selector
        groups = self.db_manager.get_all_groups()
        group_options = [f"{g.group_name} ({g.group_id})" for g in groups]
        
        self.group_dropdown = theme_manager.create_dropdown(
            label=theme_manager.t("select_group"),
            options=group_options if group_options else ["No groups"],
            on_change=self._on_group_selected,
            width=250  # Fixed width for inline display
        )
        
        # Date filters (default: current month)
        today = datetime.now()
        first_day = today.replace(day=1)
        
        self.start_date_field = ft.TextField(
            label=theme_manager.t("start_date"),
            value=first_day.strftime("%Y-%m-%d"),
            width=140,
            border_radius=theme_manager.corner_radius
        )
        
        self.end_date_field = ft.TextField(
            label=theme_manager.t("end_date"),
            value=today.strftime("%Y-%m-%d"),
            width=140,
            border_radius=theme_manager.corner_radius
        )
        
        # Export menu (three-dot menu)
        export_menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            tooltip=theme_manager.t("export"),
            items=[
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_excel"),
                    icon=ft.Icons.TABLE_CHART,
                    on_click=self._export_messages_excel
                ),
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_pdf"),
                    icon=ft.Icons.PICTURE_AS_PDF,
                    on_click=self._export_messages_pdf
                ),
            ]
        )
        
        refresh_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip=theme_manager.t("refresh"),
            on_click=self._refresh_messages
        )
        
        # Messages table
        self.messages_table = self._create_messages_table()
        
        # Get search field and clear filter button from table (if available)
        search_field = self.messages_table.search_field
        clear_filter_btn = self.messages_table.clear_filter_button
        
        return ft.Container(
            content=ft.Column([
                # Filters row - all controls inline
                # Order: Clear Filter, Search, Date fields, then Group Selection, Refresh, Menu at end
                ft.Row([
                    clear_filter_btn if clear_filter_btn else ft.Container(),  # Clear filter button
                    search_field if search_field else ft.Container(),  # Search field from table
                    self.start_date_field,
                    self.end_date_field,
                    ft.Container(width=20),  # Fixed spacer
                    self.group_dropdown,  # Group selection
                    refresh_btn,  # Refresh button
                    export_menu,  # Export menu
                ], spacing=10, wrap=False),
                
                # Table - wrapped to ensure full width
                ft.Container(
                    content=self.messages_table,
                    expand=True,
                    width=None  # Allow full width
                ),
            ], spacing=15, expand=True),
            padding=10,
            expand=True
        )
    
    def _create_messages_table(self) -> DataTable:
        """Create messages data table."""
        # Show empty state if no group selected
        if not self.selected_group:
            rows = []
            row_metadata = []
        else:
            messages = self.db_manager.get_messages(group_id=self.selected_group, limit=100)
            
            rows = []
            row_metadata = []
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
                    "",  # Link column - will be rendered as icon
                ])
                
                # Add metadata for link column (last column, index 7)
                row_meta = {
                    'cells': {
                        7: {
                            'link': msg.message_link,
                            'renderer': 'icon'
                        } if msg.message_link else {}
                    }
                }
                row_metadata.append(row_meta)
        
        # Column alignments: center all except "Message" (index 3)
        column_alignments = ["center", "center", "center", "left", "center", "center", "center", "center"]
        
        return DataTable(
            columns=["No", "User", "Phone", "Message", "Date", "Media", "Type", "Link"],
            rows=rows,
            on_row_click=self._on_message_click,
            page_size=50,
            column_alignments=column_alignments,
            row_metadata=row_metadata,
            on_clear_filters=self._clear_messages_filters,
            has_filters=self._has_messages_filters()
        )
    
    def _create_users_tab(self) -> ft.Container:
        """Create users tab content."""
        # Group selector
        groups = self.db_manager.get_all_groups()
        group_options = [f"{g.group_name} ({g.group_id})" for g in groups]
        
        self.users_group_dropdown = theme_manager.create_dropdown(
            label=theme_manager.t("select_group"),
            options=group_options if group_options else ["No groups"],
            on_change=self._on_users_group_selected,
            width=250  # Fixed width for inline display
        )
        
        # Export menu (three-dot menu)
        export_menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            tooltip=theme_manager.t("export"),
            items=[
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_excel"),
                    icon=ft.Icons.TABLE_CHART,
                    on_click=self._export_users_excel
                ),
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_pdf"),
                    icon=ft.Icons.PICTURE_AS_PDF,
                    on_click=self._export_users_pdf
                ),
            ]
        )
        
        refresh_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip=theme_manager.t("refresh"),
            on_click=self._refresh_users
        )
        
        # Users table
        self.users_table = self._create_users_table()
        
        # Get search field and clear filter button from table (if available)
        search_field = self.users_table.search_field
        clear_filter_btn = self.users_table.clear_filter_button
        
        return ft.Container(
            content=ft.Column([
                # Filters row - all controls inline
                # Order: Clear Filter, Search, Group Selection, Refresh, Menu at end
                ft.Row([
                    clear_filter_btn if clear_filter_btn else ft.Container(),  # Clear filter button
                    search_field if search_field else ft.Container(),  # Search field from table
                    ft.Container(width=20),  # Fixed spacer
                    self.users_group_dropdown,  # Group selection
                    refresh_btn,  # Refresh button
                    export_menu,  # Export menu
                ], spacing=10, wrap=False),
                
                # Table - wrapped to ensure full width
                ft.Container(
                    content=self.users_table,
                    expand=True,
                    width=None  # Allow full width
                ),
            ], spacing=15, expand=True),
            padding=10,
            expand=True
        )
    
    def _create_users_table(self) -> DataTable:
        """Create users data table."""
        # Show empty state if no group selected
        if not self.selected_users_group:
            rows = []
            row_metadata = []
        else:
            users = self.db_manager.get_users_by_group(self.selected_users_group)
            
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
                
                # Add metadata for clickable username (index 1) only
                row_meta = {
                    'cells': {}
                }
                if user_link:
                    # Username column (index 1) - clickable if username exists
                    if user.username:
                        row_meta['cells'][1] = {'link': user_link}
                row_metadata.append(row_meta)
        
        # Column alignments: center all except "Bio" (index 4)
        column_alignments = ["center", "center", "center", "center", "left"]
        
        return DataTable(
            columns=["No", "Username", "Full Name", "Phone", "Bio"],
            rows=rows,
            on_row_click=self._on_user_click,
            page_size=50,
            column_alignments=column_alignments,
            row_metadata=row_metadata,
            on_clear_filters=self._clear_users_filters,
            has_filters=self._has_users_filters()
        )
    
    def _on_group_selected(self, e):
        """Handle group selection for messages tab."""
        # Extract group_id from selection
        # Format: "Group Name (group_id)"
        if e.control.value and e.control.value != "No groups":
            group_str = e.control.value
            group_id = int(group_str.split("(")[-1].strip(")"))
            self.selected_group = group_id
        else:
            self.selected_group = None
        self._refresh_messages(None)
    
    def _has_messages_filters(self) -> bool:
        """Check if any filters are active for messages."""
        return (
            self.selected_group is not None or
            (self.start_date_field.value and self.start_date_field.value.strip()) or
            (self.end_date_field.value and self.end_date_field.value.strip()) or
            (self.messages_table.search_query if hasattr(self.messages_table, 'search_query') else False)
        )
    
    def _clear_messages_filters(self):
        """Clear all message filters."""
        self.selected_group = None
        self.group_dropdown.value = None
        self.start_date_field.value = ""
        self.end_date_field.value = ""
        if self.messages_table.search_field:
            self.messages_table.search_field.value = ""
        self.messages_table.search_query = ""
        self._refresh_messages(None)
        self.messages_table.update_filter_state(False)
    
    def _refresh_messages(self, e):
        """Refresh messages table."""
        # Show empty state if no group selected
        if not self.selected_group:
            self.messages_table.refresh([], [])
            self.messages_table.update_filter_state(self._has_messages_filters())
            return
        
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
        row_metadata = []
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
                "",  # Link column - will be rendered as icon
            ])
            
            # Add metadata for link column (last column, index 7)
            row_meta = {
                'cells': {
                    7: {
                        'link': msg.message_link,
                        'renderer': 'icon'
                    } if msg.message_link else {}
                }
            }
            row_metadata.append(row_meta)
        
        self.messages_table.refresh(rows, row_metadata)
        self.messages_table.update_filter_state(self._has_messages_filters())
    
    def _on_users_group_selected(self, e):
        """Handle group selection for users tab."""
        # Extract group_id from selection
        # Format: "Group Name (group_id)"
        if e.control.value and e.control.value != "No groups":
            group_str = e.control.value
            group_id = int(group_str.split("(")[-1].strip(")"))
            self.selected_users_group = group_id
        else:
            self.selected_users_group = None
        self._refresh_users(None)
    
    def _has_users_filters(self) -> bool:
        """Check if any filters are active for users."""
        if not hasattr(self, 'users_table') or self.users_table is None:
            return self.selected_users_group is not None
        return (
            self.selected_users_group is not None or
            (self.users_table.search_query if hasattr(self.users_table, 'search_query') else False)
        )
    
    def _clear_users_filters(self):
        """Clear all user filters."""
        self.selected_users_group = None
        if hasattr(self, 'users_group_dropdown') and self.users_group_dropdown:
            self.users_group_dropdown.value = None
        if hasattr(self, 'users_table') and self.users_table:
            if self.users_table.search_field:
                self.users_table.search_field.value = ""
            self.users_table.search_query = ""
        self._refresh_users(None)
        if hasattr(self, 'users_table') and self.users_table:
            self.users_table.update_filter_state(False)
    
    def _refresh_users(self, e):
        """Refresh users table."""
        # Show empty state if no group selected
        if not self.selected_users_group:
            self.users_table.refresh([], [])
            self.users_table.update_filter_state(self._has_users_filters())
            return
        
        users = self.db_manager.get_users_by_group(self.selected_users_group)
        
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
            
            # Add metadata for clickable username (index 1) and full name (index 2)
            row_meta = {
                'cells': {}
            }
            if user_link:
                # Username column (index 1) - clickable if username exists
                if user.username:
                    row_meta['cells'][1] = {'link': user_link}
                # Full Name column (index 2) - clickable if username exists
                if user.username:
                    row_meta['cells'][2] = {'link': user_link}
            row_metadata.append(row_meta)
        
        self.users_table.refresh(rows, row_metadata)
        self.users_table.update_filter_state(self._has_users_filters())
    
    def _on_message_click(self, row_index: int):
        """Handle message row click."""
        # Get the message from current filtered list
        # Get filter values
        group_id = self.selected_group
        
        try:
            start_date = datetime.strptime(self.start_date_field.value, "%Y-%m-%d") if self.start_date_field.value else None
            end_date = datetime.strptime(self.end_date_field.value, "%Y-%m-%d") if self.end_date_field.value else None
        except:
            start_date = None
            end_date = None
        
        # Fetch messages with current filters
        messages = self.db_manager.get_messages(
            group_id=group_id,
            start_date=start_date,
            end_date=end_date,
            limit=100
        )
        
        if row_index < len(messages):
            message = messages[row_index]
            
            # Create and show dialog
            dialog = MessageDetailDialog(
                db_manager=self.db_manager,
                message=message,
                on_delete=lambda: self._refresh_messages(None),
                on_update=lambda: self._refresh_messages(None)
            )
            
            if self.page:
                # Set page reference for dialog
                dialog.page = self.page
                # Open dialog using Flet's page.open() method
                self.page.open(dialog)
    
    def _on_user_click(self, row_index: int):
        """Handle user row click."""
        # Get users from selected group
        if not self.selected_users_group:
            return
        
        users = self.db_manager.get_users_by_group(self.selected_users_group)
        
        if row_index < len(users):
            user = users[row_index]
            
            # Create and show dialog
            dialog = UserDetailDialog(
                db_manager=self.db_manager,
                user=user,
                on_delete=lambda: self._refresh_users(None),
                on_update=lambda: self._refresh_users(None)
            )
            
            if self.page:
                # Set page reference for dialog
                dialog.page = self.page
                # Open dialog using Flet's page.open() method
                self.page.open(dialog)
    
    def _export_messages_excel(self, e):
        """Export messages to Excel - show file picker first."""
        if not self.page:
            return
        
        # Get messages count to validate
        messages = self.db_manager.get_messages(group_id=self.selected_group)
        if not messages:
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("no_data"),
                bgcolor=ft.Colors.ORANGE
            )
            return
        
        # Ensure file picker is in overlay before showing
        self._ensure_picker_in_overlay(self.messages_excel_picker)
        
        # Show file picker
        default_name = f"messages_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        try:
            self.messages_excel_picker.save_file(
                dialog_title=theme_manager.t("export_to_excel"),
                file_name=default_name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["xlsx"]
            )
        except Exception as ex:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error opening file picker: {ex}", exc_info=True)
            theme_manager.show_snackbar(
                self.page,
                f"Error opening file picker: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def _on_messages_excel_picked(self, e: ft.FilePickerResultEvent):
        """Handle messages Excel file picker result."""
        if not self.page or not e.path:
            return
        
        try:
            messages = self.db_manager.get_messages(group_id=self.selected_group)
            
            if self.export_service.export_messages_to_excel(messages, e.path):
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
    
    def _export_messages_pdf(self, e):
        """Export messages to PDF - show file picker first."""
        if not self.page:
            return
        
        # Get messages count to validate
        messages = self.db_manager.get_messages(group_id=self.selected_group)
        if not messages:
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("no_data"),
                bgcolor=ft.Colors.ORANGE
            )
            return
        
        # Ensure file picker is in overlay before showing
        self._ensure_picker_in_overlay(self.messages_pdf_picker)
        
        # Show file picker
        default_name = f"messages_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        try:
            self.messages_pdf_picker.save_file(
                dialog_title=theme_manager.t("export_to_pdf"),
                file_name=default_name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["pdf"]
            )
        except Exception as ex:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error opening file picker: {ex}", exc_info=True)
            theme_manager.show_snackbar(
                self.page,
                f"Error opening file picker: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def _on_messages_pdf_picked(self, e: ft.FilePickerResultEvent):
        """Handle messages PDF file picker result."""
        if not self.page or not e.path:
            return
        
        try:
            messages = self.db_manager.get_messages(group_id=self.selected_group)
            
            if self.export_service.export_messages_to_pdf(messages, e.path):
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
    
    def _export_users_excel(self, e):
        """Export users to Excel - show file picker first."""
        if not self.page:
            return
        
        # Get users count to validate
        users = self.db_manager.get_all_users()
        if not users:
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("no_data"),
                bgcolor=ft.Colors.ORANGE
            )
            return
        
        # Ensure file picker is in overlay before showing
        self._ensure_picker_in_overlay(self.users_excel_picker)
        
        # Show file picker
        default_name = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        try:
            self.users_excel_picker.save_file(
                dialog_title=theme_manager.t("export_to_excel"),
                file_name=default_name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["xlsx"]
            )
        except Exception as ex:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error opening file picker: {ex}", exc_info=True)
            theme_manager.show_snackbar(
                self.page,
                f"Error opening file picker: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def _on_users_excel_picked(self, e: ft.FilePickerResultEvent):
        """Handle users Excel file picker result."""
        if not self.page or not e.path:
            return
        
        try:
            users = self.db_manager.get_all_users()
            
            if self.export_service.export_users_to_excel(users, e.path):
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
    
    def _export_users_pdf(self, e):
        """Export users to PDF - show file picker first."""
        if not self.page:
            return
        
        # Get users count to validate
        users = self.db_manager.get_all_users()
        if not users:
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("no_data"),
                bgcolor=ft.Colors.ORANGE
            )
            return
        
        # Ensure file picker is in overlay before showing
        self._ensure_picker_in_overlay(self.users_pdf_picker)
        
        # Show file picker
        default_name = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        try:
            self.users_pdf_picker.save_file(
                dialog_title=theme_manager.t("export_to_pdf"),
                file_name=default_name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["pdf"]
            )
        except Exception as ex:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error opening file picker: {ex}", exc_info=True)
            theme_manager.show_snackbar(
                self.page,
                f"Error opening file picker: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def _on_users_pdf_picked(self, e: ft.FilePickerResultEvent):
        """Handle users PDF file picker result."""
        if not self.page or not e.path:
            return
        
        try:
            users = self.db_manager.get_all_users()
            
            if self.export_service.export_users_to_pdf(users, e.path):
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

