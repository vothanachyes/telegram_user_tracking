"""
Modern tab component that accepts a list of tab definitions.
Supports license-based feature disabling.
"""

import flet as ft
from typing import List, Dict, Optional, Callable
from ui.theme import theme_manager


class ModernTabs(ft.Container):
    """Modern tab component with support for dynamic tab definitions and license features."""
    
    def __init__(
        self,
        tabs: List[Dict[str, any]],
        selected_index: int = 0,
        on_tab_change: Optional[Callable[[int], None]] = None
    ):
        """
        Initialize modern tabs.
        
        Args:
            tabs: List of tab definitions. Each dict should have:
                - 'id': str - unique tab identifier
                - 'label': str - tab label (will be translated)
                - 'icon': str - icon name (optional)
                - 'content': ft.Control - tab content
                - 'enabled': bool - whether tab is enabled (default True)
                - 'badge': str - optional badge text (e.g., "Pro")
            selected_index: Initial selected tab index
            on_tab_change: Callback when tab changes (receives tab index)
        """
        self.tabs = tabs
        self.selected_index = selected_index
        self.on_tab_change = on_tab_change
        self.tab_buttons: List[ft.Control] = []
        
        # Create tab buttons
        self._create_tab_buttons()
        
        # Create content container
        self.content_container = ft.Container(
            content=self.tabs[selected_index]['content'] if tabs else ft.Container(),
            expand=True,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT)
        )
        
        # Build layout
        super().__init__(
            content=ft.Column([
                # Tab buttons row
                ft.Container(
                    content=ft.Row(
                        self.tab_buttons,
                        spacing=0,
                        scroll=ft.ScrollMode.AUTO if len(self.tab_buttons) > 5 else ft.ScrollMode.HIDDEN
                    ),
                    bgcolor=theme_manager.surface_color,
                    border=ft.border.only(
                        bottom=ft.BorderSide(1, theme_manager.border_color)
                    ),
                    padding=ft.padding.only(left=20, top=10, bottom=0)
                ),
                # Tab content
                self.content_container
            ], spacing=0, expand=True),
            expand=True
        )
    
    def _create_tab_buttons(self):
        """Create tab buttons from tab definitions."""
        self.tab_buttons = []
        
        for idx, tab_def in enumerate(self.tabs):
            if not tab_def.get('enabled', True):
                continue
            
            is_selected = idx == self.selected_index
            tab_id = tab_def.get('id', f'tab_{idx}')
            label = theme_manager.t(tab_def.get('label', tab_id))
            icon = tab_def.get('icon')
            badge = tab_def.get('badge')
            
            # Create button content
            button_content = []
            if icon:
                button_content.append(
                    ft.Icon(
                        icon,
                        size=18,
                        color=theme_manager.primary_color if is_selected else theme_manager.text_secondary_color
                    )
                )
            button_content.append(
                ft.Text(
                    label,
                    size=14,
                    weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
                    color=theme_manager.primary_color if is_selected else theme_manager.text_secondary_color
                )
            )
            if badge:
                button_content.append(
                    ft.Container(
                        content=ft.Text(
                            badge,
                            size=10,
                            color=ft.Colors.WHITE,
                            weight=ft.FontWeight.BOLD
                        ),
                        bgcolor=theme_manager.primary_color,
                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                        border_radius=10
                    )
                )
            
            # Create button
            tab_button = ft.Container(
                content=ft.Row(
                    button_content,
                    spacing=8,
                    tight=True
                ),
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
                border=ft.border.only(
                    bottom=ft.BorderSide(
                        3 if is_selected else 0,
                        theme_manager.primary_color if is_selected else ft.Colors.TRANSPARENT
                    )
                ),
                bgcolor=ft.Colors.TRANSPARENT,
                on_click=lambda e, i=idx: self._on_tab_click(i),
                animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
                data=tab_id
            )
            
            self.tab_buttons.append(tab_button)
    
    def _on_tab_click(self, index: int):
        """Handle tab button click."""
        if index == self.selected_index:
            return
        
        # Update selected index
        self.selected_index = index
        
        # Update button styles
        self._update_tab_buttons()
        
        # Update content
        self.content_container.content = self.tabs[index]['content']
        self.content_container.update()
        
        # Notify callback
        if self.on_tab_change:
            self.on_tab_change(index)
    
    def _update_tab_buttons(self):
        """Update tab button styles based on selected index."""
        button_idx = 0
        for idx, tab_def in enumerate(self.tabs):
            if not tab_def.get('enabled', True):
                continue
            
            is_selected = idx == self.selected_index
            icon = tab_def.get('icon')
            
            if button_idx < len(self.tab_buttons):
                button = self.tab_buttons[button_idx]
                button.border = ft.border.only(
                    bottom=ft.BorderSide(
                        3 if is_selected else 0,
                        theme_manager.primary_color if is_selected else ft.Colors.TRANSPARENT
                    )
                )
                
                # Update icon color
                if icon and len(button.content.controls) > 0:
                    row = button.content
                    if isinstance(row, ft.Row) and len(row.controls) > 0:
                        icon_control = row.controls[0]
                        if isinstance(icon_control, ft.Icon):
                            icon_control.color = theme_manager.primary_color if is_selected else theme_manager.text_secondary_color
                        
                        # Update text color
                        if len(row.controls) > 1:
                            text_control = row.controls[1]
                            if isinstance(text_control, ft.Text):
                                text_control.color = theme_manager.primary_color if is_selected else theme_manager.text_secondary_color
                                text_control.weight = ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL
                
                button.update()
            
            button_idx += 1
    
    def select_tab(self, index: int):
        """Programmatically select a tab."""
        if 0 <= index < len(self.tabs) and self.tabs[index].get('enabled', True):
            self._on_tab_click(index)

