"""
Fetch data dialog for fetching messages from Telegram.
"""

import flet as ft
from typing import Callable, Optional, Tuple
from datetime import datetime, timedelta
from ui.theme import theme_manager
from ui.dialogs import dialog_manager
from database.db_manager import DatabaseManager
from services.telegram import TelegramService
from services.license_service import LicenseService
import asyncio
import logging

logger = logging.getLogger(__name__)


class FetchDataDialog(ft.AlertDialog):
    """Dialog for fetching data from Telegram."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        telegram_service: TelegramService,
        on_fetch_complete: Optional[Callable] = None
    ):
        self.db_manager = db_manager
        self.telegram_service = telegram_service
        self.on_fetch_complete_callback = on_fetch_complete
        self.license_service = LicenseService(db_manager)
        
        # Default date range (last 30 days)
        today = datetime.now()
        last_month = today - timedelta(days=30)
        
        # Group ID input
        self.group_id_field = ft.TextField(
            label=theme_manager.t("group_id"),
            hint_text="e.g., -1001234567890",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=theme_manager.corner_radius,
            expand=True
        )
        
        # Date inputs
        self.start_date_field = ft.TextField(
            label=theme_manager.t("start_date"),
            hint_text="YYYY-MM-DD",
            value=last_month.strftime("%Y-%m-%d"),
            border_radius=theme_manager.corner_radius,
            expand=True
        )
        
        self.end_date_field = ft.TextField(
            label=theme_manager.t("end_date"),
            hint_text="YYYY-MM-DD",
            value=today.strftime("%Y-%m-%d"),
            border_radius=theme_manager.corner_radius,
            expand=True
        )
        
        # Progress indicator
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
        
        # Status text
        self.status_text = ft.Text(
            "",
            size=14,
            color=theme_manager.text_secondary_color,
            visible=False
        )
        
        # Create the dialog content
        super().__init__(
            modal=True,
            title=ft.Text(theme_manager.t("fetch_telegram_data")),
            content=self._build_content(),
            actions=[
                ft.TextButton(
                    theme_manager.t("cancel"),
                    on_click=self._close_dialog
                ),
                ft.ElevatedButton(
                    theme_manager.t("start_fetch"),
                    on_click=self._start_fetch,
                    icon=ft.Icons.PLAY_ARROW,
                    bgcolor=theme_manager.primary_color,
                    color=ft.Colors.WHITE
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _build_content(self) -> ft.Container:
        """Build the dialog content."""
        
        # Info card
        info_card = theme_manager.create_card(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=theme_manager.primary_color, size=20),
                    ft.Text(
                        theme_manager.t("fetch_info"),
                        size=14,
                        color=theme_manager.text_secondary_color,
                    )
                ], spacing=10),
                ft.Text(
                    "• Make sure you're authorized with Telegram\n"
                    "• Enter the group ID (e.g., -1001234567890)\n"
                    "• Select date range to fetch messages",
                    size=12,
                    color=theme_manager.text_secondary_color,
                )
            ], spacing=10)
        )
        
        # Input section
        input_section = ft.Column([
            ft.Text(
                theme_manager.t("fetch_parameters"),
                size=16,
                weight=ft.FontWeight.BOLD
            ),
            ft.Container(height=5),
            self.group_id_field,
            ft.Row([
                self.start_date_field,
                self.end_date_field,
            ], spacing=10),
        ], spacing=10)
        
        # Progress section
        progress_section = ft.Column([
            self.progress_bar,
            self.progress_text,
            self.status_text,
        ], spacing=10)
        
        return ft.Container(
            content=ft.Column(
                [
                    info_card,
                    ft.Container(height=10),
                    input_section,
                    ft.Container(height=10),
                    progress_section,
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=550,
            padding=10,
        )
    
    def _validate_inputs(self) -> Tuple[bool, Optional[str]]:
        """Validate user inputs."""
        # Validate group ID
        if not self.group_id_field.value or not self.group_id_field.value.strip():
            return False, theme_manager.t("group_id_required")
        
        try:
            group_id = int(self.group_id_field.value.strip())
        except ValueError:
            return False, theme_manager.t("invalid_group_id")
        
        # Validate dates
        try:
            start_date_str = self.start_date_field.value.strip()
            end_date_str = self.end_date_field.value.strip()
            
            if not start_date_str or not end_date_str:
                return False, theme_manager.t("dates_required")
            
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            
            if start_date > end_date:
                return False, theme_manager.t("invalid_date_range")
            
        except ValueError:
            return False, theme_manager.t("invalid_date_format")
        
        return True, None
    
    def _close_dialog(self, e):
        """Close the dialog."""
        self.open = False
        if self.page:
            self.page.update()
    
    def _show_upgrade_dialog(self, error_message: str):
        """Show upgrade dialog when group limit is reached."""
        def contact_admin(e):
            self.open = False
            if self.page:
                self.page.update()
                # Navigate to about page (this requires access to app's navigation)
                # For now, just show contact info
                try:
                    from config.settings import settings
                    import webbrowser
                    from urllib.parse import quote
                    email_url = f"mailto:{settings.developer_email}?subject={quote('License Upgrade Request')}&body={quote('I would like to upgrade my subscription.')}"
                    webbrowser.open(email_url)
                except Exception as ex:
                    from config.settings import settings
                    theme_manager.show_snackbar(
                        self.page,
                        f"Please contact admin: {settings.developer_email}",
                        bgcolor=theme_manager.info_color
                    )
        
        # Create custom content
        content = ft.Column([
            ft.Text(error_message, size=14),
            ft.Container(height=10),
            ft.Text(
                theme_manager.t("contact_admin_to_upgrade"),
                size=12,
                color=theme_manager.text_secondary_color
            )
        ], tight=True, scroll=ft.ScrollMode.AUTO)
        
        # Create actions - close button will restore main dialog automatically
        actions = [
            ft.TextButton(theme_manager.t("close")),  # Will restore main dialog on click
            ft.ElevatedButton(
                theme_manager.t("contact_admin"),
                on_click=contact_admin,  # Will restore main dialog then call contact_admin
                bgcolor=theme_manager.primary_color,
                color=ft.Colors.WHITE
            )
        ]
        
        # Show custom dialog using centralized manager
        dialog_manager.show_custom_dialog(
            page=self.page,
            title=theme_manager.t("upgrade_required"),
            content=content,
            actions=actions,
            main_dialog=self  # This is nested, so restore main dialog
        )
    
    def _start_fetch(self, e):
        """Start fetching data from Telegram."""
        logger.info("=== START FETCH CLICKED ===")
        logger.info(f"Page reference available: {self.page is not None}")
        
        # Validate inputs
        is_valid, error_msg = self._validate_inputs()
        if not is_valid:
            logger.warning(f"Validation failed: {error_msg}")
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    error_msg,
                    bgcolor=ft.Colors.RED
                )
            return
        
        # Check license - can user add more groups?
        can_add, license_error = self.license_service.can_add_group()
        if not can_add:
            logger.warning(f"License check failed: {license_error}")
            if self.page:
                self._show_upgrade_dialog(license_error)
            return
        
        logger.info("Validation passed, checking Telegram connection...")
        
        # Check if Telegram is connected
        if not self.telegram_service.is_connected():
            logger.warning("Telegram not connected, attempting to load session...")
            # Try to auto-load session first
            if self.page and hasattr(self.page, 'run_task'):
                self.page.run_task(self._try_connect_and_fetch)
            else:
                asyncio.create_task(self._try_connect_and_fetch())
            return
        
        logger.info("Telegram connected, starting fetch...")
        
        # Disable inputs during fetch
        self.group_id_field.disabled = True
        self.start_date_field.disabled = True
        self.end_date_field.disabled = True
        
        # Show progress
        self.progress_bar.visible = True
        self.progress_text.visible = True
        self.status_text.visible = True
        self.status_text.value = theme_manager.t("fetching_messages")
        
        # Update UI
        if self.page:
            self.page.update()
        
        # Start async fetch using page's run_task if available
        if self.page and hasattr(self.page, 'run_task'):
            self.page.run_task(self._fetch_messages_async)
        else:
            # Fallback to creating task directly
            asyncio.create_task(self._fetch_messages_async())
    
    async def _try_connect_and_fetch(self):
        """Try to connect to Telegram and then fetch."""
        try:
            # Show status
            self.status_text.visible = True
            self.status_text.value = "Connecting to Telegram..."
            self.status_text.color = theme_manager.text_secondary_color
            if self.page:
                self.page.update()
            
            # Try to auto-load session
            success, error = await self.telegram_service.auto_load_session()
            
            if success:
                logger.info("Session loaded successfully, proceeding with fetch")
                # Now start the fetch
                await self._fetch_messages_async()
            else:
                # Show helpful error message
                error_msg = (
                    f"Not connected to Telegram. {error}\n\n"
                    "Please ensure:\n"
                    "• Telegram API credentials are configured in Settings\n"
                    "• You have authorized the app with Telegram\n"
                    "• Your session is still valid"
                )
                self.status_text.value = error_msg
                self.status_text.color = ft.Colors.RED
                
                if self.page:
                    theme_manager.show_snackbar(
                        self.page,
                        f"Not connected to Telegram: {error}",
                        bgcolor=ft.Colors.RED
                    )
                    self.page.update()
        except Exception as ex:
            logger.error(f"Error trying to connect: {ex}")
            error_msg = f"Error connecting to Telegram: {str(ex)}"
            self.status_text.value = error_msg
            self.status_text.color = ft.Colors.RED
            
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    error_msg,
                    bgcolor=ft.Colors.RED
                )
                self.page.update()
    
    async def _fetch_messages_async(self):
        """Async method to fetch messages."""
        try:
            # Double-check connection before fetching
            if not self.telegram_service.is_connected():
                error_msg = "Not connected to Telegram. Please connect first."
                self.status_text.value = error_msg
                self.status_text.color = ft.Colors.RED
                
                # Re-enable inputs
                self.group_id_field.disabled = False
                self.start_date_field.disabled = False
                self.end_date_field.disabled = False
                self.progress_bar.visible = False
                
                if self.page:
                    theme_manager.show_snackbar(
                        self.page,
                        error_msg,
                        bgcolor=ft.Colors.RED
                    )
                    self.page.update()
                return
            
            group_id = int(self.group_id_field.value.strip())
            start_date = datetime.strptime(self.start_date_field.value.strip(), "%Y-%m-%d")
            end_date = datetime.strptime(self.end_date_field.value.strip(), "%Y-%m-%d")
            
            # Disable inputs during fetch
            self.group_id_field.disabled = True
            self.start_date_field.disabled = True
            self.end_date_field.disabled = True
            
            # Show progress
            self.progress_bar.visible = True
            self.progress_text.visible = True
            self.status_text.visible = True
            self.status_text.value = theme_manager.t("fetching_messages")
            self.status_text.color = theme_manager.text_secondary_color
            
            if self.page:
                self.page.update()
            
            # Progress callback
            def on_progress(current: int, total: int):
                self.progress_text.value = f"{theme_manager.t('messages_fetched')}: {current}"
                if self.page:
                    try:
                        self.page.update()
                    except:
                        pass
            
            # Fetch messages
            success, message_count, error = await self.telegram_service.fetch_messages(
                group_id=group_id,
                start_date=start_date,
                end_date=end_date,
                progress_callback=on_progress
            )
            
            if success:
                self.status_text.value = f"{theme_manager.t('fetch_complete')}: {message_count} {theme_manager.t('messages')}"
                self.status_text.color = ft.Colors.GREEN
                
                if self.page:
                    theme_manager.show_snackbar(
                        self.page,
                        f"{theme_manager.t('successfully_fetched')} {message_count} {theme_manager.t('messages')}",
                        bgcolor=ft.Colors.GREEN
                    )
                    
                # Call completion callback
                if self.on_fetch_complete_callback:
                    self.on_fetch_complete_callback()
                
                # Close dialog after a delay
                await asyncio.sleep(2)
                self._close_dialog(None)
            else:
                self.status_text.value = f"{theme_manager.t('fetch_error')}: {error}"
                self.status_text.color = ft.Colors.RED
                
                if self.page:
                    theme_manager.show_snackbar(
                        self.page,
                        f"{theme_manager.t('fetch_error')}: {error}",
                        bgcolor=ft.Colors.RED
                    )
            
            # Re-enable inputs
            self.group_id_field.disabled = False
            self.start_date_field.disabled = False
            self.end_date_field.disabled = False
            self.progress_bar.visible = False
            
            if self.page:
                self.page.update()
            
        except Exception as ex:
            logger.error(f"Error in fetch dialog: {ex}")
            self.status_text.value = f"{theme_manager.t('fetch_error')}: {str(ex)}"
            self.status_text.color = ft.Colors.RED
            
            # Re-enable inputs
            self.group_id_field.disabled = False
            self.start_date_field.disabled = False
            self.end_date_field.disabled = False
            self.progress_bar.visible = False
            
            if self.page:
                theme_manager.show_snackbar(
                    self.page,
                    f"{theme_manager.t('fetch_error')}: {str(ex)}",
                    bgcolor=ft.Colors.RED
                )
                self.page.update()

