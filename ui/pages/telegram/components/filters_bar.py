"""
Reusable filter bar component for date and group filters.
"""

import flet as ft
from typing import Optional, Callable, List
from datetime import datetime
from ui.theme import theme_manager


class FiltersBarComponent:
    """Reusable filter bar component."""
    
    def __init__(
        self,
        groups: List,
        on_group_change: Optional[Callable[[Optional[int]], None]] = None,
        on_date_change: Optional[Callable[[], None]] = None,
        on_message_type_change: Optional[Callable[[Optional[str]], None]] = None,
        show_dates: bool = True,
        show_message_type: bool = True,
        default_group_id: Optional[int] = None,
        message_type_filter: Optional[str] = None
    ):
        self.on_group_change = on_group_change
        self.on_date_change = on_date_change
        self.on_message_type_change = on_message_type_change
        self.selected_group: Optional[int] = default_group_id
        self.selected_message_type: Optional[str] = message_type_filter
        self.show_message_type = show_message_type
        
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
        
        # Message type filter dropdown (only for messages tab)
        if show_message_type:
            message_type_options = [
                theme_manager.t("all_types"),
                theme_manager.t("voice"),
                theme_manager.t("audio_file"),
                theme_manager.t("photos"),
                theme_manager.t("videos"),
                theme_manager.t("files"),
                theme_manager.t("link"),
                theme_manager.t("tag"),
                theme_manager.t("poll"),
                theme_manager.t("location"),
                theme_manager.t("mention")
            ]
            
            # Map display values to filter values
            self.message_type_map = {
                theme_manager.t("all_types"): None,
                theme_manager.t("voice"): "voice",
                theme_manager.t("audio_file"): "audio",
                theme_manager.t("photos"): "photos",
                theme_manager.t("videos"): "videos",
                theme_manager.t("files"): "files",
                theme_manager.t("link"): "link",
                theme_manager.t("tag"): "tag",
                theme_manager.t("poll"): "poll",
                theme_manager.t("location"): "location",
                theme_manager.t("mention"): "mention"
            }
            
            # Reverse map for getting display value from filter value
            self.message_type_reverse_map = {v: k for k, v in self.message_type_map.items()}
            
            default_message_type_value = (
                self.message_type_reverse_map.get(message_type_filter, theme_manager.t("all_types"))
                if message_type_filter else theme_manager.t("all_types")
            )
            
            self.message_type_dropdown = theme_manager.create_dropdown(
                label=theme_manager.t("filter_by_type"),
                options=message_type_options,
                value=default_message_type_value,
                on_change=self._on_message_type_selected,
                width=180
            )
        else:
            self.message_type_dropdown = None
            self.message_type_map = {}
            self.message_type_reverse_map = {}
    
    def build(self) -> ft.Row:
        """Build the filter bar."""
        controls = []
        
        if self.start_date_field and self.end_date_field:
            controls.extend([self.start_date_field, self.end_date_field, ft.Container(width=20)])
        
        controls.append(self.group_dropdown)
        
        # Only add message type dropdown if enabled
        if self.message_type_dropdown:
            controls.append(self.message_type_dropdown)
        
        # Trigger callback if default group was set (for auto-selection)
        if self.selected_group is not None and self.on_group_change:
            self.on_group_change(self.selected_group)
        
        return ft.Row(controls, spacing=10, wrap=False)
    
    def get_start_date(self) -> Optional[datetime]:
        """Get start date from field."""
        if not self.start_date_field:
            return None
        try:
            if self.start_date_field.value:
                return datetime.strptime(self.start_date_field.value, "%Y-%m-%d")
        except:
            pass
        return None
    
    def get_end_date(self) -> Optional[datetime]:
        """Get end date from field."""
        if not self.end_date_field:
            return None
        try:
            if self.end_date_field.value:
                return datetime.strptime(self.end_date_field.value, "%Y-%m-%d")
        except:
            pass
        return None
    
    def get_selected_group(self) -> Optional[int]:
        """Get selected group ID."""
        return self.selected_group
    
    def get_message_type_filter(self) -> Optional[str]:
        """Get selected message type filter."""
        if not self.show_message_type:
            return None
        return self.selected_message_type
    
    def clear_filters(self):
        """Clear all filters."""
        self.selected_group = None
        self.selected_message_type = None
        if self.group_dropdown:
            self.group_dropdown.value = None
        if self.message_type_dropdown:
            self.message_type_dropdown.value = theme_manager.t("all_types")
        if self.start_date_field:
            self.start_date_field.value = ""
        if self.end_date_field:
            self.end_date_field.value = ""
    
    def _on_group_selected(self, e):
        """Handle group selection."""
        if e.control.value and e.control.value != "No groups":
            group_str = e.control.value
            group_id = int(group_str.split("(")[-1].strip(")"))
            self.selected_group = group_id
        else:
            self.selected_group = None
        
        if self.on_group_change:
            self.on_group_change(self.selected_group)
    
    def _on_date_change(self, e):
        """Handle date field change."""
        if self.on_date_change:
            self.on_date_change()
    
    def _on_message_type_selected(self, e):
        """Handle message type selection."""
        if e.control.value:
            self.selected_message_type = self.message_type_map.get(e.control.value)
        else:
            self.selected_message_type = None
        
        if self.on_message_type_change:
            self.on_message_type_change(self.selected_message_type)

