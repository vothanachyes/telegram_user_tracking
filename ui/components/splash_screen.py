"""
Splash screen component with breathing animation.
"""

import flet as ft
import asyncio
import time
from ui.theme import theme_manager
from config.settings import settings
from utils.constants import SPLASH_SCREEN_DURATION


class SplashScreen(ft.Container):
    """Splash screen with logo and breathing animation."""
    
    def __init__(self):
        self._is_visible = True
        self._animation_task = None
        self._login_page = None  # Reference to login page for error cases
        self._start_time = time.time()  # Track when splash screen appeared
        
        # Create logo icon
        self.logo_icon = ft.Icon(
            name=ft.Icons.TELEGRAM,
            size=100,
            color=theme_manager.primary_color,
        )
        
        # Create animated container for breathing effect
        self.animated_container = ft.Container(
            content=self.logo_icon,
            animate_scale=ft.Animation(
                duration=1500,
                curve=ft.AnimationCurve.EASE_IN_OUT
            ),
            scale=1.0,
        )
        
        # Build layout
        super().__init__(
            content=ft.Column(
                [
                    self.animated_container,
                    ft.Container(height=20),
                    ft.Text(
                        settings.app_name,
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            alignment=ft.alignment.center,
            expand=True,
            bgcolor=theme_manager.background_color,
            visible=self._is_visible,
        )
    
    def start_animation(self, page: ft.Page):
        """Start the breathing animation."""
        if self._animation_task:
            return
        
        async def animate():
            while self._is_visible:
                # Scale up
                self.animated_container.scale = 1.1
                if page:
                    page.update()
                await asyncio.sleep(0.75)
                
                # Scale down
                self.animated_container.scale = 1.0
                if page:
                    page.update()
                await asyncio.sleep(0.75)
        
        if page and hasattr(page, 'run_task'):
            self._animation_task = page.run_task(animate)
        else:
            self._animation_task = asyncio.create_task(animate())
    
    async def hide(self, page: ft.Page, min_duration: float = None):
        """Hide the splash screen with fade out.
        
        Args:
            page: Flet page instance
            min_duration: Minimum duration in seconds (defaults to SPLASH_SCREEN_DURATION from env)
        """
        if min_duration is None:
            min_duration = SPLASH_SCREEN_DURATION
        # Ensure minimum duration
        elapsed = time.time() - self._start_time
        remaining_time = max(0, min_duration - elapsed)
        if remaining_time > 0:
            await asyncio.sleep(remaining_time)
        
        self._is_visible = False
        self.opacity = 0
        self.animate_opacity = ft.Animation(
            duration=300,
            curve=ft.AnimationCurve.EASE_OUT
        )
        if page:
            page.update()
        
        # Stop animation task
        if self._animation_task:
            try:
                self._animation_task.cancel()
            except:
                pass
            self._animation_task = None

