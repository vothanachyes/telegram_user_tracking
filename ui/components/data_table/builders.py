"""
Table builders for header, rows, and cells.
"""

import flet as ft
from typing import List, Any, Dict
from ui.theme import theme_manager


class TableBuilders:
    """Builders for table header, rows, and cells."""
    
    @staticmethod
    def create_header(columns: List[str]) -> ft.Container:
        """Create table header with matching column widths. All headers are center-aligned."""
        header_cells = []
        for i, col in enumerate(columns):
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
                        right=ft.BorderSide(1, theme_manager.border_color) if i < len(columns) - 1 else None
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
    
    @staticmethod
    def create_table_row(
        row_data: List[Any],
        row_index: int,
        column_alignments: List[str],
        row_metadata: List[Dict[str, Any]],
        on_row_click: callable
    ) -> ft.Container:
        """Create a table row with matching column widths to header."""
        cells = []
        row_meta = row_metadata[row_index] if row_index < len(row_metadata) else {}
        cell_metadata = row_meta.get('cells', {})
        
        for i, cell in enumerate(row_data):
            # First column ("No") gets fixed narrow width, others expand
            is_first_column = i == 0
            cell_meta = cell_metadata.get(i, {})
            
            # Determine alignment
            alignment = column_alignments[i] if i < len(column_alignments) else "left"
            cell_alignment = ft.alignment.center if alignment == "center" else ft.alignment.center_left
            
            # Create cell content based on metadata
            cell_content = TableBuilders._create_cell_content(cell, cell_meta, i)
            
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
                if on_row_click:
                    on_row_click(idx)
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
    
    @staticmethod
    def _create_cell_content(cell_value: Any, cell_meta: Dict[str, Any], column_index: int) -> ft.Control:
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
                    on_click=lambda e, url=link_url: TableBuilders._open_link(url),
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
                    on_click=lambda e, url=link_url: TableBuilders._open_link(url),
                    tooltip=link_url
                )
        
        # Default: plain text with theme color
        return ft.Text(
            str(cell_value),
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1,
            color=theme_manager.text_color  # Use theme text color for proper contrast
        )
    
    @staticmethod
    def _open_link(url: str):
        """Open a link in the default browser."""
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception:
            pass  # Silently fail if browser can't be opened

