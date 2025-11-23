"""
Telegram page skeleton loader.
"""

import flet as ft
from ui.theme import theme_manager
from ui.components.skeleton_loaders.base import (
    SkeletonCard,
    SkeletonTable,
    SkeletonText,
    SkeletonButton
)


class TelegramSkeleton:
    """Skeleton loader for telegram page."""
    
    @staticmethod
    def create() -> ft.Control:
        """Create telegram page skeleton."""
        return ft.Container(
            content=ft.Column([
                # Title
                SkeletonText(width=150, height=28, delay=0),
                
                # Tab bar with group dropdown
                ft.Container(
                    content=ft.Row([
                        SkeletonButton(width=100, height=40, delay=50),
                        SkeletonButton(width=100, height=40, delay=100),
                        ft.Container(expand=True),
                        SkeletonText(width=250, height=40, delay=150),
                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    height=48,
                    border=ft.border.only(bottom=ft.BorderSide(1, theme_manager.border_color)),
                    padding=ft.padding.only(left=20, right=10),
                ),
                
                # Filters bar skeleton
                _create_filters_bar_skeleton(200),
                
                # Table skeleton
                SkeletonTable(
                    rows=15,
                    columns=6,
                    row_height=50,
                    column_widths=[50, 200, 150, 300, 100, 150],
                    delay=250
                ),
                
            ], spacing=0, expand=True),
            padding=theme_manager.padding_lg,
            expand=True
        )


def _create_filters_bar_skeleton(delay: int) -> ft.Container:
    """Create filters bar skeleton."""
    return ft.Container(
        content=ft.Row([
            SkeletonText(width=150, height=40, delay=delay),
            SkeletonText(width=150, height=40, delay=delay + 50),
            SkeletonText(width=150, height=40, delay=delay + 100),
            ft.Container(expand=True),
            SkeletonButton(width=100, height=40, delay=delay + 150),
        ], spacing=theme_manager.spacing_md),
        padding=theme_manager.padding_md,
        border=ft.border.only(bottom=ft.BorderSide(1, theme_manager.border_color)),
    )

