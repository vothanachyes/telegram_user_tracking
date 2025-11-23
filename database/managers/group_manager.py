"""
Telegram groups manager.
"""

from typing import Optional, List
from database.managers.base import BaseDatabaseManager, _parse_datetime, _safe_get_row_value
from database.models.telegram import TelegramGroup
import logging

logger = logging.getLogger(__name__)


class GroupManager(BaseDatabaseManager):
    """Manages Telegram groups operations."""
    
    def save_group(self, group: TelegramGroup) -> Optional[int]:
        """Save or update a Telegram group."""
        try:
            # Check if group already exists
            existing_group = self.get_group_by_id(group.group_id)
            is_new_group = existing_group is None
            
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO telegram_groups 
                    (group_id, group_name, group_username, group_photo_path, last_fetch_date, total_messages)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(group_id) DO UPDATE SET
                        group_name = excluded.group_name,
                        group_username = excluded.group_username,
                        group_photo_path = excluded.group_photo_path,
                        last_fetch_date = excluded.last_fetch_date,
                        total_messages = excluded.total_messages,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    group.group_id,
                    group.group_name,
                    group.group_username,
                    group.group_photo_path,
                    group.last_fetch_date,
                    group.total_messages
                ))
                conn.commit()
                
                # Track new group addition
                if is_new_group:
                    try:
                        from services.user_activities_service import user_activities_service
                        from services.auth_service import auth_service
                        current_user = auth_service.get_current_user()
                        if current_user:
                            uid = current_user.get("uid")
                            if uid:
                                user_activities_service.increment_groups_count(uid)
                    except Exception as e:
                        logger.error(f"Error tracking group addition: {e}", exc_info=True)
                        # Don't fail if tracking fails
                
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving group: {e}")
            return None
    
    def get_all_groups(self) -> List[TelegramGroup]:
        """Get all Telegram groups."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM telegram_groups 
                ORDER BY last_fetch_date DESC
            """)
            return [TelegramGroup(
                id=row['id'],
                group_id=row['group_id'],
                group_name=row['group_name'],
                group_username=row['group_username'],
                group_photo_path=_safe_get_row_value(row, 'group_photo_path'),
                last_fetch_date=_parse_datetime(row['last_fetch_date']),
                total_messages=row['total_messages'],
                created_at=_parse_datetime(row['created_at']),
                updated_at=_parse_datetime(row['updated_at'])
            ) for row in cursor.fetchall()]
    
    def get_group_by_id(self, group_id: int) -> Optional[TelegramGroup]:
        """Get group by Telegram group ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM telegram_groups WHERE group_id = ?", 
                (group_id,)
            )
            row = cursor.fetchone()
            if row:
                return TelegramGroup(
                    id=row['id'],
                    group_id=row['group_id'],
                    group_name=row['group_name'],
                    group_username=row['group_username'],
                    group_photo_path=_safe_get_row_value(row, 'group_photo_path'),
                    last_fetch_date=_parse_datetime(row['last_fetch_date']),
                    total_messages=row['total_messages'],
                    created_at=_parse_datetime(row['created_at']),
                    updated_at=_parse_datetime(row['updated_at'])
                )
            return None

