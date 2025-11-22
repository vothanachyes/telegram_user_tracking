"""
Group chips component for displaying stacked group profile pictures.
"""

import flet as ft
from typing import List, Dict, Optional, Callable
from ui.theme import theme_manager


class GroupChipsComponent(ft.Container):
    """Component for displaying stacked group profile pictures (max 3 visible)."""
    
    def __init__(
        self,
        groups: List[Dict],
        max_display: int = 3,
        on_click: Optional[Callable[[], None]] = None,
        size: int = 32
    ):
        """
        Initialize group chips component.
        
        Args:
            groups: List of group dicts with group_id, group_name, group_username
            max_display: Maximum number of chips to display (default 3)
            on_click: Optional callback when chips are clicked
            size: Size of each chip in pixels (default 32)
        """
        self.groups = groups
        self.max_display = max_display
        self.on_click = on_click
        self.size = size
        
        super().__init__(
            content=self._build_chips(),
            on_click=self._handle_click if on_click else None
        )
    
    def _build_chips(self) -> ft.Row:
        """Build stacked chips display."""
        if not self.groups:
            return ft.Row([])
        
        # Get groups to display (max max_display)
        display_groups = self.groups[:self.max_display]
        remaining_count = max(0, len(self.groups) - self.max_display)
        
        chips = []
        for idx, group in enumerate(display_groups):
            # Create chip with negative margin for stacking effect
            chip = self._create_chip(group, idx)
            chips.append(chip)
        
        # Add "+N" indicator if there are more groups
        if remaining_count > 0:
            indicator = ft.Container(
                content=ft.Text(
                    f"+{remaining_count}",
                    size=10,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE
                ),
                width=self.size,
                height=self.size,
                border_radius=self.size // 2,
                alignment=ft.alignment.center,
                bgcolor=theme_manager.primary_color,
                border=ft.border.all(2, theme_manager.bg_color),
                margin=ft.margin.only(left=-8 if chips else 0)
            )
            chips.append(indicator)
        
        return ft.Row(
            chips,
            spacing=-8,  # Negative spacing for stacking
            tight=True
        )
    
    def _create_chip(self, group: Dict, index: int) -> ft.Container:
        """Create a single group chip."""
        group_name = group.get('group_name', 'Unknown')
        group_photo_path = group.get('group_photo_path')
        
        # Try to get group photo from database
        if not group_photo_path:
            # Try to get from group_id if available
            group_id = group.get('group_id')
            if group_id:
                try:
                    from config.settings import settings
                    db_group = settings.db_manager.get_group_by_id(group_id)
                    if db_group and db_group.group_photo_path:
                        group_photo_path = db_group.group_photo_path
                except Exception:
                    pass
        
        # Create chip content
        if group_photo_path:
            try:
                content = ft.Image(
                    src=group_photo_path,
                    width=self.size,
                    height=self.size,
                    fit=ft.ImageFit.COVER,
                    border_radius=self.size // 2
                )
            except Exception:
                content = self._create_icon_chip(group_name)
        else:
            content = self._create_icon_chip(group_name)
        
        # Add border for stacking effect
        border_width = 2 if index > 0 else 0
        
        return ft.Container(
            content=content,
            width=self.size,
            height=self.size,
            border_radius=self.size // 2,
            border=ft.border.all(border_width, theme_manager.bg_color),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            margin=ft.margin.only(left=-8 if index > 0 else 0),
            tooltip=group_name
        )
    
    def _create_icon_chip(self, group_name: str) -> ft.Container:
        """Create chip with icon fallback."""
        first_letter = group_name[0].upper() if group_name and len(group_name) > 0 else "?"
        
        return ft.Container(
            content=ft.Text(
                first_letter,
                size=self.size // 2,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE
            ),
            width=self.size,
            height=self.size,
            border_radius=self.size // 2,
            alignment=ft.alignment.center,
            bgcolor=theme_manager.primary_color,
            border=ft.border.all(2, theme_manager.bg_color)
        )
    
    def _handle_click(self, e):
        """Handle chip click."""
        if self.on_click:
            self.on_click()
    
    def update_groups(self, groups: List[Dict]):
        """Update groups and refresh display."""
        self.groups = groups
        self.content = self._build_chips()
        self.update()

