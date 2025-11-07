"""
Telegram users manager.
"""

from typing import Optional, List
from database.managers.base import BaseDatabaseManager, _parse_datetime
from database.models.telegram import TelegramUser
import logging

logger = logging.getLogger(__name__)


class UserManager(BaseDatabaseManager):
    """Manages Telegram users operations."""
    
    def save_user(self, user: TelegramUser) -> Optional[int]:
        """Save or update a Telegram user."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO telegram_users 
                    (user_id, username, first_name, last_name, full_name, phone, bio, profile_photo_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        username = excluded.username,
                        first_name = excluded.first_name,
                        last_name = excluded.last_name,
                        full_name = excluded.full_name,
                        phone = excluded.phone,
                        bio = excluded.bio,
                        profile_photo_path = excluded.profile_photo_path,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    user.user_id,
                    user.username,
                    user.first_name,
                    user.last_name,
                    user.full_name,
                    user.phone,
                    user.bio,
                    user.profile_photo_path
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            return None
    
    def get_all_users(self, include_deleted: bool = False) -> List[TelegramUser]:
        """Get all Telegram users."""
        query = "SELECT * FROM telegram_users"
        if not include_deleted:
            query += " WHERE is_deleted = 0"
        query += " ORDER BY full_name"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query)
            return [TelegramUser(
                id=row['id'],
                user_id=row['user_id'],
                username=row['username'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                full_name=row['full_name'],
                phone=row['phone'],
                bio=row['bio'],
                profile_photo_path=row['profile_photo_path'],
                is_deleted=bool(row['is_deleted']),
                created_at=_parse_datetime(row['created_at']),
                updated_at=_parse_datetime(row['updated_at'])
            ) for row in cursor.fetchall()]
    
    def get_user_by_id(self, user_id: int) -> Optional[TelegramUser]:
        """Get user by Telegram user ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM telegram_users WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return TelegramUser(
                    id=row['id'],
                    user_id=row['user_id'],
                    username=row['username'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    full_name=row['full_name'],
                    phone=row['phone'],
                    bio=row['bio'],
                    profile_photo_path=row['profile_photo_path'],
                    is_deleted=bool(row['is_deleted']),
                    created_at=_parse_datetime(row['created_at']),
                    updated_at=_parse_datetime(row['updated_at'])
                )
            return None
    
    def get_users_by_group(self, group_id: int, include_deleted: bool = False) -> List[TelegramUser]:
        """Get users who have sent messages in a specific group."""
        query = """
            SELECT DISTINCT u.* FROM telegram_users u
            INNER JOIN messages m ON u.user_id = m.user_id
            WHERE m.group_id = ?
        """
        params = [group_id]
        
        if not include_deleted:
            query += " AND u.is_deleted = 0 AND m.is_deleted = 0"
        
        query += " ORDER BY u.full_name"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [TelegramUser(
                id=row['id'],
                user_id=row['user_id'],
                username=row['username'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                full_name=row['full_name'],
                phone=row['phone'],
                bio=row['bio'],
                profile_photo_path=row['profile_photo_path'],
                is_deleted=bool(row['is_deleted']),
                created_at=_parse_datetime(row['created_at']),
                updated_at=_parse_datetime(row['updated_at'])
            ) for row in cursor.fetchall()]
    
    def search_users(
        self,
        query: str,
        limit: int = 10,
        include_deleted: bool = False
    ) -> List[TelegramUser]:
        """Search users by full name, username, or phone."""
        if not query or not query.strip():
            return []
        
        search_term = f"%{query.strip()}%"
        conditions = []
        params = []
        
        # Check if query starts with @ (username search)
        if query.strip().startswith('@'):
            username_query = query.strip().lstrip('@')
            conditions.append("(username LIKE ? OR username LIKE ?)")
            params.extend([f"%{username_query}%", username_query])
        else:
            # Search in full_name, first_name, last_name, username, phone
            conditions.append("""
                (full_name LIKE ? OR 
                 first_name LIKE ? OR 
                 last_name LIKE ? OR 
                 username LIKE ? OR 
                 phone LIKE ?)
            """)
            params.extend([search_term, search_term, search_term, search_term, search_term])
        
        if not include_deleted:
            conditions.append("is_deleted = 0")
        
        where_clause = " AND ".join(conditions)
        
        sql = f"""
            SELECT * FROM telegram_users
            WHERE {where_clause}
            ORDER BY 
                CASE 
                    WHEN full_name LIKE ? THEN 1
                    WHEN username LIKE ? THEN 2
                    WHEN phone LIKE ? THEN 3
                    ELSE 4
                END,
                full_name
            LIMIT ?
        """
        
        # Add ordering params
        params.extend([search_term, search_term, search_term, limit])
        
        with self.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [TelegramUser(
                id=row['id'],
                user_id=row['user_id'],
                username=row['username'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                full_name=row['full_name'],
                phone=row['phone'],
                bio=row['bio'],
                profile_photo_path=row['profile_photo_path'],
                is_deleted=bool(row['is_deleted']),
                created_at=_parse_datetime(row['created_at']),
                updated_at=_parse_datetime(row['updated_at'])
            ) for row in cursor.fetchall()]
    
    def soft_delete_user(self, user_id: int) -> bool:
        """Soft delete a user."""
        try:
            with self.get_connection() as conn:
                # Mark user as deleted
                conn.execute(
                    "UPDATE telegram_users SET is_deleted = 1 WHERE user_id = ?",
                    (user_id,)
                )
                # Add to deleted users tracking
                conn.execute("""
                    INSERT OR IGNORE INTO deleted_users (user_id) VALUES (?)
                """, (user_id,))
                # Soft delete all messages from this user
                conn.execute(
                    "UPDATE messages SET is_deleted = 1 WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error soft deleting user: {e}")
            return False

