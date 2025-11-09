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
            padding=theme_manager.padding_lg,
            width=250
        )
    
    def update_value(self, new_value: str):
        """Update the displayed value."""
        self.value_text = new_value
        # Update the text in the column
        self.content.controls[2].controls[1].value = new_value
        self.update()

