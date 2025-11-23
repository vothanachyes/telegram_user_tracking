"""
User activities tracking service.
Tracks user activities and syncs to Firebase.
"""

import logging
from typing import Optional, Dict
from datetime import datetime

from config.firebase_config import firebase_config
from services.auth_service import auth_service

logger = logging.getLogger(__name__)


class UserActivitiesService:
    """Handles user activity tracking and syncing to Firebase."""
    
    def __init__(self):
        self._local_counts: Dict[str, int] = {
            "devices": 0,
            "accounts": 0,
            "groups": 0
        }
        self._last_sync: Optional[datetime] = None
    
    def get_activities(self, uid: Optional[str] = None) -> Optional[dict]:
        """
        Get current user activities from Firebase.
        
        Args:
            uid: User ID (optional, uses current user if not provided)
        
        Returns:
            Activities dict if found, None otherwise
        """
        if not uid:
            current_user = auth_service.get_current_user()
            if not current_user:
                logger.warning("No user logged in")
                return None
            uid = current_user.get("uid")
            if not uid:
                return None
        
        try:
            activities = firebase_config.get_user_activities(uid)
            if activities:
                return activities
            else:
                # Initialize empty activities document
                return self._initialize_activities(uid)
        except Exception as e:
            logger.error(f"Error getting activities: {e}", exc_info=True)
            return None
    
    def _initialize_activities(self, uid: str) -> dict:
        """
        Initialize user activities document in Firebase.
        
        Args:
            uid: User ID
        
        Returns:
            Initialized activities dict
        """
        from utils.constants import APP_VERSION
        
        initial_data = {
            "total_devices_logged_on": 0,
            "total_telegram_accounts_authenticated": 0,
            "total_telegram_groups_added": 0,
            "current_app_version": APP_VERSION,
            "is_blocked": False,
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        # Create document in Firebase
        firebase_config.update_user_activities(uid, initial_data)
        
        return initial_data
    
    def increment_devices_count(self, uid: Optional[str] = None) -> bool:
        """
        Increment total devices logged on count.
        
        Args:
            uid: User ID (optional, uses current user if not provided)
        
        Returns:
            True if successful, False otherwise
        """
        if not uid:
            current_user = auth_service.get_current_user()
            if not current_user:
                logger.warning("No user logged in")
                return False
            uid = current_user.get("uid")
            if not uid:
                return False
        
        try:
            activities = self.get_activities(uid)
            if not activities:
                activities = self._initialize_activities(uid)
            
            current_count = activities.get("total_devices_logged_on", 0)
            new_count = current_count + 1
            
            updates = {"total_devices_logged_on": new_count}
            success = firebase_config.update_user_activities(uid, updates)
            
            if success:
                logger.info(f"Incremented devices count for user {uid}: {new_count}")
                self._local_counts["devices"] = new_count
            else:
                logger.warning(f"Failed to increment devices count for user {uid}")
            
            return success
        except Exception as e:
            logger.error(f"Error incrementing devices count: {e}", exc_info=True)
            return False
    
    def increment_accounts_count(self, uid: Optional[str] = None) -> bool:
        """
        Increment total telegram accounts authenticated count.
        
        Args:
            uid: User ID (optional, uses current user if not provided)
        
        Returns:
            True if successful, False otherwise
        """
        if not uid:
            current_user = auth_service.get_current_user()
            if not current_user:
                logger.warning("No user logged in")
                return False
            uid = current_user.get("uid")
            if not uid:
                return False
        
        try:
            activities = self.get_activities(uid)
            if not activities:
                activities = self._initialize_activities(uid)
            
            current_count = activities.get("total_telegram_accounts_authenticated", 0)
            new_count = current_count + 1
            
            updates = {"total_telegram_accounts_authenticated": new_count}
            success = firebase_config.update_user_activities(uid, updates)
            
            if success:
                logger.info(f"Incremented accounts count for user {uid}: {new_count}")
                self._local_counts["accounts"] = new_count
            else:
                logger.warning(f"Failed to increment accounts count for user {uid}")
            
            return success
        except Exception as e:
            logger.error(f"Error incrementing accounts count: {e}", exc_info=True)
            return False
    
    def increment_groups_count(self, uid: Optional[str] = None) -> bool:
        """
        Increment total telegram groups added count.
        
        Args:
            uid: User ID (optional, uses current user if not provided)
        
        Returns:
            True if successful, False otherwise
        """
        if not uid:
            current_user = auth_service.get_current_user()
            if not current_user:
                logger.warning("No user logged in")
                return False
            uid = current_user.get("uid")
            if not uid:
                return False
        
        try:
            activities = self.get_activities(uid)
            if not activities:
                activities = self._initialize_activities(uid)
            
            current_count = activities.get("total_telegram_groups_added", 0)
            new_count = current_count + 1
            
            updates = {"total_telegram_groups_added": new_count}
            success = firebase_config.update_user_activities(uid, updates)
            
            if success:
                logger.info(f"Incremented groups count for user {uid}: {new_count}")
                self._local_counts["groups"] = new_count
            else:
                logger.warning(f"Failed to increment groups count for user {uid}")
            
            return success
        except Exception as e:
            logger.error(f"Error incrementing groups count: {e}", exc_info=True)
            return False
    
    def update_app_version(self, uid: Optional[str] = None) -> bool:
        """
        Update current app version in user activities.
        
        Args:
            uid: User ID (optional, uses current user if not provided)
        
        Returns:
            True if successful, False otherwise
        """
        if not uid:
            current_user = auth_service.get_current_user()
            if not current_user:
                logger.warning("No user logged in")
                return False
            uid = current_user.get("uid")
            if not uid:
                return False
        
        try:
            from utils.constants import APP_VERSION
            
            updates = {"current_app_version": APP_VERSION}
            success = firebase_config.update_user_activities(uid, updates)
            
            if success:
                logger.debug(f"Updated app version for user {uid}: {APP_VERSION}")
            else:
                logger.warning(f"Failed to update app version for user {uid}")
            
            return success
        except Exception as e:
            logger.error(f"Error updating app version: {e}", exc_info=True)
            return False
    
    def check_if_blocked(self, uid: Optional[str] = None) -> bool:
        """
        Check if user is blocked for excessive account operations.
        
        Args:
            uid: User ID (optional, uses current user if not provided)
        
        Returns:
            True if blocked, False otherwise
        """
        if not uid:
            current_user = auth_service.get_current_user()
            if not current_user:
                return False
            uid = current_user.get("uid")
            if not uid:
                return False
        
        try:
            activities = self.get_activities(uid)
            if not activities:
                return False
            
            is_blocked = activities.get("is_blocked", False)
            return is_blocked
        except Exception as e:
            logger.error(f"Error checking if blocked: {e}", exc_info=True)
            return False
    
    def sync_activities_to_firebase(self, uid: Optional[str] = None) -> bool:
        """
        Sync local activity counts to Firebase.
        This is called periodically to ensure Firebase is up to date.
        
        Args:
            uid: User ID (optional, uses current user if not provided)
        
        Returns:
            True if successful, False otherwise
        """
        if not uid:
            current_user = auth_service.get_current_user()
            if not current_user:
                return False
            uid = current_user.get("uid")
            if not uid:
                return False
        
        try:
            # Get current activities from Firebase
            activities = self.get_activities(uid)
            if not activities:
                return False
            
            # Update local counts from Firebase
            self._local_counts["devices"] = activities.get("total_devices_logged_on", 0)
            self._local_counts["accounts"] = activities.get("total_telegram_accounts_authenticated", 0)
            self._local_counts["groups"] = activities.get("total_telegram_groups_added", 0)
            
            self._last_sync = datetime.utcnow()
            logger.debug(f"Synced activities to Firebase for user {uid}")
            return True
        except Exception as e:
            logger.error(f"Error syncing activities: {e}", exc_info=True)
            return False


# Global user activities service instance
user_activities_service = UserActivitiesService()

