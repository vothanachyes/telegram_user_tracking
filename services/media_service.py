"""
Media download and management service.
"""

import logging
from typing import Optional, Callable, List

try:
    from telethon import TelegramClient
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

from database.db_manager import DatabaseManager
from database.models import MediaFile, Message, TelegramUser
from services.media.media_downloader import MediaDownloader
from services.media.media_manager import MediaManager

logger = logging.getLogger(__name__)


class MediaService:
    """Handles media file downloads and management."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.downloader = MediaDownloader()
        self.manager = MediaManager(db_manager)
    
    async def download_message_media(
        self,
        client: TelegramClient,
        telegram_msg: 'TelethonMessage',
        message: Message,
        user: TelegramUser,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[MediaFile]:
        """
        Download all media from a message.
        Returns list of MediaFile objects.
        """
        media_files = await self.downloader.download_message_media(
            client, telegram_msg, message, user, progress_callback
        )
        
        # Save media files to database
        for media_file in media_files:
            self.manager.save_media_file(media_file)
        
        return media_files
    
    def get_media_for_message(self, message_id: int) -> List[MediaFile]:
        """Get all media files for a message."""
        return self.manager.get_media_for_message(message_id)
    
    def delete_media_files(self, message_id: int) -> bool:
        """Delete all media files for a message."""
        return self.manager.delete_media_files(message_id)
