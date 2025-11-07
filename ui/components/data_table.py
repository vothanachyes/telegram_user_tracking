"""
Reusable data table component with pagination and search.
"""

import flet as ft
from typing import List, Callable, Optional, Any, Dict
from ui.theme import theme_manager


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
        self.search_query = ""
        self.column_alignments = column_alignments or ["left"] * len(columns)
        self.row_metadata = row_metadata or []
        self.on_clear_filters = on_clear_filters
        self.has_filters = has_filters
        
        # Create search field (exposed as property for external placement)
        self.search_field = ft.TextField(
            hint_text=theme_manager.t("search"),
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._on_search,
            width=250,  # Width adjusted for inline display
            border_radius=theme_manager.corner_radius
        ) if searchable else None
        
        # Clear filter button (exposed as property for external placement)
        self.clear_filter_button = ft.IconButton(
            icon=ft.Icons.CLEAR,
            tooltip=theme_manager.t("clear_filters") if hasattr(theme_manager, 't') else "Clear filters",
            on_click=self._on_clear_filters,
            visible=has_filters
        ) if on_clear_filters else None
        
        # Create table header with fixed position
        self.table_header = self._create_header()
        
        # Container for table body rows (will be updated)
        self.table_body_container = ft.Column([], spacing=0)
        
        # Scrollable container for table body
        # Scrollable Column should NOT have expand=True - it needs height constraint from parent Container
        scrollable_column = ft.Column(
            [self.table_body_container],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            tight=True  # Tight layout for better scrolling behavior
        )
        
        self.scrollable_body = ft.Container(
            content=scrollable_column,
            expand=True,  # Container expands to fill available space, giving height to scrollable Column
            bgcolor=theme_manager.surface_color,  # Use theme surface color for proper visibility
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
        
        # Pagination controls
        self.page_info = ft.Text("", size=14)
        self.prev_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=self._previous_page,
            tooltip=theme_manager.t("previous")
        )
        self.next_button = ft.IconButton(
            icon=ft.Icons.ARROW_FORWARD,
            on_click=self._next_page,
            tooltip=theme_manager.t("next")
        )
        
        # Layout - use Container with expand=True per .cursorrules guidelines
        # Table structure: Column -> [header, scrollable_body Container]
        # Use Column directly for better layout control
        table_column = ft.Column([
            # Fixed header (outside scrollable area)
            self.table_header,
            # Scrollable data rows - Container expands to fill remaining space
            self.scrollable_body,
        ], spacing=0, expand=True)
        
        # Pagination row
        pagination_row = ft.Row([
            self.prev_button,
            self.page_info,
            self.next_button,
            ft.Container(expand=True),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        
        # Main content column
        super().__init__(
            content=ft.Column([
                table_column,
                pagination_row,
            ], spacing=10, expand=True),
            padding=10,
            expand=True
        )
        
        self._update_table()
    
    def _create_header(self) -> ft.Container:
        """Create table header with matching column widths. All headers are center-aligned."""
        header_cells = []
        for i, col in enumerate(self.columns):
            # First column ("No") gets fixed narrow width, others expand
            is_first_column = i == 0
            header_cells.append(
                ft.Container(
                    content=ft.Text(
                        col,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        text_align=ft.TextAlign.CENTER
                    ),
                    width=70 if is_first_column else None,
                    expand=not is_first_column,
                    padding=ft.padding.symmetric(horizontal=10, vertical=15),
                    alignment=ft.alignment.center,  # Center-align all headers
                    border=ft.border.only(
                        right=ft.BorderSide(1, theme_manager.border_color) if i < len(self.columns) - 1 else None
                    ),
                )
            )
        
        return ft.Container(
            content=ft.Row(header_cells, spacing=0),
            bgcolor=theme_manager.primary_color,
            border=ft.border.all(1, theme_manager.border_color),
            border_radius=ft.border_radius.only(
                top_left=theme_manager.corner_radius,
                top_right=theme_manager.corner_radius
            ),
        )
    
    def _create_table_row(self, row_data: List[Any], row_index: int) -> ft.Container:
        """Create a table row with matching column widths to header."""
        cells = []
        row_meta = self.row_metadata[row_index] if row_index < len(self.row_metadata) else {}
        cell_metadata = row_meta.get('cells', {})
        
        for i, cell in enumerate(row_data):
            # First column ("No") gets fixed narrow width, others expand
            is_first_column = i == 0
            cell_meta = cell_metadata.get(i, {})
            
            # Determine alignment
            alignment = self.column_alignments[i] if i < len(self.column_alignments) else "left"
            cell_alignment = ft.alignment.center if alignment == "center" else ft.alignment.center_left
            
            # Create cell content based on metadata
            cell_content = self._create_cell_content(cell, cell_meta, i)
            
            cells.append(
                ft.Container(
                    content=cell_content,
                    width=70 if is_first_column else None,
                    expand=not is_first_column,
                    padding=ft.padding.symmetric(horizontal=10, vertical=10),
                    alignment=cell_alignment,
                    bgcolor=ft.Colors.TRANSPARENT,  # Transparent to inherit row background
                    border=ft.border.only(
                        right=ft.BorderSide(1, theme_manager.border_color) if i < len(row_data) - 1 else None
                    ),
                )
            )
        
        # Create row container with click handler
        def make_click_handler(idx):
            def handler(e):
                if self.on_row_click:
                    self._on_row_click(idx)
            return handler
        
        # Use alternating row colors for better readability
        # Even rows use surface color, odd rows use a slightly different shade
        row_bgcolor = theme_manager.surface_color
        if row_index % 2 == 1:
            # For odd rows, use a slightly different shade if available
            # Fallback to same color if theme doesn't support it
            row_bgcolor = theme_manager.surface_color
        
        # Create row container with proper background color
        row_container = ft.Container(
            content=ft.Row(cells, spacing=0),
            border=ft.border.only(
                bottom=ft.BorderSide(1, theme_manager.border_color)
            ),
            bgcolor=row_bgcolor,  # Use theme surface color for proper visibility
            on_click=make_click_handler(row_index),
            data=row_index,  # Store row index for reference
        )
        
        return row_container
    
    def _create_cell_content(self, cell_value: Any, cell_meta: Dict[str, Any], column_index: int) -> ft.Control:
        """Create cell content based on metadata (for links, icons, etc.)."""
        # Check if this is a link cell
        if cell_meta.get('link'):
            link_url = cell_meta['link']
            if cell_meta.get('renderer') == 'icon':
                # Icon button for links (e.g., Telegram icon)
                return ft.IconButton(
                    icon=ft.Icons.OPEN_IN_NEW,
                    icon_color=theme_manager.primary_color,
                    tooltip=link_url,
                    on_click=lambda e, url=link_url: self._open_link(url),
                    icon_size=20
                )
            else:
                # Clickable text link - use lighter color in dark mode for better contrast
                from utils.constants import COLORS
                link_color = COLORS["secondary"] if theme_manager.is_dark else theme_manager.primary_color
                return ft.TextButton(
                    content=ft.Text(
                        str(cell_value),
                        overflow=ft.TextOverflow.ELLIPSIS,
                        max_lines=1,
                        color=link_color
                    ),
                    on_click=lambda e, url=link_url: self._open_link(url),
                    tooltip=link_url
                )
        
        # Default: plain text with theme color
        return ft.Text(
            str(cell_value),
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1,
            color=theme_manager.text_color  # Use theme text color for proper contrast
        )
    
    def _open_link(self, url: str):
        """Open a link in the default browser."""
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception:
            pass  # Silently fail if browser can't be opened
    
    def _on_clear_filters(self, e):
        """Handle clear filters button click."""
        if self.on_clear_filters:
            self.on_clear_filters()
    
    def update_filter_state(self, has_filters: bool):
        """Update the visibility of the clear filter button."""
        self.has_filters = has_filters
        if self.clear_filter_button:
            self.clear_filter_button.visible = has_filters
            try:
                self.clear_filter_button.update()
            except (AssertionError, AttributeError):
                pass
    
    def _on_row_click(self, row_index: int):
        """Handle row click."""
        if self.on_row_click:
            self.on_row_click(row_index)
    
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
        
        # Update table body rows with matching column widths
        if page_rows:
            row_containers = []
            for idx, row in enumerate(page_rows, start=start):
                row_containers.append(self._create_table_row(row, idx))
            
            # Update the Column directly (not through .content)
            self.table_body_container.controls = row_containers
        else:
            # Show empty state - display "No Data to display" message with headers visible
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
        
        # Update pagination info
        total_rows = len(self.filtered_rows)
        total_pages = (total_rows + self.page_size - 1) // self.page_size if total_rows > 0 else 0
        self.page_info.value = f"Page {self.current_page + 1} of {total_pages} ({total_rows} rows)"
        
        # Update button states
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= total_pages - 1
        
        # Only update if control has been added to a page
        try:
            self.update()
        except (AssertionError, AttributeError):
            # Control not yet added to page, skip update
            # The table will be updated when it's added to the page
            pass
    
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
        self.search_query = ""
        if self.search_field:
            self.search_field.value = ""
        self._filter_rows()
        self._update_table()
