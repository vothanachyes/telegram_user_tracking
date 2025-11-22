"""
Database path utilities for per-user database management.
"""

from pathlib import Path
from typing import Optional
from utils.constants import USER_DATA_DIR


def get_user_database_path(firebase_uid: Optional[str] = None) -> str:
    """
    Get database path for a specific user or fallback path.
    
    Note: The database will be automatically initialized (created with all tables)
    when DatabaseManager is instantiated with this path. No manual initialization needed.
    
    Args:
        firebase_uid: Firebase user ID. If provided, returns user-specific database path.
                     If None, returns fallback database path.
    
    Returns:
        Path to database file as string.
        
    Examples:
        >>> get_user_database_path("abc123")
        'C:\\Users\\...\\Telegram User Tracking\\databases\\app_abc123.db'
        
        >>> get_user_database_path(None)
        'C:\\Users\\...\\Telegram User Tracking\\app.db'
    """
    if firebase_uid:
        # User-specific database: USER_DATA_DIR/databases/app_{firebase_uid}.db
        db_dir = USER_DATA_DIR / "databases"
        db_dir.mkdir(parents=True, exist_ok=True)
        return str(db_dir / f"app_{firebase_uid}.db")
    
    # Fallback database: USER_DATA_DIR/app.db (for non-authenticated users)
    return str(USER_DATA_DIR / "app.db")

