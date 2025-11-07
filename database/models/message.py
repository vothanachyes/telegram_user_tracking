"""
Message and reaction models.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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
    message_type: Optional[str] = None  # text, sticker, video, photo, document, audio, voice, video_note, location, contact, link, poll, etc.
    has_sticker: bool = False
    has_link: bool = False  # URLs detected in content
    sticker_emoji: Optional[str] = None  # Emoji if sticker
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Reaction:
    """Reaction model for tracking user reactions to messages."""
    id: Optional[int] = None
    message_id: int = 0  # Telegram message ID that was reacted to
    group_id: int = 0  # Group where the message exists
    user_id: int = 0  # User who reacted
    emoji: str = ""  # Emoji used for reaction
    message_link: Optional[str] = None  # Telegram link to the original message
    reacted_at: Optional[datetime] = None  # When reaction was made (uses message date_sent as proxy)
    created_at: Optional[datetime] = None

