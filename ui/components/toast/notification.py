"""
Main toast notification manager.
"""

import flet as ft
import asyncio
from typing import Optional, Literal, Callable
from ui.components.toast.types import ToastType, ToastColors
from ui.components.toast.builder import ToastBuilder
from ui.components.toast.positioning import ToastPositioning


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
        
        # Create positioned container for toasts
        positioned_toast = ToastPositioning.create_positioned_container(
            content=self._toast_container,
            position=position
        )
        
        # Remove old blocking overlay if it exists
        needs_recreate = False
        if hasattr(page, '_toast_overlay'):
            if isinstance(page._toast_overlay, ft.Stack):
                needs_recreate = True
            elif isinstance(page._toast_overlay, ft.Container):
                if page._toast_overlay is not positioned_toast:
                    needs_recreate = True
            
            if needs_recreate:
                if hasattr(page, 'overlay') and page.overlay:
                    if page._toast_overlay in page.overlay:
                        page.overlay.remove(page._toast_overlay)
        
        # Add positioned toast container directly to overlay
        if not hasattr(page, '_toast_overlay') or needs_recreate:
            page._toast_overlay = positioned_toast
            
            if not hasattr(page, 'overlay') or page.overlay is None:
                page.overlay = []
            
            if positioned_toast not in page.overlay:
                page.overlay.append(positioned_toast)
    
    def show(
        self,
        message: str,
        toast_type: ToastType = ToastType.INFO,
        duration: int = 3000,
        action_label: Optional[str] = None,
        on_action: Optional[Callable] = None,
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
                colors = ToastColors.get_colors(toast_type)
                snackbar = ft.SnackBar(
                    content=ft.Text(message, color=ft.Colors.WHITE),
                    action=action_label,
                    on_action=on_action,
                    bgcolor=colors["bg"]
                )
                self._page.snack_bar = snackbar
                self._page.snack_bar.open = True
                self._page.update()
            except:
                pass
            return
        
        # Create toast card with unique ID
        toast_id = id(message + str(toast_type))
        
        def on_close():
            self._dismiss_toast(toast_id)
        
        def handle_action():
            if on_action:
                on_action()
            self._dismiss_toast(toast_id)
        
        toast_card = ToastBuilder.create_toast_card(
            message=message,
            toast_type=toast_type,
            action_label=action_label,
            on_action=handle_action if action_label else None,
            on_close=on_close
        )
        
        # Store toast ID for dismissal
        toast_card.data = toast_id
        
        # Add to container
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
        if toast_card in self._active_toasts and hasattr(toast_card, 'data'):
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

