"""
About page skeleton loader.
"""

import flet as ft
from ui.theme import theme_manager
from ui.components.skeleton_loaders.base import (
    SkeletonCard,
    SkeletonText
)


class AboutSkeleton:
    """Skeleton loader for about page."""
    
    @staticmethod
    def create() -> ft.Control:
        """Create about page skeleton."""
        return ft.Container(
            content=ft.Column([
                # Title
                SkeletonText(width=150, height=28, delay=0),
                
                # Tabs skeleton
                _create_tabs_skeleton(50),
                
            ], scroll=ft.ScrollMode.AUTO, spacing=0, expand=True),
            padding=theme_manager.padding_lg,
            expand=True
        )


def _create_tabs_skeleton(delay: int) -> ft.Container:
    """Create tabs skeleton with content."""
    # Tab buttons
    tab_buttons = ft.Row([
        SkeletonText(width=100, height=40, delay=delay),
        SkeletonText(width=100, height=40, delay=delay + 50),
        SkeletonText(width=100, height=40, delay=delay + 100),
    ], spacing=theme_manager.spacing_md)
    
    # About tab content - info cards
    about_content = ft.Column([
        SkeletonCard(width=700, height=200, delay=delay + 150),
        ft.Container(height=theme_manager.spacing_lg),
        SkeletonCard(width=700, height=250, delay=delay + 200),
        ft.Container(height=theme_manager.spacing_lg),
        SkeletonCard(width=700, height=150, delay=delay + 250),
    ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
    
    # Pricing tab content - pricing cards
    pricing_content = ft.Row([
        SkeletonCard(width=280, height=400, delay=delay + 150 + (i * 50)) for i in range(3)
    ], spacing=theme_manager.spacing_lg, wrap=True, alignment=ft.MainAxisAlignment.CENTER)
    
    # Update tab content
    update_content = ft.Column([
        SkeletonCard(width=700, height=300, delay=delay + 150),
    ], spacing=theme_manager.spacing_md, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
    
    return ft.Container(
        content=ft.Column([
            tab_buttons,
            ft.Container(height=theme_manager.spacing_md),
            about_content,  # Default visible tab
        ], spacing=0, expand=True),
        expand=True
    )

