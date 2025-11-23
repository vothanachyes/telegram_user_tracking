"""
User messages table component.
"""

import flet as ft
from typing import Optional, Callable, List
from datetime import datetime
from ui.theme import theme_manager
from ui.components import DataTable, DateRangeSelector
from utils.helpers import format_datetime


class UserMessagesComponent:
    """User messages table component."""
    
    def __init__(
        self,
        on_message_click: Callable[[int], None],
        on_refresh: Optional[Callable[[], None]] = None
    ):
        self.on_message_click = on_message_click
        self.on_refresh = on_refresh
        self.page: Optional[ft.Page] = None
        
        # Date range selector (using generic component)
        self.date_range_selector = DateRangeSelector(
            on_date_range_changed=self._on_date_range_changed,
            default_range="month"
        )
        
        # Group selector
        self.group_dropdown: Optional[ft.Dropdown] = None
        self.selected_group: Optional[int] = None
        
        # Messages table
        self.messages_table = self._create_messages_table()
    
    def build(self, groups: List, default_group_id: Optional[int] = None) -> ft.Container:
        """Build the messages component."""
        # Setup group dropdown
        group_options = [f"{g.group_name} ({g.group_id})" for g in groups]
        if group_options and default_group_id:
            self.selected_group = default_group_id
            default_group_value = next(
                (opt for opt in group_options if f"({default_group_id})" in opt),
                group_options[0] if group_options else None
            )
        else:
            default_group_value = group_options[0] if group_options else None
        
        self.group_dropdown = theme_manager.create_dropdown(
            label=theme_manager.t("select_group"),
            options=group_options if group_options else ["No groups"],
            value=default_group_value,
            on_change=self._on_group_selected,
            width=250
        )
        
        refresh_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip=theme_manager.t("refresh"),
            on_click=self._refresh_messages
        )
        
        return ft.Container(
            content=ft.Column([
                # Filters row
                ft.Row([
                    self.date_range_selector.build(),
                    ft.Container(width=20),
                    self.group_dropdown,
                    refresh_btn,
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
    
    def refresh_messages(self, messages: List):
        """Refresh messages table with new data."""
        rows = []
        row_metadata = []
        for idx, msg in enumerate(messages, 1):
            rows.append([
                idx,
                msg.content[:100] + "..." if msg.content and len(msg.content) > 100 else msg.content or "",
                format_datetime(msg.date_sent, "%Y-%m-%d %H:%M"),
                "Yes" if msg.has_media else "No",
                msg.media_type or "-",
                "",  # Link column
            ])
            
            row_meta = {
                'cells': {
                    5: {
                        'link': msg.message_link,
                        'renderer': 'icon'
                    } if msg.message_link else {}
                }
            }
            row_metadata.append(row_meta)
        
        self.messages_table.refresh(rows, row_metadata)
    
    def clear_messages(self):
        """Clear messages table."""
        self.messages_table.refresh([], [])
    
    def get_start_date(self) -> Optional[datetime]:
        """Get start date."""
        return self.date_range_selector.get_start_date()
    
    def get_end_date(self) -> Optional[datetime]:
        """Get end date."""
        return self.date_range_selector.get_end_date()
    
    def set_page(self, page: ft.Page):
        """Set page reference for date pickers."""
        self.page = page
        if self.date_range_selector:
            self.date_range_selector.set_page(page)
    
    def get_selected_group(self) -> Optional[int]:
        """Get selected group ID."""
        return self.selected_group
    
    def _create_messages_table(self) -> DataTable:
        """Create messages data table."""
        column_alignments = ["center", "left", "center", "center", "center", "center"]
        
        return DataTable(
            columns=["No", "Message", "Date", "Media", "Type", "Link"],
            rows=[],
            on_row_click=self.on_message_click,
            page_size=50,
            column_alignments=column_alignments,
            row_metadata=[],
            searchable=False
        )
    
    def _on_date_range_changed(self, start_date: datetime, end_date: datetime):
        """Handle date range change."""
        if self.on_refresh:
            self.on_refresh()
    
    def _on_group_selected(self, e):
        """Handle group selection."""
        if e.control.value and e.control.value != "No groups":
            group_str = e.control.value
            group_id = int(group_str.split("(")[-1].strip(")"))
            self.selected_group = group_id
        else:
            self.selected_group = None
        
        if self.on_refresh:
            self.on_refresh()
    
    def _refresh_messages(self, e):
        """Handle refresh button click."""
        if self.on_refresh:
            self.on_refresh()

