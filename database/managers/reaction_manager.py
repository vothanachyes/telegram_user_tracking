"""
Reactions manager.
"""

from typing import Optional, List
from database.managers.base import BaseDatabaseManager, _parse_datetime
from database.models.message import Reaction
import logging

logger = logging.getLogger(__name__)


class ReactionManager(BaseDatabaseManager):
    """Manages reactions operations."""
    
    def save_reaction(self, reaction: Reaction) -> Optional[int]:
        """Save a reaction."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO reactions 
                    (message_id, group_id, user_id, emoji, message_link, reacted_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(message_id, group_id, user_id, emoji) DO NOTHING
                """, (
                    reaction.message_id,
                    reaction.group_id,
                    reaction.user_id,
                    reaction.emoji,
                    reaction.message_link,
                    reaction.reacted_at
                ))
                conn.commit()
                return cursor.lastrowid if cursor.rowcount > 0 else None
        except Exception as e:
            logger.error(f"Error saving reaction: {e}")
            return None
    
    def get_reactions_by_message(self, message_id: int, group_id: int) -> List[Reaction]:
        """Get all reactions for a specific message."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM reactions 
                WHERE message_id = ? AND group_id = ?
                ORDER BY created_at DESC
            """, (message_id, group_id))
            return [Reaction(
                id=row['id'],
                message_id=row['message_id'],
                group_id=row['group_id'],
                user_id=row['user_id'],
                emoji=row['emoji'],
                message_link=row['message_link'],
                reacted_at=_parse_datetime(row['reacted_at']),
                created_at=_parse_datetime(row['created_at'])
            ) for row in cursor.fetchall()]
    
    def get_reactions_by_user(
        self, 
        user_id: int, 
        group_id: Optional[int] = None
    ) -> List[Reaction]:
        """Get all reactions given by a user."""
        query = "SELECT * FROM reactions WHERE user_id = ?"
        params = [user_id]
        
        if group_id:
            query += " AND group_id = ?"
            params.append(group_id)
        
        query += " ORDER BY created_at DESC"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [Reaction(
                id=row['id'],
                message_id=row['message_id'],
                group_id=row['group_id'],
                user_id=row['user_id'],
                emoji=row['emoji'],
                message_link=row['message_link'],
                reacted_at=_parse_datetime(row['reacted_at']),
                created_at=_parse_datetime(row['created_at'])
            ) for row in cursor.fetchall()]
    
    def delete_reaction(self, reaction_id: int) -> bool:
        """Delete a reaction by ID."""
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM reactions WHERE id = ?", (reaction_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting reaction: {e}")
            return False

