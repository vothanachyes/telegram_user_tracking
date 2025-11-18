"""
Statistic card component for dashboard.
"""

import flet as ft
from ui.theme import theme_manager


class StatCard(ft.Container):
    """A card displaying a statistic with icon."""
    
    def __init__(
        self,
        title: str,
        value: str,
        icon: str,
        color: str = None
    ):
        self.title = title
        self.value_text = value
        self.icon = icon
        self.color = color or theme_manager.primary_color
        self._is_hovered = False
        
        # Create shadow for depth
        self._default_shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=8,
            color=ft.Colors.BLACK12 if not theme_manager.is_dark else ft.Colors.BLACK38,
            offset=ft.Offset(0, 2),
        )
        
        self._hover_shadow = ft.BoxShadow(
            spread_radius=2,
            blur_radius=15,
            color=ft.Colors.BLACK26 if not theme_manager.is_dark else ft.Colors.BLACK54,
            offset=ft.Offset(0, 4),
        )
        
        super().__init__(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(
                        name=icon,
                        size=40,
                        color=ft.Colors.WHITE
                    ),
                    bgcolor=self.color,
                    border_radius=theme_manager.corner_radius,
                    padding=theme_manager.padding_sm,
                    width=70,
                    height=70,
                    alignment=ft.alignment.center
                ),
                theme_manager.spacing_container("md"),
                ft.Column([
                    ft.Text(
                        title,
                        size=theme_manager.font_size_body,
                        color=theme_manager.text_secondary_color
                    ),
                    ft.Text(
                        value,
                        size=theme_manager.font_size_medium_number,
                        weight=ft.FontWeight.BOLD,
                        color=theme_manager.text_color
                    )
                ], spacing=theme_manager.spacing_xs, alignment=ft.MainAxisAlignment.CENTER)
            ], alignment=ft.MainAxisAlignment.START),
            bgcolor=theme_manager.surface_color,
            border=ft.border.all(1, theme_manager.border_color),
            border_radius=theme_manager.corner_radius,
            padding=theme_manager.padding_md,
            width=250,
            shadow=[self._default_shadow],
            animate=ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT),
            animate_scale=ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT),
            animate_opacity=ft.Animation(duration=400, curve=ft.AnimationCurve.EASE_OUT),
            opacity=0,
            scale=1.0,
            on_hover=self._on_hover
        )
    
    def _on_hover(self, e: ft.ControlEvent):
        """Handle hover events for interactive effects."""
        self._is_hovered = e.data == "true"
        
        if self._is_hovered:
            # Hover state: scale up and increase shadow
            self.scale = 1.02
            self.shadow = [self._hover_shadow]
        else:
            # Normal state: scale down and reduce shadow
            self.scale = 1.0
            self.shadow = [self._default_shadow]
        
        if self.page:
            self.update()
        else:
            self.update()
    
    def _animate_in(self):
        """Animate card fade-in on mount."""
        self.opacity = 1
        # Only update through page, not directly on control
        # This ensures the control is properly added to the page tree first
        if self.page:
            self.page.update()
    
    def update_value(self, new_value: str):
        """Update the displayed value."""
        self.value_text = new_value
        # Update the text in the column
        self.content.controls[2].controls[1].value = new_value
        self.update()

