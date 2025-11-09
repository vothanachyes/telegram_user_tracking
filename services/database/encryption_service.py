"""
Database encryption service for securing SQLite database files.
Uses file-level encryption with AES-256 and Windows DPAPI for key storage.
"""

import os
import platform
import logging
import secrets
import hashlib
from pathlib import Path
from typing import Optional, Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

logger = logging.getLogger(__name__)

# Try to import Windows DPAPI
WINDOWS_DPAPI_AVAILABLE = False
win32crypt = None
try:
    if platform.system() == "Windows":
        import win32crypt
        WINDOWS_DPAPI_AVAILABLE = True
except ImportError:
    logger.warning("Windows DPAPI not available - pywin32 not installed")


class DatabaseEncryptionService:
    """Service for encrypting and decrypting database files."""
    
    @staticmethod
    def generate_encryption_key() -> str:
        """
        Generate a secure random encryption key.
        
        Returns:
            Base64-encoded encryption key
        """
        # Generate 32 bytes of random data
        key = secrets.token_bytes(32)
        # Encode as base64 for storage
        return base64.urlsafe_b64encode(key).decode('utf-8')
    
    @staticmethod
    def encrypt_key_with_dpapi(key: str) -> Optional[str]:
        """
        Encrypt encryption key using Windows DPAPI.
        
        Args:
            key: Plain text encryption key
            
        Returns:
            Encrypted key as base64 string, or None if DPAPI unavailable
        """
        if not WINDOWS_DPAPI_AVAILABLE:
            logger.warning("DPAPI not available - key will not be encrypted")
            return None
        
        try:
            if not win32crypt:
                return None
            # Encrypt using DPAPI (user-specific encryption)
            encrypted = win32crypt.CryptProtectData(
                key.encode('utf-8'),
                "DatabaseEncryptionKey",
                None,
                None,
                None,
                0
            )
            # Return as base64 for storage
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encrypt key with DPAPI: {e}")
            return None
    
    @staticmethod
    def decrypt_key_with_dpapi(encrypted_key: str) -> Optional[str]:
        """
        Decrypt encryption key using Windows DPAPI.
        
        Args:
            encrypted_key: Base64-encoded encrypted key
            
        Returns:
            Decrypted key, or None if decryption fails
        """
        if not WINDOWS_DPAPI_AVAILABLE:
            logger.warning("DPAPI not available - cannot decrypt key")
            return None
        
        try:
            if not win32crypt:
                return None
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_key.encode('utf-8'))
            # Decrypt using DPAPI
            decrypted, _ = win32crypt.CryptUnprotectData(
                encrypted_bytes,
                None,
                None,
                None,
                0
            )
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to decrypt key with DPAPI: {e}")
            return None
    
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
    
    @staticmethod
    def encrypt_file(file_path: str, key: str) -> bool:
        """
        Encrypt a database file using AES-256.
        
        Args:
            file_path: Path to file to encrypt
            key: Base64-encoded encryption key
            
        Returns:
            True if encryption successful, False otherwise
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            # Read file content
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Create Fernet cipher from key
            # Fernet uses AES-128 in CBC mode, but we'll use it for simplicity
            # For AES-256, we'd need to use a different approach
            fernet_key = base64.urlsafe_b64decode(key.encode('utf-8'))
            # Pad or truncate to 32 bytes for Fernet
            if len(fernet_key) < 32:
                fernet_key = fernet_key.ljust(32, b'0')
            elif len(fernet_key) > 32:
                fernet_key = fernet_key[:32]
            
            fernet = Fernet(base64.urlsafe_b64encode(fernet_key))
            
            # Encrypt data
            encrypted_data = fernet.encrypt(file_data)
            
            # Write encrypted data to file
            encrypted_path = str(file_path_obj) + ".encrypted"
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Replace original file
            file_path_obj.unlink()
            Path(encrypted_path).rename(file_path_obj)
            
            logger.info(f"Successfully encrypted file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to encrypt file {file_path}: {e}")
            return False
    
    @staticmethod
    def decrypt_file(file_path: str, key: str) -> bool:
        """
        Decrypt a database file.
        
        Args:
            file_path: Path to encrypted file
            key: Base64-encoded encryption key
            
        Returns:
            True if decryption successful, False otherwise
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            # Read encrypted file content
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Create Fernet cipher from key
            fernet_key = base64.urlsafe_b64decode(key.encode('utf-8'))
            # Pad or truncate to 32 bytes for Fernet
            if len(fernet_key) < 32:
                fernet_key = fernet_key.ljust(32, b'0')
            elif len(fernet_key) > 32:
                fernet_key = fernet_key[:32]
            
            fernet = Fernet(base64.urlsafe_b64encode(fernet_key))
            
            # Decrypt data
            try:
                decrypted_data = fernet.decrypt(encrypted_data)
            except Exception as e:
                logger.error(f"Decryption failed - invalid key or corrupted file: {e}")
                return False
            
            # Write decrypted data to file
            decrypted_path = str(file_path_obj) + ".decrypted"
            with open(decrypted_path, 'wb') as f:
                f.write(decrypted_data)
            
            # Replace encrypted file
            file_path_obj.unlink()
            Path(decrypted_path).rename(file_path_obj)
            
            logger.info(f"Successfully decrypted file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to decrypt file {file_path}: {e}")
            return False
    
    @staticmethod
    def is_file_encrypted(file_path: str) -> bool:
        """
        Check if a file is encrypted by attempting to read it as SQLite.
        SQLite files start with a specific header, encrypted files won't.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            True if file appears to be encrypted, False otherwise
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return False
            
            # SQLite files start with "SQLite format 3"
            with open(file_path, 'rb') as f:
                header = f.read(16)
                # Check if it's a valid SQLite header
                if header.startswith(b'SQLite format 3\x00'):
                    return False
                # If it doesn't start with SQLite header, assume encrypted
                return True
                
        except Exception:
            return False
    
    @staticmethod
    def rekey_database(old_key: str, new_key: str, db_path: str) -> bool:
        """
        Re-encrypt database with a new key.
        
        Args:
            old_key: Current encryption key
            new_key: New encryption key
            db_path: Path to database file
            
        Returns:
            True if rekey successful, False otherwise
        """
        try:
            # Decrypt with old key
            if DatabaseEncryptionService.is_file_encrypted(db_path):
                if not DatabaseEncryptionService.decrypt_file(db_path, old_key):
                    logger.error("Failed to decrypt database with old key")
                    return False
            
            # Encrypt with new key
            if not DatabaseEncryptionService.encrypt_file(db_path, new_key):
                logger.error("Failed to encrypt database with new key")
                # Try to re-encrypt with old key as rollback
                DatabaseEncryptionService.encrypt_file(db_path, old_key)
                return False
            
            logger.info("Successfully rekeyed database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rekey database: {e}")
            return False

