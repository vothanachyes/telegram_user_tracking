"""
Group multi-select component for dashboard.
"""

import flet as ft
from typing import List, Callable, Optional
from ui.theme import theme_manager


class GroupSelectorComponent:
    """Component for multi-select group selection."""
    
    def __init__(
        self,
        groups: List,
        selected_group_ids: List[int],
        selected_group_names: List[str],
        on_selection_changed: Callable[[List[int], List[str]], None]
    ):
        self.groups = groups
        self.selected_group_ids = selected_group_ids
        self.selected_group_names = selected_group_names
        self.on_selection_changed = on_selection_changed
        self.page: Optional[ft.Page] = None
        self.group_checkboxes = {}
        self.all_groups = groups
        
        # Create button
        self.button = self._create_button()
    
    def _create_button(self) -> ft.ElevatedButton:
        """Create the group selector button."""
        return ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.GROUP, size=20),
                ft.Text(
                    self._get_selected_groups_text(),
                    size=theme_manager.font_size_body
                ),
                ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=20)
            ], spacing=8, tight=True),
            on_click=self._open_dialog,
            style=ft.ButtonStyle(
                bgcolor=theme_manager.surface_color,
                color=theme_manager.text_color,
                side=ft.BorderSide(1, theme_manager.border_color),
            ),
            height=40
        )
    
    def _get_selected_groups_text(self) -> str:
        """Get text representation of selected groups."""
        if not self.selected_group_ids:
            return theme_manager.t("select_groups") or "Select Groups"
        
        if len(self.selected_group_ids) == 1:
            return self.selected_group_names[0] if self.selected_group_names else str(self.selected_group_ids[0])
        
        return f"{len(self.selected_group_ids)} {theme_manager.t('groups_selected') or 'groups selected'}"
    
    def _open_dialog(self, e):
        """Open dialog for group selection."""
        if not self.page:
            return
        
        # Create checkboxes for each group
        checkbox_list = []
        self.group_checkboxes = {}
        
        for group in self.all_groups:
            checkbox = ft.Checkbox(
                label=f"{group.group_name} ({group.group_id})",
                value=group.group_id in self.selected_group_ids,
                on_change=lambda e, gid=group.group_id: self._on_checkbox_changed(gid, e)
            )
            self.group_checkboxes[group.group_id] = checkbox
            checkbox_list.append(checkbox)
        
        # Create dialog
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(theme_manager.t("select_groups") or "Select Groups"),
            content=ft.Container(
                content=ft.Column(
                    checkbox_list,
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                    height=min(400, len(self.all_groups) * 45),
                    width=350
                ),
                padding=10
            ),
            actions=[
                ft.TextButton(
                    theme_manager.t("select_all") or "Select All",
                    on_click=lambda _: self._select_all(dialog)
                ),
                ft.TextButton(
                    theme_manager.t("deselect_all") or "Deselect All",
                    on_click=lambda _: self._deselect_all(dialog)
                ),
                ft.TextButton(
                    theme_manager.t("cancel") or "Cancel",
                    on_click=lambda _: self._close_dialog(dialog)
                ),
                ft.ElevatedButton(
                    theme_manager.t("apply") or "Apply",
                    on_click=lambda _: self._apply_selection(dialog),
                    bgcolor=theme_manager.primary_color,
                    color=ft.Colors.WHITE
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        dialog.page = self.page
        self.page.open(dialog)
    
    def _on_checkbox_changed(self, group_id: int, e):
        """Handle checkbox change in dialog."""
        pass
    
    def _select_all(self, dialog):
        """Select all groups in dialog."""
        for checkbox in self.group_checkboxes.values():
            checkbox.value = True
        if self.page:
            self.page.update()
    
    def _deselect_all(self, dialog):
        """Deselect all groups in dialog."""
        for checkbox in self.group_checkboxes.values():
            checkbox.value = False
        if self.page:
            self.page.update()
    
    def _apply_selection(self, dialog):
        """Apply group selection and notify parent."""
        new_selected_ids = []
        new_selected_names = []
        
        for group_id, checkbox in self.group_checkboxes.items():
            if checkbox.value:
                new_selected_ids.append(group_id)
                for group in self.all_groups:
                    if group.group_id == group_id:
                        new_selected_names.append(group.group_name)
                        break
        
        self.selected_group_ids = new_selected_ids
        self.selected_group_names = new_selected_names
        
        # Update button text
        self.button.content.controls[1].value = self._get_selected_groups_text()
        
        # Close dialog
        self._close_dialog(dialog)
        
        # Notify parent
        self.on_selection_changed(new_selected_ids, new_selected_names)
    
    def _close_dialog(self, dialog):
        """Close the group selection dialog."""
        if self.page:
            self.page.close(dialog)
    
    def update_selection(self, group_ids: List[int], group_names: List[str]):
        """Update selected groups externally."""
        self.selected_group_ids = group_ids
        self.selected_group_names = group_names
        self.button.content.controls[1].value = self._get_selected_groups_text()
    
    def build(self) -> ft.ElevatedButton:
        """Build and return the component."""
        if not self.groups:
            return ft.Container(
                content=ft.Text(theme_manager.t("no_groups") or "No groups available"),
                padding=10
            )
        return self.button
    
    def set_page(self, page: ft.Page):
        """Set page reference."""
        self.page = page

