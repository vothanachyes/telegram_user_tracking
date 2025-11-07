"""
Message detail dialog with CRUD operations.
"""

import flet as ft
from typing import Callable, Optional
from datetime import datetime
from ui.theme import theme_manager
from database.models import Message, TelegramUser
from database.db_manager import DatabaseManager
from utils.helpers import format_datetime


class MessageDetailDialog(ft.AlertDialog):
    """Dialog for displaying and editing message details."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        message: Message,
        on_delete: Optional[Callable] = None,
        on_update: Optional[Callable] = None
    ):
        self.db_manager = db_manager
        self.message = message
        self.on_delete_callback = on_delete
        self.on_update_callback = on_update
        
        # Get sender information
        self.sender = self.db_manager.get_user_by_id(message.user_id)
        
        # Create content fields
        self.content_field = ft.TextField(
            label=theme_manager.t("message_content"),
            value=message.content or "",
            multiline=True,
            min_lines=3,
            max_lines=10,
            border_radius=theme_manager.corner_radius,
            expand=True
        )
        
        self.caption_field = ft.TextField(
            label=theme_manager.t("caption"),
            value=message.caption or "",
            multiline=True,
            min_lines=2,
            max_lines=5,
            border_radius=theme_manager.corner_radius,
            expand=True
        )
        
        # Create the dialog content
        super().__init__(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.MESSAGE, color=theme_manager.primary_color),
                ft.Text(
                    theme_manager.t("message_details"),
                    size=20,
                    weight=ft.FontWeight.BOLD
                )
            ]),
            content=self._build_content(),
            actions=[
                ft.TextButton(
                    theme_manager.t("cancel"),
                    on_click=self._close_dialog
                ),
                ft.TextButton(
                    theme_manager.t("save"),
                    on_click=self._save_message,
                    style=ft.ButtonStyle(
                        color=theme_manager.primary_color
                    )
                ),
                ft.TextButton(
                    theme_manager.t("delete"),
                    on_click=self._delete_message,
                    style=ft.ButtonStyle(
                        color=ft.Colors.RED
                    )
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _build_content(self) -> ft.Container:
        """Build the dialog content."""
        
        # Sender profile section
        sender_name = self.sender.full_name if self.sender else "Unknown"
        sender_username = self.sender.username if self.sender and self.sender.username else "N/A"
        sender_phone = self.sender.phone if self.sender and self.sender.phone else "N/A"
        
        sender_section = theme_manager.create_card(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("sender_profile"),
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(),
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, size=50, color=theme_manager.primary_color),
                    ft.Column([
                        ft.Text(sender_name, size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(f"@{sender_username}", size=14, color=theme_manager.text_secondary_color),
                        ft.Text(f"📱 {sender_phone}", size=14),
                    ], spacing=2)
                ], spacing=15)
            ], spacing=10)
        )
        
        # Message info section
        message_link = self.message.message_link or "N/A"
        
        # Create clickable link if available
        link_control = None
        if self.message.message_link:
            link_control = ft.TextButton(
                theme_manager.t("open_message"),
                icon=ft.Icons.OPEN_IN_NEW,
                on_click=lambda e: self._open_link(self.message.message_link),
                style=ft.ButtonStyle(
                    color=theme_manager.primary_color
                )
            )
        else:
            link_control = ft.Text("N/A", color=theme_manager.text_secondary_color)
        
        info_section = theme_manager.create_card(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("message_information"),
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(),
                self._info_row("Message ID", str(self.message.message_id)),
                self._info_row("Group ID", str(self.message.group_id)),
                self._info_row("Date Sent", format_datetime(self.message.date_sent, "%Y-%m-%d %H:%M:%S")),
                self._info_row("Has Media", "Yes" if self.message.has_media else "No"),
                self._info_row("Media Type", self.message.media_type or "N/A"),
                self._info_row("Media Count", str(self.message.media_count) if self.message.has_media else "0"),
                ft.Row([
                    ft.Text("Message Link:", weight=ft.FontWeight.BOLD, width=120),
                    link_control,
                ]),
            ], spacing=10)
        )
        
        # Editable content section
        content_section = theme_manager.create_card(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("editable_content"),
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(),
                self.content_field,
                ft.Container(height=10),
                self.caption_field,
            ], spacing=10)
        )
        
        return ft.Container(
            content=ft.Column([
                sender_section,
                info_section,
                content_section,
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            width=700,
            height=600
        )
    
    def _info_row(self, label: str, value: str) -> ft.Row:
        """Create an information row."""
        return ft.Row([
            ft.Text(f"{label}:", weight=ft.FontWeight.BOLD, width=120),
            ft.Text(value, selectable=True),
        ])
    
    def _open_link(self, url: str):
        """Open the message link in browser."""
        import webbrowser
        webbrowser.open(url)
    
    def _close_dialog(self, e):
        """Close the dialog."""
        self.open = False
        if self.page:
            self.page.update()
    
    def _save_message(self, e):
        """Save message changes."""
        try:
            # Update message content
            self.message.content = self.content_field.value
            self.message.caption = self.caption_field.value
            self.message.updated_at = datetime.now()
            
            # Save to database
            self.db_manager.save_message(self.message)
            
            # Show success message
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("save_success"),
                    bgcolor=ft.Colors.GREEN
                )
            
            # Call update callback
            if self.on_update_callback:
                self.on_update_callback()
            
            # Close dialog
            self._close_dialog(e)
        except Exception as ex:
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    f"{theme_manager.t('save_error')}: {str(ex)}",
                    bgcolor=ft.Colors.RED
                )
    
    def _delete_message(self, e):
        """Delete (soft delete) the message."""
        def confirm_delete(confirm_e):
            try:
                # Soft delete the message
                self.db_manager.soft_delete_message(self.message.message_id, self.message.group_id)
                
                # Show success message
                if self.page:
                    theme_manager.show_snackbar(
                        self.page,
                        theme_manager.t("delete_success"),
                        bgcolor=ft.Colors.GREEN
                    )
                
                # Call delete callback
                if self.on_delete_callback:
                    self.on_delete_callback()
                
                # Close confirmation dialog
                confirm_dialog.open = False
                
                # Close main dialog
                self._close_dialog(e)
            except Exception as ex:
                if self.page:
                    theme_manager.show_snackbar(
                        self.page,
                        f"{theme_manager.t('delete_error')}: {str(ex)}",
                        bgcolor=ft.Colors.RED
                    )
        
        def cancel_delete(cancel_e):
            confirm_dialog.open = False
            if self.page:
                self.page.update()
        
        # Confirmation dialog
        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(theme_manager.t("confirm_delete")),
            content=ft.Text(theme_manager.t("delete_message_confirm")),
            actions=[
                ft.TextButton(theme_manager.t("cancel"), on_click=cancel_delete),
                ft.TextButton(
                    theme_manager.t("delete"),
                    on_click=confirm_delete,
                    style=ft.ButtonStyle(color=ft.Colors.RED)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        if self.page:
            self.page.dialog = confirm_dialog
            confirm_dialog.open = True
            self.page.update()

