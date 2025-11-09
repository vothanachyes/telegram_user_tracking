"""
Main data table component with pagination and search.
"""

import flet as ft
from typing import List, Callable, Optional, Any, Dict
from ui.theme import theme_manager
from ui.components.data_table.builders import TableBuilders
from ui.components.data_table.pagination import PaginationControls
from ui.components.data_table.filtering import TableFiltering


class DataTable(ft.Container):
    """Custom data table with search, filter, and pagination."""
    
    def __init__(
        self,
        columns: List[str],
        rows: List[List[Any]],
        on_row_click: Optional[Callable[[int], None]] = None,
        page_size: int = 50,
        searchable: bool = True,
        column_alignments: Optional[List[str]] = None,
        row_metadata: Optional[List[Dict[str, Any]]] = None,
        on_clear_filters: Optional[Callable[[], None]] = None,
        has_filters: bool = False
    ):
        self.columns = columns
        self.all_rows = rows
        self.filtered_rows = rows
        self.on_row_click = on_row_click
        self.page_size = page_size
        self.current_page = 0
        self.column_alignments = column_alignments or ["left"] * len(columns)
        self.row_metadata = row_metadata or []
        
        # Initialize filtering with search callback
        self.filtering = TableFiltering(
            searchable=searchable,
            on_clear_filters=on_clear_filters,
            has_filters=has_filters
        )
        
        # Override search callback to update table
        if self.filtering.search_field:
            self.filtering.search_field.on_change = self._on_search
        
        # Expose search field and clear filter button
        self.search_field = self.filtering.search_field
        self.clear_filter_button = self.filtering.clear_filter_button
        
        # Create table header
        self.table_header = TableBuilders.create_header(self.columns)
        
        # Container for table body rows (will be updated)
        self.table_body_container = ft.Column([], spacing=0)
        
        # Scrollable container for table body
        scrollable_column = ft.Column(
            [self.table_body_container],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            tight=True
        )
        
        self.scrollable_body = ft.Container(
            content=scrollable_column,
            expand=True,
            bgcolor=theme_manager.surface_color,
            border=ft.border.only(
                left=ft.BorderSide(1, theme_manager.border_color),
                right=ft.BorderSide(1, theme_manager.border_color),
                bottom=ft.BorderSide(1, theme_manager.border_color)
            ),
            border_radius=ft.border_radius.only(
                bottom_left=theme_manager.corner_radius,
                bottom_right=theme_manager.corner_radius
            ),
        )
        
        # Initialize pagination
        self.pagination = PaginationControls(
            on_previous=self._previous_page,
            on_next=self._next_page
        )
        
        # Layout
        table_column = ft.Column([
            self.table_header,
            self.scrollable_body,
        ], spacing=0, expand=True)
        
        # Main content column
        super().__init__(
            content=ft.Column([
                table_column,
                self.pagination.build_row(),
            ], spacing=10, expand=True),
            padding=10,
            expand=True
        )
        
        self._update_table()
    
    def _update_table(self):
        """Update table with current page data."""
        # Update filtered rows using filtering module
        self.filtered_rows = self.filtering.filter_rows(self.all_rows)
        
        start = self.current_page * self.page_size
        end = start + self.page_size
        page_rows = self.filtered_rows[start:end]
        
        # Update table body rows
        if page_rows:
            row_containers = []
            for idx, row in enumerate(page_rows, start=start):
                row_containers.append(
                    TableBuilders.create_table_row(
                        row_data=row,
                        row_index=idx,
                        column_alignments=self.column_alignments,
                        row_metadata=self.row_metadata,
                        on_row_click=self._on_row_click
                    )
                )
            
            self.table_body_container.controls = row_containers
        else:
            # Show empty state
            empty_row = ft.Container(
                content=ft.Text(
                    theme_manager.t("no_data") if hasattr(theme_manager, 't') else "No Data to display",
                    size=16,
                    color=theme_manager.text_secondary_color,
                    italic=True,
                    text_align=ft.TextAlign.CENTER
                ),
                padding=ft.padding.symmetric(horizontal=20, vertical=40),
                alignment=ft.alignment.center,
                bgcolor=theme_manager.surface_color,
                border=ft.border.only(
                    bottom=ft.BorderSide(1, theme_manager.border_color)
                ),
                expand=True,
            )
            
            self.table_body_container.controls = [empty_row]
        
        # Update pagination
        total_rows = len(self.filtered_rows)
        total_pages = (total_rows + self.page_size - 1) // self.page_size if total_rows > 0 else 0
        self.pagination.update(self.current_page, total_pages, total_rows)
        
        # Only update if control has been added to a page
        try:
            self.update()
        except (AssertionError, AttributeError):
            pass
    
    def _on_row_click(self, row_index: int):
        """Handle row click."""
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
    
    def refresh(self, rows: List[List[Any]], row_metadata: Optional[List[Dict[str, Any]]] = None):
        """Refresh table with new data."""
        self.all_rows = rows
        if row_metadata is not None:
            self.row_metadata = row_metadata
        self.current_page = 0
        self.filtering.reset()
        self._update_table()
    
    def _on_search(self, e):
        """Handle search input."""
        self.filtering._on_search(e)
        self.current_page = 0
        self._update_table()
    
    def update_filter_state(self, has_filters: bool):
        """Update the visibility of the clear filter button."""
        self.filtering.update_filter_state(has_filters)

