"""
Database management CLI commands.

Provides commands for:
- Clearing database data (with option to preserve system/app data)
- Initializing sample data from SQL file
- Dumping current data to SQL file
"""

import argparse
import sqlite3
import sys
import os
from pathlib import Path
from typing import Optional
import logging

# Import constants with fallback for DATABASE_PATH
try:
    from utils.constants import DATABASE_PATH
except ImportError:
    # Fallback if utils.constants can't be imported
    DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/app.db")

logger = logging.getLogger(__name__)

# Tables categorized by type
SYSTEM_TABLES = ['app_settings']  # System/app configuration data
AUTH_TABLES = ['login_credentials', 'user_license_cache', 'telegram_credentials']  # Authentication/license data
USER_DATA_TABLES = [
    'telegram_groups',
    'telegram_users',
    'messages',
    'reactions',
    'media_files',
    'deleted_messages',
    'deleted_users'
]  # User content data

ALL_TABLES = SYSTEM_TABLES + AUTH_TABLES + USER_DATA_TABLES


def get_connection(db_path: str) -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def clear_database(db_path: str, preserve_system: bool = False, preserve_auth: bool = False) -> bool:
    """
    Clear database data.
    
    Args:
        db_path: Path to database file
        preserve_system: If True, preserve app_settings table
        preserve_auth: If True, preserve auth-related tables (login_credentials, user_license_cache, telegram_credentials)
    
    Returns:
        True if successful, False otherwise
    """
    if not Path(db_path).exists():
        logger.error(f"Database file not found: {db_path}")
        return False
    
    try:
        with get_connection(db_path) as conn:
            # Disable foreign key checks temporarily
            conn.execute("PRAGMA foreign_keys = OFF")
            
            # Determine which tables to clear
            tables_to_clear = []
            
            if not preserve_system:
                tables_to_clear.extend(SYSTEM_TABLES)
            
            if not preserve_auth:
                tables_to_clear.extend(AUTH_TABLES)
            
            # Always clear user data tables
            tables_to_clear.extend(USER_DATA_TABLES)
            
            # Clear each table
            for table in tables_to_clear:
                try:
                    conn.execute(f"DELETE FROM {table}")
                    logger.info(f"Cleared table: {table}")
                except sqlite3.OperationalError as e:
                    logger.warning(f"Could not clear table {table}: {e}")
            
            # If app_settings was cleared, reinitialize it
            if not preserve_system and 'app_settings' in tables_to_clear:
                conn.execute("INSERT INTO app_settings (id) VALUES (1)")
                logger.info("Reinitialized app_settings with defaults")
            
            # Re-enable foreign key checks
            conn.execute("PRAGMA foreign_keys = ON")
            conn.commit()
            
            logger.info(f"Database cleared successfully. Preserved system: {preserve_system}, Preserved auth: {preserve_auth}")
            return True
            
    except Exception as e:
        logger.error(f"Error clearing database: {e}", exc_info=True)
        return False


def init_sample_data(db_path: str, sql_file_path: str) -> bool:
    """
    Initialize database with sample data from SQL file.
    
    Args:
        db_path: Path to database file
        sql_file_path: Path to SQL file containing sample data
    
    Returns:
        True if successful, False otherwise
    """
    sql_path = Path(sql_file_path)
    if not sql_path.exists():
        logger.error(f"SQL file not found: {sql_file_path}")
        return False
    
    if not Path(db_path).exists():
        logger.error(f"Database file not found: {db_path}")
        return False
    
    try:
        # Read SQL file
        sql_content = sql_path.read_text(encoding='utf-8')
        
        with get_connection(db_path) as conn:
            # Execute SQL script
            conn.executescript(sql_content)
            conn.commit()
            
            logger.info(f"Sample data loaded successfully from {sql_file_path}")
            return True
            
    except Exception as e:
        logger.error(f"Error loading sample data: {e}", exc_info=True)
        return False


def dump_data(db_path: str, output_file: str, include_system: bool = True, include_auth: bool = True) -> bool:
    """
    Dump database data to SQL file.
    
    Args:
        db_path: Path to database file
        output_file: Path to output SQL file
        include_system: If True, include app_settings data
        include_auth: If True, include auth-related tables
    
    Returns:
        True if successful, False otherwise
    """
    if not Path(db_path).exists():
        logger.error(f"Database file not found: {db_path}")
        return False
    
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine which tables to dump
        tables_to_dump = []
        
        if include_system:
            tables_to_dump.extend(SYSTEM_TABLES)
        
        if include_auth:
            tables_to_dump.extend(AUTH_TABLES)
        
        # Always include user data
        tables_to_dump.extend(USER_DATA_TABLES)
        
        sql_lines = [
            "-- =====================================================",
            "-- Telegram User Tracking - Database Dump",
            "-- =====================================================",
            "-- Generated by db_commands.py",
            "-- =====================================================",
            "",
            "-- Disable foreign key checks temporarily",
            "PRAGMA foreign_keys = OFF;",
            ""
        ]
        
        with get_connection(db_path) as conn:
            for table in tables_to_dump:
                try:
                    # Check if table exists
                    cursor = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (table,)
                    )
                    if not cursor.fetchone():
                        logger.warning(f"Table {table} does not exist, skipping")
                        continue
                    
                    # Get table data
                    cursor = conn.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    
                    if not rows:
                        logger.info(f"Table {table} is empty, skipping")
                        continue
                    
                    # Get column names
                    column_names = [description[0] for description in cursor.description]
                    
                    # Write table header
                    sql_lines.append(f"-- =====================================================")
                    sql_lines.append(f"-- {table.upper().replace('_', ' ')} ({len(rows)} records)")
                    sql_lines.append(f"-- =====================================================")
                    sql_lines.append(f"INSERT OR REPLACE INTO {table} (")
                    sql_lines.append(f"    {', '.join(column_names)}")
                    sql_lines.append(f") VALUES")
                    
                    # Write data rows
                    value_lines = []
                    for row in rows:
                        values = []
                        for value in row:
                            if value is None:
                                values.append("NULL")
                            elif isinstance(value, str):
                                # Escape single quotes
                                escaped = value.replace("'", "''")
                                values.append(f"'{escaped}'")
                            elif isinstance(value, (int, float)):
                                values.append(str(value))
                            else:
                                # Convert to string and escape
                                escaped = str(value).replace("'", "''")
                                values.append(f"'{escaped}'")
                        
                        value_lines.append(f"({', '.join(values)})")
                    
                    # Join values with commas, last one with semicolon
                    for i, value_line in enumerate(value_lines):
                        if i < len(value_lines) - 1:
                            sql_lines.append(f"{value_line},")
                        else:
                            sql_lines.append(f"{value_line};")
                    
                    sql_lines.append("")
                    
                except Exception as e:
                    logger.warning(f"Error dumping table {table}: {e}")
                    continue
            
            # Re-enable foreign key checks
            sql_lines.append("-- Re-enable foreign key checks")
            sql_lines.append("PRAGMA foreign_keys = ON;")
            sql_lines.append("")
            sql_lines.append("-- =====================================================")
            sql_lines.append("-- END OF DUMP")
            sql_lines.append("-- =====================================================")
        
        # Write to file
        output_path.write_text("\n".join(sql_lines), encoding='utf-8')
        
        logger.info(f"Database dumped successfully to {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error dumping database: {e}", exc_info=True)
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Database management commands for Telegram User Tracking',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clear all data (including system and auth)
  python -m utils.db_commands clear-db
  
  # Clear only user data (preserve system and auth)
  python -m utils.db_commands clear-db --preserve-system --preserve-auth
  
  # Initialize sample data
  python -m utils.db_commands init-sample-data
  
  # Dump current data to SQL file
  python -m utils.db_commands dump-data --output tests/fixtures/demo_data.sql
        """
    )
    
    parser.add_argument(
        '--db-path',
        type=str,
        default=DATABASE_PATH,
        help=f'Path to database file (default: {DATABASE_PATH})'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Clear database command
    clear_parser = subparsers.add_parser('clear-db', help='Clear database data')
    clear_parser.add_argument(
        '--preserve-system',
        action='store_true',
        help='Preserve app_settings table (system data)'
    )
    clear_parser.add_argument(
        '--preserve-auth',
        action='store_true',
        help='Preserve auth-related tables (login_credentials, user_license_cache, telegram_credentials)'
    )
    
    # Init sample data command
    init_parser = subparsers.add_parser('init-sample-data', help='Initialize database with sample data')
    init_parser.add_argument(
        '--sql-file',
        type=str,
        default='tests/fixtures/demo_data.sql',
        help='Path to SQL file with sample data (default: tests/fixtures/demo_data.sql)'
    )
    
    # Dump data command
    dump_parser = subparsers.add_parser('dump-data', help='Dump database data to SQL file')
    dump_parser.add_argument(
        '--output',
        type=str,
        default='tests/fixtures/demo_data.sql',
        help='Path to output SQL file (default: tests/fixtures/demo_data.sql)'
    )
    dump_parser.add_argument(
        '--exclude-system',
        action='store_true',
        help='Exclude app_settings table from dump'
    )
    dump_parser.add_argument(
        '--exclude-auth',
        action='store_true',
        help='Exclude auth-related tables from dump'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    success = False
    
    if args.command == 'clear-db':
        success = clear_database(
            args.db_path,
            preserve_system=args.preserve_system,
            preserve_auth=args.preserve_auth
        )
    elif args.command == 'init-sample-data':
        success = init_sample_data(args.db_path, args.sql_file)
    elif args.command == 'dump-data':
        success = dump_data(
            args.db_path,
            args.output,
            include_system=not args.exclude_system,
            include_auth=not args.exclude_auth
        )
    else:
        parser.print_help()
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

