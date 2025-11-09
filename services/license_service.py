"""
License service for managing user subscriptions and limits.
"""

import logging
from typing import Optional, Dict, Any, Tuple, TYPE_CHECKING

from database.db_manager import DatabaseManager
from services.license.license_checker import LicenseChecker
from services.license.license_sync import LicenseSync
from services.license.limit_enforcer import LimitEnforcer

if TYPE_CHECKING:
    from services.auth_service import AuthService

logger = logging.getLogger(__name__)


class LicenseService:
    """Service for managing user licenses and enforcing limits."""
    
    def __init__(self, db_manager: DatabaseManager, auth_service_instance: Optional['AuthService'] = None):
        self.db_manager = db_manager
        self._auth_service = auth_service_instance
        
        # Initialize sub-modules
        self.checker = LicenseChecker(db_manager, auth_service_instance)
        self.sync = LicenseSync(db_manager, auth_service_instance)
        self.enforcer = LimitEnforcer(db_manager, auth_service_instance)
    
    def get_user_tier(self, user_email: Optional[str] = None) -> str:
        """
        Get current user's license tier.
        Returns tier name (silver, gold, premium) or default if not found.
        """
        # Try to sync from Firebase first if needed
        if not user_email:
            auth_service = self._get_auth_service()
            current_user = auth_service.get_current_user()
            if current_user:
                user_email = current_user.get('email')
                uid = current_user.get('uid')
                if uid:
                    self.sync.sync_from_firebase(user_email, uid)
        
        return self.checker.get_user_tier(user_email)
    
    def check_license_status(self, user_email: Optional[str] = None, uid: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if user has an active license.
        Returns dict with status, tier, expiration, etc.
        """
        # Sync from Firebase if we have uid
        if uid:
            if not user_email:
                auth_service = self._get_auth_service()
                current_user = auth_service.get_current_user()
                if current_user:
                    user_email = current_user.get('email')
            
            if user_email:
                logger.info(f"Syncing license from Firebase for user {user_email} (uid: {uid})")
                sync_success = self.sync.sync_from_firebase(user_email, uid)
                if not sync_success:
                    logger.warning(f"Failed to sync license from Firebase for user {user_email}")
        
        return self.checker.check_license_status(user_email, uid)
    
    def sync_from_firebase(self, user_email: Optional[str] = None, uid: Optional[str] = None) -> bool:
        """
        Sync license data from Firebase Firestore to local cache.
        Returns True if successful.
        """
        return self.sync.sync_from_firebase(user_email, uid)
    
    def can_add_group(self, user_email: Optional[str] = None, uid: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if user can add another group.
        Returns (can_add, error_message)
        """
        # Sync before checking if we have uid
        if uid:
            if not user_email:
                auth_service = self._get_auth_service()
                current_user = auth_service.get_current_user()
                if current_user:
                    user_email = current_user.get('email')
            if user_email:
                self.sync.sync_from_firebase(user_email, uid)
        
        status = self.check_license_status(user_email, uid)
        return self.enforcer.can_add_group(user_email, uid, status)
    
    def can_add_device(self, device_id: str, user_email: Optional[str] = None, uid: Optional[str] = None) -> Tuple[bool, Optional[str], list]:
        """
        Check if user can add another device.
        Returns (can_add, error_message, active_devices)
        """
        return self.enforcer.can_add_device(device_id, user_email, uid)
    
    def get_active_devices(self, uid: Optional[str] = None) -> list:
        """Get list of active device IDs for current user."""
        return self.enforcer.get_active_devices(uid)
    
    def can_add_account(self, user_email: Optional[str] = None, uid: Optional[str] = None) -> Tuple[bool, Optional[str], int, int]:
        """
        Check if user can add another Telegram account.
        
        Args:
            user_email: User email (optional, will get from auth service if not provided)
            uid: User UID (optional, will get from auth service if not provided)
            
        Returns:
            Tuple of (can_add, error_message, current_count, max_count)
        """
        return self.enforcer.can_add_account(user_email, uid)
    
    def enforce_group_limit(self, user_email: Optional[str] = None) -> bool:
        """
        Enforce group limit - check if user can add groups.
        Returns True if allowed, False if blocked.
        """
        return self.enforcer.enforce_group_limit(user_email)
    
    def get_license_info(self, user_email: Optional[str] = None, uid: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive license information for current user.
        Returns dict with all license details.
        """
        return self.checker.get_license_info(user_email, uid)
    
    def _get_auth_service(self):
        """Lazy import of auth_service to avoid circular dependency."""
        if self._auth_service is None:
            from services.auth_service import auth_service
            return auth_service
        return self._auth_service
