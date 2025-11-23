"""
Notifications page skeleton loader.
"""

import flet as ft
from ui.theme import theme_manager
from ui.components.skeleton_loaders.base import (
    SkeletonCard,
    SkeletonRow,
    SkeletonText
)


class NotificationsSkeleton:
    """Skeleton loader for notifications page."""
    
    @staticmethod
    def create() -> ft.Control:
        """Create notifications page skeleton."""
        return ft.Container(
            content=ft.Column([
                # Title
                SkeletonText(width=200, height=28, delay=0),
                
                # Tabs skeleton
                _create_tabs_skeleton(50),
                
            ], scroll=ft.ScrollMode.AUTO, spacing=0, expand=True),
            padding=theme_manager.padding_lg,
            expand=True
        )


def _create_tabs_skeleton(delay: int) -> ft.Container:
    """Create tabs skeleton with notification cards."""
    # Tab buttons
    tab_buttons = ft.Row([
        SkeletonText(width=100, height=40, delay=delay),
        SkeletonText(width=100, height=40, delay=delay + 50),
    ], spacing=theme_manager.spacing_md)
    
    # Notification cards
    notification_cards = ft.Column([
        _create_notification_card_skeleton(delay + 100 + (i * 50)) for i in range(6)
    ], spacing=theme_manager.spacing_md, scroll=ft.ScrollMode.AUTO, expand=True)
    
    return ft.Container(
        content=ft.Column([
            tab_buttons,
            ft.Container(height=theme_manager.spacing_md),
            notification_cards,
        ], spacing=0, expand=True),
        expand=True
    )


def _create_notification_card_skeleton(delay: int) -> ft.Container:
    """Create notification card skeleton."""
    return SkeletonCard(
        padding=theme_manager.padding_md,
        delay=delay
    )

