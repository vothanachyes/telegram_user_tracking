"""
Admin decryption service for support tools.
Handles database and PIN decryption operations.
"""

import logging
import sqlite3
import shutil
import hashlib
import base64
from pathlib import Path
from typing import Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

ENCRYPTION_PREFIX = "ENC:"


class AdminDecryptionService:
    """Service for decrypting databases and PINs."""
    
    @staticmethod
    def derive_database_encryption_key(hostname: str, machine: str, system: str, encryption_key_hash: str) -> str:
        """
        Derive encryption key from device information and encryption key hash.
        
        Args:
            hostname: Device hostname
            machine: Machine type
            system: Operating system
            encryption_key_hash: Encryption key hash from app_settings
            
        Returns:
            Base64-encoded encryption key
        """
        device_id = f"{hostname}-{machine}-{system}"
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
        
        return encryption_key
    
    @staticmethod
    def derive_device_encryption_key(hostname: str, machine: str, system: str) -> bytes:
        """
        Derive device encryption key for PIN decryption.
        
        Args:
            hostname: Device hostname
            machine: Machine type
            system: Operating system
            
        Returns:
            Base64-encoded Fernet key
        """
        machine_info = f"{hostname}-{machine}-{system}"
        salt = hashlib.sha256(machine_info.encode()).digest()[:16]
        password = hashlib.sha256(machine_info.encode()).digest()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    @staticmethod
    def derive_user_encryption_key(user_id: str) -> bytes:
        """
        Derive user encryption key for PIN decryption.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            Base64-encoded Fernet key
        """
        salt = hashlib.sha256(f"user-pin-encryption-{user_id}".encode()).digest()[:16]
        password = hashlib.sha256(f"{user_id}-pin-encryption".encode()).digest()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    @staticmethod
    def create_cipher(encryption_key: str) -> Fernet:
        """
        Create Fernet cipher from encryption key.
        
        Args:
            encryption_key: Base64-encoded encryption key
            
        Returns:
            Fernet cipher instance
        """
        key_bytes = base64.urlsafe_b64decode(encryption_key.encode('utf-8'))
        
        if len(key_bytes) != 32:
            salt = hashlib.sha256(b"field_encryption_salt").digest()[:16]
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key_bytes = kdf.derive(encryption_key.encode('utf-8'))
        
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        return Fernet(fernet_key)
    
    @staticmethod
    def decrypt_field(value: Optional[str], cipher: Fernet) -> Optional[str]:
        """
        Decrypt a field value.
        
        Args:
            value: Encrypted value with prefix, or plain text
            cipher: Fernet cipher instance
            
        Returns:
            Decrypted plain text value
        """
        if value is None:
            return None
        
        if not value or not value.strip():
            return value
        
        if not value.startswith(ENCRYPTION_PREFIX):
            return value
        
        try:
            encrypted_str = value[len(ENCRYPTION_PREFIX):]
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_str.encode('utf-8'))
            decrypted_bytes = cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Error decrypting field: {e}")
            return value
    
    @staticmethod
    def get_encryption_key_hash(db_path: str) -> Optional[str]:
        """
        Get encryption key hash from app_settings table.
        
        Args:
            db_path: Path to database file
            
        Returns:
            Encryption key hash, or None if not found
        """
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT encryption_key_hash FROM app_settings WHERE id = 1"
                )
                row = cursor.fetchone()
                if row:
                    return row['encryption_key_hash']
                return None
        except Exception as e:
            logger.error(f"Error reading encryption_key_hash: {e}")
            return None
    
    @staticmethod
    def decrypt_database(
        input_db_path: str,
        output_db_path: str,
        hostname: str,
        machine: str,
        system: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Decrypt all encrypted fields in database and create new database.
        
        Args:
            input_db_path: Path to encrypted database
            output_db_path: Path to output decrypted database
            hostname: Device hostname
            machine: Machine type
            system: Operating system
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Validate input database exists
            if not Path(input_db_path).exists():
                return False, f"Input database not found: {input_db_path}"
            
            # Get encryption key hash
            encryption_key_hash = AdminDecryptionService.get_encryption_key_hash(input_db_path)
            if not encryption_key_hash:
                return False, "encryption_key_hash not found in database. Encryption may not be enabled."
            
            # Derive encryption key
            encryption_key = AdminDecryptionService.derive_database_encryption_key(
                hostname, machine, system, encryption_key_hash
            )
            
            # Create cipher
            cipher = AdminDecryptionService.create_cipher(encryption_key)
            
            # Copy database to output location
            output_path = Path(output_db_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(input_db_path, output_db_path)
            
            # Decrypt all encrypted fields
            with sqlite3.connect(output_db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Decrypt telegram_credentials
                cursor = conn.execute("SELECT id, phone_number, session_string FROM telegram_credentials")
                rows = cursor.fetchall()
                for row in rows:
                    decrypted_phone = AdminDecryptionService.decrypt_field(row['phone_number'], cipher)
                    decrypted_session = AdminDecryptionService.decrypt_field(row['session_string'], cipher)
                    
                    conn.execute("""
                        UPDATE telegram_credentials 
                        SET phone_number = ?, session_string = ?
                        WHERE id = ?
                    """, (decrypted_phone, decrypted_session, row['id']))
                
                # Decrypt telegram_users
                cursor = conn.execute("""
                    SELECT id, username, first_name, last_name, full_name, phone, bio 
                    FROM telegram_users
                """)
                rows = cursor.fetchall()
                for row in rows:
                    decrypted_username = AdminDecryptionService.decrypt_field(row['username'], cipher)
                    decrypted_first_name = AdminDecryptionService.decrypt_field(row['first_name'], cipher)
                    decrypted_last_name = AdminDecryptionService.decrypt_field(row['last_name'], cipher)
                    decrypted_full_name = AdminDecryptionService.decrypt_field(row['full_name'], cipher)
                    decrypted_phone = AdminDecryptionService.decrypt_field(row['phone'], cipher)
                    decrypted_bio = AdminDecryptionService.decrypt_field(row['bio'], cipher)
                    
                    conn.execute("""
                        UPDATE telegram_users 
                        SET username = ?, first_name = ?, last_name = ?, 
                            full_name = ?, phone = ?, bio = ?
                        WHERE id = ?
                    """, (
                        decrypted_username, decrypted_first_name, decrypted_last_name,
                        decrypted_full_name, decrypted_phone, decrypted_bio, row['id']
                    ))
                
                # Decrypt messages
                cursor = conn.execute("SELECT id, content, caption, message_link FROM messages")
                rows = cursor.fetchall()
                for row in rows:
                    decrypted_content = AdminDecryptionService.decrypt_field(row['content'], cipher)
                    decrypted_caption = AdminDecryptionService.decrypt_field(row['caption'], cipher)
                    decrypted_message_link = AdminDecryptionService.decrypt_field(row['message_link'], cipher)
                    
                    conn.execute("""
                        UPDATE messages 
                        SET content = ?, caption = ?, message_link = ?
                        WHERE id = ?
                    """, (decrypted_content, decrypted_caption, decrypted_message_link, row['id']))
                
                # Decrypt reactions
                cursor = conn.execute("SELECT id, message_link FROM reactions")
                rows = cursor.fetchall()
                for row in rows:
                    decrypted_message_link = AdminDecryptionService.decrypt_field(row['message_link'], cipher)
                    
                    conn.execute("""
                        UPDATE reactions 
                        SET message_link = ?
                        WHERE id = ?
                    """, (decrypted_message_link, row['id']))
                
                # Decrypt group_fetch_history
                cursor = conn.execute("""
                    SELECT id, account_phone_number, account_full_name, account_username 
                    FROM group_fetch_history
                """)
                rows = cursor.fetchall()
                for row in rows:
                    decrypted_phone = AdminDecryptionService.decrypt_field(row['account_phone_number'], cipher)
                    decrypted_full_name = AdminDecryptionService.decrypt_field(row['account_full_name'], cipher)
                    decrypted_username = AdminDecryptionService.decrypt_field(row['account_username'], cipher)
                    
                    conn.execute("""
                        UPDATE group_fetch_history 
                        SET account_phone_number = ?, account_full_name = ?, account_username = ?
                        WHERE id = ?
                    """, (decrypted_phone, decrypted_full_name, decrypted_username, row['id']))
                
                # Decrypt account_activity_log
                cursor = conn.execute("SELECT id, phone_number FROM account_activity_log")
                rows = cursor.fetchall()
                for row in rows:
                    decrypted_phone = AdminDecryptionService.decrypt_field(row['phone_number'], cipher)
                    
                    conn.execute("""
                        UPDATE account_activity_log 
                        SET phone_number = ?
                        WHERE id = ?
                    """, (decrypted_phone, row['id']))
                
                conn.commit()
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error decrypting database: {e}", exc_info=True)
            return False, str(e)
    
    @staticmethod
    def decrypt_pin(
        hostname: str,
        machine: str,
        system: str,
        user_id: str,
        encrypted_pin: str
    ) -> str:
        """
        Decrypt PIN using user ID and device information.
        
        Args:
            hostname: Device hostname
            machine: Machine type
            system: Operating system
            user_id: Firebase user ID
            encrypted_pin: Encrypted PIN string
            
        Returns:
            Decrypted PIN
            
        Raises:
            ValueError: If decryption fails
        """
        try:
            # Step 1: Decrypt with user ID key
            user_key = AdminDecryptionService.derive_user_encryption_key(user_id)
            user_cipher = Fernet(user_key)
            
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_pin.encode())
            device_encrypted_pin = user_cipher.decrypt(encrypted_bytes).decode()
            
            # Step 2: Decrypt with device key
            device_key = AdminDecryptionService.derive_device_encryption_key(hostname, machine, system)
            device_cipher = Fernet(device_key)
            
            device_encrypted_bytes = base64.urlsafe_b64decode(device_encrypted_pin.encode())
            decrypted = device_cipher.decrypt(device_encrypted_bytes)
            
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt PIN: {e}")


# Global service instance
admin_decryption_service = AdminDecryptionService()

