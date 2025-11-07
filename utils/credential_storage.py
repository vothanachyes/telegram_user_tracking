"""
Secure credential storage utility for login credentials.
Uses encryption to store email and password securely.
"""

import logging
import hashlib
import platform
from typing import Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)


class CredentialStorage:
    """Secure storage for login credentials using encryption."""
    
    def __init__(self):
        self._cipher: Optional[Fernet] = None
    
    def _get_encryption_key(self) -> bytes:
        """Generate encryption key from device-specific information."""
        # Use device-specific info to generate a key
        # This ensures credentials are device-specific
        machine_info = f"{platform.node()}-{platform.machine()}-{platform.system()}"
        salt = hashlib.sha256(machine_info.encode()).digest()[:16]
        
        # Use a fixed password derived from device info
        password = hashlib.sha256(machine_info.encode()).digest()
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def _get_cipher(self) -> Fernet:
        """Get or create Fernet cipher instance."""
        if self._cipher is None:
            key = self._get_encryption_key()
            self._cipher = Fernet(key)
        return self._cipher
    
    def encrypt(self, text: str) -> str:
        """Encrypt a text string."""
        try:
            cipher = self._get_cipher()
            encrypted = cipher.encrypt(text.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Error encrypting text: {e}")
            raise
    
    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt an encrypted text string."""
        try:
            cipher = self._get_cipher()
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted = cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error decrypting text: {e}")
            raise


# Global credential storage instance
credential_storage = CredentialStorage()

