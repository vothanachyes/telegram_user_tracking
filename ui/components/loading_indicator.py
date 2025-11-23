"""
Reusable loading indicator components.
"""

import flet as ft
from typing import Optional
from ui.theme import theme_manager


class LoadingIndicator:
    """Reusable loading indicator component."""
    
    @staticmethod
    def create(
        size: int = 40,
        color: Optional[str] = None,
        message: Optional[str] = None,
        full_screen: bool = False
    ) -> ft.Control:
        """
        Create a loading indicator.
        
        Args:
            size: Size of the progress ring (default: 40)
            color: Color of the indicator (uses theme primary if None)
            message: Optional message to display below indicator
            full_screen: Whether to create full-screen overlay
            
        Returns:
            Loading indicator control
        """
        color = color or theme_manager.primary_color
        
        indicator = ft.ProgressRing(
            width=size,
            height=size,
            stroke_width=3,
            color=color
        )
        
        if message:
            content = ft.Column(
                controls=[
                    indicator,
                    ft.Divider(height=10, color="transparent"),
                    ft.Text(
                        message,
                        size=14,
                        color=theme_manager.text_secondary_color,
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0
            )
        else:
            content = indicator
        
        if full_screen:
            return ft.Container(
                content=content,
                alignment=ft.alignment.center,
                expand=True,
                bgcolor=ft.Colors.with_opacity(0.7, theme_manager.background_color)
            )
        else:
            return ft.Container(
                content=content,
                alignment=ft.alignment.center,
                expand=True
            )
    
    @staticmethod
    def create_skeleton(
        width: Optional[int] = None,
        height: int = 20,
        count: int = 3,
        spacing: int = 10
    ) -> ft.Control:
        """
        Create a skeleton loader (placeholder rectangles).
        
        Args:
            width: Width of skeleton items (None = expand)
            height: Height of skeleton items
            count: Number of skeleton items
            spacing: Spacing between items
            
        Returns:
            Skeleton loader control
        """
        skeleton_items = []
        for _ in range(count):
            item = ft.Container(
                width=width,
                height=height,
                bgcolor=theme_manager.surface_color,
                border_radius=theme_manager.corner_radius,
                animate=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT)
            )
            skeleton_items.append(item)
        
        return ft.Column(
            controls=skeleton_items,
            spacing=spacing,
            expand=True if width is None else False
        )
    
    @staticmethod
    def create_progress(
        value: Optional[float] = None,
        width: Optional[int] = None,
        height: int = 8,
        color: Optional[str] = None,
        message: Optional[str] = None
    ) -> ft.Control:
        """
        Create a progress bar indicator.
        
        Args:
            value: Progress value (0.0-1.0, None = indeterminate)
            width: Width of progress bar (None = expand)
            height: Height of progress bar
            color: Color of progress bar (uses theme primary if None)
            message: Optional message to display
            
        Returns:
            Progress bar control
        """
        color = color or theme_manager.primary_color
        
        progress_bar = ft.ProgressBar(
            value=value,
            width=width,
            height=height,
            color=color,
            bgcolor=theme_manager.surface_color
        )
        
        if message:
            content = ft.Column(
                controls=[
                    progress_bar,
                    ft.Divider(height=5, color="transparent"),
                    ft.Text(
                        message,
                        size=12,
                        color=theme_manager.text_secondary_color
                    )
                ],
                spacing=0,
                expand=True if width is None else False
            )
        else:
            content = progress_bar
        
        return ft.Container(
            content=content,
            expand=True if width is None else False
        )
    
    @staticmethod
    def create_inline(size: int = 16) -> ft.Control:
        """
        Create a small inline loading indicator.
        
        Args:
            size: Size of the indicator
            
        Returns:
            Inline loading indicator
        """
        return ft.ProgressRing(
            width=size,
            height=size,
            stroke_width=2,
            color=theme_manager.primary_color
        )

