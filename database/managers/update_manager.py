"""
Update history manager for tracking app update installations.
"""

from database.managers.base import BaseDatabaseManager, _parse_datetime
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UpdateManager(BaseDatabaseManager):
    """Manages app update history operations."""
    
    def record_update_installation(
        self,
        user_email: str,
        version: str,
        download_path: Optional[str] = None
    ) -> bool:
        """
        Record an update installation in the database.
        
        Args:
            user_email: User email who installed the update
            version: Version string that was installed
            download_path: Optional path to downloaded file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO app_update_history 
                    (user_email, version, download_path, installed_at)
                    VALUES (?, ?, ?, ?)
                """, (user_email, version, download_path, datetime.now()))
                conn.commit()
                logger.info(f"Recorded update installation: {user_email} - {version}")
                return True
        except Exception as e:
            logger.error(f"Error recording update installation: {e}")
            return False
    
    def get_user_installed_versions(self, user_email: str) -> List[dict]:
        """
        Get list of versions installed by a user.
        
        Args:
            user_email: User email
        
        Returns:
            List of dictionaries with version info
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT version, installed_at, download_path
                    FROM app_update_history
                    WHERE user_email = ?
                    ORDER BY installed_at DESC
                """, (user_email,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'version': row['version'],
                        'installed_at': _parse_datetime(row['installed_at']),
                        'download_path': row['download_path']
                    })
                return results
        except Exception as e:
            logger.error(f"Error getting user installed versions: {e}")
            return []
    
    def has_user_installed_version(self, user_email: str, version: str) -> bool:
        """
        Check if user has installed a specific version.
        
        Args:
            user_email: User email
            version: Version string to check
        
        Returns:
            True if user has installed this version, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM app_update_history
                    WHERE user_email = ? AND version = ?
                """, (user_email, version))
                
                row = cursor.fetchone()
                return row['count'] > 0
        except Exception as e:
            logger.error(f"Error checking if user installed version: {e}")
            return False

