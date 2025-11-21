"""
Progress UI components for fetch data page.
"""

import flet as ft
import asyncio
import logging
from typing import Optional
from ui.theme import theme_manager
from database.db_manager import DatabaseManager
from ui.pages.fetch_data.view_model import FetchViewModel
from ui.pages.fetch_data.components import MessageCard

logger = logging.getLogger(__name__)


class ProgressUI:
    """Manages progress UI components and card animations."""
    
    def __init__(
        self,
        view_model: FetchViewModel,
        db_manager: DatabaseManager,
        page: Optional[ft.Page] = None
    ):
        self.view_model = view_model
        self.db_manager = db_manager
        self.page = page
        
        # Progress UI components
        self.progress_bar = ft.ProgressBar(
            visible=False,
            width=400
        )
        
        self.progress_text = ft.Text(
            "",
            size=14,
            color=theme_manager.text_secondary_color,
            visible=False
        )
        
        self.estimated_count_text = ft.Text(
            "",
            size=14,
            color=theme_manager.text_secondary_color,
            visible=False
        )
        
        self.stats_text = ft.Text(
            "",
            size=12,
            color=theme_manager.text_secondary_color,
            visible=False
        )
        
        self.delay_countdown_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.ORANGE,
            visible=False,
            weight=ft.FontWeight.BOLD
        )
        
        # Message cards (3-card carousel)
        self.left_card: Optional[MessageCard] = None
        self.center_card: Optional[MessageCard] = None
        self.right_card: Optional[MessageCard] = None
        self._pending_deleted_message = None  # Track if we're waiting for undelete action
    
    def set_page(self, page: ft.Page):
        """Set page reference and initialize message cards."""
        self.page = page
        
        # Initialize message cards with db_manager and callbacks
        self.left_card = MessageCard(
            position="left",
            db_manager=self.db_manager,
            on_undelete=self._on_undelete_callback,
            page=page
        )
        self.center_card = MessageCard(
            position="center",
            db_manager=self.db_manager,
            on_undelete=self._on_undelete_callback,
            page=page
        )
        self.right_card = MessageCard(
            position="right",
            db_manager=self.db_manager,
            on_undelete=self._on_undelete_callback,
            page=page
        )
    
    def clear_cards(self):
        """Clear all message cards."""
        if self.left_card:
            self.left_card.update_message(None)
        if self.center_card:
            self.center_card.update_message(None)
        if self.right_card:
            self.right_card.update_message(None)
    
    def show_progress(self):
        """Show progress UI."""
        self.progress_bar.visible = True
        self.progress_text.visible = True
        self.progress_text.value = theme_manager.t("fetching_messages") or "Fetching messages..."
        self.progress_text.color = theme_manager.text_secondary_color
    
    def hide_progress(self):
        """Hide progress UI."""
        self.progress_bar.visible = False
    
    def update_progress_text(self, text: str, color: Optional[str] = None):
        """Update progress text."""
        self.progress_text.value = text
        if color:
            self.progress_text.color = color
    
    def _on_undelete_callback(self, message):
        """Handle undelete callback from message card."""
        if message is None:
            # Timer expired, proceed to next message
            self._pending_deleted_message = None
            return
        
        # Message was undeleted successfully
        self._pending_deleted_message = None
        if self.page:
            theme_manager.show_snackbar(
                self.page,
                "Message restored successfully",
                bgcolor=ft.Colors.GREEN
            )
    
    async def update_cards_animated(self, message, user, error):
        """Update cards with animation - smoother with right card appearing during center saving."""
        try:
            # Safety check: ensure cards are initialized
            # This can happen if update is called before set_page() or during navigation
            if not self.left_card or not self.center_card or not self.right_card:
                logger.debug("Message cards not yet initialized, skipping update")
                return
            
            # Check message status if message exists
            # Note: Since the fetcher already skips existing messages before processing,
            # any message that reaches here is new. However, it may have been saved
            # by the time we check, so we check if it existed BEFORE this fetch started.
            # For simplicity, we assume messages are new during fetch (fetcher handles skipping).
            is_existing = False
            is_deleted = False
            if message and self.db_manager:
                # Only check if deleted, not if existing (fetcher already handles that)
                is_deleted = self.db_manager.is_message_deleted(
                    message.message_id,
                    message.group_id
                )
                # Messages received during fetch are new (fetcher skips existing ones)
                # So we don't need to check message_exists() here
            
            # After add_message, queue is: [previous_left, previous_center, new_message]
            # We want to show: left=previous_center, center=new_message, right=empty
            
            # Step 1: Show new message on right first (appears while center is still showing previous)
            if self.right_card:
                self.right_card.update_message(
                    message,
                    user,
                    error,
                    is_existing=is_existing,
                    is_deleted=is_deleted
                )
                self.right_card.update_position("right")
                if self.page:
                    self.page.update()
            
            await asyncio.sleep(0.1)  # Brief pause for right card to appear
            
            # Step 2: Move current center to left (if exists) - happens simultaneously with right card
            if self.center_card and self.center_card.message:
                # Update left card with current center message
                if self.left_card:
                    self.left_card.update_message(
                        self.center_card.message,
                        self.center_card.user,
                        self.center_card.error
                    )
                # Animate center card to left position
                self.center_card.update_position("left")
                if self.page:
                    self.page.update()
            
            await asyncio.sleep(0.2)  # Wait for left animation
            
            # Step 3: Move right card to center (animated) - smoother transition
            if self.right_card:
                self.right_card.update_position("center")
                if self.page:
                    self.page.update()
                await asyncio.sleep(0.2)  # Wait for animation
            
            # Step 4: Update center card to show new message (sync with right card)
            if self.center_card:
                self.center_card.update_message(
                    message,
                    user,
                    error,
                    is_existing=is_existing,
                    is_deleted=is_deleted
                )
                self.center_card.update_position("center")
            
            # Step 5: Clear right card for next message
            if self.right_card:
                self.right_card.update_message(None)
                self.right_card.update_position("right")
            
            if self.page:
                self.page.update()
            
            # If message is deleted, wait for user action (5 seconds)
            # The card timer will handle the countdown and callback
            if is_deleted and message:
                self._pending_deleted_message = message
                # Wait for undelete action or timeout (handled by card timer)
                # The card will call _on_undelete_callback when timer expires or user clicks
                await asyncio.sleep(5.5)  # Wait slightly longer than timer to ensure callback is processed
                # If still pending, proceed (timer expired)
                if self._pending_deleted_message == message:
                    self._pending_deleted_message = None
            
            # Clear right card again after deleted message handling
            if self.right_card:
                self.right_card.update_message(None)
                self.right_card.update_position("right")
            
            if self.page:
                self.page.update()
                
        except Exception as ex:
            logger.error(f"Error updating cards: {ex}")
    
    async def handle_error_delay(self):
        """Handle 1.5 second delay for error messages with countdown."""
        await self.show_delay_countdown(1.5, "Error delay")
    
    def get_cards_row(self) -> ft.Row:
        """Get the row containing message cards."""
        return ft.Row([
            self.left_card if self.left_card else MessageCard(position="left"),
            self.center_card if self.center_card else MessageCard(position="center"),
            self.right_card if self.right_card else MessageCard(position="right"),
        ], spacing=theme_manager.spacing_md, expand=True)
    
    def get_progress_column(self) -> ft.Column:
        """Get the column containing progress UI elements."""
        return ft.Column([
            self.estimated_count_text,
            self.stats_text,
            self.delay_countdown_text,
            self.progress_bar,
            self.progress_text,
        ], spacing=10)
    
    async def show_delay_countdown(self, seconds: float, message: str = "Waiting"):
        """Show countdown timer for delay."""
        self.delay_countdown_text.visible = True
        remaining = seconds
        
        while remaining > 0:
            self.delay_countdown_text.value = f"{message}: {remaining:.1f}s"
            if self.page:
                try:
                    self.page.update()
                except:
                    pass
            await asyncio.sleep(0.1)  # Update every 0.1 seconds for smooth countdown
            remaining -= 0.1
        
        self.delay_countdown_text.visible = False
        self.delay_countdown_text.value = ""
        if self.page:
            try:
                self.page.update()
            except:
                pass
    
    def hide_delay_countdown(self):
        """Hide delay countdown."""
        self.delay_countdown_text.visible = False
        self.delay_countdown_text.value = ""
    
    def update_stats(self, estimated: int = 0, fetched: int = 0, errors: int = 0, skipped: int = 0):
        """Update statistics display."""
        stats_parts = []
        if estimated > 0:
            stats_parts.append(f"Estimated: {estimated}")
        if fetched > 0:
            stats_parts.append(f"Fetched: {fetched}")
        if errors > 0:
            stats_parts.append(f"Errors: {errors}")
        if skipped > 0:
            stats_parts.append(f"Skipped: {skipped}")
        
        if stats_parts:
            self.stats_text.value = " | ".join(stats_parts)
            self.stats_text.visible = True
        else:
            self.stats_text.visible = False

