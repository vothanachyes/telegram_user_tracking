"""
Notification service for user app.
"""

import logging
from typing import List, Dict, Tuple, Optional
from config.firebase_config import firebase_config
from services.auth_service import auth_service

logger = logging.getLogger(__name__)


class NotificationService:
    """Handles notification operations for users."""
    
    def __init__(self):
        self._read_statuses_cache: Dict[str, bool] = {}
    
    def get_notifications(self, user_id: str) -> Tuple[List[dict], List[dict]]:
        """
        Get notifications for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Tuple of (all_notifications, user_specific_notifications)
            - all_notifications: Broadcast notifications (target_users == null)
            - user_specific_notifications: Notifications targeted to this user
        """
        try:
            # Get all notifications (FirebaseConfig uses stored ID token internally)
            all_notifications = firebase_config.get_notifications(user_id=user_id, id_token=None)
            
            # Separate into "All" (broadcast) and "Own" (user-specific)
            all_notifications_list = []
            user_specific_notifications = []
            
            for notification in all_notifications:
                target_users = notification.get("target_users")
                if target_users is None:
                    # Broadcast notification
                    all_notifications_list.append(notification)
                else:
                    # User-specific notification
                    user_specific_notifications.append(notification)
            
            logger.debug(f"Retrieved {len(all_notifications_list)} broadcast and {len(user_specific_notifications)} user-specific notifications")
            return all_notifications_list, user_specific_notifications
            
        except Exception as e:
            logger.error(f"Error getting notifications: {e}", exc_info=True)
            return [], []
    
    def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Count of unread notifications
        """
        try:
            # Get all notifications
            all_notifications, user_specific_notifications = self.get_notifications(user_id)
            all_relevant = all_notifications + user_specific_notifications
            
            # Get read statuses
            read_statuses = self.get_read_statuses(user_id)
            
            # Count unread
            unread_count = 0
            for notification in all_relevant:
                notification_id = notification.get("notification_id")
                if notification_id:
                    is_read = read_statuses.get(notification_id, False)
                    if not is_read:
                        unread_count += 1
            
            logger.debug(f"Unread count for user {user_id}: {unread_count}")
            return unread_count
            
        except Exception as e:
            logger.error(f"Error getting unread count: {e}", exc_info=True)
            return 0
    
    def mark_as_read(self, user_id: str, notification_id: str) -> bool:
        """
        Mark notification as read for a user.
        
        Args:
            user_id: User ID
            notification_id: Notification ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Mark as read via FirebaseConfig (uses stored ID token internally)
            success = firebase_config.mark_notification_read(user_id, notification_id, id_token=None)
            
            if success:
                # Update cache
                self._read_statuses_cache[notification_id] = True
                logger.info(f"Notification {notification_id} marked as read for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}", exc_info=True)
            return False
    
    def get_read_statuses(self, user_id: str) -> Dict[str, bool]:
        """
        Get all read statuses for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict mapping notification_id -> is_read (boolean)
        """
        try:
            # Get read statuses via FirebaseConfig (uses stored ID token internally)
            statuses = firebase_config.get_user_notification_statuses(user_id, id_token=None)
            
            # Update cache
            self._read_statuses_cache.update(statuses)
            
            return statuses
            
        except Exception as e:
            logger.error(f"Error getting read statuses: {e}", exc_info=True)
            return {}
    
    def clear_cache(self):
        """Clear the read statuses cache."""
        self._read_statuses_cache.clear()


# Global notification service instance
notification_service = NotificationService()

