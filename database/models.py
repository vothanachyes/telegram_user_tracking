"""
Database models and schema definitions for the Telegram User Tracking application.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class AppSettings:
    """Application settings model."""
    id: int = 1
    theme: str = "dark"  # dark, light
    language: str = "en"  # en, km (Khmer)
    corner_radius: int = 10
    telegram_api_id: Optional[str] = None
    telegram_api_hash: Optional[str] = None
    download_root_dir: str = "./downloads"
    download_media: bool = True
    max_file_size_mb: int = 50
    fetch_delay_seconds: float = 1.0
    download_photos: bool = True
    download_videos: bool = True
    download_documents: bool = True
    download_audio: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class TelegramCredential:
    """Telegram credential model for saved sessions."""
    id: Optional[int] = None
    phone_number: str = ""
    session_string: Optional[str] = None  # Encrypted Pyrogram session
    is_default: bool = False
    last_used: Optional[datetime] = None
    created_at: Optional[datetime] = None


@dataclass
class TelegramGroup:
    """Telegram group model."""
    id: Optional[int] = None
    group_id: int = 0  # Telegram group ID
    group_name: str = ""
    group_username: Optional[str] = None
    last_fetch_date: Optional[datetime] = None
    total_messages: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class TelegramUser:
    """Telegram user model."""
    id: Optional[int] = None
    user_id: int = 0  # Telegram user ID
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: str = ""
    phone: Optional[str] = None
    bio: Optional[str] = None
    profile_photo_path: Optional[str] = None
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Message:
    """Message model."""
    id: Optional[int] = None
    message_id: int = 0  # Telegram message ID
    group_id: int = 0  # Telegram group ID
    user_id: int = 0  # Telegram user ID
    content: Optional[str] = None
    caption: Optional[str] = None
    date_sent: Optional[datetime] = None
    has_media: bool = False
    media_type: Optional[str] = None  # photo, video, document, audio
    media_count: int = 0
    message_link: Optional[str] = None
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class MediaFile:
    """Media file model."""
    id: Optional[int] = None
    message_id: int = 0  # Links to Message.message_id
    file_path: str = ""
    file_name: str = ""
    file_size_bytes: int = 0
    file_type: str = ""  # photo, video, document, audio
    mime_type: Optional[str] = None
    thumbnail_path: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class DeletedMessage:
    """Soft deleted messages tracking."""
    id: Optional[int] = None
    message_id: int = 0  # Telegram message ID
    group_id: int = 0
    deleted_at: Optional[datetime] = None


@dataclass
class DeletedUser:
    """Soft deleted users tracking."""
    id: Optional[int] = None
    user_id: int = 0  # Telegram user ID
    deleted_at: Optional[datetime] = None


# SQL Schema Creation Statements
CREATE_TABLES_SQL = """
-- App Settings Table
CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    theme TEXT NOT NULL DEFAULT 'dark',
    language TEXT NOT NULL DEFAULT 'en',
    corner_radius INTEGER NOT NULL DEFAULT 10,
    telegram_api_id TEXT,
    telegram_api_hash TEXT,
    download_root_dir TEXT NOT NULL DEFAULT './downloads',
    download_media BOOLEAN NOT NULL DEFAULT 1,
    max_file_size_mb INTEGER NOT NULL DEFAULT 50,
    fetch_delay_seconds REAL NOT NULL DEFAULT 1.0,
    download_photos BOOLEAN NOT NULL DEFAULT 1,
    download_videos BOOLEAN NOT NULL DEFAULT 1,
    download_documents BOOLEAN NOT NULL DEFAULT 1,
    download_audio BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (id = 1)
);

-- Telegram Credentials Table
CREATE TABLE IF NOT EXISTS telegram_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT NOT NULL UNIQUE,
    session_string TEXT,
    is_default BOOLEAN NOT NULL DEFAULT 0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Telegram Groups Table
CREATE TABLE IF NOT EXISTS telegram_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL UNIQUE,
    group_name TEXT NOT NULL,
    group_username TEXT,
    last_fetch_date TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Telegram Users Table
CREATE TABLE IF NOT EXISTS telegram_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    full_name TEXT NOT NULL,
    phone TEXT,
    bio TEXT,
    profile_photo_path TEXT,
    is_deleted BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages Table
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT,
    caption TEXT,
    date_sent TIMESTAMP NOT NULL,
    has_media BOOLEAN NOT NULL DEFAULT 0,
    media_type TEXT,
    media_count INTEGER DEFAULT 0,
    message_link TEXT,
    is_deleted BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(message_id, group_id),
    FOREIGN KEY (group_id) REFERENCES telegram_groups(group_id),
    FOREIGN KEY (user_id) REFERENCES telegram_users(user_id)
);

-- Media Files Table
CREATE TABLE IF NOT EXISTS media_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    file_type TEXT NOT NULL,
    mime_type TEXT,
    thumbnail_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(message_id)
);

-- Deleted Messages Table (for soft delete tracking)
CREATE TABLE IF NOT EXISTS deleted_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL UNIQUE,
    group_id INTEGER NOT NULL,
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Deleted Users Table (for soft delete tracking)
CREATE TABLE IF NOT EXISTS deleted_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_messages_group_id ON messages(group_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_date_sent ON messages(date_sent);
CREATE INDEX IF NOT EXISTS idx_messages_deleted ON messages(is_deleted);
CREATE INDEX IF NOT EXISTS idx_media_files_message_id ON media_files(message_id);
CREATE INDEX IF NOT EXISTS idx_telegram_users_deleted ON telegram_users(is_deleted);
CREATE INDEX IF NOT EXISTS idx_deleted_messages_message_id ON deleted_messages(message_id);
CREATE INDEX IF NOT EXISTS idx_deleted_users_user_id ON deleted_users(user_id);
"""

