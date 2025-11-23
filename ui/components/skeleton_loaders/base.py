"""
Base skeleton loader components with shimmer animations.
"""

import flet as ft
from typing import Optional
from ui.theme import theme_manager


def create_shimmer_animation(delay: int = 0) -> ft.Animation:
    """
    Create shimmer animation for skeleton loaders.
    
    Args:
        delay: Delay in milliseconds before animation starts
        
    Returns:
        Animation configuration
    """
    return ft.Animation(
        duration=1800,
        curve=ft.AnimationCurve.EASE_IN_OUT,
        delay=delay
    )


class SkeletonCard(ft.Container):
    """Skeleton card component matching StatCard and info card layouts."""
    
    def __init__(
        self,
        width: Optional[float] = None,
        height: Optional[float] = None,
        padding: Optional[ft.padding] = None,
        expand: bool = False,
        delay: int = 0
    ):
        padding = padding or theme_manager.padding_md
        
        super().__init__(
            width=width,
            height=height,
            padding=padding,
            bgcolor=theme_manager.surface_color,
            border_radius=theme_manager.corner_radius,
            expand=expand,
            opacity=0.4,
            animate_opacity=create_shimmer_animation(delay)
        )


class SkeletonRow(ft.Row):
    """Skeleton row for list items and table rows."""
    
    def __init__(
        self,
        height: float = 60,
        item_widths: Optional[list] = None,
        spacing: Optional[float] = None,
        padding: Optional[ft.padding] = None,
        delay: int = 0
    ):
        spacing = spacing or theme_manager.spacing_md
        padding = padding or ft.padding.symmetric(horizontal=10, vertical=8)
        
        items = []
        if item_widths:
            for width in item_widths:
                items.append(
                    ft.Container(
                        width=width,
                        height=height - 16,
                        bgcolor=theme_manager.surface_color,
                        border_radius=theme_manager.corner_radius_sm,
                        opacity=0.4,
                        animate_opacity=create_shimmer_animation(delay)
                    )
                )
        else:
            items.append(
                ft.Container(
                    expand=True,
                    height=height - 16,
                    bgcolor=theme_manager.surface_color,
                    border_radius=theme_manager.corner_radius_sm,
                    opacity=0.4,
                    animate_opacity=create_shimmer_animation(delay)
                )
            )
        
        super().__init__(
            controls=items,
            spacing=spacing,
            height=height,
            padding=padding
        )


class SkeletonCircle(ft.Container):
    """Skeleton circle for avatars and icons."""
    
    def __init__(
        self,
        size: float = 40,
        delay: int = 0
    ):
        super().__init__(
            width=size,
            height=size,
            border_radius=size / 2,
            bgcolor=theme_manager.surface_color,
            opacity=0.4,
            animate_opacity=create_shimmer_animation(delay)
        )


class SkeletonText(ft.Container):
    """Skeleton text placeholder with varying widths."""
    
    def __init__(
        self,
        width: Optional[float] = None,
        height: float = 16,
        delay: int = 0
    ):
        super().__init__(
            width=width,
            height=height,
            bgcolor=theme_manager.surface_color,
            border_radius=theme_manager.corner_radius_sm,
            opacity=0.4,
            animate_opacity=create_shimmer_animation(delay)
        )


class SkeletonTable(ft.Container):
    """Skeleton table with multiple rows."""
    
    def __init__(
        self,
        rows: int = 10,
        columns: int = 5,
        row_height: float = 50,
        column_widths: Optional[list] = None,
        delay: int = 0
    ):
        table_rows = []
        for i in range(rows):
            row_delay = delay + (i * 50)  # Stagger animations
            if column_widths:
                row_items = [
                    ft.Container(
                        width=width,
                        height=row_height - 10,
                        bgcolor=theme_manager.surface_color,
                        border_radius=theme_manager.corner_radius_sm,
                        opacity=0.4,
                        animate_opacity=create_shimmer_animation(row_delay)
                    )
                    for width in column_widths
                ]
            else:
                row_items = [
                    ft.Container(
                        expand=True,
                        height=row_height - 10,
                        bgcolor=theme_manager.surface_color,
                        border_radius=theme_manager.corner_radius_sm,
                        opacity=0.4,
                        animate_opacity=create_shimmer_animation(row_delay)
                    )
                    for _ in range(columns)
                ]
            
            table_rows.append(
                ft.Row(
                    controls=row_items,
                    spacing=theme_manager.spacing_sm,
                    height=row_height,
                    padding=ft.padding.symmetric(horizontal=10, vertical=5)
                )
            )
        
        super().__init__(
            content=ft.Column(
                controls=table_rows,
                spacing=theme_manager.spacing_xs
            ),
            padding=theme_manager.padding_md,
            expand=True
        )


class SkeletonButton(ft.Container):
    """Skeleton button placeholder."""
    
    def __init__(
        self,
        width: Optional[float] = None,
        height: float = 36,
        delay: int = 0
    ):
        super().__init__(
            width=width or 100,
            height=height,
            bgcolor=theme_manager.surface_color,
            border_radius=theme_manager.corner_radius,
            opacity=0.4,
            animate_opacity=create_shimmer_animation(delay)
        )

