"""
Media files manager.
"""

from typing import Optional, List
from database.managers.base import BaseDatabaseManager, _parse_datetime
from database.models.media import MediaFile
import logging

logger = logging.getLogger(__name__)


class MediaManager(BaseDatabaseManager):
    """Manages media files operations."""
    
    def save_media_file(self, media: MediaFile) -> Optional[int]:
        """Save a media file record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO media_files 
                    (message_id, file_path, file_name, file_size_bytes, file_type, mime_type, thumbnail_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    media.message_id,
                    media.file_path,
                    media.file_name,
                    media.file_size_bytes,
                    media.file_type,
                    media.mime_type,
                    media.thumbnail_path
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving media file: {e}")
            return None
    
    def get_media_for_message(self, message_id: int) -> List[MediaFile]:
        """Get all media files for a message."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM media_files WHERE message_id = ?",
                (message_id,)
            )
            return [MediaFile(
                id=row['id'],
                message_id=row['message_id'],
                file_path=row['file_path'],
                file_name=row['file_name'],
                file_size_bytes=row['file_size_bytes'],
                file_type=row['file_type'],
                mime_type=row['mime_type'],
                thumbnail_path=row['thumbnail_path'],
                created_at=_parse_datetime(row['created_at'])
            ) for row in cursor.fetchall()]
    
    def get_total_media_size(self) -> int:
        """Get total size of all media files in bytes."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT SUM(file_size_bytes) FROM media_files")
            result = cursor.fetchone()[0]
            return result if result else 0

