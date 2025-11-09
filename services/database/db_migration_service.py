"""
Database migration service for moving database files to new locations.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class DatabaseMigrationService:
    """Service for migrating database files to new locations."""
    
    @staticmethod
    def validate_path(path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a path is writable and has sufficient space.
        
        Args:
            path: Path to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        try:
            path_obj = Path(path)
            
            # Check if parent directory exists or can be created
            parent = path_obj.parent
            if not parent.exists():
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return False, f"Cannot create directory: {str(e)}"
            
            # Check if directory is writable
            if not os.access(parent, os.W_OK):
                return False, "Directory is not writable"
            
            # Check available disk space (basic check)
            try:
                stat = shutil.disk_usage(parent)
                # Require at least 100MB free space
                if stat.free < 100 * 1024 * 1024:
                    return False, "Insufficient disk space (requires at least 100MB)"
            except Exception:
                # If we can't check disk space, continue anyway
                pass
            
            return True, None
            
        except Exception as e:
            return False, f"Path validation failed: {str(e)}"
    
    @staticmethod
    def migrate_database(
        old_path: str,
        new_path: str,
        encryption_key: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Migrate database from old path to new path.
        Handles database file and related files (WAL, SHM).
        
        Args:
            old_path: Current database path
            new_path: New database path
            encryption_key: Optional encryption key if database is encrypted
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            old_path_obj = Path(old_path)
            new_path_obj = Path(new_path)
            
            # Validate old path exists
            if not old_path_obj.exists():
                return False, f"Source database not found: {old_path}"
            
            # Validate new path
            is_valid, error = DatabaseMigrationService.validate_path(new_path)
            if not is_valid:
                return False, error
            
            # Ensure new directory exists
            new_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # If database is encrypted, decrypt before migration
            from services.database.encryption_service import DatabaseEncryptionService
            
            temp_path = None
            if encryption_key and DatabaseEncryptionService.is_file_encrypted(old_path):
                # Decrypt to temporary location
                temp_path = str(old_path_obj) + ".temp_decrypt"
                if not DatabaseEncryptionService.decrypt_file(old_path, encryption_key):
                    return False, "Failed to decrypt database for migration"
                # Update old_path to point to decrypted file
                old_path_obj = Path(temp_path)
            
            # Copy database file
            try:
                shutil.copy2(old_path_obj, new_path_obj)
                logger.info(f"Copied database file: {old_path} -> {new_path}")
            except Exception as e:
                if temp_path and Path(temp_path).exists():
                    # Re-encrypt if we decrypted
                    DatabaseEncryptionService.encrypt_file(temp_path, encryption_key)
                return False, f"Failed to copy database file: {str(e)}"
            
            # Copy related files (WAL, SHM) if they exist
            wal_path = Path(str(old_path_obj) + "-wal")
            shm_path = Path(str(old_path_obj) + "-shm")
            
            if wal_path.exists():
                try:
                    shutil.copy2(wal_path, Path(str(new_path_obj) + "-wal"))
                    logger.info(f"Copied WAL file: {wal_path} -> {new_path}-wal")
                except Exception as e:
                    logger.warning(f"Failed to copy WAL file: {e}")
            
            if shm_path.exists():
                try:
                    shutil.copy2(shm_path, Path(str(new_path_obj) + "-shm"))
                    logger.info(f"Copied SHM file: {shm_path} -> {new_path}-shm")
                except Exception as e:
                    logger.warning(f"Failed to copy SHM file: {e}")
            
            # Re-encrypt if we decrypted
            if temp_path and Path(temp_path).exists():
                if encryption_key:
                    DatabaseEncryptionService.encrypt_file(temp_path, encryption_key)
                # Clean up temp file
                Path(temp_path).unlink()
            
            # Verify migration by checking file size
            if new_path_obj.exists() and new_path_obj.stat().st_size > 0:
                logger.info("Database migration completed successfully")
                return True, None
            else:
                return False, "Migration verification failed - new database file is empty or missing"
            
        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            return False, f"Migration failed: {str(e)}"
    
    @staticmethod
    def get_database_size(db_path: str) -> int:
        """
        Get total size of database and related files.
        
        Args:
            db_path: Path to database file
            
        Returns:
            Total size in bytes
        """
        try:
            total_size = 0
            db_path_obj = Path(db_path)
            
            # Main database file
            if db_path_obj.exists():
                total_size += db_path_obj.stat().st_size
            
            # WAL file
            wal_path = Path(str(db_path_obj) + "-wal")
            if wal_path.exists():
                total_size += wal_path.stat().st_size
            
            # SHM file
            shm_path = Path(str(db_path_obj) + "-shm")
            if shm_path.exists():
                total_size += shm_path.stat().st_size
            
            return total_size
            
        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            return 0

