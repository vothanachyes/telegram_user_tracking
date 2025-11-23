"""
Modern splash screen component with advanced loading animations.
"""

import flet as ft
import asyncio
import time
import math
import random
from pathlib import Path
from typing import Optional, List
from ui.theme import theme_manager
from config.settings import settings
from utils.constants import SPLASH_SCREEN_DURATION


class SplashScreen(ft.Container):
    """Modern splash screen with rotating progress, pulsing logo, and loading dots."""
    
    def __init__(self):
        self._is_visible = True
        self._animation_tasks = []
        self._login_page = None  # Reference to login page for error cases
        self._start_time = time.time()  # Track when splash screen appeared
        self._page: Optional[ft.Page] = None
        
        # Get logo path (use transparent version for splash screen)
        project_root = Path(__file__).parent.parent.parent
        logo_path = project_root / 'assets' / 'appLogo_trp.png'
        
        # Fallback to regular logo if transparent version doesn't exist
        if not logo_path.exists():
            logo_path = project_root / 'assets' / 'appLogo.png'
        
        # Create logo image
        logo_image = None
        if logo_path.exists():
            logo_image = ft.Image(
                src=str(logo_path),
                width=140,
                height=140,
                fit=ft.ImageFit.CONTAIN,
            )
        else:
            # Fallback to icon if logo file doesn't exist
            logo_image = ft.Icon(
                name=ft.Icons.TELEGRAM,
                size=120,
                color=theme_manager.primary_color,
            )
        
        # Create rotating spinner ring with partial border for modern look
        # Use a gradient-like effect with partial borders
        self.rotating_ring = ft.Container(
            width=180,
            height=180,
            border=ft.border.only(
                top=ft.BorderSide(4, theme_manager.primary_color),
                right=ft.BorderSide(4, theme_manager.primary_color),
            ),
            border_radius=90,
            rotate=ft.Rotate(0, alignment=ft.alignment.center),
        )
        
        # Create pulsing logo container with shadow effect
        self.logo_container = ft.Container(
            content=logo_image,
            animate_scale=ft.Animation(
                duration=2000,
                curve=ft.AnimationCurve.EASE_IN_OUT
            ),
            animate_opacity=ft.Animation(
                duration=2000,
                curve=ft.AnimationCurve.EASE_IN_OUT
            ),
            scale=1.0,
            opacity=1.0,
        )
        
        # Create loading dots
        self.loading_dots = self._create_loading_dots()
        
        # Create app name text with subtle animation
        self.app_name_text = ft.Text(
            settings.app_name,
            size=theme_manager.font_size_page_title + 4,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            color=theme_manager.text_color,
            animate_opacity=ft.Animation(
                duration=1000,
                curve=ft.AnimationCurve.EASE_IN_OUT
            ),
            opacity=1.0,
        )
        
        # Create version/subtitle text (optional)
        self.subtitle_text = ft.Text(
            "Loading...",
            size=theme_manager.font_size_small,
            text_align=ft.TextAlign.CENTER,
            color=theme_manager.text_secondary_color,
            animate_opacity=ft.Animation(
                duration=1000,
                curve=ft.AnimationCurve.EASE_IN_OUT
            ),
            opacity=0.7,
        )
        
        # Create animated background illustration (Digital Breath effect)
        self.background_illustration = self._create_background_illustration()
        
        # Build main content with centered logo and rotating ring
        logo_with_ring = ft.Stack(
            [
                # Rotating ring (background)
                ft.Container(
                    content=self.rotating_ring,
                    alignment=ft.alignment.center,
                ),
                # Logo (foreground)
                ft.Container(
                    content=self.logo_container,
                    alignment=ft.alignment.center,
                ),
            ],
            width=180,
            height=180,
        )
        
        # Build main content column
        main_content = ft.Column(
            [
                logo_with_ring,
                ft.Container(height=theme_manager.spacing_xxl),
                self.app_name_text,
                ft.Container(height=theme_manager.spacing_sm),
                self.subtitle_text,
                ft.Container(height=theme_manager.spacing_lg),
                self.loading_dots,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=0,
        )
        
        # Build layout with background illustration and main content
        super().__init__(
            content=ft.Stack(
                [
                    # Background illustration (behind everything)
                    self.background_illustration,
                    # Main content (foreground)
                    ft.Container(
                        content=main_content,
                        alignment=ft.alignment.center,
                        expand=True,
                    ),
                ],
                expand=True,
            ),
            alignment=ft.alignment.center,
            expand=True,
            # Use gradient background for modern look
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[
                    theme_manager.background_color,
                    theme_manager.surface_color,
                ] if theme_manager.is_dark else [
                    theme_manager.background_color,
                    theme_manager.surface_color,
                ],
            ),
            visible=self._is_visible,
        )
    
    def _create_loading_dots(self) -> ft.Row:
        """Create animated loading dots."""
        dot_size = 8
        dot_color = theme_manager.primary_color
        
        # Create three dots with different initial opacities
        self.dot1 = ft.Container(
            width=dot_size,
            height=dot_size,
            border_radius=dot_size / 2,
            bgcolor=dot_color,
            animate_opacity=ft.Animation(
                duration=600,
                curve=ft.AnimationCurve.EASE_IN_OUT
            ),
            opacity=0.3,
        )
        
        self.dot2 = ft.Container(
            width=dot_size,
            height=dot_size,
            border_radius=dot_size / 2,
            bgcolor=dot_color,
            animate_opacity=ft.Animation(
                duration=600,
                curve=ft.AnimationCurve.EASE_IN_OUT
            ),
            opacity=0.6,
        )
        
        self.dot3 = ft.Container(
            width=dot_size,
            height=dot_size,
            border_radius=dot_size / 2,
            bgcolor=dot_color,
            animate_opacity=ft.Animation(
                duration=600,
                curve=ft.AnimationCurve.EASE_IN_OUT
            ),
            opacity=1.0,
        )
        
        return ft.Row(
            [self.dot1, self.dot2, self.dot3],
            spacing=theme_manager.spacing_sm,
            alignment=ft.MainAxisAlignment.CENTER,
        )
    
    def _create_background_illustration(self) -> ft.Container:
        """Create animated digital circuit background illustration."""
        # Create circuit/digital pattern elements
        self.circuit_elements: List[ft.Container] = []
        self.circuit_data: List[dict] = []  # Store animation data
        
        # Create circuit pattern with lines and nodes
        num_elements = 12
        
        for i in range(num_elements):
            # Random position (percentage of screen)
            x_percent = random.uniform(0.05, 0.95)
            y_percent = random.uniform(0.05, 0.95)
            
            # Random animation phase
            phase = random.uniform(0, math.pi * 2)
            
            # Random size for circuit element
            size = random.uniform(40, 120)
            
            # Determine if it's a horizontal or vertical line, or a node
            element_type = random.choice(['horizontal', 'vertical', 'node'])
            
            # Store circuit element data
            self.circuit_data.append({
                'x_percent': x_percent,
                'y_percent': y_percent,
                'phase': phase,
                'speed': random.uniform(0.2, 0.5),
                'size': size,
                'type': element_type,
            })
            
            # Create circuit element based on type
            if element_type == 'horizontal':
                # Horizontal line
                element = ft.Container(
                    width=size,
                    height=2,
                    bgcolor=theme_manager.primary_color,
                    opacity=0.1,
                    scale=1.0,
                    left=0,
                    top=0,
                )
            elif element_type == 'vertical':
                # Vertical line
                element = ft.Container(
                    width=2,
                    height=size,
                    bgcolor=theme_manager.primary_color,
                    opacity=0.1,
                    scale=1.0,
                    left=0,
                    top=0,
                )
            else:
                # Node/circle
                element = ft.Container(
                    width=size * 0.3,
                    height=size * 0.3,
                    border_radius=size * 0.15,
                    border=ft.border.all(2, theme_manager.primary_color),
                    bgcolor=None,
                    opacity=0.1,
                    scale=1.0,
                    left=0,
                    top=0,
                )
            
            self.circuit_elements.append(element)
        
        # Create stack container for absolute positioning
        return ft.Container(
            content=ft.Stack(
                controls=self.circuit_elements,
                expand=True,
            ),
            expand=True,
            opacity=1.0,  # Opacity controlled per element
        )
    
    def start_animation(self, page: ft.Page):
        """Start all animations."""
        if self._page:
            return  # Already started
        
        self._page = page
        
        # Start rotating progress ring animation
        self._start_progress_animation()
        
        # Start pulsing logo animation
        self._start_logo_pulse_animation()
        
        # Start loading dots animation
        self._start_dots_animation()
        
        # Start background illustration animation
        self._start_background_animation()
    
    def _start_progress_animation(self):
        """Start rotating spinner ring animation."""
        async def animate_rotation():
            rotation_angle = 0.0
            while self._is_visible:
                rotation_angle += 3.0  # Rotate 3 degrees per frame (slower)
                if rotation_angle >= 360.0:
                    rotation_angle = 0.0
                
                # Update rotation
                self.rotating_ring.rotate = ft.Rotate(
                    rotation_angle,
                    alignment=ft.alignment.center
                )
                
                if self._page:
                    self._page.update()
                
                await asyncio.sleep(0.05)  # Slower update rate for smoother, continuous rotation
        
        if self._page and hasattr(self._page, 'run_task'):
            self._page.run_task(animate_rotation)
        else:
            task = asyncio.create_task(animate_rotation())
            self._animation_tasks.append(task)
    
    def _start_logo_pulse_animation(self):
        """Start pulsing logo animation."""
        async def animate_logo():
            while self._is_visible:
                # Pulse up
                self.logo_container.scale = 1.08
                self.logo_container.opacity = 0.9
                if self._page:
                    self._page.update()
                await asyncio.sleep(1.0)
                
                # Pulse down
                self.logo_container.scale = 1.0
                self.logo_container.opacity = 1.0
                if self._page:
                    self._page.update()
                await asyncio.sleep(1.0)
        
        if self._page and hasattr(self._page, 'run_task'):
            self._page.run_task(animate_logo)
        else:
            task = asyncio.create_task(animate_logo())
            self._animation_tasks.append(task)
    
    def _start_dots_animation(self):
        """Start infinite loading dots wave animation."""
        async def animate_dots():
            while self._is_visible:
                # Infinite wave effect: dot1 -> dot2 -> dot3 -> repeat
                # Wave effect: dot1 -> dot2 -> dot3
                self.dot1.opacity = 1.0
                self.dot2.opacity = 0.3
                self.dot3.opacity = 0.3
                if self._page:
                    self._page.update()
                await asyncio.sleep(0.3)
                
                self.dot1.opacity = 0.3
                self.dot2.opacity = 1.0
                self.dot3.opacity = 0.3
                if self._page:
                    self._page.update()
                await asyncio.sleep(0.3)
                
                self.dot1.opacity = 0.3
                self.dot2.opacity = 0.3
                self.dot3.opacity = 1.0
                if self._page:
                    self._page.update()
                await asyncio.sleep(0.3)
                
                # Continue loop infinitely
        
        if self._page and hasattr(self._page, 'run_task'):
            self._page.run_task(animate_dots)
        else:
            task = asyncio.create_task(animate_dots())
            self._animation_tasks.append(task)
    
    def _start_background_animation(self):
        """Start digital circuit background animation with scale in/out."""
        async def animate_circuit():
            time_offset = 0.0
            while self._is_visible:
                time_offset += 0.02
                
                # Get page dimensions if available
                page_width = 800  # Default
                page_height = 600  # Default
                if self._page:
                    try:
                        page_width = self._page.width or 800
                        page_height = self._page.height or 600
                    except:
                        pass
                
                # Animate each circuit element with scale in/out effect
                for i, (element, data) in enumerate(zip(self.circuit_elements, self.circuit_data)):
                    # Create breathing effect using sine wave
                    phase = data['phase'] + (time_offset * data['speed'])
                    
                    # Scale animation: 0.8 to 1.2 (breathing effect)
                    scale = 0.8 + 0.4 * (math.sin(phase * 1.2) * 0.5 + 0.5)
                    element.scale = scale
                    
                    # Fixed opacity at 10% (0.1)
                    element.opacity = 0.1
                    
                    # Calculate position
                    base_x = data['x_percent'] * page_width
                    base_y = data['y_percent'] * page_height
                    
                    # Update position (center the element)
                    if data['type'] == 'horizontal':
                        element.left = base_x - (data['size'] / 2)
                        element.top = base_y - 1
                    elif data['type'] == 'vertical':
                        element.left = base_x - 1
                        element.top = base_y - (data['size'] / 2)
                    else:  # node
                        element.left = base_x - (data['size'] * 0.15)
                        element.top = base_y - (data['size'] * 0.15)
                
                if self._page:
                    self._page.update()
                
                await asyncio.sleep(0.05)  # ~20 FPS for background animation
        
        if self._page and hasattr(self._page, 'run_task'):
            self._page.run_task(animate_circuit)
        else:
            task = asyncio.create_task(animate_circuit())
            self._animation_tasks.append(task)
    
    async def hide(self, page: ft.Page, min_duration: float = None):
        """Hide the splash screen with smooth fade out.
        
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
        
        # Stop all animation tasks
        self._is_visible = False
        for task in self._animation_tasks:
            try:
                task.cancel()
            except:
                pass
        self._animation_tasks.clear()
        
        # Smooth fade out animation
        self.opacity = 0
        self.animate_opacity = ft.Animation(
            duration=400,
            curve=ft.AnimationCurve.EASE_OUT
        )
        
        # Also fade out child elements
        self.logo_container.opacity = 0
        self.app_name_text.opacity = 0
        self.subtitle_text.opacity = 0
        self.rotating_ring.opacity = 0
        self.background_illustration.opacity = 0
        self.dot1.opacity = 0
        self.dot2.opacity = 0
        self.dot3.opacity = 0
        
        # Fade out all circuit elements
        for element in self.circuit_elements:
            element.opacity = 0
        
        if page:
            page.update()
        
        # Wait for animation to complete
        await asyncio.sleep(0.4)



