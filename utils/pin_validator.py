"""
PIN validation and encryption utilities.
"""

import logging
from typing import Tuple, Optional
from utils.credential_storage import credential_storage

logger = logging.getLogger(__name__)


def validate_pin_format(pin: str) -> Tuple[bool, Optional[str]]:
    """
    Validate PIN format (must be exactly 6 digits, numeric only).
    
    Args:
        pin: PIN string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if PIN format is valid, False otherwise
        - error_message: Error message if invalid, None if valid
    """
    if not pin:
        return False, "PIN is required"
    
    if not pin.isdigit():
        return False, "PIN must contain only numbers"
    
    if len(pin) != 6:
        return False, "PIN must be exactly 6 digits"
    
    return True, None


def encrypt_pin(pin: str) -> str:
    """
    Encrypt PIN using credential storage encryption.
    
    Args:
        pin: Plain text PIN (6 digits)
        
    Returns:
        Encrypted PIN string
    """
    try:
        return credential_storage.encrypt(pin)
    except Exception as e:
        logger.error(f"Error encrypting PIN: {e}")
        raise


def decrypt_pin(encrypted_pin: str) -> str:
    """
    Decrypt PIN using credential storage decryption.
    
    Args:
        encrypted_pin: Encrypted PIN string
        
    Returns:
        Decrypted PIN string (6 digits)
    """
    try:
        return credential_storage.decrypt(encrypted_pin)
    except Exception as e:
        logger.error(f"Error decrypting PIN: {e}")
        raise


def verify_pin(entered_pin: str, encrypted_pin: str) -> bool:
    """
    Verify entered PIN against stored encrypted PIN.
    
    Args:
        entered_pin: User-entered PIN (plain text)
        encrypted_pin: Stored encrypted PIN
        
    Returns:
        True if PIN matches, False otherwise
    """
    try:
        # Validate entered PIN format first
        is_valid, error = validate_pin_format(entered_pin)
        if not is_valid:
            return False
        
        # Decrypt stored PIN and compare
        stored_pin = decrypt_pin(encrypted_pin)
        return entered_pin == stored_pin
    except Exception as e:
        logger.error(f"Error verifying PIN: {e}")
        return False

