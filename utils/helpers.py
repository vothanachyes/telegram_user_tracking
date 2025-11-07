"""
Helper utilities.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable
import logging

from utils.constants import (
    FOLDER_STRUCTURE, DATE_FORMAT, format_bytes,
    DATETIME_FORMAT
)
from utils.validators import sanitize_username

logger = logging.getLogger(__name__)


def create_message_folder(
    root_dir: str,
    group_id: int,
    username: str,
    date_sent: datetime,
    message_id: int
) -> str:
    """
    Create folder structure for message media.
    Returns the created folder path.
    """
    # Sanitize username
    safe_username = sanitize_username(username)
    
    # Format date
    date_str = date_sent.strftime(DATE_FORMAT)
    
    # Format time (HHMMSS)
    time_str = date_sent.strftime("%H%M%S")
    
    # Create folder path
    folder_path = os.path.join(
        root_dir,
        str(group_id),
        safe_username,
        date_str,
        f"{message_id}_{time_str}"
    )
    
    # Create directory
    Path(folder_path).mkdir(parents=True, exist_ok=True)
    
    return folder_path


def move_directory_with_progress(
    src: str,
    dst: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> bool:
    """
    Move directory from src to dst with progress tracking.
    progress_callback receives (current, total)
    """
    try:
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            logger.error(f"Source directory does not exist: {src}")
            return False
        
        # Count total files
        all_files = list(src_path.rglob('*'))
        total_files = len([f for f in all_files if f.is_file()])
        
        if total_files == 0:
            # Just move empty directory
            shutil.move(str(src_path), str(dst_path))
            return True
        
        # Create destination
        dst_path.mkdir(parents=True, exist_ok=True)
        
        # Move files with progress
        current = 0
        for item in all_files:
            if item.is_file():
                # Calculate relative path
                rel_path = item.relative_to(src_path)
                dest_file = dst_path / rel_path
                
                # Create parent directory
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Move file
                shutil.move(str(item), str(dest_file))
                
                current += 1
                if progress_callback:
                    progress_callback(current, total_files)
        
        # Remove source directory
        shutil.rmtree(src_path, ignore_errors=True)
        
        return True
    except Exception as e:
        logger.error(f"Error moving directory: {e}")
        return False


def get_directory_size(path: str) -> int:
    """
    Get total size of directory in bytes.
    """
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception as e:
        logger.error(f"Error calculating directory size: {e}")
    
    return total_size


def format_datetime(dt: Optional[datetime], format_str: str = DATETIME_FORMAT) -> str:
    """
    Format datetime to string.
    """
    if dt is None:
        return ""
    
    if isinstance(dt, str):
        return dt
    
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = DATETIME_FORMAT) -> Optional[datetime]:
    """
    Parse datetime string.
    """
    try:
        return datetime.strptime(dt_str, format_str)
    except Exception:
        return None


def ensure_directory(path: str) -> bool:
    """
    Ensure directory exists, create if not.
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        return False


def get_file_extension(filename: str) -> str:
    """
    Get file extension without dot.
    """
    return Path(filename).suffix.lstrip('.')


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to max length with suffix.
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def get_telegram_message_link(group_username: Optional[str], group_id: int, message_id: int) -> str:
    """
    Generate Telegram message link.
    """
    if group_username:
        return f"https://t.me/{group_username}/{message_id}"
    else:
        # For private groups, use c/ format
        # Remove the -100 prefix if present
        clean_id = str(group_id).replace('-100', '')
        return f"https://t.me/c/{clean_id}/{message_id}"


def is_directory_empty(path: str) -> bool:
    """
    Check if directory is empty.
    """
    try:
        return not any(Path(path).iterdir())
    except Exception:
        return True


def get_telegram_user_link(username: Optional[str]) -> Optional[str]:
    """
    Generate Telegram user profile link.
    Format: https://t.me/{username}
    Returns None if username is not provided or empty.
    """
    if not username or not username.strip():
        return None
    
    # Remove @ prefix if present
    clean_username = username.strip().lstrip('@')
    if not clean_username:
        return None
    
    return f"https://t.me/{clean_username}"

