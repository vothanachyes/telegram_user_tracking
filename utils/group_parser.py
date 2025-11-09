"""
Group input parser utility for parsing different group input formats.
"""

import re
from typing import Tuple, Optional


def parse_group_input(input_str: str) -> Tuple[Optional[int], Optional[str], Optional[str], Optional[str]]:
    """
    Parse group input string to extract group ID, username, or invite link.
    
    Supports:
    - Group links: https://t.me/groupname or https://t.me/c/1234567890/123
    - Invite links: https://t.me/joinchat/... or https://t.me/+...
    - Group ID: 1234567890 or -1001234567890
    - Raw group ID: -1001234567890 or 1001234567890 (auto-converts to -100...)
    - Username: @groupname or groupname
    
    Args:
        input_str: Input string to parse
        
    Returns:
        Tuple of (group_id, username, invite_link, error_message)
        - group_id: Telegram group ID if found, None otherwise
        - username: Group username if found, None otherwise
        - invite_link: Invite link URL if found, None otherwise
        - error_message: Error message if parsing failed, None otherwise
    """
    if not input_str or not input_str.strip():
        return None, None, None, "Input cannot be empty"
    
    input_str = input_str.strip()
    
    # Try invite link pattern first (before regular telegram links)
    # Pattern: https://t.me/joinchat/... or https://t.me/+...
    invite_link_pattern = r'https?://t\.me/(?:joinchat/|\+)([A-Za-z0-9_-]+)'
    match = re.search(invite_link_pattern, input_str)
    if match:
        # Return the full invite link URL - Telethon can resolve it
        invite_link = input_str.strip()
        return None, None, invite_link, None
    
    # Try to extract from Telegram links
    # Pattern: https://t.me/groupname or https://t.me/c/1234567890/123
    telegram_link_pattern = r'https?://t\.me/(?:c/)?([^/]+)'
    match = re.search(telegram_link_pattern, input_str)
    if match:
        extracted = match.group(1)
        # Check if it's a numeric ID (from /c/ path)
        if extracted.isdigit() or (extracted.startswith('-') and extracted[1:].isdigit()):
            try:
                group_id = int(extracted)
                
                # Handle case where user provides positive ID starting with "100" (should be "-100...")
                if group_id > 0 and str(group_id).startswith('100') and len(str(group_id)) > 3:
                    group_id = int(f"-{group_id}")
                
                return group_id, None, None, None
            except ValueError:
                pass
        else:
            # It's a username
            username = extracted.lstrip('@')
            return None, username, None, None
    
    # Try to parse as group ID (numeric)
    # Remove any non-numeric characters except minus sign
    numeric_str = re.sub(r'[^\d-]', '', input_str)
    if numeric_str and (numeric_str.isdigit() or (numeric_str.startswith('-') and numeric_str[1:].isdigit())):
        try:
            group_id = int(numeric_str)
            
            # Handle case where user provides positive ID starting with "100" (should be "-100...")
            # Example: 1001799272128 should be -1001799272128
            if group_id > 0 and str(group_id).startswith('100') and len(str(group_id)) > 3:
                # Convert to negative format: -100{rest}
                group_id = int(f"-{group_id}")
            
            return group_id, None, None, None
        except ValueError:
            pass
    
    # Try to extract username (starts with @ or alphanumeric)
    username_pattern = r'@?([a-zA-Z0-9_]{5,32})'
    match = re.match(username_pattern, input_str)
    if match:
        username = match.group(1)
        return None, username, None, None
    
    return None, None, None, "Could not parse group input. Please provide a group ID, username, or Telegram link."

