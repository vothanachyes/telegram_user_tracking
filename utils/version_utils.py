"""
Semantic versioning utilities for comparing app versions.
"""

import re
from typing import Tuple, Optional


def parse_version(version_string: str) -> Optional[Tuple[int, int, int]]:
    """
    Parse semantic version string to tuple (major, minor, patch).
    
    Args:
        version_string: Version string (e.g., "1.0.1", "2.3.4")
    
    Returns:
        Tuple of (major, minor, patch) or None if invalid
    """
    if not version_string:
        return None
    
    # Remove 'v' prefix if present
    version_string = version_string.lstrip('vV')
    
    # Match semantic version pattern (MAJOR.MINOR.PATCH)
    pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-.*)?$'
    match = re.match(pattern, version_string)
    
    if match:
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        return (major, minor, patch)
    
    return None


def compare_versions(current: str, latest: str) -> int:
    """
    Compare two semantic versions.
    
    Args:
        current: Current version string
        latest: Latest version string
    
    Returns:
        -1 if current < latest
         0 if current == latest
         1 if current > latest
    """
    current_tuple = parse_version(current)
    latest_tuple = parse_version(latest)
    
    if current_tuple is None or latest_tuple is None:
        # If either version is invalid, consider them equal
        return 0
    
    if current_tuple < latest_tuple:
        return -1
    elif current_tuple > latest_tuple:
        return 1
    else:
        return 0


def is_newer_version(latest: str, current: str) -> bool:
    """
    Check if latest version is newer than current version.
    
    Args:
        latest: Latest version string
        current: Current version string
    
    Returns:
        True if latest > current, False otherwise
    """
    return compare_versions(current, latest) < 0

