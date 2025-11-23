"""
Notification detail dialog.
"""

import flet as ft
import logging
from typing import Callable, Optional, Dict
from datetime import datetime
from ui.theme import theme_manager
from services.notification_service import notification_service
from services.auth_service import auth_service
from utils.html_renderer import HTMLRenderer

logger = logging.getLogger(__name__)


class NotificationDetailDialog(ft.AlertDialog):
    """Dialog for displaying notification details."""
    
    def __init__(
        self,
        notification: Dict,
        on_close: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize notification detail dialog.
        
        Args:
            notification: Notification data dict
            on_close: Callback when dialog closes (receives notification_id)
        """
        self.notification = notification
        self.on_close_callback = on_close
        self.notification_id = notification.get("notification_id", "")
        self.is_fullscreen = False
        
        # Mark as read when dialog opens
        self._mark_as_read()
        
        # Build content
        content_column = ft.Column(
            controls=[],
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
        )
        
        # Check if content is HTML (HTML content usually contains its own title/structure)
        content = notification.get("content", "")
        is_html_content = HTMLRenderer.is_html(content) if content else False
        
        # Only show separate title/subtitle if content is not HTML
        # (HTML content should be self-contained and handle its own presentation)
        if not is_html_content:
            # Title
            title_text = ft.Text(
                notification.get("title", ""),
                size=theme_manager.font_size_page_title,
                weight=ft.FontWeight.BOLD,
                color=theme_manager.text_color,
            )
            content_column.controls.append(title_text)
            
            # Subtitle
            subtitle = notification.get("subtitle", "")
            if subtitle:
                subtitle_text = ft.Text(
                    subtitle,
                    size=theme_manager.font_size_body,
                    color=theme_manager.text_secondary_color,
                )
                content_column.controls.append(subtitle_text)
            
            # Image (only show separately for non-HTML content)
            image_url = notification.get("image_url", "")
            if image_url:
                try:
                    image = ft.Image(
                        src=image_url,
                        fit=ft.ImageFit.CONTAIN,
                        error_content=ft.Text(
                            "Failed to load image",
                            color=theme_manager.text_secondary_color,
                        ),
                    )
                    content_column.controls.append(image)
                except Exception as e:
                    logger.error(f"Error loading notification image: {e}")
        
        # Content (HTML/Markdown)
        if content:
            content_text = self._render_content(content)
            content_column.controls.append(content_text)
        
        # Metadata row
        notification_type = notification.get("type", "info")
        created_at = notification.get("created_at", "")
        
        # Format date
        date_text = ""
        if created_at:
            try:
                if isinstance(created_at, str):
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    date_text = dt.strftime("%Y-%m-%d %H:%M")
                elif hasattr(created_at, "strftime"):
                    date_text = created_at.strftime("%Y-%m-%d %H:%M")
                else:
                    date_text = str(created_at)
            except Exception:
                date_text = str(created_at)
        
        # Type badge color
        type_colors = {
            "info": ft.Colors.BLUE,
            "warning": ft.Colors.ORANGE,
            "announcement": ft.Colors.PURPLE,
            "update": ft.Colors.GREEN,
        }
        type_color = type_colors.get(notification_type, ft.Colors.GREY)
        
        metadata_row = ft.Row([
            ft.Container(
                content=ft.Text(
                    notification_type.capitalize(),
                    size=12,
                    color=ft.Colors.WHITE,
                ),
                bgcolor=type_color,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=4,
            ),
            ft.Text(
                date_text,
                size=theme_manager.font_size_small,
                color=theme_manager.text_secondary_color,
            ),
        ], spacing=10)
        content_column.controls.append(metadata_row)
        
        # Store content column for resizing
        self.content_column = content_column
        self.content_container = ft.Container(
            content=content_column,
            width=600,
            height=500,
        )
        
        # Fullscreen toggle button
        self.fullscreen_button = ft.IconButton(
            icon=ft.Icons.FULLSCREEN,
            tooltip="Toggle fullscreen",
            on_click=self._toggle_fullscreen,
        )
        
        # Create dialog
        super().__init__(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Text(
                        theme_manager.t("notification_detail") or "Notification Detail",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        expand=True,
                    ),
                    self.fullscreen_button,
                ],
                spacing=10,
            ),
            content=self.content_container,
            actions=[
                ft.TextButton(
                    theme_manager.t("close") or "Close",
                    on_click=self._close_dialog,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _render_content(self, content: str) -> ft.Control:
        """
        Render content as HTML, Markdown, or plain text.
        
        Args:
            content: Content string (may be HTML, Markdown, or plain text)
            
        Returns:
            Flet control for rendering the content
        """
        if not content:
            return ft.Text("", size=theme_manager.font_size_body)
        
        # Check if content contains HTML tags
        if HTMLRenderer.is_html(content):
            # Try to render as HTML using BeautifulSoup4
            try:
                return HTMLRenderer.render_html_to_flet(content)
            except Exception as html_error:
                logger.error(f"HTML rendering failed: {html_error}", exc_info=True)
                # Fall through to Markdown/plain text fallback
        
        # Try Markdown rendering
        try:
            return ft.Markdown(
                content,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                code_theme="atom-one-dark",
            )
        except Exception:
            # Final fallback: plain text
            return ft.Text(
                content,
                size=theme_manager.font_size_body,
                color=theme_manager.text_color,
            )
    
    def _mark_as_read(self):
        """Mark notification as read."""
        try:
            current_user = auth_service.get_current_user()
            if not current_user:
                return
            
            user_id = current_user.get("uid")
            if not user_id or not self.notification_id:
                return
            
            # Mark as read
            notification_service.mark_as_read(user_id, self.notification_id)
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}", exc_info=True)
    
    def _toggle_fullscreen(self, e: ft.ControlEvent):
        """Toggle fullscreen mode."""
        self.is_fullscreen = not self.is_fullscreen
        
        if self.is_fullscreen:
            # Fullscreen mode
            self.content_container.width = None
            self.content_container.height = None
            self.content_container.expand = True
            self.fullscreen_button.icon = ft.Icons.FULLSCREEN_EXIT
            self.fullscreen_button.tooltip = "Exit fullscreen"
        else:
            # Normal mode
            self.content_container.width = 600
            self.content_container.height = 500
            self.content_container.expand = False
            self.fullscreen_button.icon = ft.Icons.FULLSCREEN
            self.fullscreen_button.tooltip = "Toggle fullscreen"
        
        if self.page:
            self.page.update()
    
    def _close_dialog(self, e: ft.ControlEvent):
        """Close the dialog."""
        if self.page:
            self.page.close(self)
        
        # Call close callback
        if self.on_close_callback and self.notification_id:
            self.on_close_callback(self.notification_id)

