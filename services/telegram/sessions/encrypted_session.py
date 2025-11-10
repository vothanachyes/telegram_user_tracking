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
        # Check if the path already ends with .session.enc - handle it directly
        logger.debug(f"Checking session path: {self.session_path}, name: {self.session_path.name}")
        if self.session_path.name.endswith('.session.enc') or str(self.session_path).endswith('.session.enc'):
            encrypted_path = self.session_path
            logger.debug(f"Detected .session.enc path, treating as encrypted: {encrypted_path}")
            if encrypted_path.exists():
                # CRITICAL: If file ends with .session.enc, it IS encrypted and MUST be decrypted
                # Even if encryption is currently disabled, we need to decrypt this file to use it
                logger.debug(f"File ends with .session.enc, attempting to decrypt: {encrypted_path}")
                
                # Try to decrypt - force=True to decrypt even if encryption is currently disabled
                # (the file is already encrypted, so we must decrypt it to use it)
                temp_file = self.encryption_service.decrypt_session_file(encrypted_path, force=True)
                if temp_file:
                    self._temp_decrypted_file = temp_file
                    logger.debug(f"Successfully decrypted encrypted session file to temp: {temp_file}")
                    # Get unencrypted path for cleanup
                    unencrypted_path = self.encryption_service.get_unencrypted_path(encrypted_path)
                    if unencrypted_path.exists():
                        try:
                            unencrypted_path.unlink()
                            logger.debug(f"Removed stale unencrypted session file: {unencrypted_path}")
                        except Exception as e:
                            logger.warning(f"Could not remove stale unencrypted session file: {e}")
                    return temp_file
                else:
                    logger.error(f"Failed to decrypt .session.enc file: {encrypted_path}")
                    # Fallback to unencrypted if decryption fails
                    unencrypted_path = self.encryption_service.get_unencrypted_path(encrypted_path)
                    if unencrypted_path.exists():
                        logger.warning(f"Falling back to unencrypted file: {unencrypted_path}")
                        return unencrypted_path
                    # If decryption fails and no unencrypted exists, this is an error
                    logger.error(f"Cannot decrypt encrypted session and no unencrypted fallback exists")
                    # Don't return the encrypted file - Telethon can't read it
                    # Instead, return the unencrypted path (even if it doesn't exist) so Telethon can create a new session
                    logger.warning(f"Returning unencrypted path for new session creation: {unencrypted_path}")
                    return unencrypted_path
            else:
                logger.warning(f"Encrypted session file does not exist: {encrypted_path}")
                # Try unencrypted fallback
                unencrypted_path = self.encryption_service.get_unencrypted_path(encrypted_path)
                if unencrypted_path.exists():
                    logger.debug(f"Encrypted file missing, using unencrypted: {unencrypted_path}")
                    return unencrypted_path
        
        # Normalize the path - if it ends with .session.enc, we already handled it above
        # So at this point, it should be a base path or .session path
        session_path = self.session_path
        
        # If path has .enc suffix but not .session.enc, it's malformed - strip it
        if session_path.suffix == '.enc' and not session_path.name.endswith('.session.enc'):
            logger.warning(f"Path has .enc suffix but not .session.enc, stripping: {session_path}")
            session_path = session_path.with_suffix('')
        
        # If path has no extension, add .session
        if not session_path.suffix:
            session_path = session_path.with_suffix('.session')
        
        logger.debug(f"Normalized session path: {session_path}")
        
        # Get both encrypted and unencrypted paths
        encrypted_path = self.encryption_service.get_encrypted_path(session_path)
        unencrypted_path = session_path
        
        # Check which files exist and their timestamps
        encrypted_exists = encrypted_path.exists() if self._use_encryption else False
        unencrypted_exists = unencrypted_path.exists()
        
        # Determine which file to use based on existence and timestamps
        use_encrypted = False
        if encrypted_exists and unencrypted_exists:
            # Both exist - use the newer one
            try:
                encrypted_mtime = encrypted_path.stat().st_mtime
                unencrypted_mtime = unencrypted_path.stat().st_mtime
                use_encrypted = encrypted_mtime >= unencrypted_mtime
                logger.debug(
                    f"Both session files exist. Encrypted: {encrypted_mtime}, "
                    f"Unencrypted: {unencrypted_mtime}. Using: {'encrypted' if use_encrypted else 'unencrypted'}"
                )
            except Exception as e:
                logger.warning(f"Error comparing file timestamps: {e}, defaulting to encrypted")
                use_encrypted = True
        elif encrypted_exists:
            use_encrypted = True
        elif unencrypted_exists:
            use_encrypted = False
        else:
            # Neither exists - return path for new session
            return session_path
        
        # Use encrypted file if selected
        if use_encrypted and self._use_encryption:
            logger.debug(f"Using encrypted session file: {encrypted_path}")
            # Decrypt to temporary file
            temp_file = self.encryption_service.decrypt_session_file(encrypted_path)
            if temp_file:
                self._temp_decrypted_file = temp_file
                logger.debug(f"Decrypted to temporary file: {temp_file}")
                # Clean up stale unencrypted file if it exists and is older
                if unencrypted_exists:
                    try:
                        unencrypted_path.unlink()
                        logger.debug(f"Removed stale unencrypted session file: {unencrypted_path}")
                    except Exception as e:
                        logger.warning(f"Could not remove stale unencrypted session file {unencrypted_path}: {e}")
                return temp_file
            else:
                logger.warning(f"Failed to decrypt session file {encrypted_path}, falling back to unencrypted")
                # Fallback to unencrypted if decryption fails
                if unencrypted_exists:
                    return unencrypted_path
        
        # Use unencrypted file
        if unencrypted_exists:
            logger.debug(f"Using unencrypted session file: {unencrypted_path}")
            # If encryption is enabled, we should encrypt this file after loading
            # But for now, just return it - save() will handle encryption
            return unencrypted_path
        
        # Neither file exists - return path for new session
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
                    # Check if there's already an encrypted file - if so, compare timestamps
                    encrypted_path = self.encryption_service.get_encrypted_path(self.session_path)
                    if not encrypted_path.suffix or encrypted_path.suffix != '.enc':
                        encrypted_path = encrypted_path.with_suffix('.session.enc')
                    
                    if encrypted_path.exists():
                        # Both files exist - check which is newer
                        try:
                            session_mtime = session_file.stat().st_mtime
                            encrypted_mtime = encrypted_path.stat().st_mtime
                            if session_mtime > encrypted_mtime:
                                # New session file is newer, encrypt it and remove old encrypted
                                encrypted_path.unlink()
                                logger.debug(f"Removed older encrypted session file: {encrypted_path}")
                                success = self.encryption_service.encrypt_session_file(session_file)
                            else:
                                # Encrypted file is newer or same, keep it and remove unencrypted
                                session_file.unlink()
                                logger.debug(f"Removed older unencrypted session file: {session_file}")
                                success = True
                        except Exception as e:
                            logger.warning(f"Error comparing session file timestamps: {e}")
                            # Fallback: just encrypt the unencrypted file
                            success = self.encryption_service.encrypt_session_file(session_file)
                    else:
                        # No encrypted file exists, encrypt the unencrypted one
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

