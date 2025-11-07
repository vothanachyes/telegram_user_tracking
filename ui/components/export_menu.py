"""
Reusable export menu component for Excel and PDF exports.
"""

import flet as ft
from typing import Optional, Callable
from ui.theme import theme_manager


class ExportMenu:
    """Reusable export menu component with Excel and PDF options."""
    
    def __init__(
        self,
        on_export_excel: Optional[Callable[[], None]] = None,
        on_export_pdf: Optional[Callable[[], None]] = None,
        show_excel: bool = True,
        show_pdf: bool = True
    ):
        """
        Initialize export menu.
        
        Args:
            on_export_excel: Callback for Excel export
            on_export_pdf: Callback for PDF export
            show_excel: Whether to show Excel option
            show_pdf: Whether to show PDF option
        """
        self.on_export_excel = on_export_excel
        self.on_export_pdf = on_export_pdf
        
        # Build menu items
        items = []
        if show_excel and on_export_excel:
            items.append(
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_excel"),
                    icon=ft.Icons.TABLE_CHART,
                    on_click=lambda e: self.on_export_excel()
                )
            )
        
        if show_pdf and on_export_pdf:
            items.append(
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_pdf"),
                    icon=ft.Icons.PICTURE_AS_PDF,
                    on_click=lambda e: self.on_export_pdf()
                )
            )
        
        self.menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            tooltip=theme_manager.t("export"),
            items=items
        )
    
    def build(self) -> ft.PopupMenuButton:
        """Build and return the export menu."""
        return self.menu
    
    def update_callbacks(
        self,
        on_export_excel: Optional[Callable[[], None]] = None,
        on_export_pdf: Optional[Callable[[], None]] = None
    ):
        """Update export callbacks."""
        self.on_export_excel = on_export_excel
        self.on_export_pdf = on_export_pdf
        
        # Rebuild menu items
        items = []
        if self.on_export_excel:
            items.append(
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_excel"),
                    icon=ft.Icons.TABLE_CHART,
                    on_click=lambda e: self.on_export_excel()
                )
            )
        
        if self.on_export_pdf:
            items.append(
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_pdf"),
                    icon=ft.Icons.PICTURE_AS_PDF,
                    on_click=lambda e: self.on_export_pdf()
                )
            )
        
        self.menu.items = items
        if hasattr(self.menu, 'update'):
            self.menu.update()

