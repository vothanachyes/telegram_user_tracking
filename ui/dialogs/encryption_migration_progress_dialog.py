"""
Dialog showing progress during encryption migration.
"""

import flet as ft
from typing import Optional
from ui.theme import theme_manager


class EncryptionMigrationProgressDialog(ft.AlertDialog):
    """Dialog showing encryption migration progress."""
    
    def __init__(self):
        """Initialize migration progress dialog."""
        # Stage text
        self.stage_text = ft.Text(
            theme_manager.t("encryption_migration_in_progress") or "Preparing migration...",
            size=14,
            weight=ft.FontWeight.BOLD
        )
        
        # Progress text
        self.progress_text = ft.Text(
            "",
            size=12,
            color=theme_manager.text_secondary_color
        )
        
        # Progress bar
        self.progress_bar = ft.ProgressBar(
            width=400,
            color=theme_manager.primary_color,
            bgcolor=theme_manager.surface_color
        )
        
        # Statistics text
        self.stats_text = ft.Text(
            "",
            size=11,
            color=theme_manager.text_secondary_color
        )
        
        super().__init__(
            title=ft.Text(theme_manager.t("encryption_migration_title") or "Encrypting Database"),
            content=ft.Container(
                content=ft.Column([
                    self.stage_text,
                    ft.Divider(height=10),
                    self.progress_text,
                    self.progress_bar,
                    ft.Divider(height=10),
                    self.stats_text
                ], spacing=10, tight=True),
                width=450,
                padding=20
            ),
            actions=[],
            modal=True
        )
    
    def update_progress(
        self,
        stage: str,
        current: int,
        total: int,
        encrypted_count: Optional[int] = None
    ):
        """
        Update progress display.
        
        Args:
            stage: Current stage name (e.g., "telegram_credentials", "messages")
            current: Current record index
            total: Total records to process
            encrypted_count: Optional total encrypted records so far
        """
        # Update stage text
        stage_display = self._format_stage_name(stage)
        self.stage_text.value = f"{stage_display}..."
        
        # Update progress text
        if total > 0:
            percentage = (current / total) * 100
            self.progress_text.value = f"Processing {current} of {total} records ({percentage:.1f}%)"
            self.progress_bar.value = current / total
        else:
            self.progress_text.value = "Processing..."
            self.progress_bar.value = None  # Indeterminate
        
        # Update statistics
        if encrypted_count is not None:
            self.stats_text.value = f"Total encrypted so far: {encrypted_count} records"
        else:
            self.stats_text.value = ""
        
        # Update UI
        if self.page:
            self.page.update()
    
    def _format_stage_name(self, stage: str) -> str:
        """Format stage name for display."""
        stage_map = {
            "telegram_credentials": "Encrypting credentials",
            "telegram_users": "Encrypting users",
            "messages": "Encrypting messages",
            "reactions": "Encrypting reactions",
            "group_fetch_history": "Encrypting group fetch history",
            "account_activity_log": "Encrypting account activity log"
        }
        return stage_map.get(stage, stage.replace("_", " ").title())

