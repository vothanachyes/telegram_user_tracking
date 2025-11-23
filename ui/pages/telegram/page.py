"""
Telegram page - main orchestration file.
"""

import flet as ft
from typing import Optional
from database.db_manager import DatabaseManager
from ui.theme import theme_manager
from ui.pages.telegram.view_model import TelegramViewModel
from ui.pages.telegram.components import MessagesTabComponent, UsersTabComponent
from ui.pages.telegram.handlers import TelegramHandlers
from services.export import ExportService


class TelegramPage(ft.Container):
    """Telegram page with tabs for messages and users."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.page: Optional[ft.Page] = None
        
        # Initialize view model
        self.view_model = TelegramViewModel(db_manager)
        
        # Initialize export service
        self.export_service = ExportService(db_manager)
        
        # File pickers for export
        self.messages_excel_picker = ft.FilePicker(
            on_result=self._on_messages_excel_picked
        )
        self.messages_pdf_picker = ft.FilePicker(
            on_result=self._on_messages_pdf_picked
        )
        self.users_excel_picker = ft.FilePicker(
            on_result=self._on_users_excel_picked
        )
        self.users_pdf_picker = ft.FilePicker(
            on_result=self._on_users_pdf_picked
        )
        
        # Initialize components
        self.messages_tab = MessagesTabComponent(
            view_model=self.view_model,
            on_message_click=self._on_message_click,
            on_refresh=self._on_refresh_messages,
            on_export_excel=self._on_export_messages_excel,
            on_export_pdf=self._on_export_messages_pdf
        )
        
        self.users_tab = UsersTabComponent(
            view_model=self.view_model,
            on_user_click=self._on_user_click,
            on_refresh=self._on_refresh_users,
            on_export_excel=self._on_export_users_excel,
            on_export_pdf=self._on_export_users_pdf,
            on_import_users=self._on_import_users
        )
        
        # Initialize handlers
        self.handlers = TelegramHandlers(
            page=None,  # Will be set in set_page
            view_model=self.view_model,
            export_service=self.export_service,
            messages_tab=self.messages_tab,
            users_tab=self.users_tab,
            excel_picker_messages=self.messages_excel_picker,
            pdf_picker_messages=self.messages_pdf_picker,
            excel_picker_users=self.users_excel_picker,
            pdf_picker_users=self.users_pdf_picker
        )
        
        # Get groups for group dropdowns (after tabs are initialized to get their default groups)
        groups = self.view_model.get_all_groups()
        messages_default_group_id = self.messages_tab.filters_bar.get_selected_group()
        users_default_group_id = self.users_tab.filters_bar.get_selected_group()
        
        # Create group options (only group names, no IDs)
        group_options = [g.group_name for g in groups] if groups else []
        
        # Create mapping from group_name to group_id for easy lookup
        self.group_name_to_id_map = {g.group_name: g.group_id for g in groups}
        
        # Get default values for each tab (group names only)
        messages_default_value = None
        if messages_default_group_id and groups:
            default_group = next((g for g in groups if g.group_id == messages_default_group_id), None)
            messages_default_value = default_group.group_name if default_group else (group_options[0] if group_options else None)
        else:
            messages_default_value = group_options[0] if group_options else None
        
        users_default_value = None
        if users_default_group_id and groups:
            default_group = next((g for g in groups if g.group_id == users_default_group_id), None)
            users_default_value = default_group.group_name if default_group else (group_options[0] if group_options else None)
        else:
            users_default_value = group_options[0] if group_options else None
        
        # Messages tab group dropdown
        self.messages_group_dropdown = theme_manager.create_dropdown(
            label=theme_manager.t("select_group"),
            options=group_options if group_options else ["No groups"],
            value=messages_default_value,
            on_change=self._on_messages_group_change,
            width=250
        )
        
        # Users tab group dropdown
        self.users_group_dropdown = theme_manager.create_dropdown(
            label=theme_manager.t("select_group"),
            options=group_options if group_options else ["No groups"],
            value=users_default_value,
            on_change=self._on_users_group_change,
            width=250
        )
        
        # Note: Refresh and export buttons are now in tab content (above filters), not in tab bar
        
        # Store selected tab index
        self.selected_tab_index = 0
        
        # Create tab content containers
        self.messages_content = self.messages_tab.build()
        self.users_content = self.users_tab.build()
        
        # Create tab buttons with references for easy updating
        self.messages_tab_btn = ft.TextButton(
            text=theme_manager.t("messages"),
            icon=ft.Icons.MESSAGE,
            on_click=lambda e: self._switch_tab(0),
            style=ft.ButtonStyle(
                color=theme_manager.primary_color if self.selected_tab_index == 0 else None
            )
        )
        
        self.users_tab_btn = ft.TextButton(
            text=theme_manager.t("users"),
            icon=ft.Icons.PEOPLE,
            on_click=lambda e: self._switch_tab(1),
            style=ft.ButtonStyle(
                color=theme_manager.primary_color if self.selected_tab_index == 1 else None
            )
        )
        
        # Create custom tab bar with buttons inline
        self.tab_content_container = ft.Container(
            content=self.messages_content,
            expand=True
        )
        
        # Store references to group dropdown containers for easy access
        self.messages_group_container = ft.Container(
            content=self.messages_group_dropdown,
            visible=self.selected_tab_index == 0
        )
        self.users_group_container = ft.Container(
            content=self.users_group_dropdown,
            visible=self.selected_tab_index == 1
        )
        
        super().__init__(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("telegram"),
                    size=theme_manager.font_size_page_title,
                    weight=ft.FontWeight.BOLD
                ),
                # Custom tab bar row with group selection
                ft.Container(
                    content=ft.Row([
                        # Tab buttons
                        ft.Row([
                            self.messages_tab_btn,
                            self.users_tab_btn,
                        ], spacing=0),
                        ft.Container(expand=True),  # Spacer
                        # Group dropdown (context-aware - shows based on selected tab)
                        self.messages_group_container,
                        self.users_group_container,
                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    height=48,
                    border=ft.border.only(bottom=ft.BorderSide(1, theme_manager.border_color)),
                    padding=ft.padding.only(left=20, right=10),
                ),
                # Tab content container
                self.tab_content_container,
            ], spacing=0, expand=True),
            padding=theme_manager.padding_lg,
            expand=True
        )
    
    def set_page(self, page: ft.Page):
        """Set page reference and add file pickers to overlay."""
        self.page = page
        self.handlers.page = page
        # Update page reference in import users handler
        if hasattr(self.handlers, 'import_users_handler'):
            self.handlers.import_users_handler.page = page
        
        # Set page reference for filters bar components (for date pickers)
        if hasattr(self.messages_tab, 'filters_bar'):
            self.messages_tab.filters_bar.set_page(page)
        if hasattr(self.users_tab, 'filters_bar'):
            self.users_tab.filters_bar.set_page(page)
        
        if not hasattr(page, 'overlay') or page.overlay is None:
            page.overlay = []
        
        pickers = [
            self.messages_excel_picker,
            self.messages_pdf_picker,
            self.users_excel_picker,
            self.users_pdf_picker,
        ]
        for picker in pickers:
            if picker not in page.overlay:
                page.overlay.append(picker)
        page.update()
    
    def _on_message_click(self, row_index: int):
        """Handle message click."""
        self.handlers.handle_message_click(row_index)
    
    def _on_user_click(self, row_index: int):
        """Handle user click."""
        self.handlers.handle_user_click(row_index)
    
    def _on_refresh_messages(self):
        """Handle messages refresh."""
        self.handlers.handle_refresh_messages()
    
    def _on_refresh_users(self):
        """Handle users refresh."""
        self.handlers.handle_refresh_users()
    
    def _on_export_messages_excel(self):
        """Handle messages Excel export."""
        self.handlers.handle_export_messages_excel()
    
    def _on_export_messages_pdf(self):
        """Handle messages PDF export."""
        self.handlers.handle_export_messages_pdf()
    
    def _on_export_users_excel(self):
        """Handle users Excel export."""
        self.handlers.handle_export_users_excel()
    
    def _on_export_users_pdf(self):
        """Handle users PDF export."""
        self.handlers.handle_export_users_pdf()
    
    def _on_messages_excel_picked(self, e: ft.FilePickerResultEvent):
        """Handle messages Excel file picker result."""
        self.handlers.handle_messages_excel_picked(e)
    
    def _on_messages_pdf_picked(self, e: ft.FilePickerResultEvent):
        """Handle messages PDF file picker result."""
        self.handlers.handle_messages_pdf_picked(e)
    
    def _on_users_excel_picked(self, e: ft.FilePickerResultEvent):
        """Handle users Excel file picker result."""
        self.handlers.handle_users_excel_picked(e)
    
    def _on_users_pdf_picked(self, e: ft.FilePickerResultEvent):
        """Handle users PDF file picker result."""
        self.handlers.handle_users_pdf_picked(e)
    
    def _on_import_users(self):
        """Handle import users button click."""
        import logging
        logger = logging.getLogger(__name__)
        logger.debug("_on_import_users called in TelegramPage")
        self.handlers.handle_import_users()
    
    def _switch_tab(self, index: int):
        """Switch to a different tab."""
        self.selected_tab_index = index
        # Update tab content
        if index == 0:
            self.tab_content_container.content = self.messages_content
        else:
            self.tab_content_container.content = self.users_content
        
        # Update tab button styles
        self.messages_tab_btn.style = ft.ButtonStyle(
            color=theme_manager.primary_color if index == 0 else None
        )
        self.users_tab_btn.style = ft.ButtonStyle(
            color=theme_manager.primary_color if index == 1 else None
        )
        
        # Show/hide group dropdowns based on selected tab
        self.messages_group_container.visible = index == 0
        self.users_group_container.visible = index == 1
        
        if self.page:
            self.tab_content_container.update()
            self.messages_tab_btn.update()
            self.users_tab_btn.update()
            self.messages_group_container.update()
            self.users_group_container.update()
    
    # Note: Refresh and export handlers are now called directly from tab components
    
    def _on_messages_group_change(self, e):
        """Handle messages tab group selection change."""
        if e.control.value and e.control.value != "No groups":
            group_name = e.control.value
            group_id = self.group_name_to_id_map.get(group_name)
            # Update messages tab filters bar
            if hasattr(self.messages_tab, 'filters_bar') and group_id is not None:
                self.messages_tab.filters_bar.selected_group = group_id
                if self.messages_tab.filters_bar.on_group_change:
                    self.messages_tab.filters_bar.on_group_change(group_id)
        else:
            if hasattr(self.messages_tab, 'filters_bar'):
                self.messages_tab.filters_bar.selected_group = None
                if self.messages_tab.filters_bar.on_group_change:
                    self.messages_tab.filters_bar.on_group_change(None)
    
    def _on_users_group_change(self, e):
        """Handle users tab group selection change."""
        if e.control.value and e.control.value != "No groups":
            group_name = e.control.value
            group_id = self.group_name_to_id_map.get(group_name)
            # Update users tab filters bar
            if hasattr(self.users_tab, 'filters_bar') and group_id is not None:
                self.users_tab.filters_bar.selected_group = group_id
                if self.users_tab.filters_bar.on_group_change:
                    self.users_tab.filters_bar.on_group_change(group_id)
        else:
            if hasattr(self.users_tab, 'filters_bar'):
                self.users_tab.filters_bar.selected_group = None
                if self.users_tab.filters_bar.on_group_change:
                    self.users_tab.filters_bar.on_group_change(None)

