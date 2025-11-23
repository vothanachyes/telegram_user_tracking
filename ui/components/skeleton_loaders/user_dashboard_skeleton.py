"""
User Dashboard page skeleton loader.
"""

import flet as ft
from ui.theme import theme_manager
from ui.components.skeleton_loaders.base import (
    SkeletonCard,
    SkeletonRow,
    SkeletonCircle,
    SkeletonText,
    SkeletonButton
)


class UserDashboardSkeleton:
    """Skeleton loader for user dashboard page."""
    
    @staticmethod
    def create() -> ft.Control:
        """Create user dashboard page skeleton."""
        return ft.Container(
            content=ft.Column([
                # Header with search
                ft.Row([
                    SkeletonText(width=300, height=40, delay=0),  # Search bar
                    ft.Container(expand=True),
                    SkeletonButton(width=40, height=40, delay=50),
                    SkeletonButton(width=40, height=40, delay=100),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=10),
                
                # User detail section
                _create_user_detail_skeleton(150),
                
                # Tabs skeleton
                _create_tabs_skeleton(200),
                
            ], spacing=theme_manager.spacing_md, expand=True),
            padding=theme_manager.padding_lg,
            expand=True
        )


def _create_user_detail_skeleton(delay: int) -> ft.Container:
    """Create user detail card skeleton."""
    return SkeletonCard(
        height=150,
        padding=theme_manager.padding_md,
        delay=delay
    )


def _create_tabs_skeleton(delay: int) -> ft.Container:
    """Create tabs skeleton with content."""
    # Tab content skeleton
    tab_content = ft.Column([
        # Stats cards row
        ft.Row([
            SkeletonCard(width=200, height=100, delay=delay + 50),
            SkeletonCard(width=200, height=100, delay=delay + 100),
            SkeletonCard(width=200, height=100, delay=delay + 150),
        ], spacing=theme_manager.spacing_md, wrap=True),
        
        ft.Container(height=theme_manager.spacing_md),
        
        # Messages list skeleton
        ft.Column([
            SkeletonRow(height=80, delay=delay + 200 + (i * 50)) for i in range(10)
        ], spacing=theme_manager.spacing_sm, expand=True),
        
    ], spacing=theme_manager.spacing_md, expand=True)
    
    return ft.Container(
        content=tab_content,
        padding=theme_manager.padding_md,
        expand=True
    )

