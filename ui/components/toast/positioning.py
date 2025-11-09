"""
Toast positioning logic.
"""

import flet as ft
from typing import Literal


class ToastPositioning:
    """Handles toast positioning on the page."""
    
    @staticmethod
    def get_position_props(position: Literal["top-right", "top-left", "bottom-right", "bottom-left"]) -> dict:
        """Get absolute positioning properties based on position."""
        # Use absolute positioning (left/top/right/bottom) to prevent expansion
        # This ensures the container only takes up space where toasts are
        # Top position accounts for header height (45px) + spacing (10px) = 55px
        props = {}
        if "top" in position:
            props["top"] = 55  # Below header (45px) + spacing (10px)
        if "bottom" in position:
            props["bottom"] = 10
        if "right" in position:
            props["right"] = 10
        if "left" in position:
            props["left"] = 10
        return props
    
    @staticmethod
    def create_positioned_container(
        content: ft.Control,
        position: Literal["top-right", "top-left", "bottom-right", "bottom-left"]
    ) -> ft.Container:
        """Create positioned container for toasts."""
        position_props = ToastPositioning.get_position_props(position)
        
        return ft.Container(
            content=content,
            width=350,
            padding=10,
            **position_props
        )

