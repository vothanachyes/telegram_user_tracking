"""
Dashboard page skeleton loader.
"""

import flet as ft
from ui.theme import theme_manager
from ui.components.skeleton_loaders.base import (
    SkeletonCard,
    SkeletonRow,
    SkeletonCircle,
    SkeletonText,
    SkeletonButton,
    create_shimmer_animation
)


class DashboardSkeleton:
    """Skeleton loader for dashboard page."""
    
    @staticmethod
    def create() -> ft.Control:
        """Create dashboard page skeleton."""
        return ft.Container(
            content=ft.Column([
                # Header row
                ft.Row([
                    SkeletonText(width=150, height=28, delay=0),
                    ft.Container(expand=True),
                    SkeletonButton(width=200, height=40, delay=50),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=10),
                
                ft.Container(height=10),
                
                # Date range selector skeleton
                SkeletonRow(
                    height=50,
                    item_widths=[150, 200, 200, 100],
                    delay=100
                ),
                
                # Stat cards row
                ft.Row([
                    _create_stat_card_skeleton(0),
                    _create_stat_card_skeleton(150),
                    _create_stat_card_skeleton(300),
                    _create_stat_card_skeleton(450),
                ], spacing=theme_manager.spacing_md, wrap=True, run_spacing=theme_manager.spacing_md),
                
                ft.Container(height=theme_manager.spacing_md),
                
                # Monthly stats and recent activity row
                ft.Row([
                    _create_monthly_stats_skeleton(600),
                    _create_recent_activity_skeleton(650),
                ], spacing=theme_manager.spacing_md, expand=True),
                
                ft.Container(height=theme_manager.spacing_md),
                
                # Active users card
                _create_active_users_skeleton(700),
                
            ], scroll=ft.ScrollMode.AUTO, spacing=theme_manager.spacing_md),
            padding=theme_manager.padding_lg,
            expand=True
        )


def _create_stat_card_skeleton(delay: int) -> ft.Container:
    """Create a stat card skeleton matching StatCard layout."""
    return SkeletonCard(
        width=300,
        height=120,
        padding=theme_manager.padding_md,
        delay=delay
    )


def _create_monthly_stats_skeleton(delay: int) -> ft.Container:
    """Create monthly stats card skeleton."""
    return SkeletonCard(
        expand=True,
        height=200,
        padding=theme_manager.padding_md,
        delay=delay
    )


def _create_recent_activity_skeleton(delay: int) -> ft.Container:
    """Create recent activity card skeleton with message list."""
    message_items = []
    for i in range(5):
        message_items.append(
            SkeletonRow(
                height=70,
                item_widths=[40, None, 100],
                delay=delay + (i * 50),
                padding=ft.padding.all(10)
            )
        )
    
    return SkeletonCard(
        expand=True,
        padding=theme_manager.padding_md,
        delay=delay
    )


def _create_active_users_skeleton(delay: int) -> ft.Container:
    """Create active users card skeleton."""
    user_items = []
    for i in range(10):
        user_items.append(
            SkeletonRow(
                height=60,
                item_widths=[40, 150, 100, 60],
                delay=delay + (i * 50),
                padding=ft.padding.all(10)
            )
        )
    
    return ft.Container(
        content=ft.Column([
            ft.Row([
                SkeletonText(width=150, height=20, delay=delay),
                ft.Container(expand=True),
                SkeletonButton(width=40, height=40, delay=delay + 50),
            ]),
            ft.Container(height=theme_manager.spacing_sm),
            ft.Column(user_items, spacing=theme_manager.spacing_sm, expand=True),
        ], spacing=theme_manager.spacing_sm),
        bgcolor=theme_manager.surface_color,
        border=ft.border.all(1, theme_manager.border_color),
        border_radius=theme_manager.corner_radius,
        padding=theme_manager.padding_md,
        opacity=0.4,
        animate_opacity=create_shimmer_animation(delay)
    )

