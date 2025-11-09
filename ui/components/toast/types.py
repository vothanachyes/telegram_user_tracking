"""
Toast types and color definitions.
"""

from enum import Enum
import flet as ft


class ToastType(Enum):
    """Toast notification types."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ToastColors:
    """Color definitions for toast types."""
    
    @staticmethod
    def get_colors(toast_type: ToastType) -> dict:
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

