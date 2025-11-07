"""
Authentication manager.
"""

from typing import Optional
from database.managers.base import BaseDatabaseManager, _parse_datetime
from database.models.auth import LoginCredential
import logging

logger = logging.getLogger(__name__)


class AuthManager(BaseDatabaseManager):
    """Manages authentication operations."""
    
    def save_login_credential(self, email: str, encrypted_password: str) -> bool:
        """Save or update login credential."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO login_credentials (email, encrypted_password)
                    VALUES (?, ?)
                    ON CONFLICT(email) DO UPDATE SET
                        encrypted_password = excluded.encrypted_password,
                        updated_at = CURRENT_TIMESTAMP
                """, (email, encrypted_password))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving login credential: {e}")
            return False
    
    def get_login_credential(self) -> Optional[LoginCredential]:
        """Get saved login credential (returns the first one if multiple exist)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM login_credentials 
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    return LoginCredential(
                        id=row['id'],
                        email=row['email'],
                        encrypted_password=row['encrypted_password'],
                        created_at=_parse_datetime(row['created_at']),
                        updated_at=_parse_datetime(row['updated_at'])
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting login credential: {e}")
            return None
    
    def delete_login_credential(self, email: Optional[str] = None) -> bool:
        """Delete login credential(s). If email is None, delete all."""
        try:
            with self.get_connection() as conn:
                if email:
                    conn.execute("DELETE FROM login_credentials WHERE email = ?", (email,))
                else:
                    conn.execute("DELETE FROM login_credentials")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting login credential: {e}")
            return False

