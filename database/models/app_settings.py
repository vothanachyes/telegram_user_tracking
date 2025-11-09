"""
Application settings model.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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
    track_reactions: bool = True
    reaction_fetch_delay: float = 0.5
    pin_enabled: bool = False
    encrypted_pin: Optional[str] = None
    rate_limit_warning_last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

