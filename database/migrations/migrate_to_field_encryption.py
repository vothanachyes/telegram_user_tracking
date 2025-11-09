"""
Migration script to encrypt existing database fields.
This script encrypts all sensitive data in the database when field-level encryption is enabled.
"""

import logging
import sqlite3
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FieldEncryptionMigration:
    """Migration to encrypt existing database fields."""
    
    def __init__(self, db_path: str):
        """
        Initialize migration.
        
        Args:
            db_path: Path to database file
        """
        self.db_path = db_path
        self.backup_path = f"{db_path}.pre_encryption_backup"
    
    def create_backup(self) -> bool:
        """
        Create backup of database before migration.
        
        Returns:
            True if backup created successfully, False otherwise
        """
        try:
            import shutil
            shutil.copy2(self.db_path, self.backup_path)
            logger.info(f"Created backup: {self.backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def restore_backup(self) -> bool:
        """
        Restore database from backup.
        
        Returns:
            True if restore successful, False otherwise
        """
        try:
            import shutil
            if Path(self.backup_path).exists():
                shutil.copy2(self.backup_path, self.db_path)
                logger.info(f"Restored database from backup: {self.backup_path}")
                return True
            else:
                logger.error(f"Backup file not found: {self.backup_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def migrate(self) -> bool:
        """
        Migrate existing data to encrypted format.
        
        Returns:
            True if migration successful, False otherwise
        """
        try:
            from services.database.field_encryption_service import FieldEncryptionService
            from database.managers.base import BaseDatabaseManager
            import platform
            import hashlib
            import base64
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.backends import default_backend
            
            # Check if encryption is enabled
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT encryption_enabled, encryption_key_hash FROM app_settings WHERE id = 1"
                )
                row = cursor.fetchone()
                
                if not row or not row['encryption_enabled']:
                    logger.info("Field encryption is not enabled - skipping migration")
                    return True
                
                encryption_key_hash = row['encryption_key_hash']
                if not encryption_key_hash:
                    logger.error("Encryption enabled but no key hash found")
                    return False
            
            # Derive encryption key (same logic as BaseDatabaseManager)
            device_id = f"{platform.node()}-{platform.machine()}-{platform.system()}"
            salt = hashlib.sha256(f"{device_id}-field-encryption".encode()).digest()[:16]
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key_material = f"{device_id}-{encryption_key_hash}".encode()
            key_bytes = kdf.derive(key_material)
            encryption_key = base64.urlsafe_b64encode(key_bytes).decode('utf-8')
            
            encryption_service = FieldEncryptionService(encryption_key)
            
            if not encryption_service.is_enabled():
                logger.error("Failed to initialize encryption service")
                return False
            
            # Create backup
            if not self.create_backup():
                logger.warning("Failed to create backup, but continuing with migration")
            
            # Encrypt all sensitive fields
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Encrypt telegram_credentials
                logger.info("Encrypting telegram_credentials...")
                cursor = conn.execute("SELECT id, phone_number, session_string FROM telegram_credentials")
                for row in cursor.fetchall():
                    encrypted_phone = encryption_service.encrypt_field(row['phone_number'])
                    encrypted_session = encryption_service.encrypt_field(row['session_string'])
                    
                    conn.execute("""
                        UPDATE telegram_credentials 
                        SET phone_number = ?, session_string = ?
                        WHERE id = ?
                    """, (encrypted_phone, encrypted_session, row['id']))
                
                # Encrypt telegram_users
                logger.info("Encrypting telegram_users...")
                cursor = conn.execute("""
                    SELECT id, username, first_name, last_name, full_name, phone, bio 
                    FROM telegram_users
                """)
                for row in cursor.fetchall():
                    encrypted_username = encryption_service.encrypt_field(row['username'])
                    encrypted_first_name = encryption_service.encrypt_field(row['first_name'])
                    encrypted_last_name = encryption_service.encrypt_field(row['last_name'])
                    encrypted_full_name = encryption_service.encrypt_field(row['full_name'])
                    encrypted_phone = encryption_service.encrypt_field(row['phone'])
                    encrypted_bio = encryption_service.encrypt_field(row['bio'])
                    
                    conn.execute("""
                        UPDATE telegram_users 
                        SET username = ?, first_name = ?, last_name = ?, 
                            full_name = ?, phone = ?, bio = ?
                        WHERE id = ?
                    """, (
                        encrypted_username, encrypted_first_name, encrypted_last_name,
                        encrypted_full_name, encrypted_phone, encrypted_bio, row['id']
                    ))
                
                # Encrypt messages
                logger.info("Encrypting messages...")
                cursor = conn.execute("SELECT id, content, caption, message_link FROM messages")
                for row in cursor.fetchall():
                    encrypted_content = encryption_service.encrypt_field(row['content'])
                    encrypted_caption = encryption_service.encrypt_field(row['caption'])
                    encrypted_message_link = encryption_service.encrypt_field(row['message_link'])
                    
                    conn.execute("""
                        UPDATE messages 
                        SET content = ?, caption = ?, message_link = ?
                        WHERE id = ?
                    """, (encrypted_content, encrypted_caption, encrypted_message_link, row['id']))
                
                # Encrypt reactions
                logger.info("Encrypting reactions...")
                cursor = conn.execute("SELECT id, message_link FROM reactions")
                for row in cursor.fetchall():
                    encrypted_message_link = encryption_service.encrypt_field(row['message_link'])
                    
                    conn.execute("""
                        UPDATE reactions 
                        SET message_link = ?
                        WHERE id = ?
                    """, (encrypted_message_link, row['id']))
                
                # Encrypt group_fetch_history
                logger.info("Encrypting group_fetch_history...")
                cursor = conn.execute("""
                    SELECT id, account_phone_number, account_full_name, account_username 
                    FROM group_fetch_history
                """)
                for row in cursor.fetchall():
                    encrypted_phone = encryption_service.encrypt_field(row['account_phone_number'])
                    encrypted_full_name = encryption_service.encrypt_field(row['account_full_name'])
                    encrypted_username = encryption_service.encrypt_field(row['account_username'])
                    
                    conn.execute("""
                        UPDATE group_fetch_history 
                        SET account_phone_number = ?, account_full_name = ?, account_username = ?
                        WHERE id = ?
                    """, (encrypted_phone, encrypted_full_name, encrypted_username, row['id']))
                
                # Encrypt account_activity_log
                logger.info("Encrypting account_activity_log...")
                cursor = conn.execute("SELECT id, phone_number FROM account_activity_log")
                for row in cursor.fetchall():
                    encrypted_phone = encryption_service.encrypt_field(row['phone_number'])
                    
                    conn.execute("""
                        UPDATE account_activity_log 
                        SET phone_number = ?
                        WHERE id = ?
                    """, (encrypted_phone, row['id']))
                
                conn.commit()
                logger.info("Migration completed successfully")
                return True
                
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def run(self) -> bool:
        """
        Run migration with backup and error handling.
        
        Returns:
            True if migration successful, False otherwise
        """
        try:
            logger.info("Starting field encryption migration...")
            success = self.migrate()
            
            if success:
                logger.info("Migration completed successfully")
            else:
                logger.error("Migration failed - consider restoring from backup")
            
            return success
        except Exception as e:
            logger.error(f"Migration error: {e}")
            return False


def run_migration(db_path: str) -> bool:
    """
    Run field encryption migration.
    
    Args:
        db_path: Path to database file
        
    Returns:
        True if migration successful, False otherwise
    """
    migration = FieldEncryptionMigration(db_path)
    return migration.run()


if __name__ == "__main__":
    # For testing/standalone execution
    import sys
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = "./data/app.db"
    
    logging.basicConfig(level=logging.INFO)
    success = run_migration(db_path)
    sys.exit(0 if success else 1)

