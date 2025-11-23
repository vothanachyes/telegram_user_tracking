"""
User multi-select component that opens a dialog for user selection.
"""

import flet as ft
import logging
from typing import Set, Optional, Callable
from admin.ui.dialogs.user_filter_dialog import UserFilterDialog

logger = logging.getLogger(__name__)


class UserMultiSelect(ft.Container):
    """Button-based user multi-select component that opens a dialog."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    CARD_BG = "#252525"
    BORDER_COLOR = "#333333"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    
    def __init__(
        self,
        label: str = "Users",
        width: int = 280,
        on_selection_changed: Optional[Callable[[Set[str]], None]] = None,
    ):
        """
        Initialize user multi-select component.
        
        Args:
            label: Label for the component
            width: Width of the component
            on_selection_changed: Callback when selection changes (receives set of user IDs)
        """
        self.on_selection_changed = on_selection_changed
        self.selected_user_ids: Set[str] = set()
        self.page: Optional[ft.Page] = None
        
        # Button to open user selection dialog
        self.select_button = ft.OutlinedButton(
            text="Select Users",
            icon=ft.Icons.PEOPLE,
            tooltip="Click to select users",
            on_click=self._on_select_click,
            width=width,
        )
        
        # Selected users display
        self.selected_display = ft.Text(
            "All users",
            color=self.TEXT_SECONDARY,
            size=12,
        )
        
        # Main container
        self.filter_container = ft.Column(
            controls=[
                ft.Text(label, size=12, color=self.TEXT_SECONDARY),
                self.select_button,
                self.selected_display,
            ],
            spacing=5,
        )
        
        super().__init__(
            content=self.filter_container,
            width=width,
        )
    
    def _on_select_click(self, e: ft.ControlEvent):
        """Handle select button click - open dialog."""
        if not self.page:
            logger.warning("Page reference not set, cannot open dialog")
            return
        
        dialog = UserFilterDialog(
            selected_user_ids=self.selected_user_ids,
            on_confirm=self._on_dialog_confirm,
        )
        dialog.page = self.page
        
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening user filter dialog: {ex}")
            # Fallback
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_dialog_confirm(self, selected_ids: Set[str]):
        """Handle dialog confirmation."""
        self.selected_user_ids = selected_ids
        self._update_selected_display()
        
        if self.on_selection_changed:
            self.on_selection_changed(self.selected_user_ids.copy())
    
    def _update_selected_display(self):
        """Update the selected users display."""
        count = len(self.selected_user_ids)
        if count == 0:
            self.selected_display.value = "All users"
        elif count == 1:
            self.selected_display.value = "1 user selected"
        else:
            self.selected_display.value = f"{count} users selected"
        
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def get_selected_user_ids(self) -> Set[str]:
        """Get currently selected user IDs."""
        return self.selected_user_ids.copy()
    
    def clear_selection(self):
        """Clear all selections."""
        self.selected_user_ids.clear()
        self._update_selected_display()
        if self.on_selection_changed:
            self.on_selection_changed(set())

