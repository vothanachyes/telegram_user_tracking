"""
Telegram credentials manager.
"""

from typing import Optional, List, Dict, Tuple
from database.managers.base import BaseDatabaseManager, _parse_datetime
from database.models.telegram import TelegramCredential
import logging

logger = logging.getLogger(__name__)


class TelegramCredentialManager(BaseDatabaseManager):
    """Manages Telegram credentials operations."""
    
    def save_telegram_credential(self, credential: TelegramCredential) -> Optional[int]:
        """Save or update Telegram credential."""
        try:
            encryption_service = self.get_encryption_service()
            
            # Encrypt sensitive fields
            encrypted_phone = encryption_service.encrypt_field(credential.phone_number) if encryption_service else credential.phone_number
            encrypted_session = encryption_service.encrypt_field(credential.session_string) if encryption_service else credential.session_string
            
            with self.get_connection() as conn:
                # If set as default, unset all others
                if credential.is_default:
                    conn.execute("UPDATE telegram_credentials SET is_default = 0")
                
                cursor = conn.execute("""
                    INSERT INTO telegram_credentials 
                    (phone_number, session_string, is_default, last_used)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(phone_number) DO UPDATE SET
                        session_string = excluded.session_string,
                        is_default = excluded.is_default,
                        last_used = CURRENT_TIMESTAMP
                """, (
                    encrypted_phone,
                    encrypted_session,
                    credential.is_default
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving telegram credential: {e}")
            return None
    
    def get_telegram_credentials(self) -> List[TelegramCredential]:
        """Get all saved Telegram credentials."""
        encryption_service = self.get_encryption_service()
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM telegram_credentials 
                ORDER BY is_default DESC, last_used DESC
            """)
            credentials = []
            for row in cursor.fetchall():
                # Decrypt sensitive fields
                phone_number = encryption_service.decrypt_field(row['phone_number']) if encryption_service else row['phone_number']
                session_string = encryption_service.decrypt_field(row['session_string']) if encryption_service else row['session_string']
                
                credentials.append(TelegramCredential(
                    id=row['id'],
                    phone_number=phone_number or "",
                    session_string=session_string,
                    is_default=bool(row['is_default']),
                    last_used=_parse_datetime(row['last_used']),
                    created_at=_parse_datetime(row['created_at'])
                ))
            return credentials
    
    def get_default_credential(self) -> Optional[TelegramCredential]:
        """Get default Telegram credential."""
        credentials = self.get_telegram_credentials()
        for cred in credentials:
            if cred.is_default:
                return cred
        return credentials[0] if credentials else None
    
    def get_credential_by_id(self, credential_id: int) -> Optional[TelegramCredential]:
        """Get Telegram credential by ID."""
        encryption_service = self.get_encryption_service()
        
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM telegram_credentials WHERE id = ?",
                (credential_id,)
            )
            row = cursor.fetchone()
            if row:
                # Decrypt sensitive fields
                phone_number = encryption_service.decrypt_field(row['phone_number']) if encryption_service else row['phone_number']
                session_string = encryption_service.decrypt_field(row['session_string']) if encryption_service else row['session_string']
                
                return TelegramCredential(
                    id=row['id'],
                    phone_number=phone_number or "",
                    session_string=session_string,
                    is_default=bool(row['is_default']),
                    last_used=_parse_datetime(row['last_used']),
                    created_at=_parse_datetime(row['created_at'])
                )
            return None
    
    def delete_telegram_credential(self, credential_id: int) -> bool:
        """
        Delete Telegram credential by ID.
        
        Args:
            credential_id: ID of the credential to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM telegram_credentials WHERE id = ?",
                    (credential_id,)
                )
                conn.commit()
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Deleted telegram credential with ID: {credential_id}")
                return deleted
        except Exception as e:
            logger.error(f"Error deleting telegram credential: {e}")
            return False
    
    def get_credential_with_status(self, credential_id: int) -> Optional[Dict]:
        """
        Get credential with status info.
        Status is populated by TelegramService.check_account_status().
        
        Args:
            credential_id: ID of the credential
            
        Returns:
            Dict with credential and status info, or None if not found
        """
        credential = self.get_credential_by_id(credential_id)
        if not credential:
            return None
        
        return {
            'credential': credential,
            'status': None,  # Will be populated by service layer
            'status_checked_at': None
        }
    
    def get_all_credentials_with_status(self) -> List[Dict]:
        """
        Get all credentials with status info.
        Status is populated by TelegramService.
        
        Returns:
            List of dicts with credential and status info
        """
        credentials = self.get_telegram_credentials()
        return [
            {
                'credential': cred,
                'status': None,  # Will be populated by service layer
                'status_checked_at': None
            }
            for cred in credentials
        ]
    
    def account_exists(self, phone_number: str) -> Tuple[bool, Optional[str]]:
        """
        Check if account exists (in database or as session file).
        
        Args:
            phone_number: Phone number to check
            
        Returns:
            Tuple of (exists, reason) where reason is None if doesn't exist
        """
        encryption_service = self.get_encryption_service()
        
        # Encrypt phone number for comparison
        encrypted_phone = encryption_service.encrypt_field(phone_number) if encryption_service else phone_number
        
        # Check if phone number exists in database
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id FROM telegram_credentials WHERE phone_number = ?",
                (encrypted_phone,)
            )
            if cursor.fetchone():
                return True, f"Account with phone number {phone_number} already exists in database"
        
        # Check if session file exists on disk
        try:
            from pathlib import Path
            from utils.constants import APP_DATA_DIR
            
            session_path = APP_DATA_DIR / "sessions"
            # Session name format: session_{phone.replace('+', '')}
            session_name = f"session_{phone_number.replace('+', '')}"
            session_file = session_path / f"{session_name}.session"
            
            if session_file.exists():
                return True, f"Session file already exists for phone number {phone_number}"
        except Exception as e:
            logger.error(f"Error checking session file: {e}")
            # Don't fail on file check errors, just log
        
        return False, None
    
    def get_account_count(self) -> int:
        """
        Get total count of saved accounts.
        
        Returns:
            Number of saved accounts
        """
        credentials = self.get_telegram_credentials()
        return len(credentials)

