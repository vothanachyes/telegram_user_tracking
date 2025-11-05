"""
Database manager for SQLite operations.
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import logging

from database.models import (
    AppSettings, TelegramCredential, TelegramGroup, TelegramUser,
    Message, MediaFile, DeletedMessage, DeletedUser, CREATE_TABLES_SQL
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all database operations for the application."""
    
    def __init__(self, db_path: str = "./data/app.db"):
        """Initialize database manager."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """Initialize database with schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(CREATE_TABLES_SQL)
                
                # Initialize default settings if not exists
                cursor = conn.execute("SELECT COUNT(*) FROM app_settings")
                if cursor.fetchone()[0] == 0:
                    conn.execute("""
                        INSERT INTO app_settings (id) VALUES (1)
                    """)
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ==================== App Settings ====================
    
    def get_settings(self) -> AppSettings:
        """Get application settings."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM app_settings WHERE id = 1")
            row = cursor.fetchone()
            if row:
                return AppSettings(
                    id=row['id'],
                    theme=row['theme'],
                    language=row['language'],
                    corner_radius=row['corner_radius'],
                    telegram_api_id=row['telegram_api_id'],
                    telegram_api_hash=row['telegram_api_hash'],
                    download_root_dir=row['download_root_dir'],
                    download_media=bool(row['download_media']),
                    max_file_size_mb=row['max_file_size_mb'],
                    fetch_delay_seconds=row['fetch_delay_seconds'],
                    download_photos=bool(row['download_photos']),
                    download_videos=bool(row['download_videos']),
                    download_documents=bool(row['download_documents']),
                    download_audio=bool(row['download_audio']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return AppSettings()
    
    def update_settings(self, settings: AppSettings) -> bool:
        """Update application settings."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE app_settings SET
                        theme = ?,
                        language = ?,
                        corner_radius = ?,
                        telegram_api_id = ?,
                        telegram_api_hash = ?,
                        download_root_dir = ?,
                        download_media = ?,
                        max_file_size_mb = ?,
                        fetch_delay_seconds = ?,
                        download_photos = ?,
                        download_videos = ?,
                        download_documents = ?,
                        download_audio = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, (
                    settings.theme,
                    settings.language,
                    settings.corner_radius,
                    settings.telegram_api_id,
                    settings.telegram_api_hash,
                    settings.download_root_dir,
                    settings.download_media,
                    settings.max_file_size_mb,
                    settings.fetch_delay_seconds,
                    settings.download_photos,
                    settings.download_videos,
                    settings.download_documents,
                    settings.download_audio
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return False
    
    # ==================== Telegram Credentials ====================
    
    def save_telegram_credential(self, credential: TelegramCredential) -> Optional[int]:
        """Save or update Telegram credential."""
        try:
            with self.get_connection() as conn:
                # If set as default, unset all others
                if credential.is_default:
                    conn.execute("UPDATE telegram_credentials SET is_default = 0")
                
                cursor = conn.execute("""
                    INSERT INTO telegram_credentials 
                    (phone_number, session_string, is_default, last_used)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(phone_number) DO UPDATE SET
                        session_string = excluded.session_string,
                        is_default = excluded.is_default,
                        last_used = CURRENT_TIMESTAMP
                """, (
                    credential.phone_number,
                    credential.session_string,
                    credential.is_default
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving telegram credential: {e}")
            return None
    
    def get_telegram_credentials(self) -> List[TelegramCredential]:
        """Get all saved Telegram credentials."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM telegram_credentials 
                ORDER BY is_default DESC, last_used DESC
            """)
            return [TelegramCredential(
                id=row['id'],
                phone_number=row['phone_number'],
                session_string=row['session_string'],
                is_default=bool(row['is_default']),
                last_used=row['last_used'],
                created_at=row['created_at']
            ) for row in cursor.fetchall()]
    
    def get_default_credential(self) -> Optional[TelegramCredential]:
        """Get default Telegram credential."""
        credentials = self.get_telegram_credentials()
        for cred in credentials:
            if cred.is_default:
                return cred
        return credentials[0] if credentials else None
    
    # ==================== Telegram Groups ====================
    
    def save_group(self, group: TelegramGroup) -> Optional[int]:
        """Save or update a Telegram group."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO telegram_groups 
                    (group_id, group_name, group_username, last_fetch_date, total_messages)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(group_id) DO UPDATE SET
                        group_name = excluded.group_name,
                        group_username = excluded.group_username,
                        last_fetch_date = excluded.last_fetch_date,
                        total_messages = excluded.total_messages,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    group.group_id,
                    group.group_name,
                    group.group_username,
                    group.last_fetch_date,
                    group.total_messages
                ))
                conn.commit()
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
                last_fetch_date=row['last_fetch_date'],
                total_messages=row['total_messages'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
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
                    last_fetch_date=row['last_fetch_date'],
                    total_messages=row['total_messages'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return None
    
    # ==================== Telegram Users ====================
    
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
                created_at=row['created_at'],
                updated_at=row['updated_at']
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
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return None
    
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
    
    # ==================== Messages ====================
    
    def save_message(self, message: Message) -> Optional[int]:
        """Save a message."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO messages 
                    (message_id, group_id, user_id, content, caption, date_sent, 
                     has_media, media_type, media_count, message_link)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(message_id, group_id) DO UPDATE SET
                        content = excluded.content,
                        caption = excluded.caption,
                        has_media = excluded.has_media,
                        media_type = excluded.media_type,
                        media_count = excluded.media_count,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    message.message_id,
                    message.group_id,
                    message.user_id,
                    message.content,
                    message.caption,
                    message.date_sent,
                    message.has_media,
                    message.media_type,
                    message.media_count,
                    message.message_link
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
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [Message(
                id=row['id'],
                message_id=row['message_id'],
                group_id=row['group_id'],
                user_id=row['user_id'],
                content=row['content'],
                caption=row['caption'],
                date_sent=row['date_sent'],
                has_media=bool(row['has_media']),
                media_type=row['media_type'],
                media_count=row['media_count'],
                message_link=row['message_link'],
                is_deleted=bool(row['is_deleted']),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ) for row in cursor.fetchall()]
    
    def get_message_count(
        self,
        group_id: Optional[int] = None,
        include_deleted: bool = False
    ) -> int:
        """Get total message count."""
        query = "SELECT COUNT(*) FROM messages WHERE 1=1"
        params = []
        
        if group_id:
            query += " AND group_id = ?"
            params.append(group_id)
        
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
    
    # ==================== Media Files ====================
    
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
                created_at=row['created_at']
            ) for row in cursor.fetchall()]
    
    def get_total_media_size(self) -> int:
        """Get total size of all media files in bytes."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT SUM(file_size_bytes) FROM media_files")
            result = cursor.fetchone()[0]
            return result if result else 0
    
    # ==================== Statistics ====================
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get statistics for dashboard."""
        with self.get_connection() as conn:
            stats = {}
            
            # Total messages
            cursor = conn.execute("SELECT COUNT(*) FROM messages WHERE is_deleted = 0")
            stats['total_messages'] = cursor.fetchone()[0]
            
            # Total users
            cursor = conn.execute("SELECT COUNT(*) FROM telegram_users WHERE is_deleted = 0")
            stats['total_users'] = cursor.fetchone()[0]
            
            # Total groups
            cursor = conn.execute("SELECT COUNT(*) FROM telegram_groups")
            stats['total_groups'] = cursor.fetchone()[0]
            
            # Total media size
            stats['total_media_size'] = self.get_total_media_size()
            
            # Messages today
            cursor = conn.execute("""
                SELECT COUNT(*) FROM messages 
                WHERE date_sent >= date('now') AND is_deleted = 0
            """)
            stats['messages_today'] = cursor.fetchone()[0]
            
            # Messages this month
            cursor = conn.execute("""
                SELECT COUNT(*) FROM messages 
                WHERE date_sent >= date('now', 'start of month') AND is_deleted = 0
            """)
            stats['messages_this_month'] = cursor.fetchone()[0]
            
            return stats

