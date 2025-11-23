"""
Settings page skeleton loader.
"""

import flet as ft
from ui.theme import theme_manager
from ui.components.skeleton_loaders.base import (
    SkeletonCard,
    SkeletonRow,
    SkeletonText,
    SkeletonButton
)


class SettingsSkeleton:
    """Skeleton loader for settings page."""
    
    @staticmethod
    def create() -> ft.Control:
        """Create settings page skeleton."""
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
    """Create tabs skeleton with settings forms."""
    # Tab buttons row
    tab_buttons = ft.Row([
        SkeletonButton(width=120, height=40, delay=delay + (i * 50)) for i in range(6)
    ], spacing=theme_manager.spacing_sm, wrap=True)
    
    # Settings form skeleton
    form_content = ft.Column([
        SkeletonCard(width=None, height=80, delay=delay + 300 + (i * 50)) for i in range(8)
    ], spacing=theme_manager.spacing_md, expand=True)
    
    # Device list skeleton
    device_list = ft.Column([
        SkeletonRow(height=70, delay=delay + 300 + (i * 50)) for i in range(5)
    ], spacing=theme_manager.spacing_sm, expand=True)
    
    # License info card
    license_card = SkeletonCard(
        width=None,
        height=200,
        delay=delay + 300
    )
    
    return ft.Container(
        content=ft.Column([
            tab_buttons,
            ft.Container(height=theme_manager.spacing_md),
            form_content,  # Default visible tab
        ], spacing=0, expand=True),
        expand=True
    )

