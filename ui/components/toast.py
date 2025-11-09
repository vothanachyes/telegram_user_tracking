"""
Global and reusable toast notification component.
"""

import flet as ft
from typing import Optional, Literal
from enum import Enum
import asyncio


class ToastType(Enum):
    """Toast notification types."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ToastNotification:
    """Global toast notification manager."""
    
    _instance: Optional['ToastNotification'] = None
    _page: Optional[ft.Page] = None
    _toast_container: Optional[ft.Container] = None
    _active_toasts: list = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, page: ft.Page, position: Literal["top-right", "top-left", "bottom-right", "bottom-left"] = "top-right"):
        """
        Initialize the toast system with a page reference.
        
        Args:
            page: Flet page instance
            position: Position of toast notifications
        """
        self._page = page
        self._position = position
        
        # Create toast container with Column for toasts
        self._toast_container = ft.Column(
            controls=[],
            spacing=10,
            tight=True,
            scroll=ft.ScrollMode.AUTO,
        )
        
        # Get positioning based on position parameter
        position_props = self._get_position_props()
        
        # Create positioned container for toasts
        # Use absolute positioning (left/top/right/bottom) instead of alignment
        # This prevents the container from expanding to fill the overlay
        # The container itself doesn't block clicks - only toast cards inside do
        positioned_toast = ft.Container(
            content=self._toast_container,
            width=350,
            padding=10,
            **position_props  # left, top, right, or bottom properties
        )
        
        # Remove old blocking overlay if it exists
        needs_recreate = False
        if hasattr(page, '_toast_overlay'):
            # Check if existing overlay is a Stack or has expand=True
            if isinstance(page._toast_overlay, ft.Stack):
                needs_recreate = True
            elif isinstance(page._toast_overlay, ft.Container):
                # Check if it's the old wrapper (not our positioned_toast)
                if page._toast_overlay is not positioned_toast:
                    needs_recreate = True
            
            if needs_recreate:
                # Remove old overlay from page.overlay if present
                if hasattr(page, 'overlay') and page.overlay:
                    if page._toast_overlay in page.overlay:
                        page.overlay.remove(page._toast_overlay)
        
        # Add positioned toast container directly to overlay (no Stack, no expand!)
        # This container only takes up 350px width space, doesn't block the page
        if not hasattr(page, '_toast_overlay') or needs_recreate:
            page._toast_overlay = positioned_toast
            
            # Initialize overlay list if needed
            if not hasattr(page, 'overlay') or page.overlay is None:
                page.overlay = []
            
            # Add to overlay if not already added
            if positioned_toast not in page.overlay:
                page.overlay.append(positioned_toast)
    
    def _get_alignment(self) -> ft.Alignment:
        """Get alignment based on position."""
        alignments = {
            "top-right": ft.alignment.top_right,
            "top-left": ft.alignment.top_left,
            "bottom-right": ft.alignment.bottom_right,
            "bottom-left": ft.alignment.bottom_left,
        }
        return alignments.get(self._position, ft.alignment.top_right)
    
    def _get_position_props(self) -> dict:
        """Get absolute positioning properties based on position."""
        # Use absolute positioning (left/top/right/bottom) to prevent expansion
        # This ensures the container only takes up space where toasts are
        # Top position accounts for header height (45px) + spacing (10px) = 55px
        props = {}
        if "top" in self._position:
            props["top"] = 55  # Below header (45px) + spacing (10px)
        if "bottom" in self._position:
            props["bottom"] = 10
        if "right" in self._position:
            props["right"] = 10
        if "left" in self._position:
            props["left"] = 10
        return props
    
    def _get_toast_colors(self, toast_type: ToastType) -> dict:
        """Get colors for toast type."""
        colors = {
            ToastType.SUCCESS: {
                "bg": ft.Colors.GREEN_700,
                "icon": ft.Icons.CHECK_CIRCLE,
                "icon_color": ft.Colors.GREEN_300,
            },
            ToastType.ERROR: {
                "bg": ft.Colors.RED_700,
                "icon": ft.Icons.ERROR,
                "icon_color": ft.Colors.RED_300,
            },
            ToastType.WARNING: {
                "bg": ft.Colors.ORANGE_700,
                "icon": ft.Icons.WARNING,
                "icon_color": ft.Colors.ORANGE_300,
            },
            ToastType.INFO: {
                "bg": ft.Colors.BLUE_700,
                "icon": ft.Icons.INFO,
                "icon_color": ft.Colors.BLUE_300,
            },
        }
        return colors.get(toast_type, colors[ToastType.INFO])
    
    def show(
        self,
        message: str,
        toast_type: ToastType = ToastType.INFO,
        duration: int = 3000,
        action_label: Optional[str] = None,
        on_action: Optional[callable] = None,
    ):
        """
        Show a toast notification.
        
        Args:
            message: Message to display
            toast_type: Type of toast (SUCCESS, ERROR, WARNING, INFO)
            duration: Duration in milliseconds before auto-dismiss
            action_label: Optional action button label
            on_action: Optional action callback
        """
        # Initialize if not already done
        if not self._page:
            return
        
        if not self._toast_container:
            self.initialize(self._page)
        
        if not self._toast_container:
            # Fallback to snackbar if toast initialization failed
            try:
                snackbar = ft.SnackBar(
                    content=ft.Text(message, color=ft.Colors.WHITE),
                    action=action_label,
                    on_action=on_action,
                    bgcolor=self._get_toast_colors(toast_type)["bg"]
                )
                self._page.snack_bar = snackbar
                self._page.snack_bar.open = True
                self._page.update()
            except:
                pass
            return
        
        colors = self._get_toast_colors(toast_type)
        
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
                    on_click=lambda e, callback=on_action: self._handle_action(e, callback),
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
            on_click=lambda e, toast_id=id(toast_content): self._dismiss_toast(toast_id),
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
            animate_opacity=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
            opacity=0,
            data=id(toast_content),  # Store ID for dismissal
        )
        
        # Add to container (toast_container is now a Column directly)
        self._toast_container.controls.append(toast_card)
        self._active_toasts.append(toast_card)
        
        # Update page
        self._page.update()
        
        # Animate in
        toast_card.opacity = 1
        self._page.update()
        
        # Auto-dismiss after duration
        if duration > 0:
            asyncio.create_task(self._auto_dismiss(toast_card, duration))
    
    def _handle_action(self, e, callback: callable):
        """Handle action button click."""
        if callback:
            callback()
        # Dismiss toast after action
        toast_card = next(
            (t for t in self._active_toasts if hasattr(t, 'data') and t.data),
            None
        )
        if toast_card:
            self._dismiss_toast(toast_card.data)
    
    def _dismiss_toast(self, toast_id: int):
        """Dismiss a specific toast by ID."""
        if not self._page or not self._toast_container:
            return
        
        toast_card = next(
            (t for t in self._active_toasts if hasattr(t, 'data') and t.data == toast_id),
            None
        )
        
        if toast_card:
            # Animate out
            toast_card.opacity = 0
            self._page.update()
            
            # Remove after animation
            async def remove_after_animation():
                await asyncio.sleep(0.3)
                if toast_card in self._toast_container.controls:
                    self._toast_container.controls.remove(toast_card)
                if toast_card in self._active_toasts:
                    self._active_toasts.remove(toast_card)
                if self._page:
                    self._page.update()
            
            asyncio.create_task(remove_after_animation())
    
    async def _auto_dismiss(self, toast_card: ft.Container, duration: int):
        """Auto-dismiss toast after duration."""
        await asyncio.sleep(duration / 1000)  # Convert to seconds
        if toast_card in self._active_toasts:
            self._dismiss_toast(toast_card.data)
    
    def success(self, message: str, duration: int = 3000):
        """Show success toast."""
        self.show(message, ToastType.SUCCESS, duration)
    
    def error(self, message: str, duration: int = 4000):
        """Show error toast."""
        self.show(message, ToastType.ERROR, duration)
    
    def warning(self, message: str, duration: int = 3500):
        """Show warning toast."""
        self.show(message, ToastType.WARNING, duration)
    
    def info(self, message: str, duration: int = 3000):
        """Show info toast."""
        self.show(message, ToastType.INFO, duration)


# Global toast instance
toast = ToastNotification()

