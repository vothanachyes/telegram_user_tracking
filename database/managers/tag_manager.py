"""
Tag manager for message tags operations.
"""

from typing import Optional, List, Dict
from datetime import datetime
from database.managers.base import BaseDatabaseManager, _parse_datetime
from database.models.message import MessageTag
import logging

logger = logging.getLogger(__name__)


class TagManager(BaseDatabaseManager):
    """Manages message tags operations."""
    
    def save_tags(
        self,
        message_id: int,
        group_id: int,
        user_id: int,
        tags: List[str],
        date_sent: datetime
    ) -> bool:
        """
        Save tags for a message.
        
        Args:
            message_id: Telegram message ID
            group_id: Group ID
            user_id: User ID
            tags: List of normalized tags (without # prefix)
            date_sent: Message date sent timestamp
            
        Returns:
            True if successful, False otherwise
        """
        if not tags:
            return True
        
        try:
            with self.get_connection() as conn:
                for tag in tags:
                    if not tag or not tag.strip():
                        continue
                    
                    try:
                        conn.execute("""
                            INSERT INTO message_tags 
                            (message_id, group_id, user_id, tag, date_sent)
                            VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT(message_id, group_id, tag) DO NOTHING
                        """, (message_id, group_id, user_id, tag.strip().lower(), date_sent))
                    except Exception as e:
                        logger.warning(f"Error saving tag '{tag}' for message {message_id}: {e}")
                        continue
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving tags for message {message_id}: {e}")
            return False
    
    def get_tags_by_message(self, message_id: int, group_id: int) -> List[MessageTag]:
        """
        Get all tags for a message.
        
        Args:
            message_id: Telegram message ID
            group_id: Group ID
            
        Returns:
            List of MessageTag objects
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM message_tags
                    WHERE message_id = ? AND group_id = ?
                    ORDER BY tag ASC
                """, (message_id, group_id))
                
                tags = []
                for row in cursor.fetchall():
                    tags.append(MessageTag(
                        id=row['id'],
                        message_id=row['message_id'],
                        group_id=row['group_id'],
                        user_id=row['user_id'],
                        tag=row['tag'],
                        date_sent=_parse_datetime(row['date_sent']),
                        created_at=_parse_datetime(row['created_at'])
                    ))
                return tags
        except Exception as e:
            logger.error(f"Error getting tags for message {message_id}: {e}")
            return []
    
    def get_messages_by_tag(
        self,
        tag: str,
        group_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[int]:
        """
        Get message IDs containing a specific tag.
        
        Args:
            tag: Normalized tag (without # prefix)
            group_id: Optional group ID to filter by
            limit: Optional limit on number of results
            offset: Offset for pagination
            
        Returns:
            List of message IDs (as tuples of (message_id, group_id))
        """
        try:
            query = """
                SELECT DISTINCT message_id, group_id FROM message_tags
                WHERE tag = ?
            """
            params = [tag.strip().lower()]
            
            if group_id:
                query += " AND group_id = ?"
                params.append(group_id)
            
            query += " ORDER BY date_sent DESC"
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                return [(row['message_id'], row['group_id']) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting messages by tag '{tag}': {e}")
            return []
    
    def get_tag_suggestions(
        self,
        prefix: str,
        group_id: Optional[int] = None,
        limit: int = 10
    ) -> List[str]:
        """
        Get tag suggestions for autocomplete.
        
        Args:
            prefix: Tag prefix to search for (without #)
            group_id: Optional group ID to filter by
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested tags (normalized, without # prefix)
        """
        if not prefix:
            return []
        
        try:
            query = """
                SELECT DISTINCT tag FROM message_tags
                WHERE tag LIKE ?
            """
            params = [f"{prefix.strip().lower()}%"]
            
            if group_id:
                query += " AND group_id = ?"
                params.append(group_id)
            
            query += " ORDER BY tag ASC LIMIT ?"
            params.append(limit)
            
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                return [row['tag'] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting tag suggestions for prefix '{prefix}': {e}")
            return []
    
    def get_tag_counts_by_group(self, group_id: int) -> Dict[str, int]:
        """
        Get tag usage counts per group.
        
        Args:
            group_id: Group ID
            
        Returns:
            Dictionary mapping tag to count
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT tag, COUNT(*) as count
                    FROM message_tags
                    WHERE group_id = ?
                    GROUP BY tag
                    ORDER BY count DESC, tag ASC
                """, (group_id,))
                
                return {row['tag']: row['count'] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Error getting tag counts for group {group_id}: {e}")
            return {}
    
    def get_tag_counts_by_user(self, group_id: int, user_id: int) -> Dict[str, int]:
        """
        Get tag usage counts per user in a group.
        
        Args:
            group_id: Group ID
            user_id: User ID
            
        Returns:
            Dictionary mapping tag to count
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT tag, COUNT(*) as count
                    FROM message_tags
                    WHERE group_id = ? AND user_id = ?
                    GROUP BY tag
                    ORDER BY count DESC, tag ASC
                """, (group_id, user_id))
                
                return {row['tag']: row['count'] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Error getting tag counts for user {user_id} in group {group_id}: {e}")
            return {}
    
    def delete_tags_for_message(self, message_id: int, group_id: int) -> bool:
        """
        Remove tags when message is deleted.
        
        Args:
            message_id: Telegram message ID
            group_id: Group ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    DELETE FROM message_tags
                    WHERE message_id = ? AND group_id = ?
                """, (message_id, group_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting tags for message {message_id}: {e}")
            return False
    
    def get_all_tags_for_group(self, group_id: int) -> List[str]:
        """
        Get all unique tags for a group.
        
        Args:
            group_id: Group ID
            
        Returns:
            List of unique tags (normalized, without # prefix)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT tag FROM message_tags
                    WHERE group_id = ?
                    ORDER BY tag ASC
                """, (group_id,))
                
                return [row['tag'] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting all tags for group {group_id}: {e}")
            return []

