"""
Admin user activities management service.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime

from admin.config.admin_config import admin_config

logger = logging.getLogger(__name__)


class AdminUserActivitiesService:
    """Handles user activities CRUD operations."""
    
    def __init__(self):
        self._db = None
    
    def _ensure_initialized(self) -> bool:
        """Ensure Firebase is initialized."""
        if not admin_config.is_initialized():
            if not admin_config.initialize():
                return False
        self._db = admin_config.get_firestore()
        return self._db is not None
    
    def get_user_activities(self, uid: str) -> Optional[dict]:
        """
        Get user activities for a specific user.
        
        Args:
            uid: User ID
        
        Returns:
            User activities document if found, None otherwise
        """
        if not self._ensure_initialized():
            return None
        
        try:
            doc_ref = self._db.collection("user_activities").document(uid)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data["uid"] = uid
                return data
            return None
            
        except Exception as e:
            logger.error(f"Error getting user activities for {uid}: {e}", exc_info=True)
            return None
    
    def get_all_activities(self) -> List[dict]:
        """
        Get all users' activities.
        
        Returns:
            List of user activities documents
        """
        if not self._ensure_initialized():
            return []
        
        try:
            activities = []
            docs = self._db.collection("user_activities").stream()
            
            for doc in docs:
                data = doc.to_dict()
                data["uid"] = doc.id
                activities.append(data)
            
            logger.info(f"Retrieved {len(activities)} user activities")
            return activities
            
        except Exception as e:
            logger.error(f"Error getting all activities: {e}", exc_info=True)
            return []
    
    def block_user(self, uid: str, reason: str) -> bool:
        """
        Block user for excessive account operations.
        
        Args:
            uid: User ID
            reason: Reason for blocking
        
        Returns:
            True if successful, False otherwise
        """
        if not self._ensure_initialized():
            return False
        
        try:
            now = datetime.utcnow().isoformat() + "Z"
            
            doc_ref = self._db.collection("user_activities").document(uid)
            
            # Get existing document or create new
            doc = doc_ref.get()
            if doc.exists:
                doc_ref.update({
                    "is_blocked": True,
                    "blocked_reason": reason,
                    "blocked_at": now,
                    "last_updated": now
                })
            else:
                # Create new document
                doc_ref.set({
                    "total_devices_logged_on": 0,
                    "total_telegram_accounts_authenticated": 0,
                    "total_telegram_groups_added": 0,
                    "current_app_version": "1.0.0",
                    "is_blocked": True,
                    "blocked_reason": reason,
                    "blocked_at": now,
                    "last_updated": now,
                    "created_at": now
                })
            
            logger.info(f"User {uid} blocked: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error blocking user {uid}: {e}", exc_info=True)
            return False
    
    def unblock_user(self, uid: str) -> bool:
        """
        Unblock user.
        
        Args:
            uid: User ID
        
        Returns:
            True if successful, False otherwise
        """
        if not self._ensure_initialized():
            return False
        
        try:
            now = datetime.utcnow().isoformat() + "Z"
            
            doc_ref = self._db.collection("user_activities").document(uid)
            doc = doc_ref.get()
            
            if doc.exists:
                # Remove block fields
                updates = {
                    "is_blocked": False,
                    "last_updated": now
                }
                
                # Use delete field to remove blocked_reason and blocked_at
                from google.cloud.firestore import DELETE_FIELD
                updates["blocked_reason"] = DELETE_FIELD
                updates["blocked_at"] = DELETE_FIELD
                
                doc_ref.update(updates)
                logger.info(f"User {uid} unblocked")
                return True
            else:
                logger.warning(f"No activities document found for user {uid}")
                return False
            
        except Exception as e:
            logger.error(f"Error unblocking user {uid}: {e}", exc_info=True)
            return False
    
    def get_blocked_users(self) -> List[dict]:
        """
        Get all blocked users.
        
        Returns:
            List of blocked user activities
        """
        if not self._ensure_initialized():
            return []
        
        try:
            blocked_users = []
            docs = self._db.collection("user_activities").where("is_blocked", "==", True).stream()
            
            for doc in docs:
                data = doc.to_dict()
                data["uid"] = doc.id
                blocked_users.append(data)
            
            logger.info(f"Retrieved {len(blocked_users)} blocked users")
            return blocked_users
            
        except Exception as e:
            logger.error(f"Error getting blocked users: {e}", exc_info=True)
            return []
    
    def get_activities_stats(self) -> dict:
        """
        Get statistics about user activities.
        
        Returns:
            Dict with statistics
        """
        if not self._ensure_initialized():
            return {
                "total_users": 0,
                "total_devices": 0,
                "total_accounts": 0,
                "total_groups": 0,
                "blocked_users": 0
            }
        
        try:
            all_activities = self.get_all_activities()
            
            total_devices = sum(a.get("total_devices_logged_on", 0) for a in all_activities)
            total_accounts = sum(a.get("total_telegram_accounts_authenticated", 0) for a in all_activities)
            total_groups = sum(a.get("total_telegram_groups_added", 0) for a in all_activities)
            blocked_users = sum(1 for a in all_activities if a.get("is_blocked", False))
            
            return {
                "total_users": len(all_activities),
                "total_devices": total_devices,
                "total_accounts": total_accounts,
                "total_groups": total_groups,
                "blocked_users": blocked_users
            }
            
        except Exception as e:
            logger.error(f"Error getting activities stats: {e}", exc_info=True)
            return {
                "total_users": 0,
                "total_devices": 0,
                "total_accounts": 0,
                "total_groups": 0,
                "blocked_users": 0
            }


# Global admin user activities service instance
admin_user_activities_service = AdminUserActivitiesService()

