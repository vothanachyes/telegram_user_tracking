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
        db_path: Path to database file. If None, uses temporary file database.
                Note: Using in-memory (":memory:") causes issues because each
                connection gets a separate database. Use temp file instead.
    
    Returns:
        DatabaseManager instance with test database.
    """
    if db_path is None:
        # Use temporary file database instead of :memory: to ensure all managers
        # share the same database connection
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        db_path = temp_file.name
    
    # Create database manager (it will initialize schema automatically via BaseDatabaseManager)
    db_manager = DatabaseManager(db_path)
    
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

