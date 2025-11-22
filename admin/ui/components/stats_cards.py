"""
Statistics cards component for admin dashboard.
"""

import flet as ft
from typing import Optional, Callable


class StatsCard(ft.Container):
    """Statistics card component."""
    
    # Dark theme colors
    BG_COLOR = "#252525"
    BORDER_COLOR = "#333333"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    
    def __init__(
        self,
        title: str,
        value: str,
        icon: Optional[str] = None,
        trend: Optional[str] = None,
        on_click: Optional[Callable] = None
    ):
        self.title = title
        self.value = value
        self.icon = icon
        self.trend = trend
        
        content_parts = []
        
        # Icon and title row
        if icon:
            content_parts.append(
                ft.Row(
                    controls=[
                        ft.Icon(icon, color=self.PRIMARY_COLOR, size=24),
                        ft.Text(
                            title,
                            color=self.TEXT_SECONDARY,
                            size=12,
                            weight=ft.FontWeight.NORMAL,
                        ),
                    ],
                    spacing=8,
                )
            )
        else:
            content_parts.append(
                ft.Text(
                    title,
                    color=self.TEXT_SECONDARY,
                    size=12,
                    weight=ft.FontWeight.NORMAL,
                )
            )
        
        # Value
        content_parts.append(
            ft.Text(
                value,
                color=self.TEXT_COLOR,
                size=28,
                weight=ft.FontWeight.BOLD,
            )
        )
        
        # Trend indicator
        if trend:
            trend_color = "#4caf50" if trend.startswith("+") else "#f44336"
            content_parts.append(
                ft.Text(
                    trend,
                    color=trend_color,
                    size=12,
                )
            )
        
        super().__init__(
            content=ft.Column(
                controls=content_parts,
                spacing=8,
            ),
            padding=ft.padding.all(20),
            bgcolor=self.BG_COLOR,
            border=ft.border.all(1, self.BORDER_COLOR),
            border_radius=8,
            on_click=on_click if on_click else None,
        )

