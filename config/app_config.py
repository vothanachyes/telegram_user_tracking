"""
Application configuration manager for sample database mode.
"""

import json
import logging
from pathlib import Path
from typing import Optional
from utils.constants import APP_DATA_DIR

logger = logging.getLogger(__name__)

# Configuration file path
CONFIG_FILE_PATH = APP_DATA_DIR / "config.json"

# Default sample database path
SAMPLE_DATABASE_PATH = APP_DATA_DIR / "sample_db" / "app.db"


class AppConfig:
    """Application configuration manager for sample database mode."""
    
    _instance: Optional['AppConfig'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._config: dict = {}
        self._load_config()
        self._initialized = True
    
    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            if CONFIG_FILE_PATH.exists():
                with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.debug(f"Loaded config from {CONFIG_FILE_PATH}")
            else:
                # Default configuration
                self._config = {
                    "sample_db_mode": False
                }
                self._save_config()
                logger.debug(f"Created default config at {CONFIG_FILE_PATH}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Use default configuration on error
            self._config = {"sample_db_mode": False}
    
    def _save_config(self):
        """Save configuration to JSON file."""
        try:
            # Ensure directory exists
            CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved config to {CONFIG_FILE_PATH}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise
    
    def is_sample_db_mode(self) -> bool:
        """
        Check if sample database mode is enabled.
        
        Returns:
            True if sample database mode is enabled, False otherwise
        """
        return self._config.get("sample_db_mode", False)
    
    def set_sample_db_mode(self, enabled: bool):
        """
        Set sample database mode.
        
        Args:
            enabled: True to enable sample database mode, False to disable
        """
        self._config["sample_db_mode"] = enabled
        self._save_config()
        logger.info(f"Sample database mode set to: {enabled}")
    
    def get_sample_db_path(self) -> str:
        """
        Get the path to the sample database.
        
        Returns:
            Path to sample database as string
        """
        # Ensure sample_db directory exists
        sample_db_dir = SAMPLE_DATABASE_PATH.parent
        sample_db_dir.mkdir(parents=True, exist_ok=True)
        
        return str(SAMPLE_DATABASE_PATH)


# Global app config instance
app_config = AppConfig()

