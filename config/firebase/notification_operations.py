"""
Notification operations for Firestore REST API.
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime
import requests

from config.firebase.core import FirebaseCore, FIRESTORE_REST_URL
from config.firebase.helpers import FirestoreHelpers

logger = logging.getLogger(__name__)


class NotificationOperations:
    """Notification-related Firestore operations."""
    
    def __init__(self, core: FirebaseCore):
        """
        Initialize notification operations.
        
        Args:
            core: FirebaseCore instance
        """
        self.core = core
        self.helpers = FirestoreHelpers()
    
    def get_notifications(self, user_id: Optional[str] = None, id_token: Optional[str] = None) -> List[dict]:
        """
        Get all notifications from Firestore using REST API.
        Filters notifications where target_users is null (all users) or contains user_id.
        
        Args:
            user_id: User ID to filter notifications (optional)
            id_token: Firebase ID token (optional, uses current token)
        
        Returns:
            List of notification documents
        """
        if not self.core.is_initialized() or not self.core.project_id:
            logger.error("Firebase not initialized")
            return []
        
        token = self.core.get_id_token(id_token)
        if not token:
            logger.error("No ID token available")
            return []
        
        try:
            from utils.constants import FIRESTORE_NOTIFICATIONS_COLLECTION
            
            url = f"{FIRESTORE_REST_URL}/projects/{self.core.project_id}/databases/(default)/documents/{FIRESTORE_NOTIFICATIONS_COLLECTION}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                notifications = []
                
                documents = data.get("documents", [])
                for doc in documents:
                    doc_name = doc.get("name", "")
                    doc_id = doc_name.split("/")[-1] if "/" in doc_name else ""
                    
                    notification_data = self.helpers.convert_firestore_document(doc)
                    if notification_data:
                        notification_data["notification_id"] = doc_id
                        
                        # Filter by user_id if provided
                        if user_id:
                            target_users = notification_data.get("target_users")
                            if target_users is None:
                                # Broadcast notification - include it
                                notifications.append(notification_data)
                            elif isinstance(target_users, list) and user_id in target_users:
                                # User-specific notification - include it
                                notifications.append(notification_data)
                        else:
                            # No filter - include all
                            notifications.append(notification_data)
                
                logger.debug(f"Retrieved {len(notifications)} notifications")
                return notifications
            elif response.status_code == 404:
                logger.debug("No notifications found")
                return []
            else:
                logger.error(f"Error getting notifications: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting notifications: {e}", exc_info=True)
            return []
    
    def get_user_notification_status(self, user_id: str, notification_id: str, id_token: Optional[str] = None) -> Optional[dict]:
        """
        Get user notification read status from Firestore using REST API.
        
        Args:
            user_id: User ID
            notification_id: Notification ID
            id_token: Firebase ID token (optional, uses current token)
        
        Returns:
            Read status document if found, None otherwise
        """
        if not self.core.is_initialized() or not self.core.project_id:
            logger.error("Firebase not initialized")
            return None
        
        token = self.core.get_id_token(id_token)
        if not token:
            logger.error("No ID token available")
            return None
        
        try:
            from utils.constants import FIRESTORE_USER_NOTIFICATIONS_COLLECTION
            
            url = f"{FIRESTORE_REST_URL}/projects/{self.core.project_id}/databases/(default)/documents/{FIRESTORE_USER_NOTIFICATIONS_COLLECTION}/{user_id}/notifications/{notification_id}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status_data = self.helpers.convert_firestore_document(data)
                if status_data:
                    logger.debug(f"Read status found for notification {notification_id}")
                    return status_data
            elif response.status_code == 404:
                logger.debug(f"No read status found for notification {notification_id}")
                return None
            else:
                logger.error(f"Error getting read status: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user notification status: {e}", exc_info=True)
            return None
    
    def mark_notification_read(self, user_id: str, notification_id: str, id_token: Optional[str] = None) -> bool:
        """
        Mark notification as read for user using Firestore REST API.
        
        Args:
            user_id: User ID
            notification_id: Notification ID
            id_token: Firebase ID token (optional, uses current token)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.core.is_initialized() or not self.core.project_id:
            logger.error("Firebase not initialized")
            return False
        
        token = self.core.get_id_token(id_token)
        if not token:
            logger.error("No ID token available")
            return False
        
        try:
            from utils.constants import FIRESTORE_USER_NOTIFICATIONS_COLLECTION
            
            url = f"{FIRESTORE_REST_URL}/projects/{self.core.project_id}/databases/(default)/documents/{FIRESTORE_USER_NOTIFICATIONS_COLLECTION}/{user_id}/notifications/{notification_id}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            now = datetime.utcnow().isoformat() + "Z"
            document_data = {
                "fields": {
                    "notification_id": {"stringValue": notification_id},
                    "is_read": {"booleanValue": True},
                    "read_at": {"timestampValue": now}
                }
            }
            
            response = requests.patch(url, headers=headers, json=document_data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Notification {notification_id} marked as read for user {user_id}")
                return True
            else:
                logger.error(f"Error marking notification as read: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}", exc_info=True)
            return False
    
    def get_user_notification_statuses(self, user_id: str, id_token: Optional[str] = None) -> dict:
        """
        Get all read statuses for a user from Firestore using REST API.
        
        Args:
            user_id: User ID
            id_token: Firebase ID token (optional, uses current token)
        
        Returns:
            Dict mapping notification_id -> is_read (boolean)
        """
        if not self.core.is_initialized() or not self.core.project_id:
            logger.error("Firebase not initialized")
            return {}
        
        token = self.core.get_id_token(id_token)
        if not token:
            logger.error("No ID token available")
            return {}
        
        try:
            from utils.constants import FIRESTORE_USER_NOTIFICATIONS_COLLECTION
            
            url = f"{FIRESTORE_REST_URL}/projects/{self.core.project_id}/databases/(default)/documents/{FIRESTORE_USER_NOTIFICATIONS_COLLECTION}/{user_id}/notifications"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                statuses = {}
                
                documents = data.get("documents", [])
                for doc in documents:
                    doc_name = doc.get("name", "")
                    notification_id = doc_name.split("/")[-1] if "/" in doc_name else ""
                    
                    status_data = self.helpers.convert_firestore_document(doc)
                    if status_data:
                        is_read = status_data.get("is_read", False)
                        statuses[notification_id] = is_read
                
                logger.debug(f"Retrieved {len(statuses)} read statuses for user {user_id}")
                return statuses
            elif response.status_code == 404:
                logger.debug(f"No read statuses found for user {user_id}")
                return {}
            else:
                logger.error(f"Error getting read statuses: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting user notification statuses: {e}", exc_info=True)
            return {}

