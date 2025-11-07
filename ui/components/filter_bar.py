"""
Reusable filter bar component for date and group filters.
"""

import flet as ft
from typing import Optional, Callable, List
from datetime import datetime
from ui.theme import theme_manager


class FilterBar:
    """Reusable filter bar component for dates, groups, and search."""
    
    def __init__(
        self,
        groups: List,
        on_group_change: Optional[Callable[[Optional[int]], None]] = None,
        on_date_change: Optional[Callable[[], None]] = None,
        on_search_change: Optional[Callable[[str], None]] = None,
        show_dates: bool = True,
        show_search: bool = False,
        default_group_id: Optional[int] = None,
        search_placeholder: Optional[str] = None
    ):
        """
        Initialize filter bar.
        
        Args:
            groups: List of group objects with group_name and group_id
            on_group_change: Callback when group selection changes
            on_date_change: Callback when date filters change
            on_search_change: Callback when search query changes
            show_dates: Whether to show date filters
            show_search: Whether to show search field
            default_group_id: Default selected group ID
            search_placeholder: Placeholder text for search field
        """
        self.on_group_change = on_group_change
        self.on_date_change = on_date_change
        self.on_search_change = on_search_change
        self.selected_group: Optional[int] = default_group_id
        
        # Date filters (default: current month)
        if show_dates:
            today = datetime.now()
            first_day = today.replace(day=1)
            
            self.start_date_field = ft.TextField(
                label=theme_manager.t("start_date"),
                value=first_day.strftime("%Y-%m-%d"),
                width=140,
                border_radius=theme_manager.corner_radius,
                on_change=self._on_date_change
            )
            
            self.end_date_field = ft.TextField(
                label=theme_manager.t("end_date"),
                value=today.strftime("%Y-%m-%d"),
                width=140,
                border_radius=theme_manager.corner_radius,
                on_change=self._on_date_change
            )
        else:
            self.start_date_field = None
            self.end_date_field = None
        
        # Search field
        if show_search:
            self.search_field = ft.TextField(
                hint_text=search_placeholder or theme_manager.t("search"),
                prefix_icon=ft.Icons.SEARCH,
                width=250,
                border_radius=theme_manager.corner_radius,
                on_change=self._on_search_change
            )
        else:
            self.search_field = None
        
        # Group selector
        group_options = [f"{g.group_name} ({g.group_id})" for g in groups]
        if group_options and default_group_id:
            default_group_value = next(
                (opt for opt in group_options if f"({default_group_id})" in opt),
                group_options[0] if group_options else None
            )
        else:
            default_group_value = group_options[0] if group_options else None
        
        self.group_dropdown = theme_manager.create_dropdown(
            label=theme_manager.t("select_group"),
            options=group_options if group_options else ["No groups"],
            value=default_group_value,
            on_change=self._on_group_selected,
            width=250
        )
    
    def build(self) -> ft.Row:
        """Build the filter bar."""
        controls = []
        
        if self.start_date_field and self.end_date_field:
            controls.extend([self.start_date_field, self.end_date_field, ft.Container(width=20)])
        
        if self.search_field:
            controls.append(self.search_field)
            if controls:  # Add spacing if there are other controls
                controls.append(ft.Container(width=20))
        
        controls.append(self.group_dropdown)
        
        return ft.Row(controls, spacing=10, wrap=False)
    
    def get_start_date(self) -> Optional[datetime]:
        """Get start date from field."""
        if not self.start_date_field:
            return None
        try:
            if self.start_date_field.value:
                return datetime.strptime(self.start_date_field.value, "%Y-%m-%d")
        except (ValueError, AttributeError):
            pass
        return None
    
    def get_end_date(self) -> Optional[datetime]:
        """Get end date from field."""
        if not self.end_date_field:
            return None
        try:
            if self.end_date_field.value:
                return datetime.strptime(self.end_date_field.value, "%Y-%m-%d")
        except (ValueError, AttributeError):
            pass
        return None
    
    def get_selected_group(self) -> Optional[int]:
        """Get selected group ID."""
        return self.selected_group
    
    def get_search_query(self) -> Optional[str]:
        """Get search query from field."""
        if not self.search_field:
            return None
        return self.search_field.value if self.search_field.value else None
    
    def clear_filters(self):
        """Clear all filters."""
        self.selected_group = None
        if self.group_dropdown:
            self.group_dropdown.value = None
        if self.start_date_field:
            self.start_date_field.value = ""
        if self.end_date_field:
            self.end_date_field.value = ""
        if self.search_field:
            self.search_field.value = ""
    
    def _on_group_selected(self, e):
        """Handle group selection."""
        if e.control.value and e.control.value != "No groups":
            group_str = e.control.value
            try:
                group_id = int(group_str.split("(")[-1].strip(")"))
                self.selected_group = group_id
            except (ValueError, IndexError):
                self.selected_group = None
        else:
            self.selected_group = None
        
        if self.on_group_change:
            self.on_group_change(self.selected_group)
    
    def _on_date_change(self, e):
        """Handle date field change."""
        if self.on_date_change:
            self.on_date_change()
    
    def _on_search_change(self, e):
        """Handle search field change."""
        if self.on_search_change:
            self.on_search_change(e.control.value or "")

