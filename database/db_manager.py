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
    Message, MediaFile, DeletedMessage, DeletedUser, LoginCredential,
    Reaction, UserLicenseCache, CREATE_TABLES_SQL
)

logger = logging.getLogger(__name__)


def _safe_get_row_value(row: sqlite3.Row, key: str, default: Any = None) -> Any:
    """
    Safely get a value from a sqlite3.Row object.
    sqlite3.Row doesn't have a .get() method, so we use try-except.
    """
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default


def _parse_datetime(dt_value: Any) -> Optional[datetime]:
    """
    Parse datetime from various formats (string, datetime, None).
    Handles SQLite timestamp strings in multiple formats.
    """
    if dt_value is None:
        return None
    
    if isinstance(dt_value, datetime):
        return dt_value
    
    if isinstance(dt_value, str):
        # Try common SQLite timestamp formats
        formats = [
            "%Y-%m-%d %H:%M:%S.%f",  # With microseconds
            "%Y-%m-%d %H:%M:%S",      # Standard format
            "%Y-%m-%dT%H:%M:%S.%f",   # ISO format with microseconds
            "%Y-%m-%dT%H:%M:%S",      # ISO format
            "%Y-%m-%d %H:%M",         # Without seconds
            "%Y-%m-%d",               # Date only
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(dt_value, fmt)
            except (ValueError, TypeError):
                continue
        
        # If all formats fail, log warning and return None
        logger.warning(f"Could not parse datetime: {dt_value}")
        return None
    
    return None


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
                
                # Run migrations
                self._run_migrations(conn)
                
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
    
    def _run_migrations(self, conn: sqlite3.Connection):
        """Run database migrations to update schema."""
        try:
            # Check if messages table has new columns
            cursor = conn.execute("PRAGMA table_info(messages)")
            columns = {row[1] for row in cursor.fetchall()}
            
            # Add message_type column if missing
            if 'message_type' not in columns:
                conn.execute("ALTER TABLE messages ADD COLUMN message_type TEXT")
                logger.info("Added message_type column to messages table")
            
            # Add has_sticker column if missing
            if 'has_sticker' not in columns:
                conn.execute("ALTER TABLE messages ADD COLUMN has_sticker BOOLEAN NOT NULL DEFAULT 0")
                logger.info("Added has_sticker column to messages table")
            
            # Add has_link column if missing
            if 'has_link' not in columns:
                conn.execute("ALTER TABLE messages ADD COLUMN has_link BOOLEAN NOT NULL DEFAULT 0")
                logger.info("Added has_link column to messages table")
            
            # Add sticker_emoji column if missing
            if 'sticker_emoji' not in columns:
                conn.execute("ALTER TABLE messages ADD COLUMN sticker_emoji TEXT")
                logger.info("Added sticker_emoji column to messages table")
            
            # Check if app_settings table has new columns
            cursor = conn.execute("PRAGMA table_info(app_settings)")
            settings_columns = {row[1] for row in cursor.fetchall()}
            
            # Add track_reactions column if missing
            if 'track_reactions' not in settings_columns:
                conn.execute("ALTER TABLE app_settings ADD COLUMN track_reactions BOOLEAN NOT NULL DEFAULT 1")
                logger.info("Added track_reactions column to app_settings table")
            
            # Add reaction_fetch_delay column if missing
            if 'reaction_fetch_delay' not in settings_columns:
                conn.execute("ALTER TABLE app_settings ADD COLUMN reaction_fetch_delay REAL NOT NULL DEFAULT 0.5")
                logger.info("Added reaction_fetch_delay column to app_settings table")
            
            # Check if user_license_cache table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_license_cache'")
            if not cursor.fetchone():
                conn.execute("""
                    CREATE TABLE user_license_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_email TEXT NOT NULL UNIQUE,
                        license_tier TEXT NOT NULL DEFAULT 'silver',
                        expiration_date TIMESTAMP,
                        max_devices INTEGER NOT NULL DEFAULT 1,
                        max_groups INTEGER NOT NULL DEFAULT 3,
                        last_synced TIMESTAMP,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_license_cache_email ON user_license_cache(user_email)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_license_cache_active ON user_license_cache(is_active)")
                logger.info("Created user_license_cache table")
            
            # Create indexes if they don't exist
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_message_type ON messages(message_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reactions_message_id ON reactions(message_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reactions_user_id_group_id ON reactions(user_id, group_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reactions_message_link ON reactions(message_link)")
            
        except Exception as e:
            logger.error(f"Error running migrations: {e}")
            # Don't raise - migrations are best effort
    
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
                    track_reactions=bool(_safe_get_row_value(row, 'track_reactions', True)),
                    reaction_fetch_delay=_safe_get_row_value(row, 'reaction_fetch_delay', 0.5),
                    created_at=_parse_datetime(row['created_at']),
                    updated_at=_parse_datetime(row['updated_at'])
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
                        track_reactions = ?,
                        reaction_fetch_delay = ?,
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
                    settings.download_audio,
                    settings.track_reactions,
                    settings.reaction_fetch_delay
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
                last_used=_parse_datetime(row['last_used']),
                created_at=_parse_datetime(row['created_at'])
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
                    last_fetch_date=_parse_datetime(row['last_fetch_date']),
                    total_messages=row['total_messages'],
                    created_at=_parse_datetime(row['created_at']),
                    updated_at=_parse_datetime(row['updated_at'])
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
    
    # ==================== Messages ====================
    
    def save_message(self, message: Message) -> Optional[int]:
        """Save a message."""
        try:
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
                    message.content,
                    message.caption,
                    message.date_sent,
                    message.has_media,
                    message.media_type,
                    message.media_count,
                    message.message_link,
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
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [Message(
                id=row['id'],
                message_id=row['message_id'],
                group_id=row['group_id'],
                user_id=row['user_id'],
                content=row['content'],
                caption=row['caption'],
                date_sent=_parse_datetime(row['date_sent']),
                has_media=bool(row['has_media']),
                media_type=row['media_type'],
                media_count=row['media_count'],
                message_link=row['message_link'],
                message_type=_safe_get_row_value(row, 'message_type'),
                has_sticker=bool(_safe_get_row_value(row, 'has_sticker', False)),
                has_link=bool(_safe_get_row_value(row, 'has_link', False)),
                sticker_emoji=_safe_get_row_value(row, 'sticker_emoji'),
                is_deleted=bool(row['is_deleted']),
                created_at=_parse_datetime(row['created_at']),
                updated_at=_parse_datetime(row['updated_at'])
            ) for row in cursor.fetchall()]
    
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
                created_at=_parse_datetime(row['created_at'])
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
    
    # ==================== Reactions ====================
    
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
    
    # ==================== User Activity Statistics ====================
    
    def get_user_activity_stats(
        self,
        user_id: int,
        group_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive activity statistics for a user."""
        stats = {}
        
        with self.get_connection() as conn:
            # Build base query conditions
            msg_conditions = ["m.user_id = ?", "m.is_deleted = 0"]
            params = [user_id]
            
            if group_id:
                msg_conditions.append("m.group_id = ?")
                params.append(group_id)
            
            if start_date:
                msg_conditions.append("m.date_sent >= ?")
                params.append(start_date)
            
            if end_date:
                msg_conditions.append("m.date_sent <= ?")
                params.append(end_date)
            
            where_clause = " AND ".join(msg_conditions)
            
            # Total messages
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM messages m
                WHERE {where_clause}
            """, params)
            stats['total_messages'] = cursor.fetchone()[0]
            
            # Total reactions given by user
            reaction_conditions = ["r.user_id = ?"]
            reaction_params = [user_id]
            
            if group_id:
                reaction_conditions.append("r.group_id = ?")
                reaction_params.append(group_id)
            
            reaction_where = " AND ".join(reaction_conditions)
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM reactions r
                WHERE {reaction_where}
            """, reaction_params)
            stats['total_reactions'] = cursor.fetchone()[0]
            
            # Message type breakdown
            cursor = conn.execute(f"""
                SELECT 
                    COUNT(CASE WHEN m.message_type = 'sticker' OR m.has_sticker = 1 THEN 1 END) as stickers,
                    COUNT(CASE WHEN m.message_type = 'video' OR m.media_type = 'video' THEN 1 END) as videos,
                    COUNT(CASE WHEN m.message_type = 'photo' OR m.media_type = 'photo' THEN 1 END) as photos,
                    COUNT(CASE WHEN m.has_link = 1 THEN 1 END) as links,
                    COUNT(CASE WHEN m.message_type = 'document' OR m.media_type = 'document' THEN 1 END) as documents,
                    COUNT(CASE WHEN m.message_type IN ('audio', 'voice') OR m.media_type = 'audio' THEN 1 END) as audio,
                    COUNT(CASE WHEN m.message_type = 'text' OR (m.content IS NOT NULL AND m.content != '') THEN 1 END) as text_messages
                FROM messages m
                WHERE {where_clause}
            """, params)
            row = cursor.fetchone()
            stats['total_stickers'] = row[0] or 0
            stats['total_videos'] = row[1] or 0
            stats['total_photos'] = row[2] or 0
            stats['total_links'] = row[3] or 0
            stats['total_documents'] = row[4] or 0
            stats['total_audio'] = row[5] or 0
            stats['total_text_messages'] = row[6] or 0
            
            # First and last activity dates
            cursor = conn.execute(f"""
                SELECT MIN(m.date_sent), MAX(m.date_sent)
                FROM messages m
                WHERE {where_clause}
            """, params)
            row = cursor.fetchone()
            stats['first_activity_date'] = _parse_datetime(row[0]) if row[0] else None
            stats['last_activity_date'] = _parse_datetime(row[1]) if row[1] else None
            
            # Messages by group (if group_id not specified)
            if not group_id:
                cursor = conn.execute(f"""
                    SELECT m.group_id, COUNT(*) as count
                    FROM messages m
                    WHERE {where_clause}
                    GROUP BY m.group_id
                """, params)
                stats['messages_by_group'] = {row[0]: row[1] for row in cursor.fetchall()}
            else:
                stats['messages_by_group'] = {}
        
        return stats
    
    def get_message_type_breakdown(
        self,
        user_id: int,
        group_id: Optional[int] = None
    ) -> Dict[str, int]:
        """Get detailed message type breakdown for a user."""
        conditions = ["user_id = ?", "is_deleted = 0"]
        params = [user_id]
        
        if group_id:
            conditions.append("group_id = ?")
            params.append(group_id)
        
        where_clause = " AND ".join(conditions)
        
        with self.get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT 
                    COALESCE(message_type, 'unknown') as msg_type,
                    COUNT(*) as count
                FROM messages
                WHERE {where_clause}
                GROUP BY msg_type
            """, params)
            return {row[0]: row[1] for row in cursor.fetchall()}
    
    # ==================== Login Credentials ====================
    
    def save_login_credential(self, email: str, encrypted_password: str) -> bool:
        """Save or update login credential."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO login_credentials (email, encrypted_password)
                    VALUES (?, ?)
                    ON CONFLICT(email) DO UPDATE SET
                        encrypted_password = excluded.encrypted_password,
                        updated_at = CURRENT_TIMESTAMP
                """, (email, encrypted_password))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving login credential: {e}")
            return False
    
    def get_login_credential(self) -> Optional[LoginCredential]:
        """Get saved login credential (returns the first one if multiple exist)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM login_credentials 
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    return LoginCredential(
                        id=row['id'],
                        email=row['email'],
                        encrypted_password=row['encrypted_password'],
                        created_at=_parse_datetime(row['created_at']),
                        updated_at=_parse_datetime(row['updated_at'])
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting login credential: {e}")
            return None
    
    def delete_login_credential(self, email: Optional[str] = None) -> bool:
        """Delete login credential(s). If email is None, delete all."""
        try:
            with self.get_connection() as conn:
                if email:
                    conn.execute("DELETE FROM login_credentials WHERE email = ?", (email,))
                else:
                    conn.execute("DELETE FROM login_credentials")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting login credential: {e}")
            return False
    
    # ==================== User License Cache ====================
    
    def save_license_cache(self, license_cache: UserLicenseCache) -> Optional[int]:
        """Save or update license cache."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO user_license_cache 
                    (user_email, license_tier, expiration_date, max_devices, max_groups, last_synced, is_active)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                    ON CONFLICT(user_email) DO UPDATE SET
                        license_tier = excluded.license_tier,
                        expiration_date = excluded.expiration_date,
                        max_devices = excluded.max_devices,
                        max_groups = excluded.max_groups,
                        last_synced = CURRENT_TIMESTAMP,
                        is_active = excluded.is_active,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    license_cache.user_email,
                    license_cache.license_tier,
                    license_cache.expiration_date,
                    license_cache.max_devices,
                    license_cache.max_groups,
                    license_cache.is_active
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving license cache: {e}")
            return None
    
    def get_license_cache(self, user_email: str) -> Optional[UserLicenseCache]:
        """Get license cache by user email."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM user_license_cache WHERE user_email = ?",
                (user_email,)
            )
            row = cursor.fetchone()
            if row:
                return UserLicenseCache(
                    id=row['id'],
                    user_email=row['user_email'],
                    license_tier=row['license_tier'],
                    expiration_date=_parse_datetime(row['expiration_date']),
                    max_devices=row['max_devices'],
                    max_groups=row['max_groups'],
                    last_synced=_parse_datetime(row['last_synced']),
                    is_active=bool(row['is_active']),
                    created_at=_parse_datetime(row['created_at']),
                    updated_at=_parse_datetime(row['updated_at'])
                )
            return None
    
    def delete_license_cache(self, user_email: str) -> bool:
        """Delete license cache for a user."""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "DELETE FROM user_license_cache WHERE user_email = ?",
                    (user_email,)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting license cache: {e}")
            return False

