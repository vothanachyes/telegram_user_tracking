"""
Service initialization utilities.
"""

import logging
from typing import Callable, Optional
from database.db_manager import DatabaseManager
from services.auth_service import auth_service
from services.connectivity_service import connectivity_service
from services.telegram import TelegramService
from services.license_service import LicenseService

logger = logging.getLogger(__name__)


class ServiceInitializer:
    """Handles application service initialization."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize service initializer.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.telegram_service: Optional[TelegramService] = None
    
    def initialize_all(
        self,
        on_connectivity_change: Optional[Callable[[bool], None]] = None
    ) -> TelegramService:
        """
        Initialize all application services.
        
        Args:
            on_connectivity_change: Optional callback for connectivity changes
            
        Returns:
            Initialized TelegramService instance
        """
        # Initialize Telegram service
        self.telegram_service = TelegramService(self.db_manager)
        
        # Start connectivity monitoring
        if on_connectivity_change:
            connectivity_service.start_monitoring(on_connectivity_change)
        
        # Initialize auth service (optional, Firebase may not be configured)
        try:
            auth_service.initialize()
        except Exception as e:
            logger.debug(f"Firebase not configured: {e}")
            # Firebase not configured, will use without auth
        
        # Initialize auth service with db_manager for license checks
        auth_service.db_manager = self.db_manager
        auth_service.license_service = LicenseService(
            self.db_manager,
            auth_service_instance=auth_service
        )
        
        return self.telegram_service
    
    def get_telegram_service(self) -> Optional[TelegramService]:
        """
        Get initialized Telegram service.
        
        Returns:
            TelegramService instance or None if not initialized
        """
        return self.telegram_service

