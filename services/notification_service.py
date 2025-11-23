"""
Notification service for user app.
"""

import logging
import asyncio
from typing import List, Dict, Tuple, Optional, Callable
from config.firebase_config import firebase_config
from services.auth_service import auth_service
from services.firestore.collection_listeners import (
    NotificationListener,
    NotificationCallbacks
)
from services.firestore.events import (
    firestore_event_bus,
    DocumentAddedEvent,
    DocumentUpdatedEvent,
    DocumentDeletedEvent
)

# Import configuration flag
try:
    from config.settings import ENABLE_REALTIME_WATCH_SERVICES
except ImportError:
    # Fallback if settings not available
    ENABLE_REALTIME_WATCH_SERVICES = False

logger = logging.getLogger(__name__)


class NotificationService:
    """Handles notification operations for users."""
    
    def __init__(self):
        self._read_statuses_cache: Dict[str, bool] = {}
        self._notifications_cache: Optional[Tuple[List[dict], List[dict]]] = None
        self._cache_timestamp: Optional[float] = None
        self._cache_ttl: float = 60.0  # Cache for 60 seconds
        self._realtime_listener: Optional[NotificationListener] = None
        self._realtime_callbacks: Optional[Callable[[int], None]] = None
    
    def get_notifications(self, user_id: str, force_refresh: bool = False) -> Tuple[List[dict], List[dict]]:
        """
        Get notifications for a user.
        
        Args:
            user_id: User ID
            force_refresh: Force refresh from Firebase (ignore cache)
        
        Returns:
            Tuple of (all_notifications, user_specific_notifications)
            - all_notifications: Broadcast notifications (target_users == null)
            - user_specific_notifications: Notifications targeted to this user
        """
        import time
        
        # Return cached data if still valid
        if not force_refresh and self._notifications_cache and self._cache_timestamp:
            if time.time() - self._cache_timestamp < self._cache_ttl:
                logger.debug("Returning cached notifications")
                return self._notifications_cache
        
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
            
            # Update cache
            result = (all_notifications_list, user_specific_notifications)
            self._notifications_cache = result
            self._cache_timestamp = time.time()
            
            logger.debug(f"Retrieved {len(all_notifications_list)} broadcast and {len(user_specific_notifications)} user-specific notifications")
            return result
            
        except Exception as e:
            logger.error(f"Error getting notifications: {e}", exc_info=True)
            # Return cached data on error if available
            if self._notifications_cache:
                logger.warning("Error fetching notifications, using cache")
                return self._notifications_cache
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
        self._notifications_cache = None
        self._cache_timestamp = None
    
    async def start_realtime_listener(
        self,
        user_id: str,
        on_unread_count_changed: Optional[Callable[[int], None]] = None
    ) -> bool:
        """
        Start real-time listener for notifications.
        
        Args:
            user_id: User ID to listen for
            on_unread_count_changed: Optional callback when unread count changes
            
        Returns:
            True if started successfully, False otherwise
        """
        if self._realtime_listener:
            logger.warning("Real-time listener already started")
            return False
        
        self._realtime_callbacks = on_unread_count_changed
        
        def on_notification_added(notification: dict):
            """Handle notification added."""
            notification_id = notification.get("document_id") or notification.get("notification_id")
            if notification_id:
                # Invalidate cache
                self._notifications_cache = None
                self._cache_timestamp = None
                
                # Update unread count if callback provided
                if self._realtime_callbacks:
                    try:
                        unread_count = self.get_unread_count(user_id)
                        self._realtime_callbacks(unread_count)
                    except Exception as e:
                        logger.error(f"Error updating unread count: {e}")
        
        def on_notification_updated(notification: dict):
            """Handle notification updated."""
            notification_id = notification.get("document_id") or notification.get("notification_id")
            if notification_id:
                # Invalidate cache
                self._notifications_cache = None
                self._cache_timestamp = None
                
                # Update unread count if callback provided
                if self._realtime_callbacks:
                    try:
                        unread_count = self.get_unread_count(user_id)
                        self._realtime_callbacks(unread_count)
                    except Exception as e:
                        logger.error(f"Error updating unread count: {e}")
        
        def on_notification_deleted(notification_id: str):
            """Handle notification deleted."""
            if notification_id:
                # Invalidate cache
                self._notifications_cache = None
                self._cache_timestamp = None
                
                # Update unread count if callback provided
                if self._realtime_callbacks:
                    try:
                        unread_count = self.get_unread_count(user_id)
                        self._realtime_callbacks(unread_count)
                    except Exception as e:
                        logger.error(f"Error updating unread count: {e}")
        
        callbacks = NotificationCallbacks(
            on_added=on_notification_added,
            on_updated=on_notification_updated,
            on_deleted=on_notification_deleted
        )
        
        self._realtime_listener = NotificationListener()
        success = await self._realtime_listener.start(user_id, callbacks)
        
        if success:
            logger.info(f"Real-time notification listener started for user {user_id}")
        else:
            # Only log as error if watch services are enabled (unexpected failure)
            # If disabled, this is expected behavior
            if ENABLE_REALTIME_WATCH_SERVICES:
                logger.error("Failed to start real-time notification listener")
            else:
                logger.debug("Real-time notification listener not started (watch services disabled - using polling)")
            self._realtime_listener = None
        
        return success
    
    def stop_realtime_listener(self) -> bool:
        """
        Stop the real-time listener.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self._realtime_listener:
            return False
        
        success = self._realtime_listener.stop()
        if success:
            self._realtime_listener = None
            self._realtime_callbacks = None
            logger.info("Real-time notification listener stopped")
        
        return success
    
    def is_realtime_active(self) -> bool:
        """Check if real-time listener is active."""
        if not self._realtime_listener:
            return False
        return self._realtime_listener.is_active()


# Global notification service instance
notification_service = NotificationService()

