"""
Reusable data table component with pagination and search.
"""

import flet as ft
from typing import List, Callable, Optional, Any
from ui.theme import theme_manager


class DataTable(ft.Container):
    """Custom data table with search, filter, and pagination."""
    
    def __init__(
        self,
        columns: List[str],
        rows: List[List[Any]],
        on_row_click: Optional[Callable[[int], None]] = None,
        page_size: int = 50,
        searchable: bool = True
    ):
        self.columns = columns
        self.all_rows = rows
        self.filtered_rows = rows
        self.on_row_click = on_row_click
        self.page_size = page_size
        self.current_page = 0
        self.search_query = ""
        
        # Create search field
        self.search_field = ft.TextField(
            hint_text=theme_manager.t("search"),
            prefix_icon=ft.icons.SEARCH,
            on_change=self._on_search,
            width=300,
            border_radius=theme_manager.corner_radius
        ) if searchable else None
        
        # Create table
        self.data_table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(col, weight=ft.FontWeight.BOLD)) for col in columns],
            rows=[],
            border=ft.border.all(1, theme_manager.border_color),
            border_radius=theme_manager.corner_radius,
            heading_row_color=theme_manager.primary_color,
            heading_row_height=50,
            data_row_min_height=60,
            column_spacing=20,
        )
        
        # Pagination controls
        self.page_info = ft.Text("", size=14)
        self.prev_button = ft.IconButton(
            icon=ft.icons.ARROW_BACK,
            on_click=self._previous_page,
            tooltip=theme_manager.t("previous")
        )
        self.next_button = ft.IconButton(
            icon=ft.icons.ARROW_FORWARD,
            on_click=self._next_page,
            tooltip=theme_manager.t("next")
        )
        
        # Layout
        controls = []
        
        # Search bar
        if self.search_field:
            controls.append(
                ft.Row([
                    self.search_field,
                    ft.Container(expand=True),
                ], alignment=ft.MainAxisAlignment.START)
            )
        
        # Table in scrollable container
        controls.append(
            ft.Container(
                content=ft.Column([
                    self.data_table
                ], scroll=ft.ScrollMode.AUTO),
                height=600,
                border=ft.border.all(1, theme_manager.border_color),
                border_radius=theme_manager.corner_radius,
                padding=10
            )
        )
        
        # Pagination
        controls.append(
            ft.Row([
                self.prev_button,
                self.page_info,
                self.next_button,
                ft.Container(expand=True),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        )
        
        super().__init__(
            content=ft.Column(controls, spacing=10),
            padding=10
        )
        
        self._update_table()
    
    def _on_search(self, e):
        """Handle search input."""
        self.search_query = e.control.value.lower()
        self._filter_rows()
        self.current_page = 0
        self._update_table()
    
    def _filter_rows(self):
        """Filter rows based on search query."""
        if not self.search_query:
            self.filtered_rows = self.all_rows
        else:
            self.filtered_rows = [
                row for row in self.all_rows
                if any(self.search_query in str(cell).lower() for cell in row)
            ]
    
    def _update_table(self):
        """Update table with current page data."""
        start = self.current_page * self.page_size
        end = start + self.page_size
        page_rows = self.filtered_rows[start:end]
        
        # Update data table rows
        self.data_table.rows = [
            ft.DataRow(
                cells=[ft.DataCell(ft.Text(str(cell))) for cell in row],
                on_select_changed=lambda e, idx=idx: self._on_row_select(idx) if self.on_row_click else None
            )
            for idx, row in enumerate(page_rows, start=start)
        ]
        
        # Update pagination info
        total_rows = len(self.filtered_rows)
        total_pages = (total_rows + self.page_size - 1) // self.page_size if total_rows > 0 else 0
        self.page_info.value = f"Page {self.current_page + 1} of {total_pages} ({total_rows} rows)"
        
        # Update button states
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= total_pages - 1
        
        self.update()
    
    def _on_row_select(self, row_index: int):
        """Handle row selection."""
        if self.on_row_click:
            self.on_row_click(row_index)
    
    def _previous_page(self, e):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_table()
    
    def _next_page(self, e):
        """Go to next page."""
        total_pages = (len(self.filtered_rows) + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._update_table()
    
    def refresh(self, rows: List[List[Any]]):
        """Refresh table with new data."""
        self.all_rows = rows
        self.current_page = 0
        self.search_query = ""
        if self.search_field:
            self.search_field.value = ""
        self._filter_rows()
        self._update_table()

