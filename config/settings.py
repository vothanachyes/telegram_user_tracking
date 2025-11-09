"""
Application settings management.
"""

import os
from pathlib import Path
from typing import Optional
import logging

from dotenv import load_dotenv
from database.db_manager import DatabaseManager
from database.models import AppSettings
from utils.constants import (
    DATABASE_PATH, DEFAULT_DOWNLOAD_DIR, PRIMARY_COLOR,
    APP_NAME, APP_VERSION, DEVELOPER_NAME, DEVELOPER_EMAIL, DEVELOPER_CONTACT
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class Settings:
    """Application settings manager."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._db_manager: Optional[DatabaseManager] = None
        self._app_settings: Optional[AppSettings] = None
        self._initialized = True
    
    @property
    def db_manager(self) -> DatabaseManager:
        """Get database manager instance."""
        if self._db_manager is None:
            self._db_manager = DatabaseManager(DATABASE_PATH)
        return self._db_manager
    
    def load_settings(self) -> AppSettings:
        """Load settings from database."""
        self._app_settings = self.db_manager.get_settings()
        
        # In dev mode, check .env for default Telegram API credentials if not set
        # Auto-save to database so subsequent operations can fetch from DB
        settings_updated = False
        
        if not self._app_settings.telegram_api_id:
            dev_api_id = os.getenv("DEV_APP_ID") or os.getenv("APP_ID")
            if dev_api_id:
                self._app_settings.telegram_api_id = dev_api_id
                settings_updated = True
                logger.debug("Loaded DEV_APP_ID from .env and will save to database")
        
        if not self._app_settings.telegram_api_hash:
            dev_api_hash = os.getenv("DEV_APP_HASH") or os.getenv("API_HASH")
            if dev_api_hash:
                self._app_settings.telegram_api_hash = dev_api_hash
                settings_updated = True
                logger.debug("Loaded DEV_APP_HASH from .env and will save to database")
        
        # Auto-save to database if we loaded dev credentials
        if settings_updated:
            try:
                if self.save_settings(self._app_settings):
                    logger.info("Auto-saved dev credentials from .env to database")
                else:
                    logger.warning("Failed to auto-save dev credentials to database")
            except Exception as e:
                logger.error(f"Error auto-saving dev credentials to database: {e}")
        
        return self._app_settings
    
    def save_settings(self, settings: AppSettings) -> bool:
        """Save settings to database."""
        success = self.db_manager.update_settings(settings)
        if success:
            self._app_settings = settings
        return success
    
    @property
    def settings(self) -> AppSettings:
        """Get current settings."""
        if self._app_settings is None:
            self._app_settings = self.load_settings()
        return self._app_settings
    
    # Convenience properties
    
    @property
    def theme(self) -> str:
        """Get current theme."""
        return self.settings.theme
    
    @property
    def language(self) -> str:
        """Get current language."""
        return self.settings.language
    
    @property
    def corner_radius(self) -> int:
        """Get corner radius."""
        return self.settings.corner_radius
    
    @property
    def download_root_dir(self) -> str:
        """Get download root directory."""
        return self.settings.download_root_dir
    
    @property
    def telegram_api_id(self) -> Optional[str]:
        """Get Telegram API ID."""
        return self.settings.telegram_api_id
    
    @property
    def telegram_api_hash(self) -> Optional[str]:
        """Get Telegram API Hash."""
        return self.settings.telegram_api_hash
    
    @property
    def has_telegram_credentials(self) -> bool:
        """Check if Telegram API credentials are configured."""
        return bool(self.telegram_api_id and self.telegram_api_hash)
    
    # Application info
    
    @property
    def app_name(self) -> str:
        return APP_NAME
    
    @property
    def app_version(self) -> str:
        return APP_VERSION
    
    @property
    def developer_name(self) -> str:
        return DEVELOPER_NAME
    
    @property
    def developer_email(self) -> str:
        return DEVELOPER_EMAIL
    
    @property
    def developer_contact(self) -> str:
        return DEVELOPER_CONTACT
    
    @property
    def primary_color(self) -> str:
        return PRIMARY_COLOR


# Global settings instance
settings = Settings()

