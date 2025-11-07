"""
Database models and schema definitions for the Telegram User Tracking application.

DEPRECATED: This file is deprecated. Please import from database.models instead.
This file will be removed in a future release.
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "database.models is deprecated. Please import from database.models instead. "
    "For example: from database.models import AppSettings, Message, etc.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from database.models import (
    AppSettings,
    TelegramCredential,
    TelegramGroup,
    TelegramUser,
    Message,
    Reaction,
    MediaFile,
    LoginCredential,
    UserLicenseCache,
    DeletedMessage,
    DeletedUser,
    CREATE_TABLES_SQL
)

__all__ = [
    'AppSettings',
    'TelegramCredential',
    'TelegramGroup',
    'TelegramUser',
    'Message',
    'Reaction',
    'MediaFile',
    'LoginCredential',
    'UserLicenseCache',
    'DeletedMessage',
    'DeletedUser',
    'CREATE_TABLES_SQL',
]
