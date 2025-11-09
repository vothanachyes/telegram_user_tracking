"""
Field-level encryption service for encrypting sensitive database fields.
Uses Fernet (AES-128) for symmetric encryption.
"""

import logging
import base64
import secrets
import hashlib
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class FieldEncryptionService:
    """Service for encrypting and decrypting individual database fields."""
    
    # Prefix to identify encrypted fields
    ENCRYPTION_PREFIX = "ENC:"
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize field encryption service.
        
        Args:
            encryption_key: Base64-encoded encryption key. If None, encryption is disabled.
        """
        self._encryption_key = encryption_key
        self._cipher: Optional[Fernet] = None
        self._enabled = encryption_key is not None
        
        if self._enabled:
            try:
                self._initialize_cipher()
            except Exception as e:
                logger.error(f"Failed to initialize encryption cipher: {e}")
                self._enabled = False
                self._cipher = None
    
    def _initialize_cipher(self):
        """Initialize Fernet cipher from encryption key."""
        if not self._encryption_key:
            raise ValueError("Encryption key is required")
        
        try:
            # Decode the base64 key
            key_bytes = base64.urlsafe_b64decode(self._encryption_key.encode('utf-8'))
            
            # Fernet requires exactly 32 bytes (URL-safe base64 encoded)
            # If key is not 32 bytes, derive a proper key using PBKDF2
            if len(key_bytes) != 32:
                # Use PBKDF2 to derive a 32-byte key
                salt = hashlib.sha256(b"field_encryption_salt").digest()[:16]
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                    backend=default_backend()
                )
                key_bytes = kdf.derive(self._encryption_key.encode('utf-8'))
            
            # Create Fernet cipher
            fernet_key = base64.urlsafe_b64encode(key_bytes)
            self._cipher = Fernet(fernet_key)
        except Exception as e:
            logger.error(f"Error initializing cipher: {e}")
            raise
    
    @staticmethod
    def generate_encryption_key() -> str:
        """
        Generate a secure random encryption key for field encryption.
        
        Returns:
            Base64-encoded encryption key
        """
        # Generate 32 bytes of random data
        key = secrets.token_bytes(32)
        # Encode as base64 for storage
        return base64.urlsafe_b64encode(key).decode('utf-8')
    
    @staticmethod
    def hash_key(key: str) -> str:
        """
        Create a hash of the encryption key for storage/verification.
        This hash is stored in settings but cannot be used to decrypt.
        
        Args:
            key: Encryption key
            
        Returns:
            SHA-256 hash of the key
        """
        return hashlib.sha256(key.encode('utf-8')).hexdigest()
    
    def is_enabled(self) -> bool:
        """Check if encryption is enabled."""
        return self._enabled and self._cipher is not None
    
    def encrypt_field(self, value: Optional[str]) -> Optional[str]:
        """
        Encrypt a field value.
        
        Args:
            value: Plain text value to encrypt (can be None or empty string)
            
        Returns:
            Encrypted value with prefix, or None/empty string if input was None/empty
        """
        # Handle None and empty strings
        if value is None:
            return None
        
        if not value or not value.strip():
            return value  # Return empty string as-is
        
        # If encryption is disabled, return value as-is
        if not self.is_enabled():
            return value
        
        # If already encrypted (has prefix), return as-is
        if value.startswith(self.ENCRYPTION_PREFIX):
            return value
        
        try:
            # Encrypt the value
            encrypted_bytes = self._cipher.encrypt(value.encode('utf-8'))
            encrypted_str = base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
            
            # Add prefix to identify encrypted fields
            return f"{self.ENCRYPTION_PREFIX}{encrypted_str}"
        except Exception as e:
            logger.error(f"Error encrypting field: {e}")
            # Return original value on error (fail open for compatibility)
            return value
    
    def decrypt_field(self, value: Optional[str]) -> Optional[str]:
        """
        Decrypt a field value.
        
        Args:
            value: Encrypted value with prefix, or plain text
            
        Returns:
            Decrypted plain text value, or None/empty string if input was None/empty
        """
        # Handle None and empty strings
        if value is None:
            return None
        
        if not value or not value.strip():
            return value  # Return empty string as-is
        
        # If encryption is disabled, return value as-is
        if not self.is_enabled():
            return value
        
        # If not encrypted (no prefix), return as-is (backward compatibility)
        if not value.startswith(self.ENCRYPTION_PREFIX):
            return value
        
        try:
            # Remove prefix
            encrypted_str = value[len(self.ENCRYPTION_PREFIX):]
            
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_str.encode('utf-8'))
            
            # Decrypt
            decrypted_bytes = self._cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Error decrypting field: {e}")
            # Return original value on error (fail open for compatibility)
            return value
    
    def encrypt_integer(self, value: Optional[int]) -> Optional[str]:
        """
        Encrypt an integer value by converting to string first.
        
        Args:
            value: Integer value to encrypt
            
        Returns:
            Encrypted string representation, or None if input was None
        """
        if value is None:
            return None
        return self.encrypt_field(str(value))
    
    def decrypt_integer(self, value: Optional[str]) -> Optional[int]:
        """
        Decrypt an integer value by decrypting string then converting to int.
        
        Args:
            value: Encrypted string representation of integer
            
        Returns:
            Decrypted integer value, or None if input was None or invalid
        """
        if value is None:
            return None
        
        decrypted_str = self.decrypt_field(value)
        if not decrypted_str:
            return None
        
        try:
            return int(decrypted_str)
        except (ValueError, TypeError):
            logger.warning(f"Failed to convert decrypted value to integer: {decrypted_str}")
            return None

