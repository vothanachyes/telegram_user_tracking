"""
Base database manager with connection management, migrations, and helper functions.
"""

import sqlite3
import os
import base64
from datetime import datetime
from typing import Any, Optional
from pathlib import Path
import logging

from database.models.schema import CREATE_TABLES_SQL

logger = logging.getLogger(__name__)

# Track initialized database paths to avoid duplicate initialization logs
_initialized_databases: set[str] = set()


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
        # First try ISO format with timezone (e.g., "2025-11-08 06:39:47+00:00" or "2025-11-08T06:39:47+00:00")
        try:
            # Check if string contains timezone info (ends with +HH:MM, -HH:MM, or Z)
            has_timezone = ('+' in dt_value and ':' in dt_value.split('+')[-1]) or \
                          ('-' in dt_value and len(dt_value.split('-')) > 3) or \
                          dt_value.endswith('Z')
            
            if has_timezone:
                # Replace space between date and time with 'T' if present, and handle 'Z' suffix
                iso_str = dt_value.replace(' ', 'T', 1).replace('Z', '+00:00')
                return datetime.fromisoformat(iso_str)
        except (ValueError, TypeError):
            pass
        
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


class BaseDatabaseManager:
    """Base class for database managers with connection management and migrations."""
    
    def __init__(self, db_path: str = None):
        """Initialize database manager."""
        # Use DATABASE_PATH from constants if no path provided
        if db_path is None:
            try:
                from utils.constants import DATABASE_PATH
                db_path = DATABASE_PATH
            except (ImportError, AttributeError):
                # Fallback to default (for development)
                db_path = "./data/app.db"
        self.db_path = db_path
        self._encryption_service = None
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists."""
        # Expand user home directory if present (~)
        db_path_expanded = str(Path(self.db_path).expanduser())
        db_dir = Path(db_path_expanded).parent
        try:
            db_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to create database directory {db_dir}: {e}")
            raise
    
    def _init_database(self):
        """Initialize database with schema."""
        # Expand user home directory and normalize database path
        db_path_expanded = str(Path(self.db_path).expanduser())
        normalized_path = str(Path(db_path_expanded).resolve())
        # Update self.db_path to the expanded/resolved path
        self.db_path = normalized_path
        
        # Check if database file already exists (first time initialization)
        db_file_exists = Path(normalized_path).exists()
        
        # Check if this database has already been initialized in this session
        is_first_init = normalized_path not in _initialized_databases
        
        try:
            # Ensure parent directory exists and is writable
            db_dir = Path(normalized_path).parent
            if not db_dir.exists():
                db_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if directory is writable
            if not os.access(db_dir, os.W_OK):
                raise PermissionError(f"Database directory is not writable: {db_dir}")
            
            with sqlite3.connect(normalized_path) as conn:
                # Enable WAL (Write-Ahead Logging) mode for better concurrency
                # WAL mode allows multiple readers while one writer is active
                # This significantly reduces database lock conflicts
                conn.execute("PRAGMA journal_mode=WAL")
                
                conn.executescript(CREATE_TABLES_SQL)
                
                # Run migrations
                self._run_migrations(conn)
                
                # Initialize default settings if not exists
                cursor = conn.execute("SELECT COUNT(*) FROM app_settings")
                if cursor.fetchone()[0] == 0:
                    conn.execute("""
                        INSERT INTO app_settings (id) VALUES (1)
                    """)
                
                # Clear user data tables ONLY on first initialization (when DB file didn't exist)
                if not db_file_exists:
                    logger.info("First time database initialization - clearing user data")
                    self._clear_user_data(conn)
                
                conn.commit()
                
                # Only log once per database path
                if is_first_init:
                    logger.info("Database initialized successfully")
                    _initialized_databases.add(normalized_path)
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _clear_user_data(self, conn: sqlite3.Connection):
        """
        Clear user data tables on first database initialization only.
        Keeps essential app data: settings, credentials, license cache, login credentials, account activity.
        Removes: groups, users, messages, reactions, media files, deleted records.
        
        Note: This only runs when the database file is created for the first time.
        """
        try:
            # Clear user data tables (in order to respect foreign key constraints)
            user_data_tables = [
                'reactions',           # Must be deleted before messages
                'media_files',         # Must be deleted before messages
                'messages',            # Must be deleted before groups/users
                'deleted_messages',    # Tracking table
                'deleted_users',       # Tracking table
                'telegram_groups',     # Groups data
                'telegram_users',      # Users data
            ]
            
            for table in user_data_tables:
                try:
                    cursor = conn.execute(f"DELETE FROM {table}")
                    deleted_count = cursor.rowcount
                    if deleted_count > 0:
                        logger.info(f"Cleared {deleted_count} rows from {table}")
                except sqlite3.OperationalError as e:
                    # Table might not exist yet (first run)
                    if "no such table" not in str(e).lower():
                        logger.warning(f"Error clearing {table}: {e}")
            
            logger.info("User data cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing user data: {e}")
            # Don't raise - allow app to continue even if cleanup fails
    
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
            
            # Add pin_enabled column if missing
            if 'pin_enabled' not in settings_columns:
                conn.execute("ALTER TABLE app_settings ADD COLUMN pin_enabled BOOLEAN NOT NULL DEFAULT 0")
                logger.info("Added pin_enabled column to app_settings table")
            
            # Add encrypted_pin column if missing
            if 'encrypted_pin' not in settings_columns:
                conn.execute("ALTER TABLE app_settings ADD COLUMN encrypted_pin TEXT")
                logger.info("Added encrypted_pin column to app_settings table")
            
            # Add pin_attempt_count column if missing
            if 'pin_attempt_count' not in settings_columns:
                conn.execute("ALTER TABLE app_settings ADD COLUMN pin_attempt_count INTEGER NOT NULL DEFAULT 0")
                logger.info("Added pin_attempt_count column to app_settings table")
            
            # Add pin_lockout_until column if missing
            if 'pin_lockout_until' not in settings_columns:
                conn.execute("ALTER TABLE app_settings ADD COLUMN pin_lockout_until TIMESTAMP")
                logger.info("Added pin_lockout_until column to app_settings table")
            
            # Add user_encrypted_pin column if missing
            if 'user_encrypted_pin' not in settings_columns:
                conn.execute("ALTER TABLE app_settings ADD COLUMN user_encrypted_pin TEXT")
                logger.info("Added user_encrypted_pin column to app_settings table")
            
            # Check if user_license_cache table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_license_cache'")
            table_exists = cursor.fetchone()
            if not table_exists:
                conn.execute("""
                    CREATE TABLE user_license_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_email TEXT NOT NULL UNIQUE,
                        license_tier TEXT NOT NULL DEFAULT 'silver',
                        expiration_date TIMESTAMP,
                        max_devices INTEGER NOT NULL DEFAULT 1,
                        max_groups INTEGER NOT NULL DEFAULT 3,
                        max_accounts INTEGER NOT NULL DEFAULT 1,
                        max_account_actions INTEGER NOT NULL DEFAULT 2,
                        last_synced TIMESTAMP,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_license_cache_email ON user_license_cache(user_email)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_license_cache_active ON user_license_cache(is_active)")
                logger.info("Created user_license_cache table")
            else:
                # Table exists - check for missing columns and add them
                cursor = conn.execute("PRAGMA table_info(user_license_cache)")
                license_columns = {row[1] for row in cursor.fetchall()}
                
                # Add max_accounts column if missing
                if 'max_accounts' not in license_columns:
                    conn.execute("ALTER TABLE user_license_cache ADD COLUMN max_accounts INTEGER NOT NULL DEFAULT 1")
                    logger.info("Added max_accounts column to user_license_cache table")
                
                # Add max_account_actions column if missing
                if 'max_account_actions' not in license_columns:
                    conn.execute("ALTER TABLE user_license_cache ADD COLUMN max_account_actions INTEGER NOT NULL DEFAULT 2")
                    logger.info("Added max_account_actions column to user_license_cache table")
            
            # Check if app_update_history table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='app_update_history'")
            if not cursor.fetchone():
                conn.execute("""
                    CREATE TABLE app_update_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_email TEXT NOT NULL,
                        version TEXT NOT NULL,
                        installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        download_path TEXT,
                        UNIQUE(user_email, version)
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_app_update_history_email ON app_update_history(user_email)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_app_update_history_version ON app_update_history(version)")
                logger.info("Created app_update_history table")
            
            # Check if telegram_groups table has group_photo_path column
            cursor = conn.execute("PRAGMA table_info(telegram_groups)")
            group_columns = {row[1] for row in cursor.fetchall()}
            
            if 'group_photo_path' not in group_columns:
                conn.execute("ALTER TABLE telegram_groups ADD COLUMN group_photo_path TEXT")
                logger.info("Added group_photo_path column to telegram_groups table")
            
            # Check if group_fetch_history table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='group_fetch_history'")
            if not cursor.fetchone():
                conn.execute("""
                    CREATE TABLE group_fetch_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_id INTEGER NOT NULL,
                        start_date TIMESTAMP NOT NULL,
                        end_date TIMESTAMP NOT NULL,
                        message_count INTEGER DEFAULT 0,
                        account_phone_number TEXT,
                        account_full_name TEXT,
                        account_username TEXT,
                        total_users_fetched INTEGER DEFAULT 0,
                        total_media_fetched INTEGER DEFAULT 0,
                        total_stickers INTEGER DEFAULT 0,
                        total_photos INTEGER DEFAULT 0,
                        total_videos INTEGER DEFAULT 0,
                        total_documents INTEGER DEFAULT 0,
                        total_audio INTEGER DEFAULT 0,
                        total_links INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (group_id) REFERENCES telegram_groups(group_id)
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_fetch_history_group_id ON group_fetch_history(group_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_fetch_history_dates ON group_fetch_history(start_date, end_date)")
                logger.info("Created group_fetch_history table")
            else:
                # Check if new columns exist and add them if missing
                cursor = conn.execute("PRAGMA table_info(group_fetch_history)")
                history_columns = {row[1] for row in cursor.fetchall()}
                
                if 'account_full_name' not in history_columns:
                    conn.execute("ALTER TABLE group_fetch_history ADD COLUMN account_full_name TEXT")
                    logger.info("Added account_full_name column to group_fetch_history table")
                
                if 'account_username' not in history_columns:
                    conn.execute("ALTER TABLE group_fetch_history ADD COLUMN account_username TEXT")
                    logger.info("Added account_username column to group_fetch_history table")
                
                if 'total_users_fetched' not in history_columns:
                    conn.execute("ALTER TABLE group_fetch_history ADD COLUMN total_users_fetched INTEGER DEFAULT 0")
                    logger.info("Added total_users_fetched column to group_fetch_history table")
                
                if 'total_media_fetched' not in history_columns:
                    conn.execute("ALTER TABLE group_fetch_history ADD COLUMN total_media_fetched INTEGER DEFAULT 0")
                    logger.info("Added total_media_fetched column to group_fetch_history table")
                
                if 'total_stickers' not in history_columns:
                    conn.execute("ALTER TABLE group_fetch_history ADD COLUMN total_stickers INTEGER DEFAULT 0")
                    logger.info("Added total_stickers column to group_fetch_history table")
                
                if 'total_photos' not in history_columns:
                    conn.execute("ALTER TABLE group_fetch_history ADD COLUMN total_photos INTEGER DEFAULT 0")
                    logger.info("Added total_photos column to group_fetch_history table")
                
                if 'total_videos' not in history_columns:
                    conn.execute("ALTER TABLE group_fetch_history ADD COLUMN total_videos INTEGER DEFAULT 0")
                    logger.info("Added total_videos column to group_fetch_history table")
                
                if 'total_documents' not in history_columns:
                    conn.execute("ALTER TABLE group_fetch_history ADD COLUMN total_documents INTEGER DEFAULT 0")
                    logger.info("Added total_documents column to group_fetch_history table")
                
                if 'total_audio' not in history_columns:
                    conn.execute("ALTER TABLE group_fetch_history ADD COLUMN total_audio INTEGER DEFAULT 0")
                    logger.info("Added total_audio column to group_fetch_history table")
                
                if 'total_links' not in history_columns:
                    conn.execute("ALTER TABLE group_fetch_history ADD COLUMN total_links INTEGER DEFAULT 0")
                    logger.info("Added total_links column to group_fetch_history table")
            
            # Add rate_limit_warning_last_seen to app_settings if missing
            if 'rate_limit_warning_last_seen' not in settings_columns:
                conn.execute("ALTER TABLE app_settings ADD COLUMN rate_limit_warning_last_seen TIMESTAMP")
                logger.info("Added rate_limit_warning_last_seen column to app_settings table")
            
            # Add db_path to app_settings if missing
            if 'db_path' not in settings_columns:
                conn.execute("ALTER TABLE app_settings ADD COLUMN db_path TEXT")
                logger.info("Added db_path column to app_settings table")
            
            # Add encryption_enabled to app_settings if missing
            if 'encryption_enabled' not in settings_columns:
                conn.execute("ALTER TABLE app_settings ADD COLUMN encryption_enabled BOOLEAN NOT NULL DEFAULT 0")
                logger.info("Added encryption_enabled column to app_settings table")
            
            # Add encryption_key_hash to app_settings if missing
            if 'encryption_key_hash' not in settings_columns:
                conn.execute("ALTER TABLE app_settings ADD COLUMN encryption_key_hash TEXT")
                logger.info("Added encryption_key_hash column to app_settings table")
            
            # Add session_encryption_enabled to app_settings if missing (default: False - disabled)
            if 'session_encryption_enabled' not in settings_columns:
                conn.execute("ALTER TABLE app_settings ADD COLUMN session_encryption_enabled BOOLEAN NOT NULL DEFAULT 0")
                logger.info("Added session_encryption_enabled column to app_settings table")
            
            # Check if message_tags table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='message_tags'")
            if not cursor.fetchone():
                conn.execute("""
                    CREATE TABLE message_tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message_id INTEGER NOT NULL,
                        group_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        tag TEXT NOT NULL,
                        date_sent TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(message_id, group_id, tag),
                        FOREIGN KEY (message_id, group_id) REFERENCES messages(message_id, group_id),
                        FOREIGN KEY (user_id) REFERENCES telegram_users(user_id)
                    )
                """)
                # Create indexes for message_tags
                conn.execute("CREATE INDEX IF NOT EXISTS idx_message_tags_tag ON message_tags(tag)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_message_tags_group_id ON message_tags(group_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_message_tags_user_id ON message_tags(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_message_tags_date_sent ON message_tags(date_sent)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_message_tags_group_tag ON message_tags(group_id, tag)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_message_tags_user_group_tag ON message_tags(user_id, group_id, tag)")
                logger.info("Created message_tags table")
            
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
        # Increase timeout to 10 seconds to handle concurrent operations better
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        
        # Ensure WAL mode is enabled for this connection
        # WAL mode allows multiple readers while one writer is active
        # This significantly reduces database lock conflicts
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except Exception:
            # If WAL mode fails (e.g., on some file systems), continue with default mode
            pass
        
        return conn
    
    def get_encryption_service(self):
        """
        Get or initialize field encryption service.
        Lazy initialization to avoid circular dependencies.
        
        Returns:
            FieldEncryptionService instance, or None if encryption is disabled
        """
        if self._encryption_service is None:
            try:
                from services.database.field_encryption_service import FieldEncryptionService
                from services.database.encryption_service import DatabaseEncryptionService
                import platform
                import hashlib
                
                # Get settings to check if encryption is enabled
                with self.get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT encryption_enabled, encryption_key_hash FROM app_settings WHERE id = 1"
                    )
                    row = cursor.fetchone()
                    
                    if row and row['encryption_enabled']:
                        # Encryption is enabled - derive key from device-specific info and hash
                        # This ensures the key is consistent for the same device but different per device
                        encryption_key_hash = row['encryption_key_hash']
                        
                        if encryption_key_hash:
                            # Derive encryption key from device info and stored hash
                            # This creates a device-specific key that's consistent across sessions
                            device_id = f"{platform.node()}-{platform.machine()}-{platform.system()}"
                            
                            # Use PBKDF2 to derive a consistent key
                            from cryptography.hazmat.primitives import hashes
                            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
                            from cryptography.hazmat.backends import default_backend
                            
                            salt = hashlib.sha256(f"{device_id}-field-encryption".encode()).digest()[:16]
                            kdf = PBKDF2HMAC(
                                algorithm=hashes.SHA256(),
                                length=32,
                                salt=salt,
                                iterations=100000,
                                backend=default_backend()
                            )
                            
                            # Use the stored hash as part of the key derivation
                            key_material = f"{device_id}-{encryption_key_hash}".encode()
                            key_bytes = kdf.derive(key_material)
                            encryption_key = base64.urlsafe_b64encode(key_bytes).decode('utf-8')
                            
                            self._encryption_service = FieldEncryptionService(encryption_key)
                        else:
                            # Encryption enabled but no key hash - disable encryption
                            logger.warning("Encryption enabled but no key hash found - disabling encryption")
                            self._encryption_service = FieldEncryptionService(None)
                    else:
                        # Encryption not enabled
                        self._encryption_service = FieldEncryptionService(None)
            except Exception as e:
                logger.error(f"Error initializing encryption service: {e}")
                # Create disabled encryption service on error
                try:
                    from services.database.field_encryption_service import FieldEncryptionService
                    self._encryption_service = FieldEncryptionService(None)
                except Exception:
                    pass
        
        return self._encryption_service

