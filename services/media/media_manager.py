"""
Media manager for database operations on media files.
"""

import logging
import os
from typing import List

from database.db_manager import DatabaseManager
from database.models import MediaFile

logger = logging.getLogger(__name__)


class MediaManager:
    """Handles database operations for media files."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_media_for_message(self, message_id: int) -> List[MediaFile]:
        """Get all media files for a message."""
        return self.db_manager.get_media_for_message(message_id)
    
    def save_media_file(self, media_file: MediaFile):
        """Save media file to database."""
        self.db_manager.save_media_file(media_file)
    
    def delete_media_files(self, message_id: int) -> bool:
        """Delete all media files for a message."""
        try:
            media_files = self.get_media_for_message(message_id)
            
            for media in media_files:
                # Delete physical files
                if os.path.exists(media.file_path):
                    os.remove(media.file_path)
                
                if media.thumbnail_path and os.path.exists(media.thumbnail_path):
                    os.remove(media.thumbnail_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting media files: {e}")
            return False

