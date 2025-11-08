"""
Telegram credentials manager.
"""

from typing import Optional, List, Dict
from database.managers.base import BaseDatabaseManager, _parse_datetime
from database.models.telegram import TelegramCredential
import logging

logger = logging.getLogger(__name__)


class TelegramCredentialManager(BaseDatabaseManager):
    """Manages Telegram credentials operations."""
    
    def save_telegram_credential(self, credential: TelegramCredential) -> Optional[int]:
        """Save or update Telegram credential."""
        try:
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
                    credential.phone_number,
                    credential.session_string,
                    credential.is_default
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving telegram credential: {e}")
            return None
    
    def get_telegram_credentials(self) -> List[TelegramCredential]:
        """Get all saved Telegram credentials."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM telegram_credentials 
                ORDER BY is_default DESC, last_used DESC
            """)
            return [TelegramCredential(
                id=row['id'],
                phone_number=row['phone_number'],
                session_string=row['session_string'],
                is_default=bool(row['is_default']),
                last_used=_parse_datetime(row['last_used']),
                created_at=_parse_datetime(row['created_at'])
            ) for row in cursor.fetchall()]
    
    def get_default_credential(self) -> Optional[TelegramCredential]:
        """Get default Telegram credential."""
        credentials = self.get_telegram_credentials()
        for cred in credentials:
            if cred.is_default:
                return cred
        return credentials[0] if credentials else None
    
    def get_credential_by_id(self, credential_id: int) -> Optional[TelegramCredential]:
        """Get Telegram credential by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM telegram_credentials WHERE id = ?",
                (credential_id,)
            )
            row = cursor.fetchone()
            if row:
                return TelegramCredential(
                    id=row['id'],
                    phone_number=row['phone_number'],
                    session_string=row['session_string'],
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

