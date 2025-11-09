"""
Messages manager.
"""

from typing import Optional, List
from datetime import datetime
from database.managers.base import BaseDatabaseManager, _safe_get_row_value, _parse_datetime
from database.models.message import Message
import logging

logger = logging.getLogger(__name__)


class MessageManager(BaseDatabaseManager):
    """Manages messages operations."""
    
    def save_message(self, message: Message) -> Optional[int]:
        """Save a message."""
        try:
            encryption_service = self.get_encryption_service()
            
            # Encrypt sensitive fields
            encrypted_content = encryption_service.encrypt_field(message.content) if encryption_service else message.content
            encrypted_caption = encryption_service.encrypt_field(message.caption) if encryption_service else message.caption
            encrypted_message_link = encryption_service.encrypt_field(message.message_link) if encryption_service else message.message_link
            
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO messages 
                    (message_id, group_id, user_id, content, caption, date_sent, 
                     has_media, media_type, media_count, message_link,
                     message_type, has_sticker, has_link, sticker_emoji)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(message_id, group_id) DO UPDATE SET
                        content = excluded.content,
                        caption = excluded.caption,
                        has_media = excluded.has_media,
                        media_type = excluded.media_type,
                        media_count = excluded.media_count,
                        message_type = excluded.message_type,
                        has_sticker = excluded.has_sticker,
                        has_link = excluded.has_link,
                        sticker_emoji = excluded.sticker_emoji,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    message.message_id,
                    message.group_id,
                    message.user_id,
                    encrypted_content,
                    encrypted_caption,
                    message.date_sent,
                    message.has_media,
                    message.media_type,
                    message.media_count,
                    encrypted_message_link,
                    message.message_type,
                    message.has_sticker,
                    message.has_link,
                    message.sticker_emoji
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None
    
    def get_messages(
        self, 
        group_id: Optional[int] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_deleted: bool = False,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Message]:
        """Get messages with filters."""
        query = "SELECT * FROM messages WHERE 1=1"
        params = []
        
        if group_id:
            query += " AND group_id = ?"
            params.append(group_id)
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if start_date:
            query += " AND date_sent >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date_sent <= ?"
            params.append(end_date)
        
        if not include_deleted:
            query += " AND is_deleted = 0"
        
        query += " ORDER BY date_sent DESC"
        
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        encryption_service = self.get_encryption_service()
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            messages = []
            for row in cursor.fetchall():
                # Decrypt sensitive fields
                content = encryption_service.decrypt_field(row['content']) if encryption_service else row['content']
                caption = encryption_service.decrypt_field(row['caption']) if encryption_service else row['caption']
                message_link = encryption_service.decrypt_field(row['message_link']) if encryption_service else row['message_link']
                
                messages.append(Message(
                    id=row['id'],
                    message_id=row['message_id'],
                    group_id=row['group_id'],
                    user_id=row['user_id'],
                    content=content,
                    caption=caption,
                    date_sent=_parse_datetime(row['date_sent']),
                    has_media=bool(row['has_media']),
                    media_type=row['media_type'],
                    media_count=row['media_count'],
                    message_link=message_link,
                    message_type=_safe_get_row_value(row, 'message_type'),
                    has_sticker=bool(_safe_get_row_value(row, 'has_sticker', False)),
                    has_link=bool(_safe_get_row_value(row, 'has_link', False)),
                    sticker_emoji=_safe_get_row_value(row, 'sticker_emoji'),
                    is_deleted=bool(row['is_deleted']),
                    created_at=_parse_datetime(row['created_at']),
                    updated_at=_parse_datetime(row['updated_at'])
                ))
            return messages
    
    def get_message_count(
        self,
        group_id: Optional[int] = None,
        user_id: Optional[int] = None,
        include_deleted: bool = False
    ) -> int:
        """Get total message count."""
        query = "SELECT COUNT(*) FROM messages WHERE 1=1"
        params = []
        
        if group_id:
            query += " AND group_id = ?"
            params.append(group_id)
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if not include_deleted:
            query += " AND is_deleted = 0"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()[0]
    
    def soft_delete_message(self, message_id: int, group_id: int) -> bool:
        """Soft delete a message."""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "UPDATE messages SET is_deleted = 1 WHERE message_id = ? AND group_id = ?",
                    (message_id, group_id)
                )
                conn.execute("""
                    INSERT OR IGNORE INTO deleted_messages (message_id, group_id) 
                    VALUES (?, ?)
                """, (message_id, group_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error soft deleting message: {e}")
            return False
    
    def is_message_deleted(self, message_id: int, group_id: int) -> bool:
        """Check if a message is soft deleted."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM deleted_messages WHERE message_id = ? AND group_id = ?",
                (message_id, group_id)
            )
            return cursor.fetchone()[0] > 0
    
    def message_exists(self, message_id: int, group_id: int) -> bool:
        """Check if a message exists in the database."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE message_id = ? AND group_id = ?",
                (message_id, group_id)
            )
            return cursor.fetchone()[0] > 0
    
    def undelete_message(self, message_id: int, group_id: int) -> bool:
        """Undelete (restore) a soft-deleted message."""
        try:
            with self.get_connection() as conn:
                # Remove from deleted_messages table
                conn.execute(
                    "DELETE FROM deleted_messages WHERE message_id = ? AND group_id = ?",
                    (message_id, group_id)
                )
                # Update is_deleted flag in messages table
                conn.execute(
                    "UPDATE messages SET is_deleted = 0 WHERE message_id = ? AND group_id = ?",
                    (message_id, group_id)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error undeleting message: {e}")
            return False

