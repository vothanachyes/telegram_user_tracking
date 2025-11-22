"""
Main fetch data page orchestration.
"""

import flet as ft
import asyncio
import logging
from typing import Optional
from datetime import datetime
from ui.theme import theme_manager
from database.db_manager import DatabaseManager
from services.telegram import TelegramService
from services.fetch_state_manager import fetch_state_manager
from ui.pages.fetch_data.view_model import FetchViewModel
from ui.pages.fetch_data.handlers import FetchHandlers
from ui.pages.fetch_data.progress_ui import ProgressUI
from ui.pages.fetch_data.summary_ui import SummaryUI
from ui.dialogs.rate_limit_warning_dialog import RateLimitWarningDialog
from ui.dialogs.fetch_configure_dialog import FetchConfigureDialog
from services.license_service import LicenseService
from config.settings import settings as app_settings
from config.app_config import app_config

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
        
        # Timeout monitoring
        self._last_update_time: Optional[datetime] = None
        self._timeout_task: Optional[asyncio.Task] = None
        self._fetch_task: Optional[asyncio.Task] = None
        self._is_fetch_stopped = False
        
        # Start button reference for styling
        self.start_button: Optional[ft.ElevatedButton] = None
        
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
        
        # Sync local view_model with global state if fetch is in progress
        if fetch_state_manager.is_fetching:
            global_state = fetch_state_manager.get_state()
            self.view_model.is_fetching = global_state['is_fetching']
            self.view_model.processed_count = global_state['processed_count']
            self.view_model.error_count = global_state['error_count']
            self.view_model.skipped_count = global_state['skipped_count']
            self.view_model.estimated_total = global_state['estimated_total']
            
            # Show progress UI if fetch is in progress
            if global_state['processed_count'] > 0:
                self.progress_ui.show_progress()
                self.progress_ui.update_progress_text(
                    f"{theme_manager.t('messages_fetched') or 'Messages fetched'}: {global_state['processed_count']}"
                )
                self.progress_ui.update_stats(
                    estimated=global_state['estimated_total'],
                    fetched=global_state['processed_count'],
                    errors=global_state['error_count'],
                    skipped=global_state['skipped_count']
                )
        
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
    
    def _create_start_button(self) -> ft.ElevatedButton:
        """Create start button with proper styling for disabled state."""
        is_sample_mode = app_config.is_sample_db_mode()
        self.start_button = ft.ElevatedButton(
            theme_manager.t("start_fetch") or "Start Fetch",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._on_start_fetch,
            bgcolor=theme_manager.primary_color,
            color=ft.Colors.WHITE,
            disabled=fetch_state_manager.is_fetching or self.view_model.is_fetching or is_sample_mode
        )
        return self.start_button
    
    def _update_start_button_style(self):
        """Update start button style based on disabled state and theme."""
        if self.start_button:
            if self.start_button.disabled:
                # Gray when disabled, aware of dark/light mode
                if theme_manager.is_dark:
                    self.start_button.bgcolor = ft.Colors.GREY_800
                else:
                    self.start_button.bgcolor = ft.Colors.GREY_400
            else:
                self.start_button.bgcolor = theme_manager.primary_color
    
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
            
            # Sample DB mode info
            ft.Container(
                content=ft.Text(
                    "Fetching data is disabled in sample database mode.",
                    size=12,
                    color=theme_manager.text_secondary_color,
                    visible=app_config.is_sample_db_mode()
                ),
                visible=app_config.is_sample_db_mode(),
                padding=10
            ) if app_config.is_sample_db_mode() else ft.Container(),
            
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
            ft.Row([
                self._create_start_button(),
                ft.ElevatedButton(
                    theme_manager.t("configure") or "Configure",
                    icon=ft.Icons.SETTINGS,
                    on_click=self._on_configure_click,
                    bgcolor=theme_manager.surface_color,
                    color=theme_manager.text_color,
                ),
                ft.ProgressRing(
                    width=20,
                    height=20,
                    stroke_width=2,
                    visible=fetch_state_manager.is_fetching or self.view_model.is_fetching
                ),
            ], spacing=5, tight=True),
            self.summary_ui.finish_button,
        ], spacing=10),
            
        ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def _on_configure_click(self, e):
        """Handle configure button click."""
        if not self.page:
            return
        
        try:
            current_settings = app_settings.load_settings()
            dialog = FetchConfigureDialog(current_settings)
            dialog.page = self.page
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening configure dialog: {ex}")
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    "Failed to open configure dialog",
                    bgcolor=ft.Colors.RED
                )
    
    def _on_start_fetch(self, e):
        """Handle start fetch button click."""
        # Prevent multiple clicks
        if fetch_state_manager.is_fetching or self.view_model.is_fetching:
            return
        
        # Reset stop flag
        self._is_fetch_stopped = False
        
        # Disable button immediately (will be re-enabled when fetch completes)
        if self.start_button:
            self.start_button.disabled = True
            self._update_start_button_style()
        if self.page:
            self.page.update()
        
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
        # Get group info for global state
        group_id = self.handlers.group_selector.get_selected_group_id()
        group_name = None
        if group_id:
            group = self.db_manager.get_group_by_id(group_id)
            if group:
                group_name = group.group_name
        
        # Start global fetch state
        fetch_state_manager.start_fetch(group_id=group_id, group_name=group_name)
        
        # Reset local view model (keep UI-specific state separate)
        self.view_model.reset()
        self._is_fetch_stopped = False
        
        # Sync local view_model with global state
        self.view_model.is_fetching = True
        self.view_model.estimated_total = 0
        
        # Show progress
        self.progress_ui.show_progress()
        
        # Hide summary and finish button
        self.summary_ui.hide_summary()
        
        # Clear cards
        self.progress_ui.clear_cards()
        
        # Update last update time
        self._last_update_time = datetime.now()
        
        # Start timeout monitoring
        self._timeout_task = asyncio.create_task(self._monitor_timeout())
        
        # Estimate message count (quick scan - sample first 100 messages in range)
        estimated_count = await self._estimate_message_count()
        self.view_model.estimated_total = estimated_count
        fetch_state_manager.update_progress(estimated_total=estimated_count)
        
        if estimated_count > 0:
            self.progress_ui.estimated_count_text.value = f"Estimated messages in range: {estimated_count} (exact total not available)"
            self.progress_ui.estimated_count_text.visible = True
        else:
            self.progress_ui.estimated_count_text.value = "Note: Exact total message count is not available upfront"
            self.progress_ui.estimated_count_text.visible = True
        
        # Show initial stats
        self.progress_ui.update_stats(estimated=estimated_count)
        
        if self.page:
            self.page.update()
        
        # Progress callback
        def on_progress(current: int, total: int):
            # Update last update time for timeout monitoring
            self._last_update_time = datetime.now()
            
            # Update global state
            fetch_state_manager.update_progress(processed_count=current)
            
            # Sync local view_model
            self.view_model.processed_count = current
            
            self.progress_ui.update_progress_text(
                f"{theme_manager.t('messages_fetched') or 'Messages fetched'}: {current}"
            )
            # Update stats during fetch
            self.progress_ui.update_stats(
                estimated=self.view_model.estimated_total,
                fetched=current,
                errors=self.view_model.error_count,
                skipped=self.view_model.skipped_count
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
                # Check if fetch was stopped
                if self._is_fetch_stopped:
                    return
                
                # Update last update time for timeout monitoring
                self._last_update_time = datetime.now()
                
                # Add to view model
                self.view_model.add_message(message, user, error)
                
                # Update global state
                if error:
                    fetch_state_manager.increment_error()
                else:
                    fetch_state_manager.increment_processed()
                
                # Sync local view_model with global state
                global_state = fetch_state_manager.get_state()
                self.view_model.processed_count = global_state['processed_count']
                self.view_model.error_count = global_state['error_count']
                
                # Update stats in real-time
                self.progress_ui.update_stats(
                    estimated=self.view_model.estimated_total,
                    fetched=self.view_model.processed_count,
                    errors=self.view_model.error_count,
                    skipped=self.view_model.skipped_count
                )
                
                # Update summary table in real-time
                self.summary_ui.update_summary_realtime()
                
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
        
        # Delay callback for countdown display
        async def on_delay(seconds: float, message: str):
            """Handle delay with countdown display."""
            await self.progress_ui.show_delay_countdown(seconds, message)
        
        # Start fetch
        try:
            self._fetch_task = asyncio.create_task(
                self.handlers.start_fetch(
                    on_progress=on_progress,
                    on_message=on_message,
                    on_delay=on_delay
                )
            )
            result = await self._fetch_task
        except asyncio.CancelledError:
            # Fetch was cancelled (timeout or user action)
            result = (False, 0, "Fetch operation was stopped", 0)
        except Exception as e:
            logger.error(f"Error during fetch: {e}")
            result = (False, 0, str(e), 0)
        finally:
            # Cancel timeout monitoring
            if self._timeout_task and not self._timeout_task.done():
                self._timeout_task.cancel()
        
        # Handle both old (3-tuple) and new (4-tuple) return formats
        if len(result) == 3:
            success, message_count, error = result
            skipped_count = 0
        else:
            success, message_count, error, skipped_count = result
        
        # Update global state with skipped count
        fetch_state_manager.update_progress(skipped_count=skipped_count)
        self.view_model.skipped_count = skipped_count
        
        # Stop global fetch state
        fetch_state_manager.stop_fetch()
        
        # Update UI after fetch
        if success:
            # Build stats text
            stats_parts = [f"Fetched: {message_count}"]
            if self.view_model.error_count > 0:
                stats_parts.append(f"Errors: {self.view_model.error_count}")
            if skipped_count > 0:
                stats_parts.append(f"Skipped: {skipped_count}")
            stats_text = " | ".join(stats_parts)
            
            self.progress_ui.update_progress_text(
                f"{theme_manager.t('fetch_complete') or 'Fetch complete'}: {stats_text}",
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
        
        # Re-enable sidebar navigation
        self._enable_sidebar()
        
        # Re-enable start button
        if self.start_button:
            self.start_button.disabled = False
            self._update_start_button_style()
        
        # Update global state
        fetch_state_manager.stop_fetch()
        
        if self.page:
            self.page.update()
    
    async def _monitor_timeout(self):
        """Monitor for timeout (30 seconds without update)."""
        try:
            while fetch_state_manager.is_fetching and not self._is_fetch_stopped:
                await asyncio.sleep(1)  # Check every second
                
                if self._last_update_time:
                    elapsed = (datetime.now() - self._last_update_time).total_seconds()
                    if elapsed >= 30:
                        # Timeout - force stop
                        logger.warning("Fetch timeout: No update for 30 seconds")
                        self._is_fetch_stopped = True
                        self.view_model.is_fetching = False
                        fetch_state_manager.stop_fetch()
                        
                        # Cancel fetch task if running
                        if self._fetch_task and not self._fetch_task.done():
                            self._fetch_task.cancel()
                        
                        # Show error toast
                        if self.page:
                            theme_manager.show_snackbar(
                                self.page,
                                "There is something wrong - fetch operation stopped due to timeout",
                                bgcolor=ft.Colors.RED
                            )
                        
                        # Re-enable sidebar navigation
                        self._enable_sidebar()
                        
                        # Re-enable start button
                        if self.start_button:
                            self.start_button.disabled = False
                            self._update_start_button_style()
                        
                        # Hide progress
                        self.progress_ui.hide_progress()
                        
                        if self.page:
                            self.page.update()
                        
                        break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in timeout monitoring: {e}")
    
    async def _estimate_message_count(self) -> int:
        """Estimate total message count in date range (quick scan)."""
        try:
            # Get date range from handlers
            start_date_str = self.handlers.start_date_field.value.strip()
            end_date_str = self.handlers.end_date_field.value.strip()
            
            if not start_date_str or not end_date_str:
                return 0
            
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            
            # Get group ID
            group_id = self.handlers.group_selector.get_selected_group_id()
            if not group_id:
                return 0
            
            # Quick estimation: Count messages in database first (if any exist)
            # Then do a quick scan of first 100 messages to estimate rate
            # This is a rough estimate, not exact
            try:
                # Count existing messages in range from database
                existing_count = len(self.db_manager.get_messages(
                    group_id=group_id,
                    start_date=start_date,
                    end_date=end_date,
                    limit=1000  # Sample up to 1000
                ))
                
                # If we have existing messages, use that as baseline
                # Otherwise, do a quick scan (sample first 50 messages to estimate rate)
                if existing_count > 0:
                    # Rough estimate: assume we've fetched some, estimate total is higher
                    return max(existing_count, 50)  # At least 50
                else:
                    # No existing messages, return 0 (will be updated during fetch)
                    return 0
            except Exception as e:
                logger.debug(f"Error estimating from database: {e}")
                return 0
                
        except Exception as e:
            logger.debug(f"Error estimating message count: {e}")
            return 0
    
    def _on_finish_click(self, e):
        """Handle finish button click - reset page to initial state."""
        # Stop any ongoing fetch
        self._is_fetch_stopped = True
        self.view_model.is_fetching = False
        fetch_state_manager.stop_fetch()
        fetch_state_manager.reset()
        
        # Cancel tasks
        if self._fetch_task and not self._fetch_task.done():
            self._fetch_task.cancel()
        if self._timeout_task and not self._timeout_task.done():
            self._timeout_task.cancel()
        
        # Reset view model (clears all data)
        self.view_model.reset()
        
        # Clear cards
        self.progress_ui.clear_cards()
        
        # Hide summary and finish button
        self.summary_ui.hide_summary()
        
        # Hide progress
        self.progress_ui.hide_progress()
        self.progress_ui.estimated_count_text.visible = False
        self.progress_ui.progress_text.value = ""
        self.progress_ui.stats_text.value = ""
        self.progress_ui.stats_text.visible = False
        
        # Reset form fields
        self.handlers.start_date_field.disabled = False
        self.handlers.end_date_field.disabled = False
        self.handlers.account_selector.enable()
        self.handlers.group_selector.enable()
        
        # Re-enable start button
        if self.start_button:
            self.start_button.disabled = False
            self._update_start_button_style()
        
        # Reset timeout tracking
        self._last_update_time = None
        
        # Re-enable sidebar navigation
        self._enable_sidebar()
        
        if self.page:
            self.page.update()
    
    def _disable_sidebar(self):
        """Disable sidebar navigation during fetch."""
        if self.page and hasattr(self.page, 'data') and self.page.data:
            router = self.page.data.get('router')
            if router and router.sidebar:
                router.sidebar.set_fetching_state(True)
    
    def _enable_sidebar(self):
        """Enable sidebar navigation after fetch."""
        if self.page and hasattr(self.page, 'data') and self.page.data:
            router = self.page.data.get('router')
            if router and router.sidebar:
                router.sidebar.set_fetching_state(False)

