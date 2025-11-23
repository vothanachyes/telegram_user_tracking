"""
Update notification toast component.
"""

import flet as ft
import logging
from typing import Optional, Callable
from pathlib import Path

from ui.components.toast import ToastNotification, ToastType
from ui.theme import theme_manager

logger = logging.getLogger(__name__)


def show_update_toast(
    page: ft.Page,
    version: str,
    download_path: str,
    on_install: Callable[[], None],
    on_ignore: Optional[Callable[[], None]] = None
):
    """
    Show update available toast notification.
    
    Args:
        page: Flet page instance
        version: New version string
        download_path: Path to downloaded update file
        on_install: Callback when Install button is clicked
        on_ignore: Optional callback when Ignore button is clicked
    """
    try:
        # Initialize toast if needed
        toast = ToastNotification()
        if not toast._page:
            toast.initialize(page)
        
        # Format file size if available
        file_path = Path(download_path)
        file_size_str = ""
        if file_path.exists():
            size_bytes = file_path.stat().st_size
            if size_bytes < 1024:
                file_size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                file_size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                file_size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
        
        # Create message
        message = f"Update {version} available"
        if file_size_str:
            message += f" ({file_size_str})"
        
        # Create custom toast with action buttons
        def handle_install():
            """Handle install button click."""
            try:
                on_install()
                # Dismiss toast after action
                if on_ignore:
                    on_ignore()
            except Exception as e:
                logger.error(f"Error in install handler: {e}")
                toast.error(f"Failed to install update: {e}", duration=4000)
        
        def handle_ignore():
            """Handle ignore button click."""
            if on_ignore:
                on_ignore()
        
        # Show toast with action buttons
        toast.show(
            message=message,
            toast_type=ToastType.INFO,
            duration=0,  # Don't auto-dismiss
            action_label="Install",
            on_action=handle_install
        )
        
        # Add ignore button by modifying the toast
        # Note: This is a workaround since toast.show() only supports one action
        # We'll use a custom implementation
        _show_custom_update_toast(page, version, file_size_str, handle_install, handle_ignore)
        
    except Exception as e:
        logger.error(f"Error showing update toast: {e}", exc_info=True)
        # Fallback to simple toast
        toast = ToastNotification()
        if not toast._page:
            toast.initialize(page)
        toast.info(f"Update {version} available. Check settings to install.")


def _show_custom_update_toast(
    page: ft.Page,
    version: str,
    file_size_str: str,
    on_install: Callable[[], None],
    on_ignore: Callable[[], None]
):
    """
    Show custom update toast with Ignore and Install buttons.
    
    Args:
        page: Flet page instance
        version: Version string
        file_size_str: Formatted file size string
        on_install: Install callback
        on_ignore: Ignore callback
    """
    try:
        # Initialize toast if needed
        toast = ToastNotification()
        if not toast._page:
            toast.initialize(page)
        
        if not toast._toast_container:
            return
        
        # Create message
        message = f"Update {version} available"
        if file_size_str:
            message += f" ({file_size_str})"
        
        # Create toast content with two buttons
        toast_content = ft.Row(
            controls=[
                ft.Icon(
                    ft.Icons.UPDATE,
                    color=ft.Colors.BLUE_300,
                    size=24,
                ),
                ft.Text(
                    message,
                    color=ft.Colors.WHITE,
                    size=14,
                    weight=ft.FontWeight.W_500,
                    expand=True,
                ),
                ft.TextButton(
                    "Ignore",
                    on_click=lambda e: _dismiss_and_callback(toast, on_ignore),
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                    ),
                ),
                ft.TextButton(
                    "Install",
                    on_click=lambda e: _dismiss_and_callback(toast, on_install),
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_600,
                    ),
                ),
            ],
            spacing=12,
            tight=True,
        )
        
        # Create close button
        close_button = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=18,
            icon_color=ft.Colors.WHITE70,
            tooltip="Close",
            on_click=lambda e, toast_id=id(toast_content): _dismiss_toast(toast, toast_id),
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
            bgcolor=ft.Colors.BLUE_700,
            border_radius=8,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.BLACK26,
                offset=ft.Offset(0, 4),
            ),
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            opacity=0,
            data=id(toast_content),
        )
        
        # Add to container
        toast._toast_container.controls.append(toast_card)
        toast._active_toasts.append(toast_card)
        
        # Update page
        page.update()
        
        # Animate in
        toast_card.opacity = 1
        page.update()
        
    except Exception as e:
        logger.error(f"Error showing custom update toast: {e}", exc_info=True)


def _dismiss_and_callback(toast: ToastNotification, callback: Callable[[], None]):
    """Dismiss toast and call callback."""
    try:
        callback()
        # Find and dismiss the toast
        if toast._active_toasts:
            last_toast = toast._active_toasts[-1]
            if hasattr(last_toast, 'data') and last_toast.data:
                _dismiss_toast(toast, last_toast.data)
    except Exception as e:
        logger.error(f"Error in dismiss callback: {e}")


def _dismiss_toast(toast: ToastNotification, toast_id: int):
    """Dismiss a specific toast by ID."""
    try:
        if not toast._page or not toast._toast_container:
            return
        
        toast_card = next(
            (t for t in toast._active_toasts if hasattr(t, 'data') and t.data == toast_id),
            None
        )
        
        if toast_card:
            # Animate out
            toast_card.opacity = 0
            toast._page.update()
            
            # Remove after animation
            import asyncio
            async def remove_after_animation():
                await asyncio.sleep(0.3)
                if toast_card in toast._toast_container.controls:
                    toast._toast_container.controls.remove(toast_card)
                if toast_card in toast._active_toasts:
                    toast._active_toasts.remove(toast_card)
                if toast._page:
                    toast._page.update()
            
            asyncio.create_task(remove_after_animation())
    except Exception as e:
        logger.error(f"Error dismissing toast: {e}")

