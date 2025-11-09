"""
Group selector component for selecting Telegram groups.
"""

import flet as ft
import logging
from typing import Optional, Callable, List
from datetime import datetime
from database.models import TelegramGroup
from ui.theme import theme_manager
from utils.group_parser import parse_group_input

logger = logging.getLogger(__name__)


class GroupSelector:
    """Component for selecting Telegram groups with manual entry option."""
    
    def __init__(
        self,
        on_group_selected: Optional[Callable[[int], None]] = None,
        on_manual_entry: Optional[Callable[[int], None]] = None,
        width: Optional[int] = None
    ):
        """
        Initialize group selector.
        
        Args:
            on_group_selected: Callback when a group is selected from dropdown
            on_manual_entry: Callback when group ID is manually entered
            width: Optional width for the components
        """
        self.on_group_selected = on_group_selected
        self.on_manual_entry = on_manual_entry
        self.page: Optional[ft.Page] = None
        self.selected_group_id: Optional[int] = None
        self.groups: List[TelegramGroup] = []
        
        # Group dropdown (create manually to support Option objects with keys)
        self.group_dropdown = ft.Dropdown(
            label=theme_manager.t("select_group"),
            options=[],
            value=None,
            on_change=self._on_group_change,
            border_radius=theme_manager.corner_radius,
            border_color=theme_manager.border_color,
            focused_border_color=theme_manager.primary_color,
            expand=True if width is None else False,
            width=width
        )
        
        # Manual entry field
        # Use TEXT keyboard type to allow negative numbers (NUMBER doesn't support minus sign)
        self.manual_entry_field = theme_manager.create_text_field(
            label=theme_manager.t("enter_group_id_manually"),
            hint_text="e.g., -1001234567890 or 1001234567890",
            keyboard_type=ft.KeyboardType.TEXT,  # Changed from NUMBER to allow negative numbers
            on_submit=self._on_manual_entry_submit,
            on_change=self._on_manual_entry_change,
            expand=True if width is None else False,
            width=width
        )
        
        # Group info display
        self.group_info_text = ft.Text(
            "",
            size=theme_manager.font_size_small,
            color=theme_manager.text_secondary_color,
            visible=False
        )
    
    def build(self) -> ft.Column:
        """Build the group selector component."""
        return ft.Column([
            self.group_dropdown,
            ft.Text(
                theme_manager.t("enter_group_id_manually"),
                size=theme_manager.font_size_small,
                color=theme_manager.text_secondary_color,
                italic=True
            ),
            self.manual_entry_field,
            self.group_info_text,
        ], spacing=theme_manager.spacing_sm, tight=True)
    
    def set_page(self, page: ft.Page):
        """Set the Flet page instance for updates."""
        self.page = page
    
    def update_groups(self, groups: List[TelegramGroup]):
        """
        Update dropdown with saved groups.
        
        Args:
            groups: List of TelegramGroup objects
        """
        self.groups = groups
        
        options = []
        for group in groups:
            # Format: "Group Name (-1001234567890) - Last fetched: 2024-01-15"
            last_fetch = ""
            if group.last_fetch_date:
                last_fetch = group.last_fetch_date.strftime("%Y-%m-%d")
            
            if last_fetch:
                option_text = f"{group.group_name} ({group.group_id}) - Last fetched: {last_fetch}"
            else:
                option_text = f"{group.group_name} ({group.group_id})"
            
            options.append(ft.dropdown.Option(
                key=str(group.group_id),
                text=option_text
            ))
        
        self.group_dropdown.options = options
        
        if self.page:
            try:
                self.group_dropdown.update()
            except AssertionError:
                # Control not added to page yet - will update when added
                pass
    
    def set_selected_group(self, group_id: int, trigger_callback: bool = False):
        """
        Set the selected group by group ID.
        
        Args:
            group_id: The group ID to select
            trigger_callback: If True, trigger the on_group_selected callback
        """
        self.selected_group_id = group_id
        self.group_dropdown.value = str(group_id)
        self.manual_entry_field.value = str(group_id)
        
        # Update group info
        self._update_group_info(group_id)
        
        # Trigger callback if requested (for auto-selection)
        if trigger_callback and self.on_group_selected:
            self.on_group_selected(group_id)
        
        if self.page:
            try:
                self.group_dropdown.update()
                self.manual_entry_field.update()
                self.group_info_text.update()
            except AssertionError:
                # Control not added to page yet - will update when added
                pass
    
    def get_selected_group_id(self) -> Optional[int]:
        """Get the currently selected group ID."""
        return self.selected_group_id
    
    def set_group_info(self, group_name: str, last_fetch_date: Optional[datetime] = None):
        """
        Set group info to display.
        
        Args:
            group_name: Name of the group
            last_fetch_date: Optional last fetch date
        """
        if last_fetch_date:
            date_str = last_fetch_date.strftime("%Y-%m-%d")
            self.group_info_text.value = theme_manager.t("group_info_loaded").format(
                name=group_name,
                date=date_str
            )
        else:
            self.group_info_text.value = f"Group: {group_name}"
        
        self.group_info_text.visible = True
        if self.page:
            try:
                self.group_info_text.update()
            except AssertionError:
                # Control not added to page yet - will update when added
                pass
    
    def clear_group_info(self):
        """Clear group info display."""
        self.group_info_text.value = ""
        self.group_info_text.visible = False
        if self.page:
            try:
                self.group_info_text.update()
            except AssertionError:
                # Control not added to page yet - will update when added
                pass
    
    def _update_group_info(self, group_id: int):
        """Update group info from saved groups."""
        for group in self.groups:
            if group.group_id == group_id:
                self.set_group_info(group.group_name, group.last_fetch_date)
                return
        self.clear_group_info()
    
    def refresh_selected_group_info(self, groups: List[TelegramGroup]):
        """
        Refresh the selected group's info after groups list is updated.
        
        Args:
            groups: Updated list of TelegramGroup objects
        """
        # Update the groups list
        self.groups = groups
        
        # If a group is selected, refresh its info
        if self.selected_group_id:
            for group in groups:
                if group.group_id == self.selected_group_id:
                    self.set_group_info(group.group_name, group.last_fetch_date)
                    # Also update the dropdown option text
                    self.update_groups(groups)
                    # Restore the selected value
                    self.group_dropdown.value = str(self.selected_group_id)
                    if self.page:
                        try:
                            self.group_dropdown.update()
                        except AssertionError:
                            # Control not added to page yet - will update when added
                            pass
                    return
    
    def _on_group_change(self, e):
        """Handle group selection change from dropdown."""
        if not e.control.value:
            self.selected_group_id = None
            self.manual_entry_field.value = ""
            self.clear_group_info()
            return
        
        try:
            group_id = int(e.control.value)
            self.selected_group_id = group_id
            self.manual_entry_field.value = str(group_id)
            self._update_group_info(group_id)
            
            if self.on_group_selected:
                self.on_group_selected(group_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid group ID: {e.control.value}")
    
    def _on_manual_entry_change(self, e):
        """Handle manual entry field change."""
        # Clear dropdown selection when manually entering
        if e.control.value and self.group_dropdown.value:
            self.group_dropdown.value = None
            self.selected_group_id = None
            self.clear_group_info()
            if self.page:
                try:
                    self.group_dropdown.update()
                except AssertionError:
                    # Control not added to page yet - will update when added
                    pass
    
    def _on_manual_entry_submit(self, e):
        """Handle manual entry field submit."""
        value = e.control.value.strip() if e.control.value else ""
        if not value:
            return
        
        try:
            # Use parser to support various formats (including "100..." conversion)
            group_id, username, invite_link, error = parse_group_input(value)
            
            if error:
                logger.error(f"Invalid group ID format: {value} - {error}")
                if self.page:
                    theme_manager.show_snackbar(
                        self.page,
                        theme_manager.t("invalid_group_id") + f": {error}",
                        bgcolor=ft.Colors.RED
                    )
                return
            
            # Prefer group_id, but also support invite_link (though manual entry typically expects ID)
            if group_id:
                self.selected_group_id = group_id
                self.manual_entry_field.value = str(group_id)  # Update field with parsed value
                self.clear_group_info()  # Clear info since it's a new group
                
                if self.on_manual_entry:
                    self.on_manual_entry(group_id)
            elif invite_link:
                # If user entered an invite link, show error (manual entry expects ID)
                if self.page:
                    theme_manager.show_snackbar(
                        self.page,
                        "Please enter a group ID, not an invite link. Use the Add Group dialog for invite links.",
                        bgcolor=ft.Colors.ORANGE
                    )
            else:
                logger.error(f"Could not parse group input: {value}")
                if self.page:
                    theme_manager.show_snackbar(
                        self.page,
                        theme_manager.t("invalid_group_id"),
                        bgcolor=ft.Colors.RED
                    )
        except Exception as ex:
            logger.error(f"Error parsing group ID: {ex}")
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("invalid_group_id"),
                    bgcolor=ft.Colors.RED
                )
    
    def disable(self):
        """Disable the group selector."""
        self.group_dropdown.disabled = True
        self.manual_entry_field.disabled = True
        if self.page:
            try:
                self.group_dropdown.update()
                self.manual_entry_field.update()
            except AssertionError:
                # Control not added to page yet - disabled state will be applied when added
                pass
    
    def enable(self):
        """Enable the group selector."""
        self.group_dropdown.disabled = False
        self.manual_entry_field.disabled = False
        if self.page:
            try:
                self.group_dropdown.update()
                self.manual_entry_field.update()
            except AssertionError:
                # Control not added to page yet - enabled state will be applied when added
                pass

