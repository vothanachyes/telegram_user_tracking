"""
Database fixtures for testing.
"""

import sqlite3
import tempfile
from pathlib import Path
from typing import Optional
from database.managers.db_manager import DatabaseManager
from database.models.schema import CREATE_TABLES_SQL


def create_test_db_manager(db_path: Optional[str] = None) -> DatabaseManager:
    """
    Create a test database manager with in-memory or temporary file database.
    
    Args:
        db_path: Path to database file. If None, uses in-memory database.
    
    Returns:
        DatabaseManager instance with test database.
    """
    if db_path is None:
        # Use in-memory database for faster tests
        db_path = ":memory:"
    
    # Create database manager
    db_manager = DatabaseManager(db_path)
    
    # Initialize schema if using in-memory database
    if db_path == ":memory:":
        with db_manager.get_connection() as conn:
            conn.executescript(CREATE_TABLES_SQL)
            conn.commit()
    
    return db_manager


def create_temp_db_file() -> str:
    """
    Create a temporary database file for testing.
    
    Returns:
        Path to temporary database file.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    return temp_file.name


def cleanup_temp_db(db_path: str):
    """
    Clean up temporary database file.
    
    Args:
        db_path: Path to database file to delete.
    """
    try:
        if db_path and db_path != ":memory:":
            path = Path(db_path)
            if path.exists():
                path.unlink()
    except Exception:
        pass

