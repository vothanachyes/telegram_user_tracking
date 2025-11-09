"""
Toast card builder.
"""

import flet as ft
from typing import Optional, Callable
from ui.components.toast.types import ToastType, ToastColors


class ToastBuilder:
    """Builder for toast notification cards."""
    
    @staticmethod
    def create_toast_card(
        message: str,
        toast_type: ToastType,
        action_label: Optional[str] = None,
        on_action: Optional[Callable] = None,
        on_close: Optional[Callable] = None
    ) -> ft.Container:
        """Create a toast notification card."""
        colors = ToastColors.get_colors(toast_type)
        
        # Create toast content
        toast_content = ft.Row(
            controls=[
                ft.Icon(
                    colors["icon"],
                    color=colors["icon_color"],
                    size=24,
                ),
                ft.Text(
                    message,
                    color=ft.Colors.WHITE,
                    size=14,
                    weight=ft.FontWeight.W_500,
                    expand=True,
                ),
            ],
            spacing=12,
            tight=True,
        )
        
        # Add action button if provided
        if action_label and on_action:
            toast_content.controls.append(
                ft.TextButton(
                    action_label,
                    on_click=lambda e, callback=on_action: callback(),
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                    ),
                )
            )
        
        # Create close button
        close_button = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=18,
            icon_color=ft.Colors.WHITE70,
            tooltip="Close",
            on_click=lambda e: on_close() if on_close else None,
            style=ft.ButtonStyle(
                padding=ft.padding.all(4),
            ),
        )
        
        toast_content.controls.append(close_button)
        
        # Create toast card
        toast_card = ft.Container(
            content=ft.Container(
                content=toast_content,
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
            ),
            bgcolor=colors["bg"],
            border_radius=8,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.BLACK26,
                offset=ft.Offset(0, 4),
            ),
            animate_opacity=ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_OUT),
            opacity=0,
        )
        
        return toast_card

