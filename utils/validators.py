"""
Validation utilities.
"""

import re
from typing import Optional, Tuple
from utils.constants import PHONE_PATTERN, EMAIL_PATTERN


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Validate phone number.
    Returns (is_valid, error_message)
    """
    if not phone:
        return False, "Phone number is required"
    
    if not re.match(PHONE_PATTERN, phone):
        return False, "Invalid phone number format"
    
    return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email address.
    Returns (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"
    
    if not re.match(EMAIL_PATTERN, email):
        return False, "Invalid email format"
    
    return True, None


def validate_telegram_api_id(api_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Telegram API ID.
    Returns (is_valid, error_message)
    """
    if not api_id:
        return False, "API ID is required"
    
    if not api_id.isdigit():
        return False, "API ID must be numeric"
    
    return True, None


def validate_telegram_api_hash(api_hash: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Telegram API Hash.
    Returns (is_valid, error_message)
    """
    if not api_hash:
        return False, "API Hash is required"
    
    if len(api_hash) != 32:
        return False, "API Hash must be 32 characters"
    
    if not re.match(r'^[a-f0-9]{32}$', api_hash):
        return False, "API Hash must contain only lowercase hex characters"
    
    return True, None


def validate_file_size(size_mb: int) -> Tuple[bool, Optional[str]]:
    """
    Validate file size limit.
    Returns (is_valid, error_message)
    """
    if size_mb < 1:
        return False, "File size must be at least 1 MB"
    
    if size_mb > 2000:  # 2GB max
        return False, "File size cannot exceed 2000 MB (2GB)"
    
    return True, None


def validate_delay(delay: float) -> Tuple[bool, Optional[str]]:
    """
    Validate fetch delay.
    Returns (is_valid, error_message)
    """
    if delay < 0:
        return False, "Delay cannot be negative"
    
    if delay > 60:
        return False, "Delay cannot exceed 60 seconds"
    
    return True, None


def validate_path(path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate directory path.
    Returns (is_valid, error_message)
    """
    if not path:
        return False, "Path is required"
    
    # Basic path validation (cross-platform)
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
    if any(char in path for char in invalid_chars):
        return False, "Path contains invalid characters"
    
    return True, None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by replacing invalid characters.
    """
    # Replace invalid characters with underscore
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Remove multiple consecutive underscores
    while '__' in filename:
        filename = filename.replace('__', '_')
    
    return filename.strip('_')


def sanitize_username(username: str) -> str:
    """
    Sanitize username for folder naming.
    """
    if not username:
        return "unknown_user"
    
    return sanitize_filename(username)

