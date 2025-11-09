"""
Main settings handlers facade - combines all handler mixins.
"""

import logging
from typing import Optional, Callable
import flet as ft
from database.models import AppSettings
from ui.dialogs.qr_code_dialog import QRCodeDialog
from ui.pages.settings.handlers.authentication import AuthenticationHandlerMixin
from ui.pages.settings.handlers.account import AccountHandlerMixin
from ui.pages.settings.handlers.configuration import ConfigurationHandlerMixin

logger = logging.getLogger(__name__)


class SettingsHandlers(
    AuthenticationHandlerMixin,
    AccountHandlerMixin,
    ConfigurationHandlerMixin
):
    """Event handlers for settings page - combines all handler mixins."""
    
    def __init__(
        self,
        page: Optional[ft.Page],
        telegram_service,
        db_manager,
        current_settings: AppSettings,
        on_settings_changed: Callable[[], None],
        authenticate_tab
    ):
        self.page = page
        self.telegram_service = telegram_service
        self.db_manager = db_manager
        self.current_settings = current_settings
        self.on_settings_changed = on_settings_changed
        self.authenticate_tab = authenticate_tab
        
        # Track authentication state
        import threading
        self._auth_event = threading.Event()
        self._auth_result: Optional[str] = None
        
        # Track QR code dialog state
        self._qr_dialog: Optional[QRCodeDialog] = None
        self._qr_cancelled = False
        self._qr_token: Optional[str] = None
        
        # Track OTP input state
        self._otp_event: Optional[threading.Event] = None
        self._otp_value_container: Optional[dict] = None
        self._waiting_for_otp = False

