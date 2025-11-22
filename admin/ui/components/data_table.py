"""
Generic data table component for admin interface.
"""

import flet as ft
from typing import List, Dict, Optional, Callable
from admin.utils.constants import DEFAULT_PAGE_SIZE


class DataTable(ft.Container):
    """Generic data table with pagination and search."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    HEADER_BG = "#252525"
    BORDER_COLOR = "#333333"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    ROW_HOVER = "#2d2d2d"
    
    def __init__(
        self,
        columns: List[Dict[str, str]],  # [{"key": "email", "label": "Email", "width": 200}]
        data: List[Dict],
        page_size: int = DEFAULT_PAGE_SIZE,
        on_row_click: Optional[Callable[[Dict], None]] = None,
        actions: Optional[List[Dict]] = None,  # [{"label": "Edit", "icon": ft.Icons.EDIT, "on_click": func}]
    ):
        self.columns = columns
        self.data = data
        self.page_size = page_size
        self.on_row_click = on_row_click
        self.actions = actions or []
        self.current_page = 0
        self.search_query = ""
        
        # Filtered data
        self.filtered_data = data.copy()
        
        # Calculate total pages
        self.total_pages = max(1, (len(self.filtered_data) + page_size - 1) // page_size)
        
        # Create UI
        self.search_field = ft.TextField(
            label="Search",
            hint_text="Type to search...",
            bgcolor=self.HEADER_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            on_change=self._on_search,
            expand=True,
        )
        
        self.table = self._create_table()
        self.pagination_controls = self._create_pagination()
        
        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[self.search_field],
                        spacing=10,
                    ),
                    ft.Container(
                        content=self.table,
                        expand=True,
                        border=ft.border.all(1, self.BORDER_COLOR),
                        border_radius=5,
                    ),
                    self.pagination_controls,
                ],
                spacing=10,
                expand=True,
            ),
            expand=True,
            padding=ft.padding.all(20),
        )
    
    def _on_search(self, e: ft.ControlEvent):
        """Handle search input."""
        self.search_query = e.control.value.lower()
        self._filter_data()
        self.current_page = 0
        self._update_table()
    
    def _filter_data(self):
        """Filter data based on search query."""
        if not self.search_query:
            self.filtered_data = self.data.copy()
        else:
            self.filtered_data = [
                row for row in self.data
                if any(
                    str(value).lower().find(self.search_query) != -1
                    for value in row.values()
                )
            ]
        
        self.total_pages = max(1, (len(self.filtered_data) + self.page_size - 1) // self.page_size)
    
    def _create_table(self) -> ft.DataTable:
        """Create data table."""
        # Header row
        data_rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(
                        ft.Text(
                            col["label"],
                            color=self.TEXT_COLOR,
                            weight=ft.FontWeight.BOLD,
                        )
                    )
                    for col in self.columns
                ] + (
                    [ft.DataCell(ft.Text("Actions", color=self.TEXT_COLOR, weight=ft.FontWeight.BOLD))]
                    if self.actions else []
                ),
            )
        ]
        
        # Data rows
        start_idx = self.current_page * self.page_size
        end_idx = start_idx + self.page_size
        page_data = self.filtered_data[start_idx:end_idx]
        
        for row_data in page_data:
            cells = [
                ft.DataCell(
                    ft.Text(
                        str(row_data.get(col["key"], "")),
                        color=self.TEXT_COLOR,
                    )
                )
                for col in self.columns
            ]
            
            # Action buttons
            if self.actions:
                action_buttons = ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=action["icon"],
                            icon_color=self.TEXT_SECONDARY,
                            icon_size=18,
                            tooltip=action["label"],
                            on_click=lambda e, a=action, r=row_data: a["on_click"](r),
                        )
                        for action in self.actions
                    ],
                    spacing=5,
                )
                cells.append(ft.DataCell(action_buttons))
            
            data_rows.append(
                ft.DataRow(
                    cells=cells,
                    on_select_changed=lambda e, r=row_data: self._on_row_click(r) if self.on_row_click else None,
                )
            )
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(
                    label=ft.Text(col["label"]),
                )
                for col in self.columns
            ] + (
                [ft.DataColumn(label=ft.Text("Actions"))] if self.actions else []
            ),
            rows=data_rows,
            heading_row_color=self.HEADER_BG,
            data_row_color={"hovered": self.ROW_HOVER},
            border=ft.border.all(1, self.BORDER_COLOR),
        )
    
    def _create_pagination(self) -> ft.Row:
        """Create pagination controls."""
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.filtered_data))
        
        return ft.Row(
            controls=[
                ft.Text(
                    f"Showing {start_idx + 1}-{end_idx} of {len(self.filtered_data)}",
                    color=self.TEXT_SECONDARY,
                ),
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.CHEVRON_LEFT,
                            icon_color=self.TEXT_COLOR if self.current_page > 0 else self.TEXT_SECONDARY,
                            disabled=self.current_page == 0,
                            on_click=self._prev_page,
                        ),
                        ft.Text(
                            f"Page {self.current_page + 1} of {self.total_pages}",
                            color=self.TEXT_COLOR,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CHEVRON_RIGHT,
                            icon_color=self.TEXT_COLOR if self.current_page < self.total_pages - 1 else self.TEXT_SECONDARY,
                            disabled=self.current_page >= self.total_pages - 1,
                            on_click=self._next_page,
                        ),
                    ],
                    spacing=5,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
    
    def _prev_page(self, e: ft.ControlEvent):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_table()
    
    def _next_page(self, e: ft.ControlEvent):
        """Go to next page."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._update_table()
    
    def _on_row_click(self, row_data: Dict):
        """Handle row click."""
        if self.on_row_click:
            self.on_row_click(row_data)
    
    def _update_table(self):
        """Update table display."""
        self.table = self._create_table()
        self.pagination_controls = self._create_pagination()
        self.content.controls[1] = ft.Container(
            content=self.table,
            expand=True,
            border=ft.border.all(1, self.BORDER_COLOR),
            border_radius=5,
        )
        self.content.controls[2] = self.pagination_controls
        self.update()
    
    def refresh_data(self, new_data: List[Dict]):
        """Refresh table with new data."""
        self.data = new_data
        self._filter_data()
        self.current_page = 0
        self._update_table()

