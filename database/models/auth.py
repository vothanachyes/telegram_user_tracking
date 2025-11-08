"""
Authentication-related models: login credentials and license cache.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class LoginCredential:
    """Firebase login credential model for saved email/password."""
    id: Optional[int] = None
    email: str = ""
    encrypted_password: str = ""  # Encrypted password
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class UserLicenseCache:
    """User license cache model for local storage."""
    id: Optional[int] = None
    user_email: str = ""
    license_tier: str = "silver"  # silver, gold, premium
    expiration_date: Optional[datetime] = None
    max_devices: int = 1
    max_groups: int = 3
    max_accounts: int = 1
    last_synced: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

