"""
Admin notification management service.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime
from admin.config.admin_config import admin_config
from admin.services.admin_auth_service import admin_auth_service
from admin.utils.constants import (
    FIRESTORE_NOTIFICATIONS_COLLECTION,
    FIRESTORE_USER_NOTIFICATIONS_COLLECTION
)

logger = logging.getLogger(__name__)


class AdminNotificationService:
    """Handles notification CRUD operations."""
    
    def __init__(self):
        self._db = None
    
    def _ensure_initialized(self) -> bool:
        """Ensure Firebase is initialized."""
        if not admin_config.is_initialized():
            if not admin_config.initialize():
                return False
        self._db = admin_config.get_firestore()
        return self._db is not None
    
    def create_notification(self, notification_data: dict) -> bool:
        """Create new notification."""
        if not self._ensure_initialized():
            return False
        
        try:
            # Validate required fields
            if "title" not in notification_data or not notification_data["title"]:
                logger.error("Notification title is required")
                return False
            
            if "content" not in notification_data or not notification_data["content"]:
                logger.error("Notification content is required")
                return False
            
            if "type" not in notification_data:
                logger.error("Notification type is required")
                return False
            
            # Set defaults
            notification_data.setdefault("created_at", datetime.utcnow())
            notification_data.setdefault("created_by", admin_auth_service.get_current_admin_uid())
            
            # Auto-generate notification_id using Firestore document ID
            # Create document reference (Firestore will auto-generate ID)
            doc_ref = self._db.collection(FIRESTORE_NOTIFICATIONS_COLLECTION).document()
            notification_id = doc_ref.id
            
            # Add notification_id to data
            notification_data["notification_id"] = notification_id
            
            # Set document
            doc_ref.set(notification_data)
            
            logger.info(f"Notification created: {notification_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}", exc_info=True)
            return False
    
    def get_all_notifications(self) -> List[dict]:
        """List all notifications from Firestore."""
        if not self._ensure_initialized():
            return []
        
        try:
            notifications = []
            docs = self._db.collection(FIRESTORE_NOTIFICATIONS_COLLECTION).order_by("created_at", direction="DESCENDING").stream()
            
            for doc in docs:
                data = doc.to_dict()
                data["notification_id"] = doc.id
                # Convert Firestore timestamp to ISO string if needed
                if "created_at" in data and hasattr(data["created_at"], "isoformat"):
                    data["created_at"] = data["created_at"].isoformat() + "Z"
                notifications.append(data)
            
            logger.info(f"Retrieved {len(notifications)} notifications")
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting all notifications: {e}", exc_info=True)
            return []
    
    def get_notification(self, notification_id: str) -> Optional[dict]:
        """Get notification by ID."""
        if not self._ensure_initialized():
            return None
        
        try:
            doc_ref = self._db.collection(FIRESTORE_NOTIFICATIONS_COLLECTION).document(notification_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data["notification_id"] = notification_id
                # Convert Firestore timestamp to ISO string if needed
                if "created_at" in data and hasattr(data["created_at"], "isoformat"):
                    data["created_at"] = data["created_at"].isoformat() + "Z"
                return data
            return None
            
        except Exception as e:
            logger.error(f"Error getting notification {notification_id}: {e}", exc_info=True)
            return None
    
    def update_notification(self, notification_id: str, data: dict) -> bool:
        """Update notification."""
        if not self._ensure_initialized():
            return False
        
        try:
            # Don't allow updating notification_id or created_at
            data.pop("notification_id", None)
            data.pop("created_at", None)
            
            doc_ref = self._db.collection(FIRESTORE_NOTIFICATIONS_COLLECTION).document(notification_id)
            doc_ref.update(data)
            
            logger.info(f"Notification updated: {notification_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating notification {notification_id}: {e}", exc_info=True)
            return False
    
    def delete_notification(self, notification_id: str) -> bool:
        """Delete notification."""
        if not self._ensure_initialized():
            return False
        
        try:
            doc_ref = self._db.collection(FIRESTORE_NOTIFICATIONS_COLLECTION).document(notification_id)
            doc_ref.delete()
            
            logger.info(f"Notification deleted: {notification_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting notification {notification_id}: {e}", exc_info=True)
            return False
    
    def get_all_users(self) -> List[dict]:
        """Get all users for selection (reuse from admin_user_service)."""
        try:
            from admin.services.admin_user_service import admin_user_service
            return admin_user_service.get_all_users()
        except Exception as e:
            logger.error(f"Error getting users: {e}", exc_info=True)
            return []


# Global admin notification service instance
admin_notification_service = AdminNotificationService()

