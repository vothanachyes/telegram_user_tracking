"""
Group Detail dialog showing group information and fetch history.
"""

import flet as ft
import asyncio
import logging
from typing import Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from database.models.telegram import TelegramGroup
from services.telegram import TelegramService
from ui.theme import theme_manager

logger = logging.getLogger(__name__)


class GroupDetailDialog(ft.AlertDialog):
    """Dialog showing group details and fetch history."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        telegram_service: TelegramService,
        group: TelegramGroup
    ):
        self.db_manager = db_manager
        self.telegram_service = telegram_service
        self.group = group
        self.page: Optional[ft.Page] = None
        
        # Fetch history
        self.fetch_history = self.db_manager.get_fetch_history_by_group(group.group_id)
        
        super().__init__(
            modal=True,
            title=ft.Text(theme_manager.t("group_details") or "Group Details"),
            content=self._build_content(),
            actions=[
                ft.TextButton(
                    theme_manager.t("close"),
                    on_click=self._close_dialog
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def set_page(self, page: ft.Page):
        """Set page reference."""
        self.page = page
    
    def _build_content(self) -> ft.Container:
        """Build dialog content."""
        # Group photo or icon
        photo_content = ft.Icon(ft.Icons.GROUP, size=64, color=theme_manager.primary_color)
        if self.group.group_photo_path:
            try:
                photo_content = ft.Image(
                    src=self.group.group_photo_path,
                    width=64,
                    height=64,
                    fit=ft.ImageFit.COVER,
                    border_radius=theme_manager.corner_radius
                )
            except:
                pass
        
        # Group info
        last_fetch_text = "Never"
        if self.group.last_fetch_date:
            last_fetch_text = self.group.last_fetch_date.strftime("%Y-%m-%d %H:%M")
        
        group_info = ft.Column([
            ft.Text(self.group.group_name, size=20, weight=ft.FontWeight.BOLD),
            ft.Text(f"ID: {self.group.group_id}", size=14, color=theme_manager.text_secondary_color),
            ft.Text(f"Username: {self.group.group_username or 'N/A'}", size=14, color=theme_manager.text_secondary_color),
            ft.Text(f"Last fetch: {last_fetch_text}", size=14, color=theme_manager.text_secondary_color),
            ft.Text(f"Total messages: {self.group.total_messages}", size=14, color=theme_manager.text_secondary_color),
        ], spacing=5)
        
        # Fetch history table
        history_rows = []
        if self.fetch_history:
            for history in self.fetch_history:
                start_date = history.start_date.strftime("%Y-%m-%d") if history.start_date else "N/A"
                end_date = history.end_date.strftime("%Y-%m-%d") if history.end_date else "N/A"
                date_range = f"{start_date} to {end_date}"
                
                # Build account display (full name, username, phone)
                account_display = history.account_phone_number or "N/A"
                if history.account_full_name:
                    account_display = history.account_full_name
                    if history.account_username:
                        account_display += f" (@{history.account_username})"
                    account_display += f" ({history.account_phone_number or 'N/A'})"
                
                # Build detailed summary text
                summary_parts = [f"{history.message_count} messages"]
                if history.total_users_fetched > 0:
                    summary_parts.append(f"{history.total_users_fetched} users")
                if history.total_stickers > 0:
                    summary_parts.append(f"{history.total_stickers} stickers")
                if history.total_photos > 0:
                    summary_parts.append(f"{history.total_photos} photos")
                if history.total_videos > 0:
                    summary_parts.append(f"{history.total_videos} videos")
                if history.total_documents > 0:
                    summary_parts.append(f"{history.total_documents} documents")
                if history.total_audio > 0:
                    summary_parts.append(f"{history.total_audio} audio")
                if history.total_links > 0:
                    summary_parts.append(f"{history.total_links} links")
                if history.total_media_fetched > 0:
                    summary_parts.append(f"{history.total_media_fetched} media files")
                summary_text = ", ".join(summary_parts)
                
                history_rows.append(ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(date_range, size=12)),
                        ft.DataCell(ft.Text(summary_text, size=12)),
                        ft.DataCell(ft.Text(account_display, size=12)),
                    ]
                ))
        else:
            history_rows.append(ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text("No fetch history", color=theme_manager.text_secondary_color)),
                    ft.DataCell(ft.Text("")),
                    ft.DataCell(ft.Text("")),
                ]
            ))
        
        history_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(theme_manager.t("date_range") or "Date Range")),
                ft.DataColumn(ft.Text("Summary")),
                ft.DataColumn(ft.Text("Account Used")),
            ],
            rows=history_rows,
            heading_row_color=theme_manager.surface_color,
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    photo_content,
                    group_info,
                ], spacing=15),
                ft.Divider(),
                ft.Text(
                    theme_manager.t("fetch_history") or "Fetch History",
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(height=10),
                history_table if history_rows else ft.Text("No fetch history", color=theme_manager.text_secondary_color),
            ], spacing=10, width=600, height=500, scroll=ft.ScrollMode.AUTO),
            padding=10
        )
    
    def _close_dialog(self, e):
        """Close dialog."""
        if self.page:
            self.page.close(self)

