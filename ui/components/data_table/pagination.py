"""
Pagination controls for data table.
"""

import flet as ft
from ui.theme import theme_manager


class PaginationControls:
    """Pagination controls for data table."""
    
    def __init__(self, on_previous: callable, on_next: callable):
        """Initialize pagination controls."""
        self.on_previous = on_previous
        self.on_next = on_next
        
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
    
    def build_row(self) -> ft.Row:
        """Build pagination row."""
        return ft.Row([
            self.prev_button,
            self.page_info,
            self.next_button,
            ft.Container(expand=True),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
    
    def update(self, current_page: int, total_pages: int, total_rows: int):
        """Update pagination info and button states."""
        self.page_info.value = f"Page {current_page + 1} of {total_pages} ({total_rows} rows)"
        self.prev_button.disabled = current_page == 0
        self.next_button.disabled = current_page >= total_pages - 1
    
    def _previous_page(self, e):
        """Go to previous page."""
        if self.on_previous:
            self.on_previous(e)
    
    def _next_page(self, e):
        """Go to next page."""
        if self.on_next:
            self.on_next(e)

