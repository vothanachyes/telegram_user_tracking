"""
General/Router skeleton loader for unknown pages.
"""

import flet as ft
from ui.theme import theme_manager
from ui.components.skeleton_loaders.base import (
    SkeletonCard,
    SkeletonText
)


class GeneralSkeleton:
    """General skeleton loader for unknown pages."""
    
    @staticmethod
    def create() -> ft.Control:
        """Create general page skeleton."""
        return ft.Container(
            content=ft.Column([
                # Header skeleton
                SkeletonText(width=200, height=28, delay=0),
                
                ft.Container(height=theme_manager.spacing_md),
                
                # Content area skeleton
                SkeletonCard(
                    expand=True,
                    height=400,
                    delay=50
                ),
                
            ], spacing=theme_manager.spacing_md, expand=True),
            padding=theme_manager.padding_lg,
            expand=True
        )

