"""
Reports page skeleton loader.
"""

import flet as ft
from ui.theme import theme_manager
from ui.components.skeleton_loaders.base import (
    SkeletonCard,
    SkeletonTable,
    SkeletonText,
    SkeletonButton,
    SkeletonCircle
)


class ReportsSkeleton:
    """Skeleton loader for reports page."""
    
    @staticmethod
    def create() -> ft.Control:
        """Create reports page skeleton."""
        return ft.Container(
            content=ft.Column([
                # Header
                SkeletonText(width=150, height=28, delay=0),
                
                theme_manager.spacing_container("md"),
                
                # Tabs skeleton
                _create_tabs_skeleton(50),
                
            ], spacing=theme_manager.spacing_sm, expand=True),
            padding=theme_manager.padding_lg,
            expand=True
        )


def _create_tabs_skeleton(delay: int) -> ft.Container:
    """Create tabs skeleton with content."""
    from ui.components.skeleton_loaders.base import create_shimmer_animation
    
    # Tab buttons
    tab_buttons = ft.Row([
        SkeletonButton(width=150, height=40, delay=delay),
        SkeletonButton(width=150, height=40, delay=delay + 50),
        SkeletonButton(width=200, height=40, delay=delay + 100),
    ], spacing=theme_manager.spacing_sm)
    
    # Tab content - Active users table (default visible)
    active_users_content = ft.Column([
        # Filters bar
        _create_filters_bar_skeleton(delay + 150),
        ft.Container(height=theme_manager.spacing_md),
        # Table
        SkeletonTable(
            rows=10,
            columns=5,
            row_height=50,
            column_widths=[50, 150, 200, 150, 100],
            delay=delay + 200
        ),
    ], spacing=theme_manager.spacing_sm, expand=True)
    
    return ft.Container(
        content=ft.Column([
            tab_buttons,
            ft.Container(height=theme_manager.spacing_md),
            active_users_content,  # Default visible tab
        ], spacing=0, expand=True),
        expand=True
    )


def _create_filters_bar_skeleton(delay: int) -> ft.Container:
    """Create filters bar skeleton."""
    return ft.Container(
        content=ft.Row([
            SkeletonText(width=200, height=40, delay=delay),
            SkeletonText(width=150, height=40, delay=delay + 50),
            SkeletonText(width=150, height=40, delay=delay + 100),
            ft.Container(expand=True),
            SkeletonButton(width=120, height=40, delay=delay + 150),
        ], spacing=theme_manager.spacing_md),
        padding=theme_manager.padding_md,
        bgcolor=theme_manager.surface_color,
        border_radius=theme_manager.corner_radius,
        border=ft.border.all(1, theme_manager.border_color),
    )


def _create_certificate_card_skeleton(delay: int) -> ft.Container:
    """Create certificate card skeleton."""
    return SkeletonCard(
        width=280,
        height=350,
        padding=theme_manager.padding_lg,
        delay=delay
    )

