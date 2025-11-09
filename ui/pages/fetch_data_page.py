"""
Fetch data page with animated message cards and real-time progress.
"""

import flet as ft
import asyncio
import logging
from typing import Optional
from ui.theme import theme_manager
from database.db_manager import DatabaseManager
from services.telegram import TelegramService
from ui.pages.fetch_data.view_model import FetchViewModel
from ui.pages.fetch_data.components import MessageCard, SummaryTable
from ui.pages.fetch_data.handlers import FetchHandlers

logger = logging.getLogger(__name__)


class FetchDataPage(ft.Container):
    """Page for fetching Telegram data with animated message cards."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        telegram_service: TelegramService
    ):
        self.db_manager = db_manager
        self.telegram_service = telegram_service
        self.page: Optional[ft.Page] = None
        
        # Initialize view model and handlers
        self.view_model = FetchViewModel()
        self.handlers = FetchHandlers(
            db_manager=db_manager,
            telegram_service=telegram_service,
            view_model=self.view_model
        )
        
        # UI components
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
        
        # Message cards (3-card carousel)
        self.left_card = MessageCard(position="left")
        self.center_card = MessageCard(position="center")
        self.right_card = MessageCard(position="right")
        
        # Summary table (hidden initially)
        self.summary_table_container = ft.Container(
            visible=False,
            content=None
        )
        
        # Finish button (hidden initially)
        self.finish_button = ft.ElevatedButton(
            theme_manager.t("finish") or "Finish",
            icon=ft.Icons.CHECK_CIRCLE,
            on_click=self._on_finish_click,
            bgcolor=theme_manager.primary_color,
            color=ft.Colors.WHITE,
            visible=False
        )
        
        # Build UI
        super().__init__(
            content=self._build_content(),
            padding=theme_manager.padding_lg,
            expand=True
        )
    
    def set_page(self, page: ft.Page):
        """Set page reference and initialize handlers."""
        self.page = page
        self.handlers.set_page(page)
    
    def _build_content(self) -> ft.Column:
        """Build page content."""
        return ft.Column([
            # Header
            ft.Row([
                ft.Icon(ft.Icons.DOWNLOAD, size=theme_manager.font_size_page_title, color=theme_manager.primary_color),
                ft.Text(
                    theme_manager.t("fetch_telegram_data") or "Fetch Telegram Data",
                    size=theme_manager.font_size_page_title,
                    weight=ft.FontWeight.BOLD
                )
            ], spacing=theme_manager.spacing_sm),
            
            # Info card
            theme_manager.create_card(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE, color=theme_manager.primary_color, size=20),
                        ft.Text(
                            theme_manager.t("fetch_info") or "Fetch Information",
                            size=14,
                            color=theme_manager.text_secondary_color,
                        )
                    ], spacing=10),
                    ft.Text(
                        "• Make sure you're authorized with Telegram\n"
                        "• Select account and group\n"
                        "• Select date range to fetch messages",
                        size=12,
                        color=theme_manager.text_secondary_color,
                    )
                ], spacing=10)
            ),
            
            ft.Container(height=20),
            
            # Input section
            ft.Column([
                ft.Text(
                    theme_manager.t("fetch_parameters") or "Fetch Parameters",
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(height=10),
                self.handlers.account_selector.build(),
                ft.Container(height=10),
                self.handlers.group_selector.build(),
                ft.Container(height=10),
                ft.Row([
                    self.handlers.start_date_field,
                    self.handlers.end_date_field,
                ], spacing=10),
            ], spacing=10),
            
            ft.Container(height=20),
            
            # Progress section
            ft.Column([
                self.estimated_count_text,
                self.progress_bar,
                self.progress_text,
            ], spacing=10),
            
            ft.Container(height=20),
            
            # Animated message cards section
            ft.Column([
                ft.Text(
                    "Messages",
                    size=18,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(height=10),
                ft.Row([
                    self.left_card,
                    self.center_card,
                    self.right_card,
                ], spacing=20, alignment=ft.MainAxisAlignment.CENTER),
            ], spacing=10),
            
            ft.Container(height=20),
            
            # Summary table
            self.summary_table_container,
            
            ft.Container(height=10),
            
            # Action buttons
            ft.Row([
                ft.ElevatedButton(
                    theme_manager.t("start_fetch") or "Start Fetch",
                    icon=ft.Icons.PLAY_ARROW,
                    on_click=self._on_start_fetch,
                    bgcolor=theme_manager.primary_color,
                    color=ft.Colors.WHITE,
                    disabled=self.view_model.is_fetching
                ),
                self.finish_button,
            ], spacing=10),
            
        ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def _on_start_fetch(self, e):
        """Handle start fetch button click."""
        if self.view_model.is_fetching:
            return
        
        if self.page and hasattr(self.page, 'run_task'):
            self.page.run_task(self._fetch_async)
        else:
            asyncio.create_task(self._fetch_async())
    
    async def _fetch_async(self):
        """Async fetch method."""
        # Reset view model
        self.view_model.reset()
        
        # Show progress
        self.progress_bar.visible = True
        self.progress_text.visible = True
        self.progress_text.value = theme_manager.t("fetching_messages") or "Fetching messages..."
        self.progress_text.color = theme_manager.text_secondary_color
        
        # Hide summary and finish button
        self.summary_table_container.visible = False
        self.finish_button.visible = False
        
        # Clear cards
        self._clear_cards()
        
        if self.page:
            self.page.update()
        
        # Progress callback
        def on_progress(current: int, total: int):
            self.progress_text.value = f"{theme_manager.t('messages_fetched') or 'Messages fetched'}: {current}"
            if self.page:
                try:
                    self.page.update()
                except:
                    pass
        
        # Message callback (synchronous, will be called from async context)
        def on_message(message, user, error):
            """Handle each message during fetch."""
            try:
                # Add to view model
                self.view_model.add_message(message, user, error)
                
                # Schedule card update (async operation)
                if self.page and hasattr(self.page, 'run_task'):
                    self.page.run_task(self._update_cards_animated, message, user, error)
                else:
                    asyncio.create_task(self._update_cards_animated(message, user, error))
                
                # If error, schedule delay
                if error:
                    if self.page and hasattr(self.page, 'run_task'):
                        self.page.run_task(self._handle_error_delay)
                    else:
                        asyncio.create_task(self._handle_error_delay())
                
            except Exception as ex:
                logger.error(f"Error in message callback: {ex}")
        
        # Start fetch
        success, message_count, error = await self.handlers.start_fetch(
            on_progress=on_progress,
            on_message=on_message
        )
        
        # Update UI after fetch
        if success:
            self.progress_text.value = f"{theme_manager.t('fetch_complete') or 'Fetch complete'}: {message_count} {theme_manager.t('messages') or 'messages'}"
            self.progress_text.color = ft.Colors.GREEN
            
            # Show summary table
            await self._show_summary_table()
            
            # Show finish button
            self.finish_button.visible = True
            
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    f"{theme_manager.t('successfully_fetched') or 'Successfully fetched'} {message_count} {theme_manager.t('messages') or 'messages'}",
                    bgcolor=ft.Colors.GREEN
                )
        else:
            self.progress_text.value = f"{theme_manager.t('fetch_error') or 'Fetch error'}: {error}"
            self.progress_text.color = ft.Colors.RED
            
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    f"{theme_manager.t('fetch_error') or 'Fetch error'}: {error}",
                    bgcolor=ft.Colors.RED
                )
        
        # Hide progress bar
        self.progress_bar.visible = False
        
        if self.page:
            self.page.update()
    
    def _clear_cards(self):
        """Clear all message cards."""
        self.left_card.update_message(None)
        self.center_card.update_message(None)
        self.right_card.update_message(None)
    
    async def _update_cards_animated(self, message, user, error):
        """Update cards with animation."""
        try:
            # After add_message, queue is: [previous_left, previous_center, new_message]
            # We want to show: left=previous_center, center=new_message, right=empty
            
            # Step 1: If there was a previous center message, move it to left
            previous_center_msg = self.view_model.message_queue[1]
            if previous_center_msg:
                # Update left card with previous center message
                self.left_card.update_message(
                    previous_center_msg,
                    self.view_model.user_queue[1],
                    self.view_model.error_queue[1]
                )
                self.left_card.update_position("left")
                
                # Animate current center to left (if it exists)
                if self.center_card.message:
                    self.center_card.update_position("left")
                    await asyncio.sleep(0.2)  # Wait for animation
            
            # Step 2: Show new message on right first
            self.right_card.update_message(message, user, error)
            self.right_card.update_position("right")
            
            if self.page:
                self.page.update()
            
            await asyncio.sleep(0.1)  # Brief pause
            
            # Step 3: Move right card to center
            self.right_card.update_position("center")
            
            # Step 4: Update center card to show new message
            self.center_card.update_message(message, user, error)
            self.center_card.update_position("center")
            
            # Step 5: Clear right card for next message
            self.right_card.update_message(None)
            self.right_card.update_position("right")
            
            if self.page:
                self.page.update()
                
        except Exception as ex:
            logger.error(f"Error updating cards: {ex}")
    
    async def _handle_error_delay(self):
        """Handle 1.5 second delay for error messages."""
        await asyncio.sleep(1.5)
    
    async def _show_summary_table(self):
        """Show post-fetch summary table."""
        try:
            summary_data = self.view_model.get_summary_data()
            
            # Build user map
            user_map = {}
            for data in summary_data:
                user_id = data['user_id']
                user = self.db_manager.get_user_by_id(user_id)
                if user:
                    user_map[user_id] = user
            
            # Create summary table
            summary_table = SummaryTable(summary_data, user_map)
            self.summary_table_container.content = summary_table
            self.summary_table_container.visible = True
            
            if self.page:
                self.page.update()
                
        except Exception as ex:
            logger.error(f"Error showing summary table: {ex}")
    
    def _on_finish_click(self, e):
        """Handle finish button click - reset page to initial state."""
        # Reset view model
        self.view_model.reset()
        
        # Clear cards
        self._clear_cards()
        
        # Hide summary and finish button
        self.summary_table_container.visible = False
        self.finish_button.visible = False
        
        # Hide progress
        self.progress_bar.visible = False
        self.progress_text.visible = False
        self.estimated_count_text.visible = False
        
        # Reset form fields
        self.handlers.start_date_field.disabled = False
        self.handlers.end_date_field.disabled = False
        self.handlers.account_selector.enable()
        self.handlers.group_selector.enable()
        
        if self.page:
            self.page.update()

