"""
UI components for fetch data page.
"""

import flet as ft
import asyncio
from typing import Optional, Callable
from datetime import datetime
from ui.theme import theme_manager
from database.models import Message, TelegramUser
from database.db_manager import DatabaseManager
from utils.helpers import format_datetime


class MessageCard(ft.Container):
    """Animated message card component."""
    
    def __init__(
        self,
        message: Optional[Message] = None,
        user: Optional[TelegramUser] = None,
        error: Optional[str] = None,
        position: str = "center",  # "left", "center", "right"
        on_animation_complete: Optional[callable] = None,
        db_manager: Optional[DatabaseManager] = None,
        on_undelete: Optional[Callable] = None,
        page: Optional[ft.Page] = None
    ):
        self.message = message
        self.user = user
        self.error = error
        self.position = position
        self.on_animation_complete = on_animation_complete
        self.db_manager = db_manager
        self.on_undelete = on_undelete
        self.page = page
        
        # Status tracking
        self.is_existing = False
        self.is_deleted = False
        self.undelete_timer: Optional[asyncio.Task] = None
        self.undelete_button: Optional[ft.ElevatedButton] = None
        self.timer_text: Optional[ft.Text] = None
        self.timer_seconds = 5
        
        # Check message status if message and db_manager are provided
        if self.message and self.db_manager:
            self._check_message_status()
        
        # Calculate size and position based on position
        width, height, opacity, scale = self._get_position_props()
        
        # Set expand for responsive width
        expand_value = width is None
        
        super().__init__(
            content=self._build_content(),
            width=width,
            height=height,
            opacity=opacity,
            scale=scale,
            expand=expand_value,
            animate=ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT),
            border_radius=theme_manager.corner_radius,
            padding=theme_manager.padding_md,
            bgcolor=theme_manager.surface_color,
            border=ft.border.all(1, theme_manager.border_color),
        )
    
    def _get_position_props(self) -> tuple:
        """Get width, height, opacity, and scale based on position (responsive)."""
        # Use fixed height to prevent flickering - all cards same height
        FIXED_HEIGHT = 300
        # Use None for width to allow expand=True for responsive design
        if self.position == "center":
            return None, FIXED_HEIGHT, 1.0, 1.0
        elif self.position == "left":
            return None, FIXED_HEIGHT, 0.6, 0.8
        elif self.position == "right":
            return None, FIXED_HEIGHT, 0.6, 0.8
        else:
            return None, FIXED_HEIGHT, 0.0, 0.8
    
    def _check_message_status(self):
        """Check if message exists and is deleted."""
        if not self.message or not self.db_manager:
            return
        
        self.is_existing = self.db_manager.message_exists(
            self.message.message_id,
            self.message.group_id
        )
        self.is_deleted = self.db_manager.is_message_deleted(
            self.message.message_id,
            self.message.group_id
        )
    
    def _build_content(self) -> ft.Column:
        """Build card content."""
        if self.error:
            return self._build_error_content()
        elif self.message:
            return self._build_message_content()
        else:
            return self._build_empty_content()
    
    def _build_error_content(self) -> ft.Column:
        """Build error state content."""
        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED, size=theme_manager.font_size_page_title),
                ft.Text(
                    "Error",
                    size=theme_manager.font_size_subsection_title,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED
                )
            ], spacing=theme_manager.spacing_sm),
            ft.Divider(),
            ft.Text(
                self.error or "Unknown error",
                size=theme_manager.font_size_body,
                color=ft.Colors.RED,
                max_lines=3,
                overflow=ft.TextOverflow.ELLIPSIS
            )
        ], spacing=theme_manager.spacing_sm, tight=True)
    
    def _build_message_content(self) -> ft.Column:
        """Build message content."""
        # Sender profile section
        sender_name = self.user.full_name if self.user else "Unknown"
        sender_username = f"@{self.user.username}" if self.user and self.user.username else "N/A"
        sender_phone = self.user.phone if self.user and self.user.phone else "N/A"
        
        # Message preview
        message_preview = self.message.content[:100] + "..." if self.message.content and len(self.message.content) > 100 else (self.message.content or "No content")
        
        # Media indicator
        media_indicator = ""
        if self.message.has_media:
            media_type = self.message.media_type or "Media"
            media_indicator = f"📎 {media_type}"
        
        # Date
        date_str = format_datetime(self.message.date_sent, "%Y-%m-%d %H:%M") if self.message.date_sent else "N/A"
        
        # Build status badges/notes
        status_badges = []
        if self.is_existing:
            status_badges.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=ft.Colors.BLUE),
                        ft.Text(
                            "Already in database",
                            size=theme_manager.font_size_small,
                            color=ft.Colors.BLUE
                        )
                    ], spacing=5, tight=True),
                    padding=5,
                    bgcolor=ft.Colors.BLUE_50 if not theme_manager.is_dark else ft.Colors.BLUE_900,
                    border_radius=5
                )
            )
        
        if self.is_deleted:
            status_badges.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.DELETE_OUTLINE, size=16, color=ft.Colors.RED),
                        ft.Text(
                            "Deleted",
                            size=theme_manager.font_size_small,
                            color=ft.Colors.RED
                        )
                    ], spacing=5, tight=True),
                    padding=5,
                    bgcolor=ft.Colors.RED_50 if not theme_manager.is_dark else ft.Colors.RED_900,
                    border_radius=5
                )
            )
        
        # Build undelete button if deleted
        undelete_section = None
        if self.is_deleted and self.on_undelete:
            self.timer_text = ft.Text(
                f"Undelete ({self.timer_seconds}s)",
                size=theme_manager.font_size_small,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD
            )
            self.undelete_button = ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.RESTORE, size=18),
                    self.timer_text
                ], spacing=5, tight=True),
                on_click=self._on_undelete_click,
                bgcolor=ft.Colors.GREEN,
                color=ft.Colors.WHITE,
                width=200
            )
            undelete_section = ft.Container(
                content=ft.Column([
                    self.undelete_button
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=10,
                bgcolor=ft.Colors.GREEN_50 if not theme_manager.is_dark else ft.Colors.GREEN_900,
                border_radius=5
            )
        
        content_items = []
        
        # Status badges at top
        if status_badges:
            content_items.append(
                ft.Row(status_badges, spacing=5, wrap=True)
            )
        
        # Sender profile
        content_items.append(
            ft.Row([
                ft.Icon(ft.Icons.PERSON, size=40, color=theme_manager.primary_color),
                ft.Column([
                    ft.Text(sender_name, size=theme_manager.font_size_body, weight=ft.FontWeight.BOLD),
                    ft.Text(sender_username, size=theme_manager.font_size_small, color=theme_manager.text_secondary_color),
                    ft.Text(f"📱 {sender_phone}", size=theme_manager.font_size_small, color=theme_manager.text_secondary_color),
                ], spacing=theme_manager.spacing_xs, tight=True)
            ], spacing=theme_manager.spacing_sm)
        )
        
        content_items.append(ft.Divider())
        
        # Message content
        content_items.append(
            ft.Text(
                message_preview,
                size=theme_manager.font_size_body,
                max_lines=4,
                overflow=ft.TextOverflow.ELLIPSIS
            )
        )
        
        # Media and date
        content_items.append(
            ft.Row([
                ft.Text(media_indicator, size=theme_manager.font_size_small, color=theme_manager.text_secondary_color) if media_indicator else ft.Container(),
                ft.Container(expand=True),
                ft.Text(date_str, size=theme_manager.font_size_small, color=theme_manager.text_secondary_color),
            ], spacing=theme_manager.spacing_sm)
        )
        
        # Undelete section if deleted
        if undelete_section:
            content_items.append(undelete_section)
        
        return ft.Column(content_items, spacing=theme_manager.spacing_sm, tight=True, scroll=ft.ScrollMode.AUTO)
    
    def _build_empty_content(self) -> ft.Column:
        """Build empty state content."""
        return ft.Column([
            ft.Text(
                "Waiting for messages...",
                size=theme_manager.font_size_body,
                color=theme_manager.text_secondary_color,
                italic=True
            )
        ], spacing=theme_manager.spacing_sm, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    def update_position(self, new_position: str):
        """Update card position with animation."""
        self.position = new_position
        width, height, opacity, scale = self._get_position_props()
        # Use expand=True for responsive width instead of fixed width
        if width is None:
            self.expand = True
            self.width = None
        else:
            self.expand = False
            self.width = width
        self.height = height
        self.opacity = opacity
        self.scale = scale
        # Ensure animation is enabled
        if not self.animate:
            self.animate = ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT)
        # Update the card
        if self.page:
            self.update()
        else:
            self.update()
    
    def _on_undelete_click(self, e):
        """Handle undelete button click."""
        if self.undelete_timer:
            self.undelete_timer.cancel()
            self.undelete_timer = None
        
        if self.message and self.db_manager and self.on_undelete:
            # Undelete the message
            success = self.db_manager.undelete_message(
                self.message.message_id,
                self.message.group_id
            )
            if success:
                self.is_deleted = False
                # Call the callback to notify parent
                self.on_undelete(self.message)
    
    async def _start_undelete_timer(self):
        """Start 5-second timer for undelete action."""
        if not self.is_deleted or not self.timer_text:
            return
        
        for remaining in range(self.timer_seconds, 0, -1):
            if self.timer_text:
                self.timer_text.value = f"Undelete ({remaining}s)"
                if self.page:
                    try:
                        self.page.update()
                    except:
                        pass
            await asyncio.sleep(1)
        
        # Timer expired, proceed to next message
        if self.on_undelete:
            self.on_undelete(None)  # Pass None to indicate timeout
    
    def start_undelete_timer(self):
        """Start the undelete timer (non-blocking)."""
        if self.is_deleted and not self.undelete_timer:
            if self.page and hasattr(self.page, 'run_task'):
                self.undelete_timer = self.page.run_task(self._start_undelete_timer)
            else:
                self.undelete_timer = asyncio.create_task(self._start_undelete_timer())
    
    def update_message(
        self,
        message: Optional[Message],
        user: Optional[TelegramUser] = None,
        error: Optional[str] = None,
        is_existing: Optional[bool] = None,
        is_deleted: Optional[bool] = None
    ):
        """Update card with new message data."""
        # Cancel any existing timer
        if self.undelete_timer:
            self.undelete_timer.cancel()
            self.undelete_timer = None
        
        self.message = message
        self.user = user
        self.error = error
        
        # Update status if provided, otherwise check
        if message and self.db_manager:
            if is_existing is not None:
                self.is_existing = is_existing
            else:
                self.is_existing = self.db_manager.message_exists(
                    message.message_id,
                    message.group_id
                )
            
            if is_deleted is not None:
                self.is_deleted = is_deleted
            else:
                self.is_deleted = self.db_manager.is_message_deleted(
                    message.message_id,
                    message.group_id
                )
        else:
            self.is_existing = False
            self.is_deleted = False
        
        self.content = self._build_content()
        
        # Only update if control is attached to the page
        # In Flet, update() can only be called after control is added to page
        # Check if control has a parent (is in the page hierarchy)
        is_attached = hasattr(self, 'parent') and self.parent is not None
        
        if is_attached:
            try:
                self.update()
            except (AssertionError, AttributeError, RuntimeError) as e:
                # Control might have been removed from page (e.g., during navigation)
                # This is expected when navigating away and back
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"MessageCard update skipped (control not attached): {e}")
            except Exception as e:
                # Other errors - log but don't crash
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Error updating MessageCard: {e}")
        # If not attached, skip update - it will update when added to page via get_cards_row()
        
        # Start timer if deleted
        if self.is_deleted and self.on_undelete:
            self.start_undelete_timer()


class SummaryTable(ft.Container):
    """Post-fetch summary table component."""
    
    def __init__(self, summary_data: list, user_map: dict):
        """
        Initialize summary table.
        
        Args:
            summary_data: List of dicts with user_id, messages, reactions, media
            user_map: Dict mapping user_id to TelegramUser for name lookup
        """
        self.summary_data = summary_data
        self.user_map = user_map
        
        super().__init__(
            content=self._build_table(),
            padding=theme_manager.padding_md,
            bgcolor=theme_manager.surface_color,
            border_radius=theme_manager.corner_radius,
            border=ft.border.all(1, theme_manager.border_color),
        )
    
    def _build_table(self) -> ft.Column:
        """Build summary table."""
        if not self.summary_data:
            return ft.Column([
                ft.Text(
                    "No data to display",
                    size=theme_manager.font_size_body,
                    color=theme_manager.text_secondary_color,
                    italic=True
                )
            ], spacing=theme_manager.spacing_sm)
        
        # Create table rows
        rows = []
        for idx, data in enumerate(self.summary_data, 1):
            user = self.user_map.get(data['user_id'])
            user_name = user.full_name if user else f"User {data['user_id']}"
            
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(idx))),
                        ft.DataCell(ft.Text(user_name)),
                        ft.DataCell(ft.Text(str(data['messages']))),
                        ft.DataCell(ft.Text(str(data['reactions']))),
                        ft.DataCell(ft.Text(str(data['media']))),
                    ]
                )
            )
        
        return ft.Column([
            ft.Text(
                "Fetch Summary",
                size=theme_manager.font_size_subsection_title,
                weight=ft.FontWeight.BOLD
            ),
            ft.Divider(),
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("No")),
                    ft.DataColumn(ft.Text("User Name")),
                    ft.DataColumn(ft.Text("Messages Sent")),
                    ft.DataColumn(ft.Text("Reactions Given")),
                    ft.DataColumn(ft.Text("Media Shared")),
                ],
                rows=rows,
                heading_row_color=theme_manager.primary_color,
                heading_text_style=ft.TextStyle(color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            )
        ], spacing=theme_manager.spacing_sm)

