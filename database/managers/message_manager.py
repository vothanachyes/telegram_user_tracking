"""
Messages manager.
"""

from typing import Optional, List
from datetime import datetime
from database.managers.base import BaseDatabaseManager, _safe_get_row_value, _parse_datetime
from database.models.message import Message
from database.managers.tag_manager import TagManager
from utils.tag_extractor import TagExtractor
import logging

logger = logging.getLogger(__name__)


class MessageManager(BaseDatabaseManager):
    """Manages messages operations."""
    
    def __init__(self, db_path: str = "./data/app.db"):
        """Initialize message manager."""
        super().__init__(db_path)
        self._tag_manager = TagManager(db_path)
    
    def save_message(self, message: Message) -> Optional[int]:
        """Save a message and its tags."""
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
                message_db_id = cursor.lastrowid
                
                # Extract and save tags (don't fail message save if tag save fails)
                try:
                    # Decrypt content and caption for tag extraction
                    decrypted_content = encryption_service.decrypt_field(encrypted_content) if encryption_service else encrypted_content
                    decrypted_caption = encryption_service.decrypt_field(encrypted_caption) if encryption_service else encrypted_caption
                    
                    tags = TagExtractor.extract_tags_from_content_and_caption(decrypted_content, decrypted_caption)
                    if tags:
                        self._tag_manager.save_tags(
                            message.message_id,
                            message.group_id,
                            message.user_id,
                            tags,
                            message.date_sent
                        )
                except Exception as tag_error:
                    logger.warning(f"Error saving tags for message {message.message_id}: {tag_error}")
                    # Don't fail message save if tag save fails
                
                return message_db_id
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None
    
    def get_messages(
        self, 
        group_id: Optional[int] = None,
        group_ids: Optional[List[int]] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_deleted: bool = False,
        limit: Optional[int] = None,
        offset: int = 0,
        tags: Optional[List[str]] = None,
        message_type_filter: Optional[str] = None
    ) -> List[Message]:
        """
        Get messages with filters.
        
        Args:
            group_id: Filter by single group ID (for backward compatibility)
            group_ids: Filter by list of group IDs (takes precedence over group_id)
            user_id: Filter by user ID
            start_date: Filter by start date
            end_date: Filter by end date
            include_deleted: Include soft-deleted messages
            limit: Maximum number of results
            offset: Offset for pagination
            tags: List of tags to filter by (normalized, without # prefix)
            message_type_filter: Filter by message type (voice, audio, photos, videos, files, link, tag, poll, location, mention)
        """
        # Determine if we need to use table alias (for tag filter or when tags are specified)
        use_alias = False
        if message_type_filter == "tag":
            use_alias = True
        
        # If tags are specified, we need to join with message_tags table
        if tags and len(tags) > 0:
            # Filter by tags - get messages that have ALL specified tags
            # We use a subquery approach to ensure all tags are present
            normalized_tags = [t.strip().lower() for t in tags if t and t.strip()]
            
            if normalized_tags:
                # For each tag, we need to ensure the message has it
                # We'll use multiple JOINs or a subquery approach
                query = """
                    SELECT DISTINCT m.* FROM messages m
                    WHERE 1=1
                """
                params = []
                use_alias = True
                
                # Add a condition for each tag using EXISTS subqueries
                for tag in normalized_tags:
                    query += f"""
                        AND EXISTS (
                            SELECT 1 FROM message_tags mt
                            WHERE mt.message_id = m.message_id
                            AND mt.group_id = m.group_id
                            AND mt.tag = ?
                        )
                    """
                    params.append(tag)
            else:
                # No valid tags, fall back to regular query
                if use_alias:
                    query = "SELECT m.* FROM messages m WHERE 1=1"
                else:
                    query = "SELECT * FROM messages WHERE 1=1"
                params = []
        else:
            if use_alias:
                query = "SELECT m.* FROM messages m WHERE 1=1"
            else:
                query = "SELECT * FROM messages WHERE 1=1"
            params = []
        
        # Handle group filtering - use group_ids if provided, otherwise use group_id
        table_prefix = "m." if use_alias else ""
        if group_ids and len(group_ids) > 0:
            placeholders = ",".join("?" * len(group_ids))
            query += f" AND {table_prefix}group_id IN ({placeholders})"
            params.extend(group_ids)
        elif group_id:
            query += f" AND {table_prefix}group_id = ?"
            params.append(group_id)
        
        if user_id:
            query += f" AND {table_prefix}user_id = ?"
            params.append(user_id)
        
        if start_date:
            query += f" AND {table_prefix}date_sent >= ?"
            params.append(start_date)
        
        if end_date:
            query += f" AND {table_prefix}date_sent <= ?"
            params.append(end_date)
        
        if not include_deleted:
            query += f" AND {table_prefix}is_deleted = 0"
        
        # Handle message type filtering
        if message_type_filter:
            if message_type_filter == "voice":
                query += f" AND {table_prefix}message_type = 'voice'"
            elif message_type_filter == "audio":
                query += f" AND {table_prefix}message_type = 'audio'"
            elif message_type_filter == "photos":
                query += f" AND {table_prefix}message_type = 'photo'"
            elif message_type_filter == "videos":
                query += f" AND {table_prefix}message_type = 'video'"
            elif message_type_filter == "files":
                query += f" AND {table_prefix}message_type = 'document'"
            elif message_type_filter == "link":
                query += f" AND {table_prefix}has_link = 1"
            elif message_type_filter == "poll":
                query += f" AND {table_prefix}message_type = 'poll'"
            elif message_type_filter == "location":
                query += f" AND {table_prefix}message_type = 'location'"
            elif message_type_filter == "tag":
                # Filter messages that have at least one tag
                # Ensure we use alias (should already be set, but safety check)
                if not use_alias:
                    # Need to rewrite query with alias
                    query = query.replace("SELECT * FROM messages WHERE", "SELECT m.* FROM messages m WHERE")
                    use_alias = True
                    table_prefix = "m."
                query += """
                    AND EXISTS (
                        SELECT 1 FROM message_tags mt
                        WHERE mt.message_id = m.message_id
                        AND mt.group_id = m.group_id
                    )
                """
            # Note: "mention" filter is handled after decryption in Python
        
        query += f" ORDER BY {table_prefix}date_sent DESC"
        
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
                
                message = Message(
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
                )
                
                # Handle "@ Mention" filter after decryption
                if message_type_filter == "mention":
                    # Check if content or caption contains "@"
                    has_mention = False
                    if content and "@" in content:
                        has_mention = True
                    if caption and "@" in caption:
                        has_mention = True
                    if not has_mention:
                        continue  # Skip this message
                
                messages.append(message)
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
        """Soft delete a message and its tags."""
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
                
                # Delete associated tags
                try:
                    self._tag_manager.delete_tags_for_message(message_id, group_id)
                except Exception as tag_error:
                    logger.warning(f"Error deleting tags for message {message_id}: {tag_error}")
                    # Don't fail message deletion if tag deletion fails
                
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
    
    def get_messages_by_tags(
        self,
        tags: List[str],
        group_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_deleted: bool = False,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Message]:
        """
        Filter messages by multiple tags.
        
        Args:
            tags: List of tags to filter by (normalized, without # prefix)
            group_id: Optional group ID to filter by
            start_date: Optional start date filter
            end_date: Optional end date filter
            include_deleted: Include soft-deleted messages
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of messages that contain all specified tags
        """
        return self.get_messages(
            group_id=group_id,
            start_date=start_date,
            end_date=end_date,
            include_deleted=include_deleted,
            limit=limit,
            offset=offset,
            tags=tags
        )

