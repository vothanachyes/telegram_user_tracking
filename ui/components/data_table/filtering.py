"""
Search and filtering logic for data table.
"""

import flet as ft
from typing import List, Any, Optional, Callable
from ui.theme import theme_manager


class TableFiltering:
    """Search and filtering functionality for data table."""
    
    def __init__(
        self,
        searchable: bool = True,
        on_clear_filters: callable = None,
        has_filters: bool = False,
        enable_tag_filtering: bool = False,
        on_tag_query_change: Optional[Callable[[Optional[str]], None]] = None,
        get_tag_suggestions: Optional[Callable[[str, Optional[int], int], List[str]]] = None,
        group_id: Optional[int] = None
    ):
        """
        Initialize filtering.
        
        Args:
            searchable: Enable search functionality
            on_clear_filters: Callback for clearing filters
            has_filters: Whether filters are currently active
            enable_tag_filtering: Enable tag-based filtering (detects # prefix)
            on_tag_query_change: Callback when tag query changes (for database-level filtering)
            get_tag_suggestions: Function to get tag suggestions
            group_id: Current group ID for tag suggestions
        """
        self.search_query = ""
        self.tag_query: Optional[str] = None  # Normalized tag without #
        self.on_clear_filters = on_clear_filters
        self.has_filters = has_filters
        self.enable_tag_filtering = enable_tag_filtering
        self.on_tag_query_change = on_tag_query_change
        self.get_tag_suggestions = get_tag_suggestions
        self.group_id = group_id
        
        # Create search field (exposed as property for external placement)
        # Note: on_change will be set by the table component
        self.search_field = ft.TextField(
            hint_text=theme_manager.t("search"),
            prefix_icon=ft.Icons.SEARCH,
            width=250,  # Width adjusted for inline display
            border_radius=theme_manager.corner_radius
        ) if searchable else None
        
        # Helper text below search field
        self.search_helper_text = ft.Text(
            "",
            size=11,
            color=theme_manager.text_secondary_color,
            visible=False
        ) if searchable else None
        
        # Setup helper text handler for all search fields
        if self.search_field:
            self._setup_helper_text_handler()
        
        # Tag autocomplete dropdown (will be created if tag filtering is enabled)
        self.tag_autocomplete_container = None
        if enable_tag_filtering and self.search_field:
            self._setup_tag_autocomplete()
        
        # Clear filter button (exposed as property for external placement)
        self.clear_filter_button = ft.IconButton(
            icon=ft.Icons.CLEAR,
            tooltip=theme_manager.t("clear_filters") if hasattr(theme_manager, 't') else "Clear filters",
            on_click=self._on_clear_filters,
            visible=has_filters
        ) if on_clear_filters else None
    
    def _setup_helper_text_handler(self):
        """Setup helper text handler that wraps the on_change callback."""
        original_on_change = self.search_field.on_change
        
        def wrapped_on_change(e):
            """Wrapper that updates helper text before calling original handler."""
            value = e.control.value or ""
            self._update_helper_text(value)
            if original_on_change:
                original_on_change(e)
        
        self.search_field.on_change = wrapped_on_change
        self._original_on_change = original_on_change
    
    def _setup_tag_autocomplete(self):
        """Setup tag autocomplete dropdown."""
        from ui.components.tag_autocomplete import TagAutocomplete
        
        self.tag_autocomplete = TagAutocomplete(
            on_tag_selected=self._on_tag_selected,
            group_id=self.group_id,
            get_tag_suggestions=self.get_tag_suggestions,
            width=self.search_field.width if self.search_field else 250
        )
        
        self.tag_autocomplete_container = self.tag_autocomplete.build()
        
        # Override search field on_change to detect # prefix
        # Note: This will wrap the existing handler (which already handles helper text)
        original_on_change = self.search_field.on_change
        
        def enhanced_on_change(e):
            """Enhanced on_change that handles both text and tag filtering."""
            value = e.control.value or ""
            
            # Update helper text based on prefix
            self._update_helper_text(value)
            
            # Check if input starts with #
            if value.startswith('#'):
                # Extract tag prefix (everything after #)
                prefix = value[1:].strip()
                if prefix:
                    self.tag_autocomplete.update_suggestions(prefix, self.group_id)
                else:
                    self.tag_autocomplete.clear()
                    self.tag_query = None
                    if self.on_tag_query_change:
                        self.on_tag_query_change(None)
            else:
                # Regular text search
                self.tag_autocomplete.clear()
                self.tag_query = None
                if self.on_tag_query_change:
                    self.on_tag_query_change(None)
                self.search_query = value.lower()
                if original_on_change:
                    original_on_change(e)
        
        self.search_field.on_change = enhanced_on_change
    
    def _update_helper_text(self, value: str):
        """Update helper text based on search prefix."""
        if not self.search_helper_text:
            return
        
        if value.startswith('@'):
            self.search_helper_text.value = theme_manager.t("searching_by_username")
            self.search_helper_text.visible = True
        elif value.startswith('#'):
            self.search_helper_text.value = theme_manager.t("searching_by_tag")
            self.search_helper_text.visible = True
        else:
            self.search_helper_text.visible = False
        
        try:
            self.search_helper_text.update()
        except (AssertionError, AttributeError):
            pass
    
    def _on_tag_selected(self, tag: str):
        """
        Handle tag selection from autocomplete.
        
        Args:
            tag: Normalized tag (without # prefix)
        """
        self.tag_query = tag
        if self.search_field:
            self.search_field.value = f"#{tag}"
            self._update_helper_text(f"#{tag}")
        if self.on_tag_query_change:
            self.on_tag_query_change(tag)
        if self.tag_autocomplete:
            self.tag_autocomplete.clear()
    
    def set_group_id(self, group_id: Optional[int]):
        """Update group ID for tag suggestions."""
        self.group_id = group_id
        if self.tag_autocomplete:
            self.tag_autocomplete.set_group_id(group_id)
    
    def filter_rows(self, all_rows: List[List[Any]]) -> List[List[Any]]:
        """
        Filter rows based on search query.
        
        Note: If tag filtering is enabled and a tag query is set,
        the actual filtering should be done at the database level.
        This method only handles text-based filtering.
        """
        # If tag filtering is active, return all rows (filtering done at DB level)
        if self.enable_tag_filtering and self.tag_query:
            return all_rows
        
        # Regular text-based filtering
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
    
    def reset(self, notify_tag_change: bool = False):
        """Reset search query and tag query.
        
        Args:
            notify_tag_change: If True, notify on_tag_query_change callback. 
                              Default False to prevent recursion when called from refresh().
        """
        old_tag_query = self.tag_query
        self.search_query = ""
        self.tag_query = None
        if self.search_field:
            self.search_field.value = ""
            self._update_helper_text("")
        if hasattr(self, 'tag_autocomplete') and self.tag_autocomplete:
            self.tag_autocomplete.clear()
        # Only notify if explicitly requested and tag query actually changed
        if notify_tag_change and self.on_tag_query_change and old_tag_query is not None:
            self.on_tag_query_change(None)
    
    def _on_search(self, e):
        """Handle search input."""
        self.search_query = e.control.value.lower() if e.control.value else ""
    
    def _on_clear_filters(self, e):
        """Handle clear filters button click."""
        if self.on_clear_filters:
            self.on_clear_filters()

