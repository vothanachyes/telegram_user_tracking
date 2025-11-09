"""
Limit enforcer for checking and enforcing license limits.
"""

import logging
from typing import Optional, Tuple, TYPE_CHECKING

from config.firebase_config import firebase_config
from database.db_manager import DatabaseManager
from utils.constants import LICENSE_PRICING

if TYPE_CHECKING:
    from services.auth_service import AuthService

logger = logging.getLogger(__name__)


class LimitEnforcer:
    """Handles license limit checking and enforcement."""
    
    def __init__(self, db_manager: DatabaseManager, auth_service_instance: Optional['AuthService'] = None):
        self.db_manager = db_manager
        self._auth_service = auth_service_instance
    
    def _get_auth_service(self):
        """Lazy import of auth_service to avoid circular dependency."""
        if self._auth_service is None:
            from services.auth_service import auth_service
            return auth_service
        return self._auth_service
    
    def can_add_group(self, user_email: Optional[str] = None, uid: Optional[str] = None, license_status: Optional[dict] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if user can add another group.
        Returns (can_add, error_message)
        """
        # Import here to avoid circular dependency
        from services.license.license_checker import LicenseChecker
        
        if license_status is None:
            checker = LicenseChecker(self.db_manager, self._auth_service)
            license_status = checker.check_license_status(user_email, uid)
        
        if not license_status['is_active']:
            return False, "Your license has expired. Please contact admin to renew."
        
        if license_status['expired']:
            return False, "Your license has expired. Please contact admin to renew."
        
        tier = license_status['tier']
        max_groups = license_status['max_groups']
        
        # Premium tier has unlimited groups
        if max_groups == -1:
            return True, None
        
        # Count current groups
        groups = self.db_manager.get_all_groups()
        current_count = len(groups)
        
        if current_count >= max_groups:
            tier_name = LICENSE_PRICING.get(tier, {}).get('name', tier.capitalize())
            return False, f"You have reached the group limit ({max_groups}) for {tier_name} tier. Please contact admin to upgrade."
        
        return True, None
    
    def can_add_device(self, device_id: str, user_email: Optional[str] = None, uid: Optional[str] = None, license_status: Optional[dict] = None) -> Tuple[bool, Optional[str], list]:
        """
        Check if user can add another device.
        Returns (can_add, error_message, active_devices)
        """
        if not uid:
            auth_service = self._get_auth_service()
            current_user = auth_service.get_current_user()
            if not current_user:
                return False, "User not authenticated", []
            uid = current_user.get('uid')
            if not user_email:
                user_email = current_user.get('email')
        
        # Import here to avoid circular dependency
        from services.license.license_sync import LicenseSync
        from services.license.license_checker import LicenseChecker
        
        # Ensure we sync from Firebase before checking status
        # This ensures license is created if it doesn't exist
        if uid and user_email:
            logger.info(f"Syncing license before device check for user {user_email} (uid: {uid})")
            sync = LicenseSync(self.db_manager, self._auth_service)
            sync.sync_from_firebase(user_email, uid)
        
        if license_status is None:
            checker = LicenseChecker(self.db_manager, self._auth_service)
            license_status = checker.check_license_status(user_email, uid)
        
        if not license_status['is_active']:
            return False, "Your license has expired. Please contact admin to renew.", []
        
        if license_status['expired']:
            return False, "Your license has expired. Please contact admin to renew.", []
        
        max_devices = license_status['max_devices']
        
        # Get active devices from Firebase
        active_devices = firebase_config.get_active_devices(uid)
        
        # Check if current device is already registered
        if device_id in active_devices:
            return True, None, active_devices
        
        # Check if limit reached
        if len(active_devices) >= max_devices:
            tier = license_status['tier']
            tier_name = LICENSE_PRICING.get(tier, {}).get('name', tier.capitalize())
            return False, f"You have reached the device limit ({max_devices}) for {tier_name} tier. Please contact admin to upgrade or deactivate a device.", active_devices
        
        return True, None, active_devices
    
    def get_active_devices(self, uid: Optional[str] = None) -> list:
        """Get list of active device IDs for current user."""
        if not uid:
            auth_service = self._get_auth_service()
            current_user = auth_service.get_current_user()
            if not current_user:
                return []
            uid = current_user.get('uid')
        
        return firebase_config.get_active_devices(uid)
    
    def can_add_account(self, user_email: Optional[str] = None, uid: Optional[str] = None, license_status: Optional[dict] = None) -> Tuple[bool, Optional[str], int, int]:
        """
        Check if user can add another Telegram account.
        
        Args:
            user_email: User email (optional, will get from auth service if not provided)
            uid: User UID (optional, will get from auth service if not provided)
            license_status: Optional pre-fetched license status
            
        Returns:
            Tuple of (can_add, error_message, current_count, max_count)
        """
        if not user_email or not uid:
            auth_service = self._get_auth_service()
            current_user = auth_service.get_current_user()
            if not current_user:
                return False, "User not authenticated", 0, 0
            if not user_email:
                user_email = current_user.get('email')
            if not uid:
                uid = current_user.get('uid')
        
        # Import here to avoid circular dependency
        from services.license.license_checker import LicenseChecker
        
        if license_status is None:
            checker = LicenseChecker(self.db_manager, self._auth_service)
            license_status = checker.check_license_status(user_email, uid)
        
        if not license_status['is_active']:
            return False, "Your license has expired. Please contact admin to renew.", 0, 0
        
        if license_status['expired']:
            return False, "Your license has expired. Please contact admin to renew.", 0, 0
        
        max_accounts = license_status['max_accounts']
        
        # Get current account count from database
        credentials = self.db_manager.get_telegram_credentials()
        current_count = len(credentials)
        
        if current_count >= max_accounts:
            tier = license_status['tier']
            tier_name = LICENSE_PRICING.get(tier, {}).get('name', tier.capitalize())
            return False, f"You have reached the account limit ({max_accounts}) for {tier_name} tier. Please contact admin to upgrade.", current_count, max_accounts
        
        return True, None, current_count, max_accounts
    
    def enforce_group_limit(self, user_email: Optional[str] = None) -> bool:
        """
        Enforce group limit - check if user can add groups.
        Returns True if allowed, False if blocked.
        """
        can_add, _ = self.can_add_group(user_email)
        return can_add

