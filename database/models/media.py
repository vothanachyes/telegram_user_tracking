"""
Media file model.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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

