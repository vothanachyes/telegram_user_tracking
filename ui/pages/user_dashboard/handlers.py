"""
Event handlers for User Dashboard page.
"""

import flet as ft
import webbrowser
from typing import Optional
from datetime import datetime
from database.models import TelegramUser
from ui.theme import theme_manager
from ui.dialogs import UserDetailDialog
from utils.helpers import get_telegram_user_link


class UserDashboardHandlers:
    """Event handlers for user dashboard."""
    
    def __init__(
        self,
        page: Optional[ft.Page],
        view_model,
        export_service,
        user_messages_component,
        user_stats_component,
        user_search_component,
        user_detail_section,
        telegram_button,
        excel_picker,
        pdf_picker
    ):
        self.page = page
        self.view_model = view_model
        self.export_service = export_service
        self.user_messages_component = user_messages_component
        self.user_stats_component = user_stats_component
        self.user_search_component = user_search_component
        self.user_detail_section = user_detail_section
        self.telegram_button = telegram_button
        self.excel_picker = excel_picker
        self.pdf_picker = pdf_picker
        self.selected_user: Optional[TelegramUser] = None
    
    def handle_user_selected(self, user: TelegramUser):
        """Handle user selection."""
        self.selected_user = user
        
        # Update Telegram button
        user_link = get_telegram_user_link(user.username)
        self.telegram_button.disabled = not user_link
        if user_link:
            self.telegram_button.data = user_link
        
        # Update user detail section
        self._update_user_detail_section()
        
        # Update statistics
        self._update_statistics()
        
        # Refresh messages
        self._refresh_messages()
        
        if self.page:
            self.page.update()
    
    def handle_search_change(self, query: str):
        """Handle search field change."""
        users = self.view_model.search_users(query)
        self.user_search_component.update_dropdown(users)
    
    def handle_refresh_messages(self):
        """Handle messages refresh."""
        self._refresh_messages()
    
    def handle_message_click(self, row_index: int):
        """Handle message row click."""
        if not self.selected_user:
            return
        
        messages = self.view_model.get_user_messages(
            user_id=self.selected_user.user_id,
            group_id=self.user_messages_component.get_selected_group(),
            start_date=self.user_messages_component.get_start_date(),
            end_date=self.user_messages_component.get_end_date(),
            limit=100
        )
        
        if row_index < len(messages):
            from ui.dialogs.message_detail_dialog import MessageDetailDialog
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
    
    def handle_open_telegram_user(self, e):
        """Handle Telegram user link click."""
        if self.telegram_button.data:
            webbrowser.open(self.telegram_button.data)
    
    def handle_open_user_detail_dialog(self, e):
        """Open user detail dialog."""
        if not self.selected_user:
            return
        
        dialog = UserDetailDialog(
            db_manager=self.view_model.db_manager,
            user=self.selected_user,
            on_delete=self.handle_user_deleted,
            on_update=self.handle_user_updated
        )
        
        if self.page:
            dialog.page = self.page
            self.page.open(dialog)
    
    def handle_user_deleted(self):
        """Handle user deletion."""
        self.selected_user = None
        self.user_search_component.clear()
        self.telegram_button.disabled = True
        self._update_user_detail_section()  # Show empty state
        self.user_stats_component.show_empty_state()
        self.user_messages_component.clear_messages()
        if self.page:
            self.page.update()
    
    def handle_user_updated(self):
        """Handle user update."""
        if self.selected_user:
            updated_user = self.view_model.get_user_by_id(self.selected_user.user_id)
            if updated_user:
                self.selected_user = updated_user
                self._update_user_detail_section()
                if self.page:
                    self.page.update()
    
    def handle_export_excel(self, e=None):
        """Handle Excel export."""
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.page:
            logger.error("Page not set in UserDashboardHandlers")
            return
        
        if not self.selected_user:
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("select_user_first"),
                bgcolor=ft.Colors.ORANGE
            )
            return
        
        try:
            if not hasattr(self.page, 'overlay') or self.page.overlay is None:
                self.page.overlay = []
            if self.excel_picker not in self.page.overlay:
                self.page.overlay.append(self.excel_picker)
            
            # Set page reference on picker
            self.excel_picker.page = self.page
            self.page.update()
            
            # Small delay on macOS to ensure picker is ready
            import time
            time.sleep(0.1)
            
            default_name = f"user_{self.selected_user.user_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            logger.info(f"Opening Excel export dialog for user {self.selected_user.user_id}")
            
            # File pickers use save_file() directly (not page.open() like dialogs)
            # On macOS, ensure picker is in overlay and page is updated before calling save_file
            self.excel_picker.save_file(
                dialog_title=theme_manager.t("export_to_excel"),
                file_name=default_name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["xlsx"]
            )
        except Exception as ex:
            logger.error(f"Error opening Excel export dialog: {ex}", exc_info=True)
            theme_manager.show_snackbar(
                self.page,
                f"Error: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def handle_export_pdf(self, e=None):
        """Handle PDF export."""
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.page:
            logger.error("Page not set in UserDashboardHandlers")
            return
        
        if not self.selected_user:
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("select_user_first"),
                bgcolor=ft.Colors.ORANGE
            )
            return
        
        try:
            if not hasattr(self.page, 'overlay') or self.page.overlay is None:
                self.page.overlay = []
            if self.pdf_picker not in self.page.overlay:
                self.page.overlay.append(self.pdf_picker)
            
            # Set page reference on picker
            self.pdf_picker.page = self.page
            self.page.update()
            
            # Small delay on macOS to ensure picker is ready
            import time
            time.sleep(0.1)
            
            default_name = f"user_{self.selected_user.user_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            logger.info(f"Opening PDF export dialog for user {self.selected_user.user_id}")
            
            # File pickers use save_file() directly (not page.open() like dialogs)
            # On macOS, ensure picker is in overlay and page is updated before calling save_file
            self.pdf_picker.save_file(
                dialog_title=theme_manager.t("export_to_pdf"),
                file_name=default_name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["pdf"]
            )
        except Exception as ex:
            logger.error(f"Error opening PDF export dialog: {ex}", exc_info=True)
            theme_manager.show_snackbar(
                self.page,
                f"Error: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def handle_excel_picked(self, e: ft.FilePickerResultEvent):
        """Handle Excel file picker result."""
        if not self.page or not e.path or not self.selected_user:
            return
        
        try:
            messages = self.view_model.get_user_messages(
                user_id=self.selected_user.user_id,
                group_id=self.user_messages_component.get_selected_group(),
                start_date=self.user_messages_component.get_start_date(),
                end_date=self.user_messages_component.get_end_date()
            )
            
            stats = self.view_model.get_user_stats(
                user_id=self.selected_user.user_id,
                group_id=self.user_messages_component.get_selected_group(),
                start_date=self.user_messages_component.get_start_date(),
                end_date=self.user_messages_component.get_end_date()
            )
            
            if self.export_service.export_user_data_to_excel(
                user=self.selected_user,
                messages=messages,
                stats=stats,
                output_path=e.path
            ):
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
    
    def handle_pdf_picked(self, e: ft.FilePickerResultEvent):
        """Handle PDF file picker result."""
        if not self.page or not e.path or not self.selected_user:
            return
        
        try:
            messages = self.view_model.get_user_messages(
                user_id=self.selected_user.user_id,
                group_id=self.user_messages_component.get_selected_group(),
                start_date=self.user_messages_component.get_start_date(),
                end_date=self.user_messages_component.get_end_date()
            )
            
            stats = self.view_model.get_user_stats(
                user_id=self.selected_user.user_id,
                group_id=self.user_messages_component.get_selected_group(),
                start_date=self.user_messages_component.get_start_date(),
                end_date=self.user_messages_component.get_end_date()
            )
            
            if self.export_service.export_user_data_to_pdf(
                user=self.selected_user,
                messages=messages,
                stats=stats,
                output_path=e.path
            ):
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
    
    def _update_user_detail_section(self):
        """Update user detail section with selected user info."""
        if not self.selected_user:
            # Show empty state
            self.user_detail_section.content = ft.Container(
                content=ft.Column([
                    ft.Icon(
                        ft.Icons.PERSON_OUTLINE,
                        size=64,
                        color=theme_manager.text_secondary_color
                    ),
                    ft.Text(
                        theme_manager.t("select_user_to_view_details"),
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=theme_manager.text_secondary_color
                    ),
                    ft.Text(
                        theme_manager.t("search_user_to_get_started"),
                        size=14,
                        color=theme_manager.text_secondary_color
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                alignment=ft.alignment.center,
                padding=40
            )
            self.user_detail_section.visible = True
            return
        
        user = self.selected_user
        profile_photo = ft.Icon(
            ft.Icons.ACCOUNT_CIRCLE,
            size=80,
            color=theme_manager.primary_color
        ) if not user.profile_photo_path else ft.Image(
            src=user.profile_photo_path,
            width=80,
            height=80,
            fit=ft.ImageFit.COVER,
            border_radius=40
        )
        
        self.user_detail_section.content = ft.Row([
            ft.Row([
                profile_photo,
                ft.Column([
                    ft.Text(
                        user.full_name,
                        size=18,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        f"User ID: {user.user_id}",
                        size=14,
                        color=theme_manager.text_secondary_color
                    ),
                    ft.Text(
                        f"Profile Photo: {'Available' if user.profile_photo_path else 'Not Available'}",
                        size=12,
                        color=theme_manager.text_secondary_color
                    ),
                ], spacing=5)
            ], spacing=20, alignment=ft.MainAxisAlignment.START),
            ft.Container(
                content=ft.IconButton(
                    icon=ft.Icons.EDIT,
                    tooltip=theme_manager.t("view_user_details"),
                    on_click=self.handle_open_user_detail_dialog
                ),
                alignment=ft.alignment.center_right
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        self.user_detail_section.visible = True
    
    def _update_statistics(self):
        """Update statistics in General tab."""
        if not self.selected_user:
            self.user_stats_component.show_empty_state()
            return
        
        stats = self.view_model.get_user_stats(
            user_id=self.selected_user.user_id,
            group_id=self.user_messages_component.get_selected_group(),
            start_date=self.user_messages_component.get_start_date(),
            end_date=self.user_messages_component.get_end_date()
        )
        
        self.user_stats_component.update_stats(stats)
    
    def _refresh_messages(self):
        """Refresh messages table."""
        if not self.selected_user:
            self.user_messages_component.clear_messages()
            return
        
        messages = self.view_model.get_user_messages(
            user_id=self.selected_user.user_id,
            group_id=self.user_messages_component.get_selected_group(),
            start_date=self.user_messages_component.get_start_date(),
            end_date=self.user_messages_component.get_end_date(),
            limit=100
        )
        
        self.user_messages_component.refresh_messages(messages)

