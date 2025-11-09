"""
User Dashboard page - main orchestration file.
"""

import flet as ft
from typing import Optional
from database.db_manager import DatabaseManager
from ui.theme import theme_manager
from ui.pages.user_dashboard.view_model import UserDashboardViewModel
from ui.pages.user_dashboard.components import (
    UserSearchComponent,
    UserStatsComponent,
    UserMessagesComponent
)
from ui.pages.user_dashboard.handlers import UserDashboardHandlers
from services.export import ExportService


class UserDashboardPage(ft.Container):
    """User dashboard page for viewing user details and activity."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.page: Optional[ft.Page] = None
        
        # Initialize view model
        self.view_model = UserDashboardViewModel(db_manager)
        
        # Initialize export service
        self.export_service = ExportService(db_manager)
        
        # File pickers for export
        self.user_excel_picker = ft.FilePicker(
            on_result=self._on_user_excel_picked
        )
        self.user_pdf_picker = ft.FilePicker(
            on_result=self._on_user_pdf_picked
        )
        
        # Initialize components
        self.user_search_component = UserSearchComponent(
            on_user_selected=self._on_user_selected,
            on_search_change=self._on_search_change
        )
        
        self.user_stats_component = UserStatsComponent()
        
        self.user_messages_component = UserMessagesComponent(
            on_message_click=self._on_message_click,
            on_refresh=self._on_refresh_messages
        )
        
        # Telegram button
        self.telegram_button = ft.IconButton(
            icon=ft.Icons.TELEGRAM,
            tooltip=theme_manager.t("open_in_telegram"),
            disabled=True,
            on_click=self._open_telegram_user
        )
        
        # User detail section (created before handlers, will be updated after)
        self.user_detail_section = self._create_user_detail_section()
        
        # Initialize handlers
        self.handlers = UserDashboardHandlers(
            page=None,  # Will be set in set_page
            view_model=self.view_model,
            export_service=self.export_service,
            user_messages_component=self.user_messages_component,
            user_stats_component=self.user_stats_component,
            user_search_component=self.user_search_component,
            user_detail_section=self.user_detail_section,
            telegram_button=self.telegram_button,
            excel_picker=self.user_excel_picker,
            pdf_picker=self.user_pdf_picker
        )
        
        # Update user detail section button callback now that handlers exist
        self._update_user_detail_button()
        
        # Setup groups for messages component
        groups = self.view_model.get_all_groups()
        default_group_id = groups[0].group_id if groups else None
        
        # Build UI
        super().__init__(
            content=ft.Column([
                # Top Header
                self._create_header(),
                # User detail section
                self.user_detail_section,
                # Tabs
                self._create_tabs(groups, default_group_id),
            ], spacing=theme_manager.spacing_md, expand=True),
            padding=theme_manager.padding_lg,
            expand=True
        )
    
    def set_page(self, page: ft.Page):
        """Set page reference and add file pickers to overlay."""
        self.page = page
        self.user_search_component.page = page
        self.handlers.page = page
        
        if not hasattr(page, 'overlay') or page.overlay is None:
            page.overlay = []
        
        pickers = [self.user_excel_picker, self.user_pdf_picker]
        for picker in pickers:
            if picker not in page.overlay:
                page.overlay.append(picker)
        page.update()
    
    def _create_header(self) -> ft.Container:
        """Create top header with search and actions."""
        # Export menu
        export_menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            tooltip=theme_manager.t("export"),
            items=[
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_excel"),
                    icon=ft.Icons.TABLE_CHART,
                    on_click=self.handlers.handle_export_excel
                ),
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_pdf"),
                    icon=ft.Icons.PICTURE_AS_PDF,
                    on_click=self.handlers.handle_export_pdf
                ),
            ]
        )
        
        return ft.Container(
            content=ft.Row([
                # Left: Search field with dropdown
                self.user_search_component.build(),
                # Right: Telegram button and Export menu
                ft.Row([
                    self.telegram_button,
                    export_menu,
                ], spacing=10),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=10
        )
    
    def _create_user_detail_section(self) -> ft.Container:
        """Create user detail section."""
        # Create button with wrapper method that will call handlers when available
        self._detail_button = ft.IconButton(
            icon=ft.Icons.EDIT,
            tooltip=theme_manager.t("view_user_details"),
            disabled=True,
            on_click=self._handle_user_detail_click
        )
        
        return theme_manager.create_card(
            content=ft.Row([
                # Profile photo and info
                ft.Row([
                    ft.Icon(
                        ft.Icons.ACCOUNT_CIRCLE,
                        size=80,
                        color=theme_manager.primary_color
                    ),
                    ft.Column([
                        ft.Text(
                            theme_manager.t("select_user_to_view_details"),
                            size=18,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(
                            theme_manager.t("search_user_to_get_started"),
                            size=14,
                            color=theme_manager.text_secondary_color
                        ),
                    ], spacing=5)
                ], spacing=20, alignment=ft.MainAxisAlignment.START),
                # Right: View details button
                ft.Container(
                    content=self._detail_button,
                    alignment=ft.alignment.center_right
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            visible=False
        )
    
    def _handle_user_detail_click(self, e):
        """Wrapper method to handle user detail button click."""
        if hasattr(self, 'handlers') and self.handlers:
            self.handlers.handle_open_user_detail_dialog(e)
    
    def _update_user_detail_button(self):
        """Update user detail button callback after handlers are initialized."""
        # No-op: button already uses wrapper method
        pass
    
    def _create_tabs(self, groups, default_group_id) -> ft.Tabs:
        """Create tabs for General and Messages."""
        return ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text=theme_manager.t("general"),
                    icon=ft.Icons.DASHBOARD,
                    content=self.user_stats_component.build()
                ),
                ft.Tab(
                    text=theme_manager.t("messages"),
                    icon=ft.Icons.MESSAGE,
                    content=self.user_messages_component.build(groups, default_group_id)
                ),
            ],
            expand=True
        )
    
    def _on_user_selected(self, user):
        """Handle user selection."""
        self.handlers.handle_user_selected(user)
    
    def _on_search_change(self, query: str):
        """Handle search change."""
        self.handlers.handle_search_change(query)
    
    def _on_message_click(self, row_index: int):
        """Handle message click."""
        self.handlers.handle_message_click(row_index)
    
    def _on_refresh_messages(self):
        """Handle messages refresh."""
        self.handlers.handle_refresh_messages()
    
    def _open_telegram_user(self, e):
        """Open Telegram user link."""
        self.handlers.handle_open_telegram_user(e)
    
    def _on_user_excel_picked(self, e: ft.FilePickerResultEvent):
        """Handle Excel file picker result."""
        self.handlers.handle_excel_picked(e)
    
    def _on_user_pdf_picked(self, e: ft.FilePickerResultEvent):
        """Handle PDF file picker result."""
        self.handlers.handle_pdf_picked(e)

