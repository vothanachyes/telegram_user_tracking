"""
Centralized file picker management for export operations.
"""

import flet as ft
from typing import Optional, Callable, Dict
from datetime import datetime
from ui.theme import theme_manager


class FilePickerManager:
    """Centralized manager for file pickers used in export operations."""
    
    def __init__(self, page: Optional[ft.Page] = None):
        """
        Initialize file picker manager.
        
        Args:
            page: Flet page instance (can be set later with set_page)
        """
        self.page = page
        self.pickers: Dict[str, ft.FilePicker] = {}
        self.callbacks: Dict[str, Callable] = {}
    
    def set_page(self, page: ft.Page):
        """Set the Flet page instance."""
        self.page = page
        # Ensure all existing pickers are in overlay
        for picker in self.pickers.values():
            self._ensure_picker_in_overlay(picker)
    
    def register_picker(
        self,
        name: str,
        on_result: Callable[[ft.FilePickerResultEvent], None]
    ) -> ft.FilePicker:
        """
        Register a file picker with a name and callback.
        
        Args:
            name: Unique name for the picker
            on_result: Callback when file is selected
            
        Returns:
            The created FilePicker instance
        """
        picker = ft.FilePicker(on_result=on_result)
        self.pickers[name] = picker
        self.callbacks[name] = on_result
        
        if self.page:
            self._ensure_picker_in_overlay(picker)
        
        return picker
    
    def get_picker(self, name: str) -> Optional[ft.FilePicker]:
        """
        Get a registered file picker by name.
        
        Args:
            name: Name of the picker
            
        Returns:
            FilePicker instance or None if not found
        """
        return self.pickers.get(name)
    
    def show_save_dialog(
        self,
        name: str,
        file_type: str = "excel",
        default_name: Optional[str] = None,
        dialog_title: Optional[str] = None
    ) -> bool:
        """
        Show save file dialog for a registered picker.
        
        Args:
            name: Name of the registered picker
            file_type: Type of file ("excel", "pdf", or "custom")
            default_name: Default filename
            dialog_title: Dialog title
            
        Returns:
            True if dialog was shown, False otherwise
        """
        picker = self.pickers.get(name)
        if not picker or not self.page:
            return False
        
        # Ensure picker is in overlay
        if not self._ensure_picker_in_overlay(picker):
            return False
        
        # Generate default name if not provided
        if not default_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if file_type == "excel":
                default_name = f"export_{timestamp}.xlsx"
            elif file_type == "pdf":
                default_name = f"export_{timestamp}.pdf"
            else:
                default_name = f"export_{timestamp}"
        
        # Map file type to Flet file type
        flet_file_type = ft.FilePickerFileType.CUSTOM
        allowed_extensions = []
        
        if file_type == "excel":
            flet_file_type = ft.FilePickerFileType.CUSTOM
            allowed_extensions = ["xlsx"]
        elif file_type == "pdf":
            flet_file_type = ft.FilePickerFileType.CUSTOM
            allowed_extensions = ["pdf"]
        
        try:
            picker.save_file(
                dialog_title=dialog_title or theme_manager.t("save_file"),
                file_name=default_name,
                file_type=flet_file_type,
                allowed_extensions=allowed_extensions if allowed_extensions else None
            )
            return True
        except Exception as ex:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error opening file picker: {ex}", exc_info=True)
            theme_manager.show_snackbar(
                self.page,
                f"Error opening file picker: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
            return False
    
    def show_excel_save_dialog(
        self,
        name: str,
        default_name: Optional[str] = None,
        dialog_title: Optional[str] = None
    ) -> bool:
        """
        Show Excel save dialog.
        
        Args:
            name: Name of the registered picker
            default_name: Default filename
            dialog_title: Dialog title
            
        Returns:
            True if dialog was shown, False otherwise
        """
        return self.show_save_dialog(
            name=name,
            file_type="excel",
            default_name=default_name,
            dialog_title=dialog_title or theme_manager.t("export_to_excel")
        )
    
    def show_pdf_save_dialog(
        self,
        name: str,
        default_name: Optional[str] = None,
        dialog_title: Optional[str] = None
    ) -> bool:
        """
        Show PDF save dialog.
        
        Args:
            name: Name of the registered picker
            default_name: Default filename
            dialog_title: Dialog title
            
        Returns:
            True if dialog was shown, False otherwise
        """
        return self.show_save_dialog(
            name=name,
            file_type="pdf",
            default_name=default_name,
            dialog_title=dialog_title or theme_manager.t("export_to_pdf")
        )
    
    def _ensure_picker_in_overlay(self, picker: ft.FilePicker) -> bool:
        """
        Ensure file picker is in page overlay.
        
        Args:
            picker: FilePicker instance
            
        Returns:
            True if picker is in overlay, False otherwise
        """
        if not self.page:
            return False
        
        if picker not in self.page.overlay:
            self.page.overlay.append(picker)
            self.page.update()
        
        return True
    
    def remove_picker(self, name: str):
        """
        Remove a registered picker.
        
        Args:
            name: Name of the picker to remove
        """
        picker = self.pickers.pop(name, None)
        if picker and self.page and picker in self.page.overlay:
            self.page.overlay.remove(picker)
            self.page.update()
        
        self.callbacks.pop(name, None)
    
    def clear(self):
        """Clear all registered pickers."""
        if self.page:
            for picker in self.pickers.values():
                if picker in self.page.overlay:
                    self.page.overlay.remove(picker)
            self.page.update()
        
        self.pickers.clear()
        self.callbacks.clear()

