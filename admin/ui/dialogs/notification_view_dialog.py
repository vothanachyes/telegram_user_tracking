"""
Notification view dialog for displaying notification details in read-only mode.
"""

import flet as ft
import logging
from typing import Optional, Dict, Callable
from datetime import datetime
from utils.html_renderer import HTMLRenderer

logger = logging.getLogger(__name__)


class NotificationViewDialog(ft.AlertDialog):
    """Dialog for viewing notification details in read-only mode."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    CARD_BG = "#252525"
    BORDER_COLOR = "#333333"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    ERROR_COLOR = "#f44336"
    
    def __init__(
        self,
        notification_data: Dict,
        on_edit: Optional[Callable[[Dict], None]] = None,
    ):
        """
        Initialize notification view dialog.
        
        Args:
            notification_data: Notification data to display
            on_edit: Optional callback to open edit dialog
        """
        self.notification_data = notification_data
        self.on_edit = on_edit
        
        # Format created_at
        created_at = notification_data.get("created_at", "")
        if created_at:
            try:
                if isinstance(created_at, str):
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    created_at = dt.strftime("%Y-%m-%d %H:%M:%S")
                elif hasattr(created_at, "strftime"):
                    created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                created_at = str(created_at)
        
        # Get notification type
        notif_type = notification_data.get("type", "info").lower()
        type_display = notif_type.capitalize()
        
        # Get target users
        target_users = notification_data.get("target_users")
        if target_users is None:
            target_display = "All Users"
        else:
            count = len(target_users) if isinstance(target_users, list) else 0
            target_display = f"{count} User(s)"
        
        # Create type badge
        color_map = {
            "info": "#2196f3",
            "warning": "#ff9800",
            "error": "#f44336",
            "announcement": "#0078d4",
            "update": "#4caf50",
            "welcome": "#4caf50",
        }
        type_bg_color = color_map.get(notif_type, self.TEXT_SECONDARY)
        
        type_badge = ft.Container(
            content=ft.Text(
                type_display,
                size=12,
                weight=ft.FontWeight.BOLD,
                color="#ffffff",
            ),
            bgcolor=type_bg_color,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=12,
            width=120,
            alignment=ft.alignment.center,
        )
        
        # Content field (read-only)
        # Check if content is HTML (HTML content usually contains its own title/structure)
        content_value = notification_data.get("content", "")
        is_html_content = HTMLRenderer.is_html(content_value) if content_value else False
        
        if not content_value:
            content_display = ft.Text("*No content*", color=self.TEXT_SECONDARY)
        elif is_html_content:
            # Render HTML content using BeautifulSoup4
            try:
                content_display = HTMLRenderer.render_html_to_flet(content_value)
            except Exception as e:
                logger.error(f"Error rendering HTML content: {e}", exc_info=True)
                # Fallback to Markdown
                content_display = ft.Markdown(
                    value=content_value,
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                )
        else:
            # Render as Markdown
            content_display = ft.Markdown(
                value=content_value,
                selectable=True,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            )
        
        # Image URL if present
        image_url = notification_data.get("image_url", "")
        image_display = None
        if image_url:
            image_display = ft.Column(
                controls=[
                    ft.Text("Image:", size=12, color=self.TEXT_SECONDARY, weight=ft.FontWeight.BOLD),
                        ft.Image(
                            src=image_url,
                            fit=ft.ImageFit.CONTAIN,
                            width=400,
                            error_content=ft.Text("Failed to load image", color="#f44336"),
                        ),
                ],
                spacing=5,
            )
        
        # Build details content
        details_content = ft.Column(
            controls=[
                # Title
                ft.Row(
                    controls=[
                        ft.Text("Title:", size=12, color=self.TEXT_SECONDARY, weight=ft.FontWeight.BOLD, width=120),
                        ft.Text(
                            notification_data.get("title", "N/A"),
                            size=14,
                            color=self.TEXT_COLOR,
                            expand=True,
                        ),
                    ],
                    spacing=10,
                ),
                ft.Divider(height=10, color="transparent"),
                # Subtitle
                ft.Row(
                    controls=[
                        ft.Text("Subtitle:", size=12, color=self.TEXT_SECONDARY, weight=ft.FontWeight.BOLD, width=120),
                        ft.Text(
                            notification_data.get("subtitle", "N/A") if notification_data.get("subtitle") else "N/A",
                            size=14,
                            color=self.TEXT_COLOR,
                            expand=True,
                        ),
                    ],
                    spacing=10,
                ),
                ft.Divider(height=10, color="transparent"),
                # Type
                ft.Row(
                    controls=[
                        ft.Text("Type:", size=12, color=self.TEXT_SECONDARY, weight=ft.FontWeight.BOLD, width=120),
                        type_badge,
                    ],
                    spacing=10,
                ),
                ft.Divider(height=10, color="transparent"),
                # Target
                ft.Row(
                    controls=[
                        ft.Text("Target:", size=12, color=self.TEXT_SECONDARY, weight=ft.FontWeight.BOLD, width=120),
                        ft.Text(
                            target_display,
                            size=14,
                            color=self.TEXT_COLOR,
                            expand=True,
                        ),
                    ],
                    spacing=10,
                ),
                ft.Divider(height=10, color="transparent"),
                # Created At
                ft.Row(
                    controls=[
                        ft.Text("Created At:", size=12, color=self.TEXT_SECONDARY, weight=ft.FontWeight.BOLD, width=120),
                        ft.Text(
                            created_at or "N/A",
                            size=14,
                            color=self.TEXT_COLOR,
                            expand=True,
                        ),
                    ],
                    spacing=10,
                ),
                ft.Divider(height=15, color="transparent"),
                # Content
                ft.Text("Content:", size=12, color=self.TEXT_SECONDARY, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=content_display,
                    padding=ft.padding.all(10),
                    bgcolor=self.CARD_BG,
                    border_radius=5,
                    border=ft.border.all(1, self.BORDER_COLOR),
                ),
            ],
            spacing=5,
            scroll=ft.ScrollMode.AUTO,
        )
        
        # Add image if present
        if image_display:
            details_content.controls.append(ft.Divider(height=15, color="transparent"))
            details_content.controls.append(image_display)
        
        # Dialog actions
        actions_list = [
            ft.TextButton(
                "Close",
                on_click=self._on_close_click,
            ),
        ]
        
        # Add Edit button if callback provided
        if self.on_edit:
            actions_list.append(
                ft.ElevatedButton(
                    "Edit",
                    icon=ft.Icons.EDIT,
                    bgcolor=self.PRIMARY_COLOR,
                    color=self.TEXT_COLOR,
                    on_click=self._on_edit_click,
                )
            )
        
        super().__init__(
            modal=True,
            title=ft.Text("Notification Details", color=self.TEXT_COLOR),
            content=ft.Container(
                content=details_content,
                width=600,
                height=500,
            ),
            actions=actions_list,
            bgcolor=self.BG_COLOR,
        )
    
    def _on_close_click(self, e: ft.ControlEvent):
        """Handle close button click."""
        if self.page:
            self.page.close(self)
    
    def _on_edit_click(self, e: ft.ControlEvent):
        """Handle edit button click."""
        if self.page:
            self.page.close(self)
        
        if self.on_edit:
            self.on_edit(self.notification_data)

