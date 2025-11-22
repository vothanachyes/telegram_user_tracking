"""
User groups manager - tracks which groups users have joined.
"""

from typing import Optional, List, Dict, Tuple
from database.managers.base import BaseDatabaseManager, _parse_datetime, _safe_get_row_value
import logging

logger = logging.getLogger(__name__)


class UserGroupManager(BaseDatabaseManager):
    """Manages user-group relationships operations."""
    
    def save_user_group(
        self,
        user_id: int,
        group_id: int,
        group_name: str,
        group_username: Optional[str] = None
    ) -> Optional[int]:
        """
        Save or update a user-group relationship.
        
        Args:
            user_id: Telegram user ID
            group_id: Telegram group ID
            group_name: Group name
            group_username: Group username (optional)
            
        Returns:
            Database ID if successful, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO user_groups 
                    (user_id, group_id, group_name, group_username)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, group_id) DO UPDATE SET
                        group_name = excluded.group_name,
                        group_username = excluded.group_username
                """, (
                    user_id,
                    group_id,
                    group_name,
                    group_username
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving user group: {e}")
            return None
    
    def get_user_groups(self, user_id: int) -> List[Dict]:
        """
        Get all groups for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            List of group dictionaries with group_id, group_name, group_username
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT group_id, group_name, group_username, created_at
                FROM user_groups
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            return [
                {
                    'group_id': row['group_id'],
                    'group_name': row['group_name'],
                    'group_username': row['group_username'],
                    'created_at': _parse_datetime(row['created_at'])
                }
                for row in cursor.fetchall()
            ]
    
    def get_users_by_group(self, group_id: int) -> List[int]:
        """
        Get all user IDs in a specific group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            List of user IDs
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT user_id FROM user_groups
                WHERE group_id = ?
            """, (group_id,))
            return [row['user_id'] for row in cursor.fetchall()]
    
    def get_user_group_count(self, user_id: int) -> int:
        """
        Count groups for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Number of groups the user has joined
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM user_groups
                WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    def delete_user_group(self, user_id: int, group_id: int) -> bool:
        """
        Remove a user-group relationship.
        
        Args:
            user_id: Telegram user ID
            group_id: Telegram group ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    DELETE FROM user_groups
                    WHERE user_id = ? AND group_id = ?
                """, (user_id, group_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting user group: {e}")
            return False
    
    def get_groups_with_user_counts(self, group_ids: Optional[List[int]] = None) -> List[Dict]:
        """
        Get groups with user counts for filtering.
        
        Args:
            group_ids: Optional list of group IDs to filter by
            
        Returns:
            List of dictionaries with group_id, group_name, group_username, user_count
        """
        with self.get_connection() as conn:
            if group_ids:
                placeholders = ','.join('?' * len(group_ids))
                query = f"""
                    SELECT 
                        group_id,
                        MAX(group_name) as group_name,
                        MAX(group_username) as group_username,
                        COUNT(DISTINCT user_id) as user_count
                    FROM user_groups
                    WHERE group_id IN ({placeholders})
                    GROUP BY group_id
                    ORDER BY user_count DESC, group_name ASC
                """
                cursor = conn.execute(query, group_ids)
            else:
                cursor = conn.execute("""
                    SELECT 
                        group_id,
                        MAX(group_name) as group_name,
                        MAX(group_username) as group_username,
                        COUNT(DISTINCT user_id) as user_count
                    FROM user_groups
                    GROUP BY group_id
                    ORDER BY user_count DESC, group_name ASC
                """)
            
            return [
                {
                    'group_id': row['group_id'],
                    'group_name': row['group_name'],
                    'group_username': row['group_username'],
                    'user_count': row['user_count']
                }
                for row in cursor.fetchall()
            ]
    
    def get_users_with_group_counts(
        self,
        group_ids: Optional[List[int]] = None,
        search_query: Optional[str] = None
    ) -> List[Dict]:
        """
        Get users with their group counts, optionally filtered by groups and search query.
        
        Args:
            group_ids: Optional list of group IDs to filter by
            search_query: Optional search query to filter users by name/username
            
        Returns:
            List of dictionaries with user_id, full_name, username, group_count
        """
        with self.get_connection() as conn:
            # Build WHERE clause
            where_clauses = []
            params = []
            
            if group_ids:
                placeholders = ','.join('?' * len(group_ids))
                where_clauses.append(f"ug.group_id IN ({placeholders})")
                params.extend(group_ids)
            
            if search_query:
                where_clauses.append("""
                    (tu.full_name LIKE ? OR tu.username LIKE ? OR CAST(tu.user_id AS TEXT) LIKE ?)
                """)
                search_pattern = f"%{search_query}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            query = f"""
                SELECT 
                    tu.user_id,
                    tu.full_name,
                    tu.username,
                    COUNT(DISTINCT ug.group_id) as group_count
                FROM telegram_users tu
                INNER JOIN user_groups ug ON tu.user_id = ug.user_id
                WHERE tu.is_deleted = 0 AND {where_sql}
                GROUP BY tu.user_id, tu.full_name, tu.username
                ORDER BY group_count DESC, tu.full_name ASC
            """
            
            cursor = conn.execute(query, params)
            return [
                {
                    'user_id': row['user_id'],
                    'full_name': row['full_name'],
                    'username': row['username'],
                    'group_count': row['group_count']
                }
                for row in cursor.fetchall()
            ]

