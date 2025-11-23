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
        cell_renderers: Optional[Dict[str, Callable]] = None,  # {"type": lambda row: ft.Container(...)}
    ):
        self.columns = columns
        self.data = data
        self.page_size = page_size
        self.on_row_click = on_row_click
        self.actions = actions or []
        self.cell_renderers = cell_renderers or {}
        self.current_page = 0
        self.search_query = ""
        
        # Sorting state
        self.sort_column: Optional[str] = None
        self.sort_direction: str = "asc"  # "asc" or "desc"
        
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
        
        # Apply sorting after filtering
        self._sort_data()
        
        self.total_pages = max(1, (len(self.filtered_data) + self.page_size - 1) // self.page_size)
    
    def _on_column_sort(self, column_key: str):
        """Handle column header click for sorting."""
        if self.sort_column == column_key:
            # Toggle direction: asc -> desc -> none (reset)
            if self.sort_direction == "asc":
                self.sort_direction = "desc"
            else:
                # Reset to no sorting
                self.sort_column = None
                self.sort_direction = "asc"
        else:
            # New column, start with ascending
            self.sort_column = column_key
            self.sort_direction = "asc"
        
        # Reset to first page and update table
        self.current_page = 0
        self._sort_data()
        self._update_table()
    
    def _sort_data(self):
        """Sort filtered data based on current sort column and direction."""
        if not self.sort_column or not self.filtered_data:
            return
        
        # Detect data type from first non-empty value
        def detect_type(column_key: str) -> str:
            """Detect the data type of a column."""
            for row in self.filtered_data:
                value = row.get(column_key)
                if value is None or value == "":
                    continue
                
                # Try to parse as number
                try:
                    # Remove currency symbols and commas for price columns
                    clean_value = str(value).replace("$", "").replace(",", "").replace(" KHR", "").strip()
                    if clean_value and clean_value != "Unlimited" and clean_value != "N/A":
                        float(clean_value)
                        return "numeric"
                except (ValueError, TypeError):
                    pass
                
                # Try to parse as date (ISO format)
                try:
                    if isinstance(value, str):
                        from datetime import datetime
                        datetime.fromisoformat(value.replace("Z", "+00:00"))
                        return "date"
                except (ValueError, TypeError):
                    pass
                
                # Default to string
                return "string"
            
            return "string"
        
        col_type = detect_type(self.sort_column)
        reverse = self.sort_direction == "desc"
        
        def sort_key(row: Dict) -> tuple:
            """Get sort key for a row."""
            value = row.get(self.sort_column)
            
            # Handle None/empty values - always sort to end (tuple with 1 as first element)
            if value is None or value == "":
                return (1, "")
            
            value_str = str(value)
            
            # Handle special formatted values - sort to end
            if value_str in ("Unlimited", "N/A", "Never"):
                return (1, value_str)
            
            if col_type == "numeric":
                try:
                    # Remove currency symbols and commas
                    clean_value = value_str.replace("$", "").replace(",", "").replace(" KHR", "").strip()
                    num_value = float(clean_value) if clean_value else 0.0
                    return (0, num_value)
                except (ValueError, TypeError):
                    return (0, 0.0)
            elif col_type == "date":
                try:
                    from datetime import datetime
                    if isinstance(value, str):
                        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                        return (0, dt.timestamp())
                    return (0, 0.0)
                except (ValueError, TypeError):
                    return (0, 0.0)
            else:
                # String comparison (case-insensitive)
                return (0, value_str.lower())
        
        # Sort the data
        self.filtered_data.sort(key=sort_key, reverse=reverse)
    
    def _create_table(self) -> ft.DataTable:
        """Create data table."""
        # Data rows (no manual header row - ft.DataTable handles headers via columns)
        data_rows = []
        start_idx = self.current_page * self.page_size
        end_idx = start_idx + self.page_size
        page_data = self.filtered_data[start_idx:end_idx]
        
        for row_data in page_data:
            cells = []
            for col in self.columns:
                col_key = col["key"]
                # Check if there's a custom renderer for this column
                if col_key in self.cell_renderers:
                    cell_content = self.cell_renderers[col_key](row_data)
                    cells.append(ft.DataCell(cell_content))
                else:
                    cells.append(
                        ft.DataCell(
                            ft.Text(
                                str(row_data.get(col_key, "")),
                                color=self.TEXT_COLOR,
                            )
                        )
                    )
            
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
        
        # Create sortable column headers with indicators
        data_columns = []
        for col in self.columns:
            col_key = col["key"]
            label = col["label"]
            
            # Determine sort indicator
            if self.sort_column == col_key:
                if self.sort_direction == "asc":
                    sort_icon = ft.Icons.ARROW_UPWARD
                else:
                    sort_icon = ft.Icons.ARROW_DOWNWARD
            else:
                sort_icon = None
            
            # Create header label with sort indicator
            if sort_icon:
                header_content = ft.Row(
                    controls=[
                        ft.Text(label, color=self.TEXT_COLOR, weight=ft.FontWeight.BOLD),
                        ft.Icon(sort_icon, size=16, color=self.TEXT_COLOR),
                    ],
                    spacing=5,
                    tight=True,
                )
            else:
                header_content = ft.Text(label, color=self.TEXT_COLOR, weight=ft.FontWeight.BOLD)
            
            # Create sortable column
            data_columns.append(
                ft.DataColumn(
                    label=header_content,
                    on_sort=lambda e, key=col_key: self._on_column_sort(key),
                    tooltip=f"Click to sort by {label}",
                )
            )
        
        # Add Actions column if needed (not sortable)
        if self.actions:
            data_columns.append(
                ft.DataColumn(
                    label=ft.Text("Actions", color=self.TEXT_COLOR, weight=ft.FontWeight.BOLD),
                )
            )
        
        return ft.DataTable(
            columns=data_columns,
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

