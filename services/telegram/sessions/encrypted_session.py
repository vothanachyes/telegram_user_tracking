"""
Encrypted SQLite session wrapper for Telethon.
Provides transparent encryption/decryption of session files.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

try:
    from telethon.sessions import SQLiteSession
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    SQLiteSession = None

from .session_encryption_service import SessionEncryptionService
from database.managers.base import BaseDatabaseManager

logger = logging.getLogger(__name__)


class EncryptedSQLiteSession(SQLiteSession):
    """
    Encrypted wrapper for Telethon's SQLiteSession.
    
    This class extends SQLiteSession and handles encryption/decryption of session files
    transparently. New sessions are encrypted by default, while existing unencrypted
    sessions remain compatible.
    """
    
    def __init__(
        self,
        session_path: str,
        db_manager: Optional[BaseDatabaseManager] = None
    ):
        """
        Initialize encrypted SQLite session.
        
        Args:
            session_path: Path to session file (will use .session.enc for encrypted)
            db_manager: Database manager for accessing encryption service
        """
        if not TELETHON_AVAILABLE:
            raise ImportError("Telethon is not available")
        
        self.session_path = Path(session_path)
        self.db_manager = db_manager
        self.encryption_service = SessionEncryptionService(db_manager)
        
        # Determine if we should use encryption
        self._use_encryption = self.encryption_service.is_encryption_enabled()
        
        # Determine actual session file path to use
        actual_session_path = self._get_session_path_for_loading()
        
        # Initialize parent SQLiteSession with the actual path
        super().__init__(str(actual_session_path))
        
        # Track temporary decrypted file for cleanup
        self._temp_decrypted_file: Optional[Path] = None
    
    def _get_session_path_for_loading(self) -> Path:
        """
        Get the session path to use for loading (decrypts if needed).
        
        Returns:
            Path to session file (may be temporary decrypted file)
        """
        # Ensure paths have proper extensions
        session_path = self.session_path
        if not session_path.suffix:
            session_path = session_path.with_suffix('.session')
        
        # Check for encrypted session file first
        encrypted_path = self.encryption_service.get_encrypted_path(session_path)
        
        # Check if encrypted file exists
        if self._use_encryption and encrypted_path.exists():
            # Decrypt to temporary file
            temp_file = self.encryption_service.decrypt_session_file(encrypted_path)
            if temp_file:
                self._temp_decrypted_file = temp_file
                logger.debug(f"Using decrypted temporary session file: {temp_file}")
                return temp_file
            else:
                logger.warning(f"Failed to decrypt session file {encrypted_path}, trying unencrypted")
                # Fallback to unencrypted if decryption fails
                if session_path.exists():
                    return session_path
        
        # Use unencrypted session or create new one
        return session_path
    
    def save(self):
        """
        Save session and encrypt if encryption is enabled.
        """
        try:
            # Let parent save normally (this saves to the actual file path, which might be temp)
            super().save()
            
            # If encryption is enabled and we're using a temp file, re-encrypt back to encrypted file
            if self._use_encryption:
                # Get the actual session file path that was saved
                session_file = Path(self.filename) if hasattr(self, 'filename') else self.session_path
                
                # Ensure it has .session extension
                if not session_file.suffix:
                    session_file = session_file.with_suffix('.session')
                
                # If we're working with a temp decrypted file, encrypt it back to the encrypted location
                if self._temp_decrypted_file and session_file == self._temp_decrypted_file:
                    # This is a temp file - encrypt it back to the encrypted location
                    encrypted_path = self.encryption_service.get_encrypted_path(self.session_path)
                    if not encrypted_path.suffix or encrypted_path.suffix != '.enc':
                        encrypted_path = encrypted_path.with_suffix('.session.enc')
                    
                    # Read the temp file and encrypt it to the encrypted location
                    if session_file.exists():
                        try:
                            # Read the decrypted session data from temp file
                            with open(session_file, 'rb') as f:
                                session_data = f.read()
                            
                            # Encrypt and write to encrypted location
                            import base64
                            from services.database.field_encryption_service import FieldEncryptionService
                            encryption_service = self.encryption_service._get_encryption_service()
                            
                            if encryption_service:
                                session_data_b64 = base64.b64encode(session_data).decode('utf-8')
                                encrypted_data = encryption_service.encrypt_field(session_data_b64)
                                
                                if encrypted_data and encrypted_data.startswith(FieldEncryptionService.ENCRYPTION_PREFIX):
                                    encrypted_b64 = encrypted_data[len(FieldEncryptionService.ENCRYPTION_PREFIX):]
                                    encrypted_bytes = base64.b64decode(encrypted_b64.encode('utf-8'))
                                    
                                    # Write encrypted file
                                    with open(encrypted_path, 'wb') as f:
                                        f.write(encrypted_bytes)
                                    
                                    logger.debug(f"Re-encrypted session file from temp to: {encrypted_path}")
                                else:
                                    logger.warning(f"Failed to encrypt session data from temp file")
                            else:
                                logger.warning(f"Encryption service not available for re-encryption")
                        except Exception as e:
                            logger.error(f"Error re-encrypting temp session file: {e}", exc_info=True)
                # If it's not a temp file and not already encrypted, encrypt it
                elif session_file.exists() and not self.encryption_service.is_encrypted(session_file):
                    success = self.encryption_service.encrypt_session_file(session_file)
                    if success:
                        logger.debug(f"Encrypted session file: {session_file}")
                    else:
                        logger.warning(f"Failed to encrypt session file: {session_file}")
        except Exception as e:
            logger.error(f"Error saving encrypted session: {e}", exc_info=True)
            # Re-raise to let Telethon handle the error
            raise
    
    def cleanup(self):
        """
        Clean up temporary decrypted file if it exists.
        """
        if self._temp_decrypted_file and self._temp_decrypted_file.exists():
            try:
                self._temp_decrypted_file.unlink()
                logger.debug(f"Cleaned up temporary decrypted session file: {self._temp_decrypted_file}")
            except Exception as e:
                logger.warning(f"Could not clean up temporary file {self._temp_decrypted_file}: {e}")
            finally:
                self._temp_decrypted_file = None
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during cleanup

