"""
Search and filtering logic for data table.
"""

import flet as ft
from typing import List, Any
from ui.theme import theme_manager


class TableFiltering:
    """Search and filtering functionality for data table."""
    
    def __init__(
        self,
        searchable: bool = True,
        on_clear_filters: callable = None,
        has_filters: bool = False
    ):
        """Initialize filtering."""
        self.search_query = ""
        self.on_clear_filters = on_clear_filters
        self.has_filters = has_filters
        
        # Create search field (exposed as property for external placement)
        # Note: on_change will be set by the table component
        self.search_field = ft.TextField(
            hint_text=theme_manager.t("search"),
            prefix_icon=ft.Icons.SEARCH,
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
    
    def filter_rows(self, all_rows: List[List[Any]]) -> List[List[Any]]:
        """Filter rows based on search query."""
        if not self.search_query:
            return all_rows
        else:
            return [
                row for row in all_rows
                if any(self.search_query in str(cell).lower() for cell in row)
            ]
    
    def update_filter_state(self, has_filters: bool):
        """Update the visibility of the clear filter button."""
        self.has_filters = has_filters
        if self.clear_filter_button:
            self.clear_filter_button.visible = has_filters
            try:
                self.clear_filter_button.update()
            except (AssertionError, AttributeError):
                pass
    
    def reset(self):
        """Reset search query."""
        self.search_query = ""
        if self.search_field:
            self.search_field.value = ""
    
    def _on_search(self, e):
        """Handle search input."""
        self.search_query = e.control.value.lower() if e.control.value else ""
    
    def _on_clear_filters(self, e):
        """Handle clear filters button click."""
        if self.on_clear_filters:
            self.on_clear_filters()

