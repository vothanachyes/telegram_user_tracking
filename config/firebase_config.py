"""
Firebase configuration and initialization using REST API (no Admin SDK).
This eliminates the need for Admin credentials in the desktop app.
"""

import logging
from typing import Optional, List, Dict

from config.firebase.core import FirebaseCore
from config.firebase.helpers import FirestoreHelpers
from config.firebase.license_operations import LicenseOperations
from config.firebase.notification_operations import NotificationOperations
from config.firebase.update_operations import UpdateOperations
from config.firebase.activity_operations import ActivityOperations
from config.firebase.device_operations import DeviceOperations

logger = logging.getLogger(__name__)


class FirebaseConfig:
    """
    Firebase configuration manager using REST API.
    No Admin SDK required - uses Firebase REST API with ID token authentication.
    Composes specialized operation modules for better organization.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseConfig, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Firebase config with composed operation modules."""
        # Core functionality
        self._core = FirebaseCore()
        
        # Operation modules
        self._license_ops = LicenseOperations(self._core)
        self._notification_ops = NotificationOperations(self._core)
        self._update_ops = UpdateOperations(self._core)
        self._activity_ops = ActivityOperations(self._core)
        self._device_ops = DeviceOperations(self._core)
        
        # Expose core properties for backward compatibility
        self.is_available = self._core.is_available
        self.project_id = self._core.project_id
        self.web_api_key = self._core.web_api_key
    
    # ==================== Core Methods ====================
    
    def initialize(self, id_token: Optional[str] = None) -> bool:
        """Initialize Firebase (delegates to core)."""
        result = self._core.initialize(id_token)
        if result:
            self._initialized = True
        return result
    
    def set_id_token(self, id_token: str) -> None:
        """Set the current ID token (delegates to core)."""
        self._core.set_id_token(id_token)
    
    def is_initialized(self) -> bool:
        """Check if Firebase is initialized."""
        return self._core.is_initialized()
    
    def verify_token(self, id_token: str) -> Optional[dict]:
        """Verify Firebase ID token (delegates to core)."""
        return self._core.verify_token(id_token)
    
    def get_user(self, uid: Optional[str] = None, id_token: Optional[str] = None) -> Optional[dict]:
        """Get user info (delegates to core)."""
        return self._core.get_user(uid, id_token)
    
    # Expose _current_id_token for backward compatibility (used by watch_service)
    @property
    def _current_id_token(self) -> Optional[str]:
        """Get current ID token (for backward compatibility)."""
        return self._core._current_id_token
    
    # ==================== License Methods ====================
    
    def get_user_license(self, uid: str, id_token: Optional[str] = None) -> Optional[dict]:
        """Get user license (delegates to license operations)."""
        return self._license_ops.get_user_license(uid, id_token)
    
    def get_license_tiers(self, id_token: Optional[str] = None) -> List[dict]:
        """Get all license tiers (delegates to license operations)."""
        return self._license_ops.get_license_tiers(id_token)
    
    def get_license_tier(self, tier_key: str, id_token: Optional[str] = None) -> Optional[dict]:
        """Get specific license tier (delegates to license operations)."""
        return self._license_ops.get_license_tier(tier_key, id_token)
    
    def get_active_devices(self, uid: str) -> list:
        """Get active devices from license (delegates to license operations)."""
        return self._license_ops.get_active_devices(uid)
    
    # ==================== Notification Methods ====================
    
    def get_notifications(self, user_id: Optional[str] = None, id_token: Optional[str] = None) -> List[dict]:
        """Get notifications (delegates to notification operations)."""
        return self._notification_ops.get_notifications(user_id, id_token)
    
    def get_user_notification_status(self, user_id: str, notification_id: str, id_token: Optional[str] = None) -> Optional[dict]:
        """Get user notification status (delegates to notification operations)."""
        return self._notification_ops.get_user_notification_status(user_id, notification_id, id_token)
    
    def mark_notification_read(self, user_id: str, notification_id: str, id_token: Optional[str] = None) -> bool:
        """Mark notification as read (delegates to notification operations)."""
        return self._notification_ops.mark_notification_read(user_id, notification_id, id_token)
    
    def get_user_notification_statuses(self, user_id: str, id_token: Optional[str] = None) -> dict:
        """Get all notification statuses (delegates to notification operations)."""
        return self._notification_ops.get_user_notification_statuses(user_id, id_token)
    
    # ==================== Update Methods ====================
    
    def get_app_update_info(self, id_token: Optional[str] = None) -> Optional[dict]:
        """Get app update info (delegates to update operations)."""
        return self._update_ops.get_app_update_info(id_token)
    
    # ==================== User Activities Methods ====================
    
    def get_user_activities(self, uid: str, id_token: Optional[str] = None) -> Optional[dict]:
        """Get user activities (delegates to activity operations)."""
        return self._activity_ops.get_user_activities(uid, id_token)
    
    def update_user_activities(self, uid: str, updates: dict, id_token: Optional[str] = None) -> bool:
        """Update user activities (delegates to activity operations)."""
        return self._activity_ops.update_user_activities(uid, updates, id_token)
    
    # ==================== Device Methods ====================
    
    def get_user_devices(self, uid: str, id_token: Optional[str] = None) -> List[dict]:
        """Get user devices (delegates to device operations)."""
        return self._device_ops.get_user_devices(uid, id_token)
    
    def add_user_device(self, uid: str, device_id: str, device_info: dict, id_token: Optional[str] = None) -> bool:
        """Add user device (delegates to device operations)."""
        return self._device_ops.add_user_device(uid, device_id, device_info, id_token)
    
    def check_device_revoked(self, uid: str, device_id: str, id_token: Optional[str] = None) -> bool:
        """Check if device is revoked (delegates to device operations)."""
        return self._device_ops.check_device_revoked(uid, device_id, id_token)
    
    # ==================== Helper Methods (for backward compatibility) ====================
    
    def _convert_firestore_document(self, firestore_doc: dict) -> Optional[dict]:
        """Convert Firestore document (delegates to helpers)."""
        return FirestoreHelpers.convert_firestore_document(firestore_doc)
    
    def _convert_firestore_value(self, value: dict) -> any:
        """Convert Firestore value (delegates to helpers)."""
        return FirestoreHelpers.convert_firestore_value(value)
    
    def _convert_to_firestore_value(self, value: any) -> dict:
        """Convert to Firestore value (delegates to helpers)."""
        return FirestoreHelpers.convert_to_firestore_value(value)
    
    # ==================== Admin-Only Methods (Not Available in Desktop App) ====================
    # These methods require Admin SDK and should only be used in deployment scripts
    
    def set_user_license(self, uid: str, license_data: dict) -> bool:
        """Set user license - not available in desktop app."""
        logger.warning("set_user_license() is not available in desktop app - use admin tools")
        return False
    
    def add_device_to_license(self, uid: str, device_id: str) -> bool:
        """Add device to license - not available in desktop app."""
        logger.warning("add_device_to_license() is not available in desktop app")
        return False
    
    def remove_device_from_license(self, uid: str, device_id: str) -> bool:
        """Remove device from license - not available in desktop app."""
        logger.warning("remove_device_from_license() is not available in desktop app")
        return False
    
    def create_user(self, email: str, password: str, display_name: Optional[str] = None) -> Optional[str]:
        """Create user - not available in desktop app."""
        logger.warning("create_user() is not available in desktop app - use admin tools")
        return None
    
    def delete_user(self, uid: str) -> bool:
        """Delete user - not available in desktop app."""
        logger.warning("delete_user() is not available in desktop app - use admin tools")
        return False
    
    def set_custom_claims(self, uid: str, claims: dict) -> bool:
        """Set custom claims - not available in desktop app."""
        logger.warning("set_custom_claims() is not available in desktop app - use admin tools")
        return False
    
    def set_app_update_info(self, update_data: dict) -> bool:
        """Set app update info - not available in desktop app."""
        logger.warning("set_app_update_info() is not available in desktop app - use deployment scripts")
        return False


# Global Firebase config instance
firebase_config = FirebaseConfig()
