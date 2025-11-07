"""
Messages tab component for Telegram page.
"""

import flet as ft
from typing import Optional, Callable, List
from ui.theme import theme_manager
from ui.components import DataTable
from utils.helpers import format_datetime
from ui.pages.telegram.components.filters_bar import FiltersBarComponent


class MessagesTabComponent:
    """Messages tab component."""
    
    def __init__(
        self,
        view_model,
        on_message_click: Callable[[int], None],
        on_refresh: Optional[Callable[[], None]] = None,
        on_export_excel: Optional[Callable[[], None]] = None,
        on_export_pdf: Optional[Callable[[], None]] = None
    ):
        self.view_model = view_model
        self.on_message_click = on_message_click
        self.on_refresh = on_refresh
        self.on_export_excel = on_export_excel
        self.on_export_pdf = on_export_pdf
        
        # Filters bar
        groups = view_model.get_all_groups()
        self.filters_bar = FiltersBarComponent(
            groups=groups,
            on_group_change=self._on_group_change,
            on_date_change=self._on_date_change,
            show_dates=True
        )
        
        # Messages table
        self.messages_table = self._create_messages_table()
        
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
            on_click=self._refresh_messages
        )
    
    def build(self) -> ft.Container:
        """Build the messages tab."""
        # Get search field and clear filter button from table
        search_field = self.messages_table.search_field
        clear_filter_btn = self.messages_table.clear_filter_button
        
        return ft.Container(
            content=ft.Column([
                # Filters row
                ft.Row([
                    clear_filter_btn if clear_filter_btn else ft.Container(),
                    search_field if search_field else ft.Container(),
                    self.filters_bar.build(),
                    self.refresh_btn,
                    self.export_menu,
                ], spacing=10, wrap=False),
                
                # Table
                ft.Container(
                    content=self.messages_table,
                    expand=True,
                    width=None
                ),
            ], spacing=15, expand=True),
            padding=10,
            expand=True
        )
    
    def refresh_messages(self):
        """Refresh messages table."""
        group_id = self.filters_bar.get_selected_group()
        
        if not group_id:
            self.messages_table.refresh([], [])
            self.messages_table.update_filter_state(self._has_filters())
            return
        
        messages = self.view_model.get_messages(
            group_id=group_id,
            start_date=self.filters_bar.get_start_date(),
            end_date=self.filters_bar.get_end_date(),
            limit=100
        )
        
        rows = []
        row_metadata = []
        for idx, msg in enumerate(messages, 1):
            user = self.view_model.get_user_by_id(msg.user_id)
            user_name = user.full_name if user else "Unknown"
            
            rows.append([
                idx,
                user_name,
                user.phone if user and user.phone else "-",
                msg.content[:100] + "..." if msg.content and len(msg.content) > 100 else msg.content or "",
                format_datetime(msg.date_sent, "%Y-%m-%d %H:%M"),
                "Yes" if msg.has_media else "No",
                msg.media_type or "-",
                "",  # Link column
            ])
            
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
        self.messages_table.update_filter_state(self._has_filters())
    
    def clear_filters(self):
        """Clear all filters."""
        self.filters_bar.clear_filters()
        if self.messages_table.search_field:
            self.messages_table.search_field.value = ""
        self.messages_table.search_query = ""
        self.refresh_messages()
        self.messages_table.update_filter_state(False)
    
    def get_selected_group(self) -> Optional[int]:
        """Get selected group ID."""
        return self.filters_bar.get_selected_group()
    
    def get_messages(self) -> List:
        """Get current filtered messages."""
        return self.view_model.get_messages(
            group_id=self.filters_bar.get_selected_group(),
            start_date=self.filters_bar.get_start_date(),
            end_date=self.filters_bar.get_end_date(),
            limit=100
        )
    
    def _create_messages_table(self) -> DataTable:
        """Create messages data table."""
        column_alignments = ["center", "center", "center", "left", "center", "center", "center", "center"]
        
        return DataTable(
            columns=["No", "User", "Phone", "Message", "Date", "Media", "Type", "Link"],
            rows=[],
            on_row_click=self.on_message_click,
            page_size=50,
            column_alignments=column_alignments,
            row_metadata=[],
            on_clear_filters=self.clear_filters,
            has_filters=self._has_filters()
        )
    
    def _has_filters(self) -> bool:
        """Check if any filters are active."""
        return (
            self.filters_bar.get_selected_group() is not None or
            (self.filters_bar.get_start_date() is not None) or
            (self.filters_bar.get_end_date() is not None) or
            (self.messages_table.search_query if hasattr(self.messages_table, 'search_query') else False)
        )
    
    def _on_group_change(self, group_id: Optional[int]):
        """Handle group change."""
        if self.on_refresh:
            self.on_refresh()
    
    def _on_date_change(self):
        """Handle date change."""
        if self.on_refresh:
            self.on_refresh()
    
    def _refresh_messages(self, e):
        """Handle refresh button click."""
        if self.on_refresh:
            self.on_refresh()

