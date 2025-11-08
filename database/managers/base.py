"""
Base database manager with connection management, migrations, and helper functions.
"""

import sqlite3
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
        # Normalize database path for comparison
        normalized_path = str(Path(self.db_path).resolve())
        
        # Check if database file already exists (first time initialization)
        db_file_exists = Path(self.db_path).exists()
        
        # Check if this database has already been initialized in this session
        is_first_init = normalized_path not in _initialized_databases
        
        try:
            with sqlite3.connect(self.db_path) as conn:
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

