"""
Pie chart component for displaying statistics.
"""

import math
import flet as ft
from typing import Dict, Optional
from ui.theme import theme_manager


class PieChart(ft.Container):
    """Custom pie chart component using Flet containers."""
    
    def __init__(
        self,
        data: Dict[str, int],
        size: int = 200,
        colors: Optional[Dict[str, str]] = None
    ):
        """
        Initialize pie chart.
        
        Args:
            data: Dictionary with label -> value mapping
            size: Size of the pie chart in pixels
            colors: Optional dictionary mapping labels to colors
        """
        self.size = size
        self.data = data
        self.colors = colors or {}
        self._default_colors = {
            'fetched': ft.Colors.GREEN,
            'skipped_exist': ft.Colors.YELLOW,
            'skipped_deleted': ft.Colors.ORANGE,
            'total': ft.Colors.BLUE
        }
        
        super().__init__(
            content=self._build_chart(),
            width=size,
            height=size
        )
    
    def _build_chart(self) -> ft.Stack:
        """Build the pie chart using Stack and positioned containers."""
        if not self.data or sum(self.data.values()) == 0:
            # Empty chart
            return ft.Stack([
                ft.Container(
                    width=self.size,
                    height=self.size,
                    border_radius=self.size // 2,
                    bgcolor=ft.Colors.GREY_300,
                    content=ft.Center(
                        content=ft.Text(
                            "No Data",
                            size=12,
                            color=ft.Colors.GREY_600
                        )
                    )
                )
            ])
        
        # Calculate total
        total = sum(self.data.values())
        if total == 0:
            total = 1  # Avoid division by zero
        
        # Build segments
        segments = []
        current_angle = -90  # Start at top (12 o'clock)
        
        for label, value in self.data.items():
            if value == 0:
                continue
            
            # Calculate angle for this segment
            angle = (value / total) * 360
            
            # Get color
            color = self.colors.get(label, self._default_colors.get(label, ft.Colors.BLUE))
            
            # Create segment using Container with border_radius
            segment = self._create_segment(
                current_angle,
                angle,
                color,
                label,
                value,
                total
            )
            segments.append(segment)
            
            current_angle += angle
        
        return ft.Stack(segments)
    
    def _create_segment(
        self,
        start_angle: float,
        angle: float,
        color: str,
        label: str,
        value: int,
        total: int
    ) -> ft.Container:
        """Create a pie chart segment."""
        # For simplicity, we'll use a circular container with a colored background
        # A more sophisticated implementation would use Canvas or custom drawing
        # For now, we'll create a simple visual representation
        
        # Calculate percentage
        percentage = (value / total) * 100 if total > 0 else 0
        
        # Create a simple colored circle segment
        # Note: This is a simplified version. For a true pie chart, you'd need
        # to use Canvas or create multiple overlapping containers
        return ft.Container(
            width=self.size,
            height=self.size,
            border_radius=self.size // 2,
            bgcolor=color,
            opacity=0.7,
            tooltip=f"{label}: {value} ({percentage:.1f}%)"
        )
    
    def update_data(self, data: Dict[str, int]):
        """Update chart data and refresh."""
        self.data = data
        self.content = self._build_chart()
        if hasattr(self, 'page') and self.page:
            try:
                self.update()
            except:
                pass


class SimplePieChart(ft.Container):
    """Simplified pie chart using colored segments in a row."""
    
    def __init__(
        self,
        data: Dict[str, int],
        height: int = 20,
        colors: Optional[Dict[str, str]] = None
    ):
        """
        Initialize simple pie chart.
        
        Args:
            data: Dictionary with label -> value mapping
            height: Height of the chart bar
            colors: Optional dictionary mapping labels to colors
        """
        self.data = data
        self.colors = colors or {}
        self._default_colors = {
            'fetched': ft.Colors.GREEN,
            'skipped_exist': ft.Colors.YELLOW,
            'skipped_deleted': ft.Colors.ORANGE,
            'total': ft.Colors.BLUE
        }
        
        super().__init__(
            content=self._build_chart(),
            height=height
        )
    
    def _build_chart(self) -> ft.Row:
        """Build the simple pie chart as horizontal bars."""
        chart_height = getattr(self, '_chart_height', 20)
        
        if not self.data or sum(self.data.values()) == 0:
            return ft.Row([
                ft.Container(
                    expand=True,
                    height=chart_height,
                    bgcolor=ft.Colors.GREY_300,
                    border_radius=4
                )
            ])
        
        total = sum(self.data.values())
        if total == 0:
            total = 1
        
        segments = []
        for label, value in self.data.items():
            if value == 0:
                continue
            
            percentage = (value / total) * 100
            color = self.colors.get(label, self._default_colors.get(label, ft.Colors.BLUE))
            
            segments.append(
                ft.Container(
                    expand=value,
                    height=chart_height,
                    bgcolor=color,
                    border_radius=4,
                    tooltip=f"{label}: {value} ({percentage:.1f}%)"
                )
            )
        
        return ft.Row(segments, spacing=2, expand=True)
    
    def update_data(self, data: Dict[str, int]):
        """Update chart data and refresh."""
        self.data = data
        self.content = self._build_chart()
        if hasattr(self, 'page') and self.page:
            try:
                self.update()
            except:
                pass

