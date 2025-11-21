"""
Event handlers for Telegram page.
"""

import flet as ft
from typing import Optional
from datetime import datetime
from ui.theme import theme_manager
from ui.dialogs import MessageDetailDialog, UserDetailDialog


class TelegramHandlers:
    """Event handlers for telegram page."""
    
    def __init__(
        self,
        page: Optional[ft.Page],
        view_model,
        export_service,
        messages_tab,
        users_tab,
        excel_picker_messages,
        pdf_picker_messages,
        excel_picker_users,
        pdf_picker_users
    ):
        self.page = page
        self.view_model = view_model
        self.export_service = export_service
        self.messages_tab = messages_tab
        self.users_tab = users_tab
        self.excel_picker_messages = excel_picker_messages
        self.pdf_picker_messages = pdf_picker_messages
        self.excel_picker_users = excel_picker_users
        self.pdf_picker_users = pdf_picker_users
    
    def handle_message_click(self, row_index: int):
        """Handle message row click."""
        messages = self.messages_tab.get_messages()
        
        if row_index < len(messages):
            message = messages[row_index]
            
            dialog = MessageDetailDialog(
                db_manager=self.view_model.db_manager,
                message=message,
                on_delete=self.handle_refresh_messages,
                on_update=self.handle_refresh_messages
            )
            
            if self.page:
                dialog.page = self.page
                self.page.open(dialog)
    
    def handle_user_click(self, row_index: int):
        """Handle user row click."""
        users = self.users_tab.get_users()
        
        if row_index < len(users):
            user = users[row_index]
            
            dialog = UserDetailDialog(
                db_manager=self.view_model.db_manager,
                user=user,
                on_delete=self.handle_refresh_users,
                on_update=self.handle_refresh_users
            )
            
            if self.page:
                dialog.page = self.page
                self.page.open(dialog)
    
    def handle_refresh_messages(self):
        """Handle messages refresh."""
        self.messages_tab.refresh_messages()
    
    def handle_refresh_users(self):
        """Handle users refresh."""
        self.users_tab.refresh_users()
    
    def handle_export_messages_excel(self):
        """Handle messages Excel export."""
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.page:
            logger.error("Page not set in TelegramHandlers")
            return
        
        messages = self.view_model.get_messages(
            group_id=self.messages_tab.get_selected_group(),
            start_date=self.messages_tab.filters_bar.get_start_date(),
            end_date=self.messages_tab.filters_bar.get_end_date()
        )
        if not messages:
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("no_data"),
                bgcolor=ft.Colors.ORANGE
            )
            return
        
        try:
            if not hasattr(self.page, 'overlay') or self.page.overlay is None:
                self.page.overlay = []
            if self.excel_picker_messages not in self.page.overlay:
                self.page.overlay.append(self.excel_picker_messages)
            
            # Set page reference on picker
            self.excel_picker_messages.page = self.page
            
            # Verify picker is in overlay
            if self.excel_picker_messages not in self.page.overlay:
                logger.warning("File picker not in overlay, adding it")
                self.page.overlay.append(self.excel_picker_messages)
            
            self.page.update()
            
            # Small delay on macOS to ensure picker is ready (Flet 0.28.3 macOS bug workaround)
            import time
            time.sleep(0.15)
            
            default_name = f"messages_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            logger.info(f"Opening Excel export dialog for messages (picker in overlay: {self.excel_picker_messages in self.page.overlay})")
            
            # File pickers use save_file() directly (not page.open() like dialogs)
            # On macOS with Flet 0.28.3, there's a known bug - try calling save_file
            try:
                self.excel_picker_messages.save_file(
                    dialog_title=theme_manager.t("export_to_excel"),
                    file_name=default_name,
                    file_type=ft.FilePickerFileType.CUSTOM,
                    allowed_extensions=["xlsx"]
                )
                logger.info("save_file() called successfully")
            except AttributeError as attr_err:
                logger.error(f"FilePicker.save_file() failed: {attr_err}")
                raise
        except Exception as ex:
            logger.error(f"Error opening Excel export dialog: {ex}", exc_info=True)
            theme_manager.show_snackbar(
                self.page,
                f"Error opening file picker: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def handle_export_messages_pdf(self):
        """Handle messages PDF export."""
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.page:
            logger.error("Page not set in TelegramHandlers")
            return
        
        messages = self.view_model.get_messages(
            group_id=self.messages_tab.get_selected_group(),
            start_date=self.messages_tab.filters_bar.get_start_date(),
            end_date=self.messages_tab.filters_bar.get_end_date()
        )
        if not messages:
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("no_data"),
                bgcolor=ft.Colors.ORANGE
            )
            return
        
        try:
            if not hasattr(self.page, 'overlay') or self.page.overlay is None:
                self.page.overlay = []
            if self.pdf_picker_messages not in self.page.overlay:
                self.page.overlay.append(self.pdf_picker_messages)
            
            # Set page reference on picker
            self.pdf_picker_messages.page = self.page
            self.page.update()
            
            # Small delay on macOS to ensure picker is ready
            import time
            time.sleep(0.1)
            
            default_name = f"messages_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            logger.info(f"Opening PDF export dialog for messages")
            
            # File pickers use save_file() directly (not page.open() like dialogs)
            # On macOS, ensure picker is in overlay and page is updated before calling save_file
            self.pdf_picker_messages.save_file(
                dialog_title=theme_manager.t("export_to_pdf"),
                file_name=default_name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["pdf"]
            )
        except Exception as ex:
            logger.error(f"Error opening PDF export dialog: {ex}", exc_info=True)
            theme_manager.show_snackbar(
                self.page,
                f"Error opening file picker: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def handle_export_users_excel(self):
        """Handle users Excel export."""
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.page:
            logger.error("Page not set in TelegramHandlers")
            return
        
        users = self.view_model.get_all_users()
        if not users:
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("no_data"),
                bgcolor=ft.Colors.ORANGE
            )
            return
        
        try:
            if not hasattr(self.page, 'overlay') or self.page.overlay is None:
                self.page.overlay = []
            if self.excel_picker_users not in self.page.overlay:
                self.page.overlay.append(self.excel_picker_users)
            
            # Set page reference on picker
            self.excel_picker_users.page = self.page
            self.page.update()
            
            # Small delay on macOS to ensure picker is ready
            import time
            time.sleep(0.1)
            
            default_name = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            logger.info(f"Opening Excel export dialog for users")
            
            # File pickers use save_file() directly (not page.open() like dialogs)
            # On macOS, ensure picker is in overlay and page is updated before calling save_file
            self.excel_picker_users.save_file(
                dialog_title=theme_manager.t("export_to_excel"),
                file_name=default_name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["xlsx"]
            )
        except Exception as ex:
            logger.error(f"Error opening Excel export dialog: {ex}", exc_info=True)
            theme_manager.show_snackbar(
                self.page,
                f"Error opening file picker: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def handle_export_users_pdf(self):
        """Handle users PDF export."""
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.page:
            logger.error("Page not set in TelegramHandlers")
            return
        
        users = self.view_model.get_all_users()
        if not users:
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("no_data"),
                bgcolor=ft.Colors.ORANGE
            )
            return
        
        try:
            if not hasattr(self.page, 'overlay') or self.page.overlay is None:
                self.page.overlay = []
            if self.pdf_picker_users not in self.page.overlay:
                self.page.overlay.append(self.pdf_picker_users)
            
            # Set page reference on picker
            self.pdf_picker_users.page = self.page
            self.page.update()
            
            # Small delay on macOS to ensure picker is ready
            import time
            time.sleep(0.1)
            
            default_name = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            logger.info(f"Opening PDF export dialog for users")
            
            # File pickers use save_file() directly (not page.open() like dialogs)
            # On macOS, ensure picker is in overlay and page is updated before calling save_file
            self.pdf_picker_users.save_file(
                dialog_title=theme_manager.t("export_to_pdf"),
                file_name=default_name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["pdf"]
            )
        except Exception as ex:
            logger.error(f"Error opening PDF export dialog: {ex}", exc_info=True)
            theme_manager.show_snackbar(
                self.page,
                f"Error opening file picker: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def handle_messages_excel_picked(self, e: ft.FilePickerResultEvent):
        """Handle messages Excel file picker result."""
        if not self.page or not e.path:
            return
        
        try:
            messages = self.view_model.get_messages(
                group_id=self.messages_tab.get_selected_group(),
                start_date=self.messages_tab.filters_bar.get_start_date(),
                end_date=self.messages_tab.filters_bar.get_end_date()
            )
            
            if self.export_service.export_messages_to_excel(messages, e.path):
                theme_manager.show_snackbar(
                    self.page,
                    f"{theme_manager.t('export_success')}: {e.path}",
                    bgcolor=ft.Colors.GREEN
                )
            else:
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("export_error"),
                    bgcolor=ft.Colors.RED
                )
        except Exception as ex:
            theme_manager.show_snackbar(
                self.page,
                f"{theme_manager.t('export_error')}: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def handle_messages_pdf_picked(self, e: ft.FilePickerResultEvent):
        """Handle messages PDF file picker result."""
        if not self.page or not e.path:
            return
        
        try:
            messages = self.view_model.get_messages(
                group_id=self.messages_tab.get_selected_group(),
                start_date=self.messages_tab.filters_bar.get_start_date(),
                end_date=self.messages_tab.filters_bar.get_end_date()
            )
            
            if self.export_service.export_messages_to_pdf(messages, e.path):
                theme_manager.show_snackbar(
                    self.page,
                    f"{theme_manager.t('export_success')}: {e.path}",
                    bgcolor=ft.Colors.GREEN
                )
            else:
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("export_error"),
                    bgcolor=ft.Colors.RED
                )
        except Exception as ex:
            theme_manager.show_snackbar(
                self.page,
                f"{theme_manager.t('export_error')}: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def handle_users_excel_picked(self, e: ft.FilePickerResultEvent):
        """Handle users Excel file picker result."""
        if not self.page or not e.path:
            return
        
        try:
            users = self.view_model.get_all_users()
            
            if self.export_service.export_users_to_excel(users, e.path):
                theme_manager.show_snackbar(
                    self.page,
                    f"{theme_manager.t('export_success')}: {e.path}",
                    bgcolor=ft.Colors.GREEN
                )
            else:
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("export_error"),
                    bgcolor=ft.Colors.RED
                )
        except Exception as ex:
            theme_manager.show_snackbar(
                self.page,
                f"{theme_manager.t('export_error')}: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def handle_users_pdf_picked(self, e: ft.FilePickerResultEvent):
        """Handle users PDF file picker result."""
        if not self.page or not e.path:
            return
        
        try:
            users = self.view_model.get_all_users()
            
            if self.export_service.export_users_to_pdf(users, e.path):
                theme_manager.show_snackbar(
                    self.page,
                    f"{theme_manager.t('export_success')}: {e.path}",
                    bgcolor=ft.Colors.GREEN
                )
            else:
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("export_error"),
                    bgcolor=ft.Colors.RED
                )
        except Exception as ex:
            theme_manager.show_snackbar(
                self.page,
                f"{theme_manager.t('export_error')}: {str(ex)}",
                bgcolor=ft.Colors.RED
            )

