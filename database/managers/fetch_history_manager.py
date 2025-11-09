"""
Fetch history manager for tracking group fetch operations.
"""

from typing import Optional, List
from database.managers.base import BaseDatabaseManager, _parse_datetime, _safe_get_row_value
from database.models.telegram import GroupFetchHistory
import logging

logger = logging.getLogger(__name__)


class FetchHistoryManager(BaseDatabaseManager):
    """Manages group fetch history operations."""
    
    def save_fetch_history(self, history: GroupFetchHistory) -> Optional[int]:
        """Save fetch history record."""
        try:
            encryption_service = self.get_encryption_service()
            
            # Encrypt sensitive fields
            encrypted_phone = encryption_service.encrypt_field(history.account_phone_number) if encryption_service else history.account_phone_number
            encrypted_full_name = encryption_service.encrypt_field(history.account_full_name) if encryption_service else history.account_full_name
            encrypted_username = encryption_service.encrypt_field(history.account_username) if encryption_service else history.account_username
            
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO group_fetch_history 
                    (group_id, start_date, end_date, message_count, account_phone_number, 
                     account_full_name, account_username, total_users_fetched, total_media_fetched,
                     total_stickers, total_photos, total_videos, total_documents, total_audio, total_links)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    history.group_id,
                    history.start_date,
                    history.end_date,
                    history.message_count,
                    encrypted_phone,
                    encrypted_full_name,
                    encrypted_username,
                    history.total_users_fetched,
                    history.total_media_fetched,
                    history.total_stickers,
                    history.total_photos,
                    history.total_videos,
                    history.total_documents,
                    history.total_audio,
                    history.total_links
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving fetch history: {e}")
            return None
    
    def get_fetch_history_by_group(self, group_id: int) -> List[GroupFetchHistory]:
        """Get all fetch history records for a specific group."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM group_fetch_history 
                WHERE group_id = ?
                ORDER BY created_at DESC
            """, (group_id,))
            encryption_service = self.get_encryption_service()
            
            histories = []
            for row in cursor.fetchall():
                # Decrypt sensitive fields
                account_phone_number = encryption_service.decrypt_field(row['account_phone_number']) if encryption_service else row['account_phone_number']
                account_full_name = encryption_service.decrypt_field(_safe_get_row_value(row, 'account_full_name')) if encryption_service else _safe_get_row_value(row, 'account_full_name')
                account_username = encryption_service.decrypt_field(_safe_get_row_value(row, 'account_username')) if encryption_service else _safe_get_row_value(row, 'account_username')
                
                histories.append(GroupFetchHistory(
                    id=row['id'],
                    group_id=row['group_id'],
                    start_date=_parse_datetime(row['start_date']),
                    end_date=_parse_datetime(row['end_date']),
                    message_count=row['message_count'],
                    account_phone_number=account_phone_number,
                    account_full_name=account_full_name,
                    account_username=account_username,
                    total_users_fetched=_safe_get_row_value(row, 'total_users_fetched', 0),
                    total_media_fetched=_safe_get_row_value(row, 'total_media_fetched', 0),
                    total_stickers=_safe_get_row_value(row, 'total_stickers', 0),
                    total_photos=_safe_get_row_value(row, 'total_photos', 0),
                    total_videos=_safe_get_row_value(row, 'total_videos', 0),
                    total_documents=_safe_get_row_value(row, 'total_documents', 0),
                    total_audio=_safe_get_row_value(row, 'total_audio', 0),
                    total_links=_safe_get_row_value(row, 'total_links', 0),
                    created_at=_parse_datetime(row['created_at'])
                ))
            return histories
    
    def get_all_fetch_history(self) -> List[GroupFetchHistory]:
        """Get all fetch history records."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM group_fetch_history 
                ORDER BY created_at DESC
            """)
            encryption_service = self.get_encryption_service()
            
            histories = []
            for row in cursor.fetchall():
                # Decrypt sensitive fields
                account_phone_number = encryption_service.decrypt_field(row['account_phone_number']) if encryption_service else row['account_phone_number']
                account_full_name = encryption_service.decrypt_field(_safe_get_row_value(row, 'account_full_name')) if encryption_service else _safe_get_row_value(row, 'account_full_name')
                account_username = encryption_service.decrypt_field(_safe_get_row_value(row, 'account_username')) if encryption_service else _safe_get_row_value(row, 'account_username')
                
                histories.append(GroupFetchHistory(
                    id=row['id'],
                    group_id=row['group_id'],
                    start_date=_parse_datetime(row['start_date']),
                    end_date=_parse_datetime(row['end_date']),
                    message_count=row['message_count'],
                    account_phone_number=account_phone_number,
                    account_full_name=account_full_name,
                    account_username=account_username,
                    total_users_fetched=_safe_get_row_value(row, 'total_users_fetched', 0),
                    total_media_fetched=_safe_get_row_value(row, 'total_media_fetched', 0),
                    total_stickers=_safe_get_row_value(row, 'total_stickers', 0),
                    total_photos=_safe_get_row_value(row, 'total_photos', 0),
                    total_videos=_safe_get_row_value(row, 'total_videos', 0),
                    total_documents=_safe_get_row_value(row, 'total_documents', 0),
                    total_audio=_safe_get_row_value(row, 'total_audio', 0),
                    total_links=_safe_get_row_value(row, 'total_links', 0),
                    created_at=_parse_datetime(row['created_at'])
                ))
            return histories

