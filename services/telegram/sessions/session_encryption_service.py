"""
Session encryption service for encrypting/decrypting Telegram session files.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

from services.database.field_encryption_service import FieldEncryptionService
from database.managers.base import BaseDatabaseManager

logger = logging.getLogger(__name__)


class SessionEncryptionService:
    """Service for encrypting and decrypting Telegram session files."""
    
    ENCRYPTED_EXTENSION = ".session.enc"
    SESSION_EXTENSION = ".session"
    
    def __init__(self, db_manager: Optional[BaseDatabaseManager] = None):
        """
        Initialize session encryption service.
        
        Args:
            db_manager: Database manager instance for accessing encryption service
        """
        self.db_manager = db_manager
        self._encryption_service: Optional[FieldEncryptionService] = None
    
    def _get_encryption_service(self) -> Optional[FieldEncryptionService]:
        """Get field encryption service instance."""
        if self._encryption_service is None and self.db_manager:
            self._encryption_service = self.db_manager.get_encryption_service()
        return self._encryption_service
    
    def is_encryption_enabled(self) -> bool:
        """
        Check if session encryption is enabled.
        
        Returns:
            True if encryption is enabled and available, False otherwise
        """
        # Check if session encryption is enabled in settings
        try:
            from config.settings import settings
            if not settings.is_session_encryption_enabled():
                return False
        except Exception as e:
            logger.warning(f"Could not check session encryption setting: {e}")
            # Default to enabled if we can't check
        
        # Check if field encryption service is available (required for session encryption)
        encryption_service = self._get_encryption_service()
        return encryption_service is not None and encryption_service.is_enabled()
    
    def is_encrypted(self, session_path: Path) -> bool:
        """
        Check if a session file is encrypted.
        
        Args:
            session_path: Path to session file (can be .session or .session.enc)
            
        Returns:
            True if file has .session.enc extension, False otherwise
        """
        return session_path.suffix == ".enc" or session_path.name.endswith(self.ENCRYPTED_EXTENSION)
    
    def get_encrypted_path(self, session_path: Path) -> Path:
        """
        Get encrypted session file path.
        
        Args:
            session_path: Original session file path
            
        Returns:
            Path with .session.enc extension
        """
        if self.is_encrypted(session_path):
            return session_path
        
        # Replace .session with .session.enc
        if session_path.suffix == ".session":
            return session_path.with_suffix(".session.enc")
        
        # If no extension, add .session.enc
        return session_path.with_suffix(self.ENCRYPTED_EXTENSION)
    
    def get_unencrypted_path(self, encrypted_path: Path) -> Path:
        """
        Get unencrypted session file path from encrypted path.
        
        Args:
            encrypted_path: Encrypted session file path
            
        Returns:
            Path with .session extension
        """
        if encrypted_path.name.endswith(self.ENCRYPTED_EXTENSION):
            return encrypted_path.with_name(encrypted_path.name.replace(self.ENCRYPTED_EXTENSION, self.SESSION_EXTENSION))
        return encrypted_path.with_suffix(self.SESSION_EXTENSION)
    
    def encrypt_session_file(self, session_path: Path) -> bool:
        """
        Encrypt a session file.
        
        Args:
            session_path: Path to unencrypted session file
            
        Returns:
            True if encryption succeeded, False otherwise
        """
        if not self.is_encryption_enabled():
            logger.warning("Session encryption is not enabled")
            return False
        
        if not session_path.exists():
            logger.error(f"Session file does not exist: {session_path}")
            return False
        
        if self.is_encrypted(session_path):
            logger.debug(f"Session file is already encrypted: {session_path}")
            return True
        
        try:
            encryption_service = self._get_encryption_service()
            if not encryption_service:
                logger.error("Encryption service not available")
                return False
            
            # Read session file content
            with open(session_path, 'rb') as f:
                session_data = f.read()
            
            # Encrypt the data
            # Convert bytes to string for encryption (base64 encode first)
            import base64
            session_data_b64 = base64.b64encode(session_data).decode('utf-8')
            encrypted_data = encryption_service.encrypt_field(session_data_b64)
            
            if not encrypted_data or not encrypted_data.startswith(FieldEncryptionService.ENCRYPTION_PREFIX):
                logger.error("Failed to encrypt session data")
                return False
            
            # Remove prefix and decode
            encrypted_b64 = encrypted_data[len(FieldEncryptionService.ENCRYPTION_PREFIX):]
            encrypted_bytes = base64.b64decode(encrypted_b64.encode('utf-8'))
            
            # Write encrypted file
            encrypted_path = self.get_encrypted_path(session_path)
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_bytes)
            
            # Delete original unencrypted file
            try:
                session_path.unlink()
                logger.info(f"Encrypted session file: {session_path} -> {encrypted_path}")
            except Exception as e:
                logger.warning(f"Could not delete original session file {session_path}: {e}")
                # If we can't delete, at least we have the encrypted version
            
            return True
            
        except Exception as e:
            logger.error(f"Error encrypting session file {session_path}: {e}", exc_info=True)
            return False
    
    def decrypt_session_file(self, encrypted_path: Path) -> Optional[Path]:
        """
        Decrypt a session file to a temporary file.
        
        Args:
            encrypted_path: Path to encrypted session file
            
        Returns:
            Path to temporary decrypted file, or None if decryption failed
        """
        if not self.is_encryption_enabled():
            logger.warning("Session encryption is not enabled")
            return None
        
        if not encrypted_path.exists():
            logger.error(f"Encrypted session file does not exist: {encrypted_path}")
            return None
        
        try:
            encryption_service = self._get_encryption_service()
            if not encryption_service:
                logger.error("Encryption service not available")
                return None
            
            # Read encrypted file
            with open(encrypted_path, 'rb') as f:
                encrypted_bytes = f.read()
            
            # Convert to base64 string for decryption
            import base64
            encrypted_b64 = base64.b64encode(encrypted_bytes).decode('utf-8')
            encrypted_data = f"{FieldEncryptionService.ENCRYPTION_PREFIX}{encrypted_b64}"
            
            # Decrypt
            decrypted_b64 = encryption_service.decrypt_field(encrypted_data)
            if not decrypted_b64:
                logger.error("Failed to decrypt session data")
                return None
            
            # Decode from base64
            session_data = base64.b64decode(decrypted_b64.encode('utf-8'))
            
            # Write to temporary file
            temp_file = tempfile.NamedTemporaryFile(
                mode='wb',
                suffix=self.SESSION_EXTENSION,
                delete=False
            )
            temp_file.write(session_data)
            temp_file.close()
            
            logger.debug(f"Decrypted session file to temporary file: {temp_file.name}")
            return Path(temp_file.name)
            
        except Exception as e:
            logger.error(f"Error decrypting session file {encrypted_path}: {e}", exc_info=True)
            return None
    
    def migrate_session_to_encrypted(self, session_path: Path) -> bool:
        """
        Migrate an existing unencrypted session to encrypted format.
        
        Args:
            session_path: Path to unencrypted session file
            
        Returns:
            True if migration succeeded, False otherwise
        """
        if not self.is_encryption_enabled():
            logger.debug("Session encryption is not enabled, skipping migration")
            return False
        
        if self.is_encrypted(session_path):
            logger.debug(f"Session file is already encrypted: {session_path}")
            return True
        
        return self.encrypt_session_file(session_path)

