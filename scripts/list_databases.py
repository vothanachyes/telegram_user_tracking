#!/usr/bin/env python3
"""
List all databases used by the Telegram User Tracking application.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.constants import USER_DATA_DIR, APP_DATA_DIR, DATABASE_PATH, SAMPLE_DATABASE_PATH
from utils.database_path import get_user_database_path


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def list_databases():
    """List all databases found in the application."""
    print("=" * 80)
    print("Telegram User Tracking - Database List")
    print("=" * 80)
    print()
    
    databases = []
    
    # 1. Development database (from DATABASE_PATH)
    dev_db = Path(DATABASE_PATH).resolve()
    if dev_db.exists():
        size = dev_db.stat().st_size
        databases.append({
            "name": "Development Database",
            "path": str(dev_db),
            "size": size,
            "type": "Development"
        })
    
    # 2. Sample database
    sample_db = Path(SAMPLE_DATABASE_PATH).resolve()
    if sample_db.exists():
        size = sample_db.stat().st_size
        databases.append({
            "name": "Sample Database",
            "path": str(sample_db),
            "size": size,
            "type": "Sample"
        })
    
    # 3. Fallback database
    fallback_db = USER_DATA_DIR / "app.db"
    if fallback_db.exists():
        size = fallback_db.stat().st_size
        databases.append({
            "name": "Fallback Database",
            "path": str(fallback_db.resolve()),
            "size": size,
            "type": "Fallback"
        })
    
    # 4. Per-user databases
    databases_dir = USER_DATA_DIR / "databases"
    if databases_dir.exists():
        for db_file in databases_dir.glob("app_*.db"):
            size = db_file.stat().st_size
            # Extract UID from filename
            uid = db_file.stem.replace("app_", "")
            databases.append({
                "name": f"User Database (UID: {uid[:8]}...)",
                "path": str(db_file.resolve()),
                "size": size,
                "type": "Per-User",
                "uid": uid
            })
    
    # Print results
    if not databases:
        print("No databases found.")
        print()
        print("Expected locations:")
        print(f"  Development: {dev_db}")
        print(f"  Sample: {sample_db}")
        print(f"  Fallback: {fallback_db}")
        print(f"  Per-user: {databases_dir}/app_*.db")
        return
    
    print(f"Found {len(databases)} database(s):")
    print()
    
    for i, db in enumerate(databases, 1):
        print(f"{i}. {db['name']}")
        print(f"   Type: {db['type']}")
        print(f"   Path: {db['path']}")
        print(f"   Size: {format_size(db['size'])}")
        if 'uid' in db:
            print(f"   UID: {db['uid']}")
        print()
    
    # Summary
    total_size = sum(db['size'] for db in databases)
    print("=" * 80)
    print(f"Total: {len(databases)} database(s), {format_size(total_size)} total")
    print()
    
    # Path information
    print("Path Information:")
    print(f"  USER_DATA_DIR: {USER_DATA_DIR}")
    print(f"  USER_DATA_DIR (resolved): {USER_DATA_DIR.resolve()}")
    print(f"  APP_DATA_DIR: {APP_DATA_DIR}")
    print(f"  APP_DATA_DIR (resolved): {APP_DATA_DIR.resolve()}")
    print(f"  DATABASE_PATH: {DATABASE_PATH}")
    print(f"  DATABASE_PATH (resolved): {Path(DATABASE_PATH).resolve()}")
    print()


if __name__ == "__main__":
    try:
        list_databases()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

