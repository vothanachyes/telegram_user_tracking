"""
Dialog management handlers for settings.
"""

import logging
import time
from typing import Optional
import flet as ft
from ui.dialogs.telegram_auth_dialog import TelegramAuthDialog
from ui.pages.settings.handlers.base import BaseHandlerMixin

logger = logging.getLogger(__name__)


class DialogHandlerMixin(BaseHandlerMixin):
    """Handlers for dialog management."""
    
    def _show_auth_dialog(self, is_2fa: bool = False) -> str:
        """Show authentication dialog and wait for user input."""
        return self._show_auth_dialog_nested(is_2fa=is_2fa, main_dialog=None)
    
    def _show_auth_dialog_nested(self, is_2fa: bool = False, main_dialog: Optional[ft.AlertDialog] = None) -> str:
        """Show authentication dialog and wait for user input, optionally as nested dialog."""
        if not self.page:
            logger.error("No page available for auth dialog")
            return ""
        
        logger.debug(f"Showing auth dialog (2FA: {is_2fa}, nested: {main_dialog is not None})")
        logger.debug(f"Page ID: {getattr(self.page, 'id', 'unknown')}, Page type: {type(self.page)}")
        
        self._auth_event.clear()
        self._auth_result = None
        
        dialog = TelegramAuthDialog(
            is_2fa=is_2fa,
            on_submit=self._on_auth_dialog_submit
        )
        
        dialog.page = self.page
        logger.debug(f"Dialog created, page reference set: {dialog.page is not None}")
        
        try:
            self.page.open(dialog)
            logger.info(f"Auth dialog opened using page.open() (2FA: {is_2fa}, nested: {main_dialog is not None})")
        except (AttributeError, Exception) as e:
            logger.warning(f"page.open() failed ({e}), using page.dialog method")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
            logger.info(f"Auth dialog opened using page.dialog (2FA: {is_2fa})")
        
        time.sleep(0.05)
        
        logger.debug("Waiting for user input in auth dialog...")
        timeout = 300
        start_time = time.time()
        event_set = False
        
        while time.time() - start_time < timeout:
            if self._auth_event.is_set():
                event_set = True
                break
            time.sleep(0.1)
        
        if event_set:
            result = self._auth_result or ""
            logger.debug(f"Auth dialog returned: {'***' if result else '(empty/cancelled)'}")
            
            try:
                if hasattr(self.page, 'close'):
                    self.page.close(dialog)
                    logger.debug("Dialog closed using page.close()")
                else:
                    dialog.open = False
                    if self.page.dialog == dialog:
                        self.page.dialog = None
                    self.page.update()
                    logger.debug("Dialog closed using page.dialog method")
            except Exception as close_error:
                logger.debug(f"Error closing dialog: {close_error}")
                try:
                    dialog.open = False
                    if self.page.dialog == dialog:
                        self.page.dialog = None
                    self.page.update()
                except:
                    pass
            
            if not result and main_dialog:
                try:
                    self.page.open(main_dialog)
                    logger.debug("Restored main dialog after auth dialog cancellation")
                except:
                    self.page.dialog = main_dialog
                    main_dialog.open = True
                    self.page.update()
            
            return result
        
        logger.warning("Auth dialog timed out")
        try:
            if hasattr(self.page, 'close'):
                self.page.close(dialog)
            else:
                dialog.open = False
                if self.page.dialog == dialog:
                    self.page.dialog = None
                self.page.update()
            
            if main_dialog:
                try:
                    self.page.open(main_dialog)
                except:
                    self.page.dialog = main_dialog
                    main_dialog.open = True
                    self.page.update()
        except:
            pass
        return ""
    
    def _on_auth_dialog_submit(self, value: str):
        """Handle authentication dialog submission."""
        self._auth_result = value
        self._auth_event.set()

