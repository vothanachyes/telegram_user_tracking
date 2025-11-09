"""
License cache manager.
"""

from typing import Optional
from database.managers.base import BaseDatabaseManager, _parse_datetime
from database.models.auth import UserLicenseCache
import logging

logger = logging.getLogger(__name__)


class LicenseManager(BaseDatabaseManager):
    """Manages license cache operations."""
    
    def save_license_cache(self, license_cache: UserLicenseCache) -> Optional[int]:
        """Save or update license cache."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO user_license_cache 
                    (user_email, license_tier, expiration_date, max_devices, max_groups, max_accounts, max_account_actions, last_synced, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                    ON CONFLICT(user_email) DO UPDATE SET
                        license_tier = excluded.license_tier,
                        expiration_date = excluded.expiration_date,
                        max_devices = excluded.max_devices,
                        max_groups = excluded.max_groups,
                        max_accounts = excluded.max_accounts,
                        max_account_actions = excluded.max_account_actions,
                        last_synced = CURRENT_TIMESTAMP,
                        is_active = excluded.is_active,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    license_cache.user_email,
                    license_cache.license_tier,
                    license_cache.expiration_date,
                    license_cache.max_devices,
                    license_cache.max_groups,
                    license_cache.max_accounts,
                    license_cache.max_account_actions,
                    license_cache.is_active
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving license cache: {e}")
            return None
    
    def get_license_cache(self, user_email: str) -> Optional[UserLicenseCache]:
        """Get license cache by user email."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM user_license_cache WHERE user_email = ?",
                (user_email,)
            )
            row = cursor.fetchone()
            if row:
                # Handle max_accounts column - may not exist in older databases
                try:
                    max_accounts = row['max_accounts']
                except (KeyError, IndexError):
                    max_accounts = 1  # Default to 1 for backward compatibility
                
                # Handle max_account_actions column - may not exist in older databases
                try:
                    max_account_actions = row['max_account_actions']
                except (KeyError, IndexError):
                    max_account_actions = 2  # Default to 2 for backward compatibility
                
                return UserLicenseCache(
                    id=row['id'],
                    user_email=row['user_email'],
                    license_tier=row['license_tier'],
                    expiration_date=_parse_datetime(row['expiration_date']),
                    max_devices=row['max_devices'],
                    max_groups=row['max_groups'],
                    max_accounts=max_accounts,
                    max_account_actions=max_account_actions,
                    last_synced=_parse_datetime(row['last_synced']),
                    is_active=bool(row['is_active']),
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

