"""
Groups page skeleton loader.
"""

import flet as ft
from ui.theme import theme_manager
from ui.components.skeleton_loaders.base import (
    SkeletonCard,
    SkeletonCircle,
    SkeletonText,
    SkeletonButton
)


class GroupsSkeleton:
    """Skeleton loader for groups page."""
    
    @staticmethod
    def create() -> ft.Control:
        """Create groups page skeleton."""
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Row([
                    ft.Icon(ft.Icons.GROUP, size=theme_manager.font_size_page_title, color=theme_manager.primary_color),
                    SkeletonText(width=100, height=28, delay=0),
                    ft.Container(expand=True),
                    SkeletonButton(width=50, height=50, delay=50),
                    SkeletonButton(width=50, height=50, delay=100),
                ], spacing=10),
                
                ft.Container(height=20),
                
                # Group cards list
                ft.Column([
                    _create_group_card_skeleton(i * 50) for i in range(8)
                ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True),
                
            ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True),
            padding=theme_manager.padding_lg,
            expand=True
        )


def _create_group_card_skeleton(delay: int) -> ft.Container:
    """Create a group card skeleton matching group card layout."""
    from ui.components.skeleton_loaders.base import SkeletonCircle, SkeletonText, create_shimmer_animation
    
    return ft.Container(
        content=ft.Row([
            SkeletonCircle(size=48, delay=delay),
            ft.Container(width=theme_manager.spacing_md),
            ft.Column([
                SkeletonText(width=200, height=18, delay=delay + 10),
                SkeletonText(width=150, height=14, delay=delay + 20),
                SkeletonText(width=180, height=14, delay=delay + 30),
                SkeletonText(width=120, height=14, delay=delay + 40),
            ], spacing=5, expand=True),
            SkeletonText(width=24, height=24, delay=delay + 50),
        ], spacing=15),
        bgcolor=theme_manager.surface_color,
        border=ft.border.all(1, theme_manager.border_color),
        border_radius=theme_manager.corner_radius,
        padding=theme_manager.padding_md,
        opacity=0.4,
        animate_opacity=create_shimmer_animation(delay)
    )

