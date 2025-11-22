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
    APP_NAME, APP_VERSION, DEVELOPER_NAME, DEVELOPER_EMAIL, DEVELOPER_CONTACT,
    SAMPLE_DATABASE_PATH
)
from config.app_config import app_config

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
            # Check if in sample_db mode first
            if app_config.is_sample_db_mode():
                db_path = SAMPLE_DATABASE_PATH
            else:
                # Use custom path from settings if available, otherwise use default
                db_path = DATABASE_PATH
                if self._app_settings and self._app_settings.db_path:
                    db_path = self._app_settings.db_path
            self._db_manager = DatabaseManager(db_path)
        return self._db_manager
    
    def reload_db_manager(self, new_path: Optional[str] = None):
        """
        Reload database manager with a new path.
        Used when database path is changed.
        
        Args:
            new_path: New database path (if None, uses path from settings or sample_db)
        """
        # Close existing connection if any
        if self._db_manager:
            # DatabaseManager doesn't have explicit close, but we can recreate it
            pass
        
        # Determine path to use
        if new_path:
            db_path = new_path
        elif app_config.is_sample_db_mode():
            db_path = SAMPLE_DATABASE_PATH
        elif self._app_settings and self._app_settings.db_path:
            db_path = self._app_settings.db_path
        else:
            db_path = DATABASE_PATH
        
        # Create new manager
        self._db_manager = DatabaseManager(db_path)
    
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
    
    def enable_field_encryption(self) -> bool:
        """
        Enable field-level encryption and generate encryption key if not exists.
        
        Returns:
            True if encryption was enabled successfully, False otherwise
        """
        try:
            from services.database.field_encryption_service import FieldEncryptionService
            from services.database.encryption_service import DatabaseEncryptionService
            
            settings = self.load_settings()
            
            # If encryption is already enabled, return True
            if settings.encryption_enabled:
                return True
            
            # Generate encryption key if not exists
            if not settings.encryption_key_hash:
                encryption_key = FieldEncryptionService.generate_encryption_key()
                key_hash = FieldEncryptionService.hash_key(encryption_key)
                settings.encryption_key_hash = key_hash
                logger.info("Generated new field encryption key")
            
            # Enable encryption
            settings.encryption_enabled = True
            
            # Save settings
            if self.save_settings(settings):
                logger.info("Field-level encryption enabled successfully")
                return True
            else:
                logger.error("Failed to save encryption settings")
                return False
        except Exception as e:
            logger.error(f"Error enabling field encryption: {e}")
            return False
    
    def disable_field_encryption(self) -> bool:
        """
        Disable field-level encryption.
        Note: This does NOT decrypt existing data - data remains encrypted.
        
        Returns:
            True if encryption was disabled successfully, False otherwise
        """
        try:
            settings = self.load_settings()
            settings.encryption_enabled = False
            
            if self.save_settings(settings):
                logger.info("Field-level encryption disabled")
                return True
            else:
                logger.error("Failed to save encryption settings")
                return False
        except Exception as e:
            logger.error(f"Error disabling field encryption: {e}")
            return False
    
    def is_field_encryption_enabled(self) -> bool:
        """
        Check if field-level encryption is enabled.
        
        Returns:
            True if encryption is enabled, False otherwise
        """
        settings = self.load_settings()
        return settings.encryption_enabled
    
    def is_session_encryption_enabled(self) -> bool:
        """
        Check if session file encryption is enabled.
        
        Returns:
            True if session encryption is enabled, False otherwise
        """
        settings = self.load_settings()
        return settings.session_encryption_enabled


# Global settings instance
settings = Settings()

