"""
User detail dialog with CRUD operations.
"""

import flet as ft
from typing import Callable, Optional
from datetime import datetime
from ui.theme import theme_manager
from ui.dialogs import dialog_manager
from database.models import TelegramUser
from database.db_manager import DatabaseManager


class UserDetailDialog(ft.AlertDialog):
    """Dialog for displaying and editing user details."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        user: TelegramUser,
        on_delete: Optional[Callable] = None,
        on_update: Optional[Callable] = None
    ):
        self.db_manager = db_manager
        self.user = user
        self.on_delete_callback = on_delete
        self.on_update_callback = on_update
        
        # Create editable fields
        self.username_field = ft.TextField(
            label=theme_manager.t("username"),
            value=user.username or "",
            border_radius=theme_manager.corner_radius,
            prefix_text="@"
        )
        
        self.first_name_field = ft.TextField(
            label=theme_manager.t("first_name"),
            value=user.first_name or "",
            border_radius=theme_manager.corner_radius
        )
        
        self.last_name_field = ft.TextField(
            label=theme_manager.t("last_name"),
            value=user.last_name or "",
            border_radius=theme_manager.corner_radius
        )
        
        self.phone_field = ft.TextField(
            label=theme_manager.t("phone"),
            value=user.phone or "",
            border_radius=theme_manager.corner_radius
        )
        
        self.bio_field = ft.TextField(
            label=theme_manager.t("bio"),
            value=user.bio or "",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_radius=theme_manager.corner_radius
        )
        
        # Create the dialog
        super().__init__(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.PERSON, color=theme_manager.primary_color),
                ft.Text(
                    theme_manager.t("user_details"),
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
                    theme_manager.t("delete_profile_photo"),
                    on_click=self._delete_profile_photo,
                    style=ft.ButtonStyle(
                        color=ft.Colors.ORANGE
                    )
                ),
                ft.TextButton(
                    theme_manager.t("save"),
                    on_click=self._save_user,
                    style=ft.ButtonStyle(
                        color=theme_manager.primary_color
                    )
                ),
                ft.TextButton(
                    theme_manager.t("delete"),
                    on_click=self._delete_user,
                    style=ft.ButtonStyle(
                        color=ft.Colors.RED
                    )
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _build_content(self) -> ft.Container:
        """Build the dialog content."""
        
        # Profile photo section
        profile_photo_section = theme_manager.create_card(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("profile_photo"),
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(),
                ft.Row([
                    ft.Icon(
                        ft.Icons.ACCOUNT_CIRCLE,
                        size=80,
                        color=theme_manager.primary_color
                    ) if not self.user.profile_photo_path else ft.Image(
                        src=self.user.profile_photo_path,
                        width=80,
                        height=80,
                        fit=ft.ImageFit.COVER,
                        border_radius=40
                    ),
                    ft.Column([
                        ft.Text(
                            self.user.full_name,
                            size=18,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(
                            f"User ID: {self.user.user_id}",
                            size=14,
                            color=theme_manager.text_secondary_color
                        ),
                        ft.Text(
                            f"Profile Photo: {'Available' if self.user.profile_photo_path else 'Not Available'}",
                            size=12,
                            color=theme_manager.text_secondary_color
                        ),
                    ], spacing=5)
                ], spacing=20, alignment=ft.MainAxisAlignment.START)
            ], spacing=10)
        )
        
        # User information section (read-only)
        info_section = theme_manager.create_card(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("user_information"),
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(),
                self._info_row("User ID", str(self.user.user_id)),
                self._info_row("Created At", str(self.user.created_at or "N/A")),
                self._info_row("Updated At", str(self.user.updated_at or "N/A")),
            ], spacing=10)
        )
        
        # Editable fields section
        edit_section = theme_manager.create_card(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("editable_information"),
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(),
                self.username_field,
                ft.Row([
                    self.first_name_field,
                    self.last_name_field,
                ], spacing=10),
                self.phone_field,
                self.bio_field,
            ], spacing=10)
        )
        
        # Get message count for this user
        message_count = self.db_manager.get_message_count(user_id=self.user.user_id)
        
        # Statistics section
        stats_section = theme_manager.create_card(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("statistics"),
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(),
                ft.Row([
                    ft.Column([
                        ft.Text(
                            str(message_count),
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            color=theme_manager.primary_color
                        ),
                        ft.Text(
                            theme_manager.t("total_messages"),
                            size=14,
                            color=theme_manager.text_secondary_color
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=10)
        )
        
        return ft.Container(
            content=ft.Column([
                profile_photo_section,
                info_section,
                edit_section,
                stats_section,
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            width=650,
            height=600
        )
    
    def _info_row(self, label: str, value: str) -> ft.Row:
        """Create an information row."""
        return ft.Row([
            ft.Text(f"{label}:", weight=ft.FontWeight.BOLD, width=120),
            ft.Text(value, selectable=True),
        ])
    
    def _close_dialog(self, e):
        """Close the dialog."""
        self.open = False
        if self.page:
            self.page.update()
    
    def _save_user(self, e):
        """Save user changes."""
        try:
            # Update user information
            self.user.username = self.username_field.value or None
            self.user.first_name = self.first_name_field.value or None
            self.user.last_name = self.last_name_field.value or None
            
            # Update full name
            if self.user.first_name and self.user.last_name:
                self.user.full_name = f"{self.user.first_name} {self.user.last_name}"
            elif self.user.first_name:
                self.user.full_name = self.user.first_name
            elif self.user.last_name:
                self.user.full_name = self.user.last_name
            else:
                self.user.full_name = self.user.username or f"User_{self.user.user_id}"
            
            self.user.phone = self.phone_field.value or None
            self.user.bio = self.bio_field.value or None
            self.user.updated_at = datetime.now()
            
            # Save to database
            self.db_manager.save_user(self.user)
            
            # Show success toast
            if self.page:
                theme_manager.show_toast_success(
                    self.page,
                    theme_manager.t("save_success")
                )
            
            # Call update callback
            if self.on_update_callback:
                self.on_update_callback()
            
            # Close dialog
            self._close_dialog(e)
        except Exception as ex:
            if self.page:
                theme_manager.show_toast_error(
                    self.page,
                    f"{theme_manager.t('save_error')}: {str(ex)}"
                )
    
    def _delete_profile_photo(self, e):
        """Delete user's profile photo."""
        import os
        
        if not self.user.profile_photo_path:
            if self.page:
                theme_manager.show_toast_warning(
                    self.page,
                    theme_manager.t("no_profile_photo")
                )
            return
        
        def confirm_delete_photo(confirm_e):
            try:
                # Delete the file if it exists
                if self.user.profile_photo_path and os.path.exists(self.user.profile_photo_path):
                    os.remove(self.user.profile_photo_path)
                
                # Update user record
                self.user.profile_photo_path = None
                self.user.updated_at = datetime.now()
                self.db_manager.save_user(self.user)
                
                # Get page for toast
                page = dialog_manager._get_page_from_event(confirm_e, getattr(self, 'page', None))
                if page:
                    theme_manager.show_toast_success(
                        page,
                        theme_manager.t("profile_photo_deleted")
                    )
                
                # Call update callback
                if self.on_update_callback:
                    self.on_update_callback()
                
                # Close main dialog
                self._close_dialog(e)
            except Exception as ex:
                # Get page for error toast
                page = dialog_manager._get_page_from_event(confirm_e, getattr(self, 'page', None))
                if page:
                    theme_manager.show_toast_error(
                        page,
                        f"{theme_manager.t('delete_error')}: {str(ex)}"
                    )
        
        # Show confirmation dialog using centralized manager
        dialog_manager.show_confirmation_dialog(
            page=getattr(self, 'page', None),
            title=theme_manager.t("confirm_delete"),
            message=theme_manager.t("delete_profile_photo_confirm"),
            on_confirm=confirm_delete_photo,
            confirm_text=theme_manager.t("delete"),
            cancel_text=theme_manager.t("cancel"),
            confirm_color=ft.Colors.ORANGE,
            main_dialog=self,  # Restore this dialog on cancel
            event=e
        )
    
    def _delete_user(self, e):
        """Delete (soft delete) the user."""
        def confirm_delete(confirm_e):
            try:
                # Soft delete the user
                self.db_manager.soft_delete_user(self.user.user_id)
                
                # Get page for toast
                page = dialog_manager._get_page_from_event(confirm_e, getattr(self, 'page', None))
                if page:
                    theme_manager.show_toast_success(
                        page,
                        theme_manager.t("delete_success")
                    )
                
                # Call delete callback
                if self.on_delete_callback:
                    self.on_delete_callback()
                
                # Close main dialog
                self._close_dialog(e)
            except Exception as ex:
                # Get page for error toast
                page = dialog_manager._get_page_from_event(confirm_e, getattr(self, 'page', None))
                if page:
                    theme_manager.show_toast_error(
                        page,
                        f"{theme_manager.t('delete_error')}: {str(ex)}"
                    )
        
        # Show confirmation dialog using centralized manager
        dialog_manager.show_confirmation_dialog(
            page=getattr(self, 'page', None),
            title=theme_manager.t("confirm_delete"),
            message=theme_manager.t("delete_user_confirm"),
            on_confirm=confirm_delete,
            confirm_text=theme_manager.t("delete"),
            cancel_text=theme_manager.t("cancel"),
            confirm_color=ft.Colors.RED,
            main_dialog=self,  # Restore this dialog on cancel
            event=e
        )

