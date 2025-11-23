"""
Dialog for enabling database field encryption with migration confirmation.
"""

import flet as ft
from typing import Optional, Callable, Dict
from ui.theme import theme_manager


class EnableEncryptionDialog(ft.AlertDialog):
    """Dialog for enabling database field encryption with statistics."""
    
    def __init__(
        self,
        stats: Dict[str, int],
        on_start: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None
    ):
        """
        Initialize enable encryption dialog.
        
        Args:
            stats: Dictionary with encryption statistics
            on_start: Callback when user clicks Start button
            on_cancel: Callback when user clicks Cancel or closes dialog
        """
        self.on_start_callback = on_start
        self.on_cancel_callback = on_cancel
        self.stats = stats
        
        # Check if there are any records to encrypt
        total_to_encrypt = (
            stats.get('unencrypted_messages', 0) +
            stats.get('unencrypted_users', 0) +
            stats.get('unencrypted_credentials', 0)
        )
        has_records_to_encrypt = total_to_encrypt > 0
        
        # Build content
        content = self._build_content(stats)
        
        # Start button - disabled if no records to encrypt
        self.start_button = ft.TextButton(
            text=theme_manager.t("start") or "Start",
            on_click=self._on_start,
            disabled=not has_records_to_encrypt,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=theme_manager.primary_color if has_records_to_encrypt else ft.Colors.GREY
            )
        )
        
        super().__init__(
            title=ft.Text(theme_manager.t("enable_encryption_dialog_title") or "Enable Database Encryption"),
            content=ft.Container(
                content=content,
                width=500,
                padding=10
            ),
            actions=[
                ft.TextButton(
                    text=theme_manager.t("cancel"),
                    on_click=self._on_cancel
                ),
                self.start_button
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True
        )
    
    def _build_content(self, stats: Dict[str, int]) -> ft.Column:
        """Build dialog content with information, statistics, and warnings."""
        # Information section
        info_text = ft.Text(
            theme_manager.t("enable_encryption_dialog_info") or 
            "Field-level encryption will encrypt sensitive data in your database. "
            "This provides an additional layer of security for your data.",
            size=12,
            color=theme_manager.text_secondary_color
        )
        
        # What will be encrypted section
        what_encrypted_title = ft.Text(
            theme_manager.t("encryption_what_will_be_encrypted") or "What will be encrypted:",
            size=14,
            weight=ft.FontWeight.BOLD
        )
        
        encrypted_list = ft.Column([
            ft.Text("• Messages: content, caption, message_link", size=11),
            ft.Text("• Users: username, first_name, last_name, full_name, phone, bio", size=11),
            ft.Text("• Credentials: phone_number, session_string", size=11),
            ft.Text("• Reactions: message_link", size=11),
            ft.Text("• Group fetch history: account_phone_number, account_full_name, account_username", size=11),
            ft.Text("• Account activity log: phone_number", size=11)
        ], spacing=5, tight=True)
        
        # Statistics section
        stats_card = self._build_statistics_card(stats)
        
        # Warning section
        warning_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE_700, size=20),
                    ft.Text(
                        theme_manager.t("encryption_warning_irreversible") or 
                        "WARNING: This action cannot be undone. Once encrypted, data will be encrypted in the database. Make sure you have a backup.",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ORANGE_700
                    )
                ], spacing=10),
                ft.Text(
                    theme_manager.t("encryption_warning_device_specific") or 
                    "Note: Data encrypted on this device cannot be decrypted on another device. "
                    "The encryption key is device-specific.",
                    size=11,
                    color=theme_manager.text_secondary_color
                )
            ], spacing=10, tight=True),
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ORANGE_700),
            border=ft.border.all(1, ft.Colors.ORANGE_700),
            border_radius=8,
            padding=15
        )
        
        return ft.Column([
            info_text,
            ft.Divider(height=20),
            what_encrypted_title,
            encrypted_list,
            ft.Divider(height=20),
            stats_card,
            ft.Divider(height=20),
            warning_card
        ], spacing=15, tight=True, scroll=ft.ScrollMode.AUTO)
    
    def _build_statistics_card(self, stats: Dict[str, int]) -> ft.Container:
        """Build statistics card showing encrypted vs unencrypted counts."""
        # Already encrypted section
        already_encrypted_text = ft.Text(
            theme_manager.t("encryption_already_encrypted") or "Already Encrypted:",
            size=12,
            weight=ft.FontWeight.BOLD
        )
        
        already_encrypted_counts = ft.Text(
            f"{stats.get('encrypted_messages', 0)} messages, "
            f"{stats.get('encrypted_users', 0)} users, "
            f"{stats.get('encrypted_credentials', 0)} credentials",
            size=11,
            color=theme_manager.text_secondary_color
        )
        
        # Will be encrypted section
        will_be_encrypted_text = ft.Text(
            theme_manager.t("encryption_will_be_encrypted") or "Will Be Encrypted:",
            size=12,
            weight=ft.FontWeight.BOLD
        )
        
        total_to_encrypt = (
            stats.get('unencrypted_messages', 0) +
            stats.get('unencrypted_users', 0) +
            stats.get('unencrypted_credentials', 0)
        )
        
        if total_to_encrypt == 0:
            will_be_encrypted_counts = ft.Text(
                theme_manager.t("encryption_no_records_to_encrypt") or 
                "No records need to be encrypted (all data is already encrypted or database is empty).",
                size=11,
                color=ft.Colors.ORANGE_700,
                weight=ft.FontWeight.BOLD
            )
        else:
            will_be_encrypted_counts = ft.Text(
                f"{stats.get('unencrypted_messages', 0)} messages, "
                f"{stats.get('unencrypted_users', 0)} users, "
                f"{stats.get('unencrypted_credentials', 0)} credentials",
                size=11,
                color=theme_manager.text_secondary_color
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=theme_manager.primary_color, size=18),
                    ft.Text(
                        theme_manager.t("encryption_statistics") or "Encryption Statistics",
                        size=14,
                        weight=ft.FontWeight.BOLD
                    )
                ], spacing=10),
                ft.Divider(height=10),
                already_encrypted_text,
                already_encrypted_counts,
                ft.Divider(height=10),
                will_be_encrypted_text,
                will_be_encrypted_counts
            ], spacing=10, tight=True),
            bgcolor=theme_manager.surface_color,
            border=ft.border.all(1, theme_manager.border_color),
            border_radius=8,
            padding=15
        )
    
    def _on_start(self, e):
        """Handle Start button click."""
        if self.on_start_callback:
            self.on_start_callback()
        
        # Close dialog
        if self.page:
            self.page.close(self)
    
    def _on_cancel(self, e):
        """Handle Cancel button click."""
        if self.on_cancel_callback:
            self.on_cancel_callback()
        
        # Close dialog
        if self.page:
            self.page.close(self)

