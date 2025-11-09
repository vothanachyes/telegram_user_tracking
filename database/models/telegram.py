"""
Telegram-related models: credentials, groups, and users.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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
    group_photo_path: Optional[str] = None
    last_fetch_date: Optional[datetime] = None
    total_messages: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class GroupFetchHistory:
    """Group fetch history model."""
    id: Optional[int] = None
    group_id: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    message_count: int = 0
    account_phone_number: Optional[str] = None
    account_full_name: Optional[str] = None  # Static copy to avoid losing reference if account deleted
    account_username: Optional[str] = None  # Static copy to avoid losing reference if account deleted
    total_users_fetched: int = 0  # Total unique users in this fetch
    total_media_fetched: int = 0  # Total media files in this fetch
    total_stickers: int = 0  # Total stickers in this fetch
    total_photos: int = 0  # Total photos in this fetch
    total_videos: int = 0  # Total videos in this fetch
    total_documents: int = 0  # Total documents in this fetch
    total_audio: int = 0  # Total audio files in this fetch
    total_links: int = 0  # Total messages with links in this fetch
    created_at: Optional[datetime] = None


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

