"""
Tag autocomplete component for tag suggestions.
"""

import flet as ft
from typing import Optional, List, Callable
from ui.theme import theme_manager


class TagAutocomplete:
    """Tag autocomplete component with dropdown suggestions."""
    
    def __init__(
        self,
        on_tag_selected: Optional[Callable[[str], None]] = None,
        group_id: Optional[int] = None,
        get_tag_suggestions: Optional[Callable[[str, Optional[int], int], List[str]]] = None,
        width: int = 250
    ):
        """
        Initialize tag autocomplete.
        
        Args:
            on_tag_selected: Callback when a tag is selected
            group_id: Current group ID for filtering suggestions
            get_tag_suggestions: Function to get tag suggestions (prefix, group_id, limit) -> List[str]
            width: Width of the autocomplete field
        """
        self.on_tag_selected = on_tag_selected
        self.group_id = group_id
        self.get_tag_suggestions = get_tag_suggestions
        self.width = width
        self.suggestions: List[str] = []
        self.current_prefix = ""
        
        # Create list view for suggestions
        self.suggestions_list = ft.ListView(
            controls=[],
            height=200,
            spacing=2,
            padding=ft.padding.all(4)
        )
        
        # Container to hold suggestions list (for positioning)
        self.dropdown_container = ft.Container(
            content=ft.Container(
                content=self.suggestions_list,
                bgcolor=theme_manager.surface_color if hasattr(theme_manager, 'surface_color') else ft.Colors.WHITE,
                border=ft.border.all(1, theme_manager.border_color if hasattr(theme_manager, 'border_color') else ft.Colors.GREY_300),
                border_radius=theme_manager.corner_radius,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=15,
                    color=ft.Colors.BLACK26,
                    offset=ft.Offset(0, 4)
                )
            ),
            visible=False,
            width=width,
            margin=ft.margin.only(top=2),
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT)
        )
    
    def build(self) -> ft.Column:
        """
        Build the autocomplete component.
        
        Returns:
            Column containing the autocomplete UI
        """
        return ft.Column(
            controls=[
                self.dropdown_container
            ],
            spacing=0,
            tight=True
        )
    
    def update_suggestions(self, prefix: str, group_id: Optional[int] = None):
        """
        Update tag suggestions based on prefix.
        
        Args:
            prefix: Tag prefix to search for (without #)
            group_id: Optional group ID to filter by
        """
        if not self.get_tag_suggestions:
            return
        
        # Remove # prefix if present
        clean_prefix = prefix.lstrip('#').strip().lower()
        self.current_prefix = clean_prefix
        
        if not clean_prefix:
            self.suggestions = []
            self._hide_dropdown()
            return
        
        # Get suggestions
        try:
            suggestions = self.get_tag_suggestions(clean_prefix, group_id or self.group_id, limit=10)
            self.suggestions = suggestions
            
            if suggestions:
                # Update suggestions list
                self.suggestions_list.controls = [
                    ft.ListTile(
                        title=ft.Text(f"#{tag}", size=14),
                        on_click=lambda e, t=tag: self.select_tag(t),
                        dense=True,
                        content_padding=ft.padding.symmetric(horizontal=10, vertical=4)
                    )
                    for tag in suggestions
                ]
                self._show_dropdown()
            else:
                self._hide_dropdown()
        except Exception as e:
            # Hide dropdown on error
            self._hide_dropdown()
    
    def select_tag(self, tag: str):
        """
        Select a tag.
        
        Args:
            tag: Normalized tag (without # prefix)
        """
        if self.on_tag_selected:
            self.on_tag_selected(tag)
        self._hide_dropdown()
    
    def _show_dropdown(self):
        """Show the dropdown with suggestions."""
        self.dropdown_container.visible = True
        try:
            self.dropdown_container.update()
        except (AssertionError, AttributeError):
            pass
    
    def _hide_dropdown(self):
        """Hide the dropdown."""
        self.dropdown_container.visible = False
        try:
            self.dropdown_container.update()
        except (AssertionError, AttributeError):
            pass
    
    def set_group_id(self, group_id: Optional[int]):
        """Update the group ID for filtering."""
        self.group_id = group_id
    
    def clear(self):
        """Clear suggestions and hide dropdown."""
        self.suggestions = []
        self.current_prefix = ""
        self._hide_dropdown()


class TagAutocompleteHelper:
    """Helper class to integrate tag autocomplete with search field."""
    
    @staticmethod
    def create_tag_autocomplete_row(
        search_field: ft.TextField,
        on_tag_selected: Optional[Callable[[str], None]] = None,
        group_id: Optional[int] = None,
        get_tag_suggestions: Optional[Callable[[str, Optional[int], int], List[str]]] = None
    ) -> ft.Column:
        """
        Create a row with search field and tag autocomplete dropdown.
        
        Args:
            search_field: Text field for search input
            on_tag_selected: Callback when tag is selected
            group_id: Current group ID
            get_tag_suggestions: Function to get tag suggestions
            
        Returns:
            Column containing search field and autocomplete dropdown
        """
        autocomplete = TagAutocomplete(
            on_tag_selected=on_tag_selected,
            group_id=group_id,
            get_tag_suggestions=get_tag_suggestions,
            width=search_field.width if search_field.width else 250
        )
        
        # Store autocomplete reference in search field for later access
        search_field.data = {'tag_autocomplete': autocomplete}
        
        def on_search_change(e):
            """Handle search field changes."""
            value = e.control.value or ""
            
            # Check if input starts with #
            if value.startswith('#'):
                # Extract prefix (everything after #)
                prefix = value[1:].strip()
                autocomplete.update_suggestions(prefix, group_id)
            else:
                # Hide autocomplete if not starting with #
                autocomplete.clear()
        
        search_field.on_change = on_search_change
        
        return ft.Column(
            controls=[
                search_field,
                autocomplete.build()
            ],
            spacing=0,
            tight=True
        )

