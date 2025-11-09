"""
Client utilities for creating temporary Telegram clients.
"""

import logging
from typing import Optional

try:
    from pyrogram import Client
    PYROGRAM_AVAILABLE = True
except ImportError:
    PYROGRAM_AVAILABLE = False
    Client = None

from database.models import TelegramCredential
from config.settings import settings
from services.telegram.client_manager import ClientManager

logger = logging.getLogger(__name__)


class ClientUtils:
    """Utility functions for creating temporary Telegram clients."""
    
    def __init__(self, client_manager: ClientManager):
        self.client_manager = client_manager
    
    def create_client(self, phone: str, api_id: str, api_hash: str) -> Optional[Client]:
        """Create Pyrogram client."""
        return self.client_manager.create_client(phone, api_id, api_hash)
    
    async def create_temporary_client(
        self,
        credential: TelegramCredential
    ) -> Optional[Client]:
        """
        Create a temporary client for a specific credential.
        Does not affect the current connected client.
        
        Args:
            credential: TelegramCredential to create client for
            
        Returns:
            Temporary Client instance or None if failed
        """
        if not settings.has_telegram_credentials:
            return None
        
        try:
            client = self.client_manager.create_client(
                credential.phone_number,
                settings.telegram_api_id,
                settings.telegram_api_hash
            )
            
            if client:
                await client.connect()
                # Verify it's authorized
                me = await client.get_me()
                if not me:
                    await client.disconnect()
                    return None
                return client
            return None
        except Exception as e:
            logger.error(f"Error creating temporary client: {e}")
            return None

