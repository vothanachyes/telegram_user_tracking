"""
Database manager for SQLite operations.

DEPRECATED: This file is deprecated. Please import from database.managers instead.
This file will be removed in a future release.
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "database.db_manager is deprecated. Please import from database.managers instead. "
    "For example: from database.managers import DatabaseManager",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from database.managers import DatabaseManager

__all__ = ['DatabaseManager']
