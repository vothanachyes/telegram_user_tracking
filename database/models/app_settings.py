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
    download_media: bool = False
    max_file_size_mb: int = 3
    fetch_delay_seconds: float = 5.0
    download_photos: bool = False
    download_videos: bool = False
    download_documents: bool = False
    download_audio: bool = False
    track_reactions: bool = True
    reaction_fetch_delay: float = 0.5
    pin_enabled: bool = False
    encrypted_pin: Optional[str] = None
    user_encrypted_pin: Optional[str] = None  # PIN encrypted with Firebase user ID
    pin_attempt_count: int = 0
    pin_lockout_until: Optional[datetime] = None
    rate_limit_warning_last_seen: Optional[datetime] = None
    db_path: Optional[str] = None  # Custom database path (None = use default)
    encryption_enabled: bool = False  # Database encryption enabled
    encryption_key_hash: Optional[str] = None  # Hash of encryption key (encrypted with DPAPI)
    session_encryption_enabled: bool = False  # Session file encryption disabled (reverted - using Telethon's built-in encryption)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

