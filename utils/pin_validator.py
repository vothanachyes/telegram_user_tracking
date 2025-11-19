"""
PIN validation and encryption utilities.
"""

import logging
import hashlib
import base64
from typing import Tuple, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
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


def encrypt_pin_with_user_id(encrypted_pin: str, user_id: str) -> str:
    """
    Encrypt PIN (already encrypted) with Firebase user ID for additional layer of security.
    
    Args:
        encrypted_pin: Already encrypted PIN string
        user_id: Firebase user ID (UID)
        
    Returns:
        Double-encrypted PIN string
    """
    try:
        if not encrypted_pin or not user_id:
            logger.error("Missing encrypted_pin or user_id for user encryption")
            return encrypted_pin
        
        # Derive encryption key from user ID
        salt = hashlib.sha256(f"user-pin-encryption-{user_id}".encode()).digest()[:16]
        password = hashlib.sha256(f"{user_id}-pin-encryption".encode()).digest()
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        # Create Fernet cipher
        cipher = Fernet(key)
        
        # Encrypt the already-encrypted PIN
        encrypted = cipher.encrypt(encrypted_pin.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"Error encrypting PIN with user ID: {e}")
        raise


def decrypt_pin_with_user_id(user_encrypted_pin: str, user_id: str) -> str:
    """
    Decrypt PIN that was encrypted with Firebase user ID.
    
    Args:
        user_encrypted_pin: PIN encrypted with user ID
        user_id: Firebase user ID (UID)
        
    Returns:
        Decrypted PIN (still encrypted with device key)
    """
    try:
        if not user_encrypted_pin or not user_id:
            logger.error("Missing user_encrypted_pin or user_id for decryption")
            return user_encrypted_pin
        
        # Derive encryption key from user ID (same as encryption)
        salt = hashlib.sha256(f"user-pin-encryption-{user_id}".encode()).digest()[:16]
        password = hashlib.sha256(f"{user_id}-pin-encryption".encode()).digest()
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        # Create Fernet cipher
        cipher = Fernet(key)
        
        # Decrypt
        encrypted_bytes = base64.urlsafe_b64decode(user_encrypted_pin.encode())
        decrypted = cipher.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Error decrypting PIN with user ID: {e}")
        raise

