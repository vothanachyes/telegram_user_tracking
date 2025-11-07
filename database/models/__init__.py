"""
Database models package - re-exports all models for backward compatibility.
"""

from database.models.app_settings import AppSettings
from database.models.telegram import TelegramCredential, TelegramGroup, TelegramUser
from database.models.message import Message, Reaction
from database.models.media import MediaFile
from database.models.auth import LoginCredential, UserLicenseCache
from database.models.deleted import DeletedMessage, DeletedUser
from database.models.schema import CREATE_TABLES_SQL

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

