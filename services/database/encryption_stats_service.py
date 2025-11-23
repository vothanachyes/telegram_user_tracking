"""
Service to count encrypted vs unencrypted records in the database.
"""

import logging
import sqlite3
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class EncryptionStatsService:
    """Service to get encryption statistics from database."""
    
    ENCRYPTION_PREFIX = "ENC:"
    
    def __init__(self, db_path: str):
        """
        Initialize encryption stats service.
        
        Args:
            db_path: Path to database file
        """
        self.db_path = db_path
    
    def count_encrypted_messages(self) -> int:
        """
        Count messages with encrypted fields (content, caption, or message_link).
        
        Returns:
            Number of messages with at least one encrypted field
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM messages
                    WHERE (content IS NOT NULL AND content != '' AND content LIKE ?)
                       OR (caption IS NOT NULL AND caption != '' AND caption LIKE ?)
                       OR (message_link IS NOT NULL AND message_link != '' AND message_link LIKE ?)
                """, (f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%"))
                row = cursor.fetchone()
                return row['count'] if row else 0
        except Exception as e:
            logger.error(f"Error counting encrypted messages: {e}")
            return 0
    
    def count_unencrypted_messages(self) -> int:
        """
        Count messages without encrypted fields.
        
        Returns:
            Number of messages with unencrypted fields
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM messages
                    WHERE (
                        (content IS NOT NULL AND content != '' AND content NOT LIKE ?)
                        OR (caption IS NOT NULL AND caption != '' AND caption NOT LIKE ?)
                        OR (message_link IS NOT NULL AND message_link != '' AND message_link NOT LIKE ?)
                    )
                    AND id NOT IN (
                        SELECT id FROM messages
                        WHERE (content IS NOT NULL AND content != '' AND content LIKE ?)
                           OR (caption IS NOT NULL AND caption != '' AND caption LIKE ?)
                           OR (message_link IS NOT NULL AND message_link != '' AND message_link LIKE ?)
                    )
                """, (
                    f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%",
                    f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%"
                ))
                row = cursor.fetchone()
                return row['count'] if row else 0
        except Exception as e:
            logger.error(f"Error counting unencrypted messages: {e}")
            return 0
    
    def count_encrypted_users(self) -> int:
        """
        Count users with encrypted fields.
        
        Returns:
            Number of users with at least one encrypted field
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM telegram_users
                    WHERE (username IS NOT NULL AND username != '' AND username LIKE ?)
                       OR (first_name IS NOT NULL AND first_name != '' AND first_name LIKE ?)
                       OR (last_name IS NOT NULL AND last_name != '' AND last_name LIKE ?)
                       OR (full_name IS NOT NULL AND full_name != '' AND full_name LIKE ?)
                       OR (phone IS NOT NULL AND phone != '' AND phone LIKE ?)
                       OR (bio IS NOT NULL AND bio != '' AND bio LIKE ?)
                """, (
                    f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%",
                    f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%"
                ))
                row = cursor.fetchone()
                return row['count'] if row else 0
        except Exception as e:
            logger.error(f"Error counting encrypted users: {e}")
            return 0
    
    def count_unencrypted_users(self) -> int:
        """
        Count users without encrypted fields.
        
        Returns:
            Number of users with unencrypted fields
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM telegram_users
                    WHERE (
                        (username IS NOT NULL AND username != '' AND username NOT LIKE ?)
                        OR (first_name IS NOT NULL AND first_name != '' AND first_name NOT LIKE ?)
                        OR (last_name IS NOT NULL AND last_name != '' AND last_name NOT LIKE ?)
                        OR (full_name IS NOT NULL AND full_name != '' AND full_name NOT LIKE ?)
                        OR (phone IS NOT NULL AND phone != '' AND phone NOT LIKE ?)
                        OR (bio IS NOT NULL AND bio != '' AND bio NOT LIKE ?)
                    )
                    AND id NOT IN (
                        SELECT id FROM telegram_users
                        WHERE (username IS NOT NULL AND username != '' AND username LIKE ?)
                           OR (first_name IS NOT NULL AND first_name != '' AND first_name LIKE ?)
                           OR (last_name IS NOT NULL AND last_name != '' AND last_name LIKE ?)
                           OR (full_name IS NOT NULL AND full_name != '' AND full_name LIKE ?)
                           OR (phone IS NOT NULL AND phone != '' AND phone LIKE ?)
                           OR (bio IS NOT NULL AND bio != '' AND bio LIKE ?)
                    )
                """, (
                    f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%",
                    f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%",
                    f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%",
                    f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%"
                ))
                row = cursor.fetchone()
                return row['count'] if row else 0
        except Exception as e:
            logger.error(f"Error counting unencrypted users: {e}")
            return 0
    
    def count_encrypted_credentials(self) -> int:
        """
        Count credentials with encrypted fields.
        
        Returns:
            Number of credentials with encrypted phone_number or session_string
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM telegram_credentials
                    WHERE (phone_number IS NOT NULL AND phone_number != '' AND phone_number LIKE ?)
                       OR (session_string IS NOT NULL AND session_string != '' AND session_string LIKE ?)
                """, (f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%"))
                row = cursor.fetchone()
                return row['count'] if row else 0
        except Exception as e:
            logger.error(f"Error counting encrypted credentials: {e}")
            return 0
    
    def count_unencrypted_credentials(self) -> int:
        """
        Count credentials without encrypted fields.
        
        Returns:
            Number of credentials with unencrypted fields
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM telegram_credentials
                    WHERE (
                        (phone_number IS NOT NULL AND phone_number != '' AND phone_number NOT LIKE ?)
                        OR (session_string IS NOT NULL AND session_string != '' AND session_string NOT LIKE ?)
                    )
                    AND id NOT IN (
                        SELECT id FROM telegram_credentials
                        WHERE (phone_number IS NOT NULL AND phone_number != '' AND phone_number LIKE ?)
                           OR (session_string IS NOT NULL AND session_string != '' AND session_string LIKE ?)
                    )
                """, (
                    f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%",
                    f"{self.ENCRYPTION_PREFIX}%", f"{self.ENCRYPTION_PREFIX}%"
                ))
                row = cursor.fetchone()
                return row['count'] if row else 0
        except Exception as e:
            logger.error(f"Error counting unencrypted credentials: {e}")
            return 0
    
    def get_encryption_statistics(self) -> Dict[str, int]:
        """
        Get all encryption statistics.
        
        Returns:
            Dictionary with counts:
            - encrypted_messages
            - unencrypted_messages
            - encrypted_users
            - unencrypted_users
            - encrypted_credentials
            - unencrypted_credentials
        """
        return {
            "encrypted_messages": self.count_encrypted_messages(),
            "unencrypted_messages": self.count_unencrypted_messages(),
            "encrypted_users": self.count_encrypted_users(),
            "unencrypted_users": self.count_unencrypted_users(),
            "encrypted_credentials": self.count_encrypted_credentials(),
            "unencrypted_credentials": self.count_unencrypted_credentials()
        }

