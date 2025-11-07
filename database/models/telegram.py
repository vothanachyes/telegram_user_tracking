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

