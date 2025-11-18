"""
Tag analytics service for future analytics features.
"""

from typing import Dict, List, Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from database.managers.tag_manager import TagManager
import logging

logger = logging.getLogger(__name__)


class TagAnalyticsService:
    """Service for tag analytics and statistics."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize tag analytics service.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self._tag_manager = TagManager(db_manager.db_path)
    
    def get_top_tags_by_group(
        self,
        group_id: int,
        limit: int = 10
    ) -> List[Dict[str, any]]:
        """
        Get most used tags in a group.
        
        Args:
            group_id: Group ID
            limit: Maximum number of tags to return
            
        Returns:
            List of dictionaries with 'tag' and 'count' keys, sorted by count descending
        """
        try:
            tag_counts = self._tag_manager.get_tag_counts_by_group(group_id)
            
            # Sort by count descending, then by tag name ascending
            sorted_tags = sorted(
                tag_counts.items(),
                key=lambda x: (-x[1], x[0])
            )[:limit]
            
            return [
                {'tag': tag, 'count': count}
                for tag, count in sorted_tags
            ]
        except Exception as e:
            logger.error(f"Error getting top tags for group {group_id}: {e}")
            return []
    
    def get_tag_usage_by_user(
        self,
        group_id: int,
        tag: str
    ) -> List[Dict[str, any]]:
        """
        Get which users use a specific tag.
        
        Args:
            group_id: Group ID
            tag: Normalized tag (without # prefix)
            
        Returns:
            List of dictionaries with 'user_id' and 'count' keys
        """
        try:
            # Get all messages with this tag
            message_ids = self._tag_manager.get_messages_by_tag(
                tag.strip().lower(),
                group_id=group_id
            )
            
            # Count by user_id
            user_counts: Dict[int, int] = {}
            for message_id, msg_group_id in message_ids:
                # Get message to find user_id
                messages = self.db_manager.get_messages(
                    group_id=msg_group_id,
                    limit=1
                )
                # This is a simplified approach - in production, you'd want to
                # query the message_tags table directly for user_id
                # For now, we'll use a different approach
                pass
            
            # Better approach: query message_tags directly
            with self._tag_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT user_id, COUNT(*) as count
                    FROM message_tags
                    WHERE group_id = ? AND tag = ?
                    GROUP BY user_id
                    ORDER BY count DESC
                """, (group_id, tag.strip().lower()))
                
                return [
                    {'user_id': row['user_id'], 'count': row['count']}
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Error getting tag usage by user for tag '{tag}': {e}")
            return []
    
    def get_tag_usage_by_date(
        self,
        group_id: int,
        tag: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, any]]:
        """
        Get tag usage over time.
        
        Args:
            group_id: Group ID
            tag: Normalized tag (without # prefix)
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of dictionaries with 'date' and 'count' keys
        """
        try:
            query = """
                SELECT DATE(date_sent) as date, COUNT(*) as count
                FROM message_tags
                WHERE group_id = ? AND tag = ?
            """
            params = [group_id, tag.strip().lower()]
            
            if start_date:
                query += " AND date_sent >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND date_sent <= ?"
                params.append(end_date)
            
            query += " GROUP BY DATE(date_sent) ORDER BY date ASC"
            
            with self._tag_manager.get_connection() as conn:
                cursor = conn.execute(query, params)
                
                return [
                    {'date': row['date'], 'count': row['count']}
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Error getting tag usage by date for tag '{tag}': {e}")
            return []
    
    def get_user_tag_stats(
        self,
        group_id: int,
        user_id: int
    ) -> Dict[str, any]:
        """
        Get user's tag usage statistics.
        
        Args:
            group_id: Group ID
            user_id: User ID
            
        Returns:
            Dictionary with tag statistics for the user
        """
        try:
            tag_counts = self._tag_manager.get_tag_counts_by_user(group_id, user_id)
            
            total_tags = sum(tag_counts.values())
            unique_tags = len(tag_counts)
            
            # Get top tags
            sorted_tags = sorted(
                tag_counts.items(),
                key=lambda x: (-x[1], x[0])
            )[:5]
            
            return {
                'total_tags': total_tags,
                'unique_tags': unique_tags,
                'top_tags': [
                    {'tag': tag, 'count': count}
                    for tag, count in sorted_tags
                ],
                'all_tags': tag_counts
            }
        except Exception as e:
            logger.error(f"Error getting user tag stats for user {user_id}: {e}")
            return {
                'total_tags': 0,
                'unique_tags': 0,
                'top_tags': [],
                'all_tags': {}
            }

