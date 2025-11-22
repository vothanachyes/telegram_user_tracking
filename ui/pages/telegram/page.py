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
        
        # Create tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text=theme_manager.t("messages"),
                    icon=ft.Icons.MESSAGE,
                    content=self.messages_tab.build()
                ),
                ft.Tab(
                    text=theme_manager.t("users"),
                    icon=ft.Icons.PEOPLE,
                    content=self.users_tab.build()
                ),
            ],
            expand=True
        )
        
        super().__init__(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("telegram"),
                    size=theme_manager.font_size_page_title,
                    weight=ft.FontWeight.BOLD
                ),
                self.tabs,
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

