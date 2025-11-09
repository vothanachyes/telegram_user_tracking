"""
License cache manager.
"""

from typing import Optional, Any
from datetime import datetime
from database.managers.base import BaseDatabaseManager, _parse_datetime, _safe_get_row_value
from database.models.auth import UserLicenseCache
from utils.credential_storage import credential_storage
import logging

logger = logging.getLogger(__name__)


class LicenseManager(BaseDatabaseManager):
    """Manages license cache operations."""
    
    def _encrypt_field(self, value) -> Optional[str]:
        """Encrypt a field value for storage."""
        if value is None:
            return None
        try:
            # Convert to string before encryption
            if isinstance(value, datetime):
                str_value = value.isoformat()
            elif isinstance(value, bool):
                str_value = "True" if value else "False"
            else:
                str_value = str(value)
            return credential_storage.encrypt(str_value)
        except Exception as e:
            logger.error(f"Error encrypting field: {e}")
            return None
    
    def _decrypt_field(self, encrypted_value: Optional[str], field_type: type) -> Optional[Any]:
        """Decrypt a field value and convert back to original type."""
        if encrypted_value is None:
            return None
        try:
            decrypted_str = credential_storage.decrypt(encrypted_value)
            # Convert back to original type
            if field_type == datetime:
                return _parse_datetime(decrypted_str)
            elif field_type == bool:
                return decrypted_str == "True"
            elif field_type == int:
                return int(decrypted_str)
            else:
                return decrypted_str
        except Exception as e:
            logger.error(f"Error decrypting field: {e}")
            return None
    
    def save_license_cache(self, license_cache: UserLicenseCache) -> Optional[int]:
        """Save or update license cache with encrypted sensitive fields."""
        try:
            # Encrypt sensitive fields
            encrypted_tier = self._encrypt_field(license_cache.license_tier)
            encrypted_expiration = self._encrypt_field(license_cache.expiration_date)
            encrypted_max_devices = self._encrypt_field(license_cache.max_devices)
            encrypted_max_groups = self._encrypt_field(license_cache.max_groups)
            encrypted_max_accounts = self._encrypt_field(license_cache.max_accounts)
            encrypted_max_account_actions = self._encrypt_field(license_cache.max_account_actions)
            encrypted_is_active = self._encrypt_field(license_cache.is_active)
            encrypted_last_synced = self._encrypt_field(license_cache.last_synced)
            
            # Check if encryption failed for any required field
            if encrypted_tier is None and license_cache.license_tier is not None:
                logger.error("Failed to encrypt license_tier")
                return None
            
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO user_license_cache 
                    (user_email, license_tier, expiration_date, max_devices, max_groups, max_accounts, max_account_actions, last_synced, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_email) DO UPDATE SET
                        license_tier = excluded.license_tier,
                        expiration_date = excluded.expiration_date,
                        max_devices = excluded.max_devices,
                        max_groups = excluded.max_groups,
                        max_accounts = excluded.max_accounts,
                        max_account_actions = excluded.max_account_actions,
                        last_synced = excluded.last_synced,
                        is_active = excluded.is_active,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    license_cache.user_email,
                    encrypted_tier,
                    encrypted_expiration,
                    encrypted_max_devices,
                    encrypted_max_groups,
                    encrypted_max_accounts,
                    encrypted_max_account_actions,
                    encrypted_last_synced,
                    encrypted_is_active
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving license cache: {e}")
            return None
    
    def get_license_cache(self, user_email: str) -> Optional[UserLicenseCache]:
        """Get license cache by user email and decrypt sensitive fields."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM user_license_cache WHERE user_email = ?",
                (user_email,)
            )
            row = cursor.fetchone()
            if row:
                # Handle max_accounts column - may not exist in older databases
                try:
                    encrypted_max_accounts = row['max_accounts']
                except (KeyError, IndexError):
                    encrypted_max_accounts = None
                
                # Handle max_account_actions column - may not exist in older databases
                try:
                    encrypted_max_account_actions = row['max_account_actions']
                except (KeyError, IndexError):
                    encrypted_max_account_actions = None
                
                # Decrypt all sensitive fields
                license_tier = self._decrypt_field(_safe_get_row_value(row, 'license_tier'), str)
                expiration_date = self._decrypt_field(_safe_get_row_value(row, 'expiration_date'), datetime)
                max_devices = self._decrypt_field(_safe_get_row_value(row, 'max_devices'), int)
                max_groups = self._decrypt_field(_safe_get_row_value(row, 'max_groups'), int)
                max_accounts = self._decrypt_field(encrypted_max_accounts, int) if encrypted_max_accounts is not None else 1
                max_account_actions = self._decrypt_field(encrypted_max_account_actions, int) if encrypted_max_account_actions is not None else 2
                is_active = self._decrypt_field(_safe_get_row_value(row, 'is_active'), bool)
                last_synced = self._decrypt_field(_safe_get_row_value(row, 'last_synced'), datetime)
                
                # If decryption failed for critical fields, return None
                if license_tier is None:
                    logger.error(f"Failed to decrypt license_tier for user {user_email}")
                    return None
                
                return UserLicenseCache(
                    id=row['id'],
                    user_email=row['user_email'],
                    license_tier=license_tier,
                    expiration_date=expiration_date,
                    max_devices=max_devices if max_devices is not None else 1,
                    max_groups=max_groups if max_groups is not None else 3,
                    max_accounts=max_accounts,
                    max_account_actions=max_account_actions,
                    last_synced=last_synced,
                    is_active=is_active if is_active is not None else True,
                    created_at=_parse_datetime(row['created_at']),
                    updated_at=_parse_datetime(row['updated_at'])
                )
            return None
    
    def delete_license_cache(self, user_email: str) -> bool:
        """Delete license cache for a user."""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "DELETE FROM user_license_cache WHERE user_email = ?",
                    (user_email,)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting license cache: {e}")
            return False

