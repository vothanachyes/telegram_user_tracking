"""
Gradient background service with rotation.
"""

import asyncio
import logging
import threading
from typing import Optional
import flet as ft
from ui.theme import theme_manager

logger = logging.getLogger(__name__)


class GradientBackgroundService:
    """Service to manage rotating gradient background."""
    
    def __init__(self, page: ft.Page, container: ft.Container):
        """
        Initialize gradient background service.
        
        Args:
            page: Flet page instance
            container: Container to apply gradient to
        """
        self.page = page
        self.container = container
        self.rotation_angle = 0
        self._rotation_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Initialize gradient
        self._update_gradient()
    
    def _update_gradient(self):
        """Update container gradient with current rotation angle."""
        try:
            gradient = theme_manager.get_gradient_background(self.rotation_angle)
            self.container.gradient = gradient
            if self.page:
                self.page.update()
        except Exception as e:
            logger.error(f"Error updating gradient: {e}")
    
    async def _rotate_gradient(self):
        """Rotate gradient every 5 minutes."""
        while self._running:
            try:
                await asyncio.sleep(300)  # 5 minutes = 300 seconds
                # Rotate by 45 degrees
                self.rotation_angle = (self.rotation_angle + 45) % 360
                self._update_gradient()
                logger.debug(f"Gradient rotated to {self.rotation_angle}°")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in gradient rotation: {e}")
    
    def start(self):
        """Start gradient rotation."""
        if self._running:
            return
        
        self._running = True
        
        if hasattr(self.page, 'run_task'):
            self._rotation_task = self.page.run_task(self._rotate_gradient)
        else:
            # Fallback: use asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    self._rotation_task = asyncio.create_task(self._rotate_gradient())
                else:
                    def run_in_thread():
                        asyncio.run(self._rotate_gradient())
                    threading.Thread(target=run_in_thread, daemon=True).start()
            except Exception as e:
                logger.error(f"Error starting gradient rotation: {e}")
    
    def stop(self):
        """Stop gradient rotation."""
        self._running = False
        if self._rotation_task:
            try:
                self._rotation_task.cancel()
            except Exception:
                pass
            self._rotation_task = None

