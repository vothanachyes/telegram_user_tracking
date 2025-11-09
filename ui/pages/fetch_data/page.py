"""
Main fetch data page orchestration.
"""

import flet as ft
import asyncio
import logging
from typing import Optional
from ui.theme import theme_manager
from database.db_manager import DatabaseManager
from services.telegram import TelegramService
from ui.pages.fetch_data.view_model import FetchViewModel
from ui.pages.fetch_data.handlers import FetchHandlers
from ui.pages.fetch_data.progress_ui import ProgressUI
from ui.pages.fetch_data.summary_ui import SummaryUI
from ui.dialogs.rate_limit_warning_dialog import RateLimitWarningDialog
from services.license_service import LicenseService

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
        self.license_service = LicenseService(db_manager)
        
        # Initialize view model and handlers
        self.view_model = FetchViewModel()
        self.handlers = FetchHandlers(
            db_manager=db_manager,
            telegram_service=telegram_service,
            view_model=self.view_model
        )
        
        # License warning banner
        self.license_warning_banner = ft.Container(visible=False)
        
        # Initialize UI components
        self.progress_ui = ProgressUI(
            view_model=self.view_model,
            db_manager=db_manager
        )
        
        self.summary_ui = SummaryUI(
            view_model=self.view_model,
            db_manager=db_manager
        )
        
        # Set finish callback
        self.summary_ui.set_finish_callback(self._on_finish_click)
        
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
        self.progress_ui.set_page(page)
        self.summary_ui.set_page(page)
        
        # Update license warning
        self._update_license_warning()
        
        # Rebuild content to include initialized cards
        self.content = self._build_content()
        if page:
            page.update()
    
    def _update_license_warning(self):
        """Update license warning banner."""
        try:
            # Check if selected group is new (not in database)
            group_id = self.handlers.group_selector.get_selected_group_id()
            is_new_group = False
            if group_id:
                existing_group = self.db_manager.get_group_by_id(group_id)
                is_new_group = existing_group is None
            
            if is_new_group:
                license_info = self.license_service.get_license_info()
                current = license_info.get('current_groups', 0)
                max_groups = license_info.get('max_groups', 0)
                
                if max_groups != -1:  # Not unlimited
                    warning_text = theme_manager.t("new_group_warning") or "This group will be automatically saved when you start fetching."
                    license_text = theme_manager.t("license_group_limit_warning") or f"You have {current}/{max_groups} groups. Your license allows up to {max_groups} groups."
                    
                    self.license_warning_banner.content = theme_manager.create_card(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE, size=20),
                                ft.Text(warning_text, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE, expand=True)
                            ], spacing=10),
                            ft.Text(license_text.format(current=current, max=max_groups), size=12, color=theme_manager.text_secondary_color)
                        ], spacing=5)
                    )
                    self.license_warning_banner.visible = True
                else:
                    self.license_warning_banner.visible = False
            else:
                self.license_warning_banner.visible = False
        except Exception as e:
            logger.error(f"Error updating license warning: {e}")
            self.license_warning_banner.visible = False
    
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
            
            # License warning banner
            self.license_warning_banner,
            
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
            self.progress_ui.get_progress_column(),
            
            ft.Container(height=20),
            
            # Animated message cards section
            ft.Column([
                ft.Text(
                    "Messages",
                    size=18,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(height=10),
                self.progress_ui.get_cards_row(),
            ], spacing=10),
            
            ft.Container(height=20),
            
            # Summary table
            self.summary_ui.summary_table_container,
            
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
                self.summary_ui.finish_button,
            ], spacing=10),
            
        ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def _on_start_fetch(self, e):
        """Handle start fetch button click."""
        if self.view_model.is_fetching:
            return
        
        # Check and show rate limit warning if needed
        if RateLimitWarningDialog.should_show(self.db_manager):
            try:
                dialog = RateLimitWarningDialog(
                    self.db_manager,
                    on_confirm=self._start_fetch_after_warning
                )
                dialog.page = self.page
                if self.page:
                    self.page.open(dialog)
                    return
            except Exception as ex:
                logger.error(f"Error showing rate limit warning: {ex}")
        
        # Start fetch directly if no warning needed
        self._start_fetch_after_warning()
    
    def _start_fetch_after_warning(self):
        """Start fetch after rate limit warning is confirmed."""
        if self.page and hasattr(self.page, 'run_task'):
            self.page.run_task(self._fetch_async)
        else:
            asyncio.create_task(self._fetch_async())
    
    async def _fetch_async(self):
        """Async fetch method."""
        # Reset view model
        self.view_model.reset()
        
        # Show progress
        self.progress_ui.show_progress()
        
        # Hide summary and finish button
        self.summary_ui.hide_summary()
        
        # Clear cards
        self.progress_ui.clear_cards()
        
        if self.page:
            self.page.update()
        
        # Progress callback
        def on_progress(current: int, total: int):
            self.progress_ui.update_progress_text(
                f"{theme_manager.t('messages_fetched') or 'Messages fetched'}: {current}"
            )
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
                    self.page.run_task(
                        self.progress_ui.update_cards_animated,
                        message,
                        user,
                        error
                    )
                else:
                    asyncio.create_task(
                        self.progress_ui.update_cards_animated(message, user, error)
                    )
                
                # If error, schedule delay
                if error:
                    if self.page and hasattr(self.page, 'run_task'):
                        self.page.run_task(self.progress_ui.handle_error_delay)
                    else:
                        asyncio.create_task(self.progress_ui.handle_error_delay())
                
            except Exception as ex:
                logger.error(f"Error in message callback: {ex}")
        
        # Start fetch
        success, message_count, error = await self.handlers.start_fetch(
            on_progress=on_progress,
            on_message=on_message
        )
        
        # Update UI after fetch
        if success:
            self.progress_ui.update_progress_text(
                f"{theme_manager.t('fetch_complete') or 'Fetch complete'}: {message_count} {theme_manager.t('messages') or 'messages'}",
                color=ft.Colors.GREEN
            )
            
            # Show summary table
            await self.summary_ui.display_summary_table()
            
            # Show finish button
            self.summary_ui.show_summary()
            
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    f"{theme_manager.t('successfully_fetched') or 'Successfully fetched'} {message_count} {theme_manager.t('messages') or 'messages'}",
                    bgcolor=ft.Colors.GREEN
                )
        else:
            self.progress_ui.update_progress_text(
                f"{theme_manager.t('fetch_error') or 'Fetch error'}: {error}",
                color=ft.Colors.RED
            )
            
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    f"{theme_manager.t('fetch_error') or 'Fetch error'}: {error}",
                    bgcolor=ft.Colors.RED
                )
        
        # Hide progress bar
        self.progress_ui.hide_progress()
        
        if self.page:
            self.page.update()
    
    def _on_finish_click(self, e):
        """Handle finish button click - reset page to initial state."""
        # Reset view model
        self.view_model.reset()
        
        # Clear cards
        self.progress_ui.clear_cards()
        
        # Hide summary and finish button
        self.summary_ui.hide_summary()
        
        # Hide progress
        self.progress_ui.hide_progress()
        self.progress_ui.estimated_count_text.visible = False
        
        # Reset form fields
        self.handlers.start_date_field.disabled = False
        self.handlers.end_date_field.disabled = False
        self.handlers.account_selector.enable()
        self.handlers.group_selector.enable()
        
        if self.page:
            self.page.update()

