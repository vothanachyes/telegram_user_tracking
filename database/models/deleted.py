"""
Soft-deleted entities tracking models.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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

