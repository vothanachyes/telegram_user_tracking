"""
Collection-specific listeners for Firestore real-time updates.
Provides high-level listeners for common collections.
"""

import logging
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

from services.firestore.grpc_watch_service import FirestoreGRPCWatchService, grpc_watch_service
from services.firestore.watch_service import FirestoreWatchService, firestore_watch_service  # Keep for fallback

# Import configuration flag
try:
    from config.settings import ENABLE_REALTIME_WATCH_SERVICES
except ImportError:
    # Fallback if settings not available
    ENABLE_REALTIME_WATCH_SERVICES = False
from services.firestore.events import (
    firestore_event_bus,
    DocumentAddedEvent,
    DocumentUpdatedEvent,
    DocumentDeletedEvent
)
from utils.constants import (
    FIRESTORE_NOTIFICATIONS_COLLECTION,
    FIREBASE_APP_UPDATES_COLLECTION,
    FIREBASE_APP_UPDATES_DOCUMENT
)

logger = logging.getLogger(__name__)


@dataclass
class NotificationCallbacks:
    """Callbacks for notification events."""
    on_added: Optional[Callable[[dict], None]] = None
    on_updated: Optional[Callable[[dict], None]] = None
    on_deleted: Optional[Callable[[str], None]] = None


@dataclass
class UserProfileCallbacks:
    """Callbacks for user profile events."""
    on_updated: Optional[Callable[[dict], None]] = None


@dataclass
class LicenseCallbacks:
    """Callbacks for license events."""
    on_updated: Optional[Callable[[dict], None]] = None


@dataclass
class AppUpdateCallbacks:
    """Callbacks for app update events."""
    on_updated: Optional[Callable[[dict], None]] = None


class NotificationListener:
    """Listener for notifications collection."""
    
    def __init__(self, watch_service: Optional[FirestoreWatchService] = None):
        """
        Initialize notification listener.
        
        Args:
            watch_service: Optional watch service instance (uses global gRPC service if not provided, falls back to REST)
        """
        if watch_service:
            self.watch_service = watch_service
        else:
            # Check if watch services are enabled via configuration
            if not ENABLE_REALTIME_WATCH_SERVICES:
                # Watch services disabled - set to None (will use polling fallback)
                self.watch_service = None
                logger.debug("Real-time watch services disabled - will use polling fallback")
            else:
                # Try gRPC service first, fall back to REST API if not available
                if grpc_watch_service.is_available():
                    self.watch_service = grpc_watch_service
                else:
                    logger.warning("gRPC watch service not available, falling back to REST API")
                    self.watch_service = firestore_watch_service
        self.listener_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.callbacks: Optional[NotificationCallbacks] = None
    
    async def start(self, user_id: str, callbacks: NotificationCallbacks) -> bool:
        """
        Start listening for notification changes.
        
        Args:
            user_id: User ID to filter notifications
            callbacks: Callback functions for events
            
        Returns:
            True if started successfully, False otherwise
        """
        if self.listener_id:
            logger.warning("Notification listener already started")
            return False
        
        self.user_id = user_id
        self.callbacks = callbacks
        
        # Build filters for user-specific notifications
        # We want both broadcast (target_users is null) and user-specific notifications
        # Note: Firestore watch doesn't support OR queries easily, so we'll watch all
        # and filter in the callback
        
        def on_added(doc: dict):
            """Handle notification added."""
            # Filter by user_id in callback
            target_users = doc.get("target_users")
            if target_users is None or (isinstance(target_users, list) and user_id in target_users):
                # This notification is relevant to the user
                if callbacks.on_added:
                    try:
                        callbacks.on_added(doc)
                    except Exception as e:
                        logger.error(f"Error in notification on_added callback: {e}")
                
                # Publish event
                event = DocumentAddedEvent(
                    collection_path=FIRESTORE_NOTIFICATIONS_COLLECTION,
                    document_id=doc.get("document_id", ""),
                    document_data=doc
                )
                firestore_event_bus.publish(event)
        
        def on_updated(doc: dict):
            """Handle notification updated."""
            target_users = doc.get("target_users")
            if target_users is None or (isinstance(target_users, list) and user_id in target_users):
                if callbacks.on_updated:
                    try:
                        callbacks.on_updated(doc)
                    except Exception as e:
                        logger.error(f"Error in notification on_updated callback: {e}")
                
                # Publish event
                event = DocumentUpdatedEvent(
                    collection_path=FIRESTORE_NOTIFICATIONS_COLLECTION,
                    document_id=doc.get("document_id", ""),
                    document_data=doc
                )
                firestore_event_bus.publish(event)
        
        def on_deleted(doc_id: str):
            """Handle notification deleted."""
            if callbacks.on_deleted:
                try:
                    callbacks.on_deleted(doc_id)
                except Exception as e:
                    logger.error(f"Error in notification on_deleted callback: {e}")
            
            # Publish event
            event = DocumentDeletedEvent(
                collection_path=FIRESTORE_NOTIFICATIONS_COLLECTION,
                document_id=doc_id,
                document_data={}
            )
            firestore_event_bus.publish(event)
        
        # Check if watch service is available
        if not self.watch_service:
            logger.debug("Watch service not available - will use polling fallback")
            return False
        
        # Start watch stream
        self.listener_id = await self.watch_service.watch_collection(
            collection_path=FIRESTORE_NOTIFICATIONS_COLLECTION,
            on_added=on_added,
            on_updated=on_updated,
            on_deleted=on_deleted
        )
        
        if self.listener_id:
            logger.info(f"Notification listener started for user {user_id}")
            return True
        else:
            logger.debug("Failed to start notification listener - will use polling fallback")
            return False
    
    def stop(self) -> bool:
        """
        Stop the notification listener.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.listener_id or not self.watch_service:
            return False
        
        success = self.watch_service.stop_listener(self.listener_id)
        if success:
            self.listener_id = None
            self.user_id = None
            self.callbacks = None
            logger.info("Notification listener stopped")
        
        return success
    
    def is_active(self) -> bool:
        """Check if listener is active."""
        if not self.listener_id or not self.watch_service:
            return False
        return self.watch_service.is_listener_active(self.listener_id)


class UserProfileListener:
    """Listener for user_profile collection."""
    
    def __init__(self, watch_service: Optional[FirestoreWatchService] = None):
        """
        Initialize user profile listener.
        
        Args:
            watch_service: Optional watch service instance (uses global gRPC service if not provided, falls back to REST)
        """
        if watch_service:
            self.watch_service = watch_service
        else:
            # Check if watch services are enabled via configuration
            if not ENABLE_REALTIME_WATCH_SERVICES:
                # Watch services disabled - set to None (will use polling fallback)
                self.watch_service = None
                logger.debug("Real-time watch services disabled - will use polling fallback")
            else:
                # Try gRPC service first, fall back to REST API if not available
                if grpc_watch_service.is_available():
                    self.watch_service = grpc_watch_service
                else:
                    logger.warning("gRPC watch service not available, falling back to REST API")
                    self.watch_service = firestore_watch_service
        self.listener_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.callbacks: Optional[UserProfileCallbacks] = None
    
    async def start(self, user_id: str, callbacks: UserProfileCallbacks) -> bool:
        """
        Start listening for user profile changes.
        
        Args:
            user_id: User ID to watch
            callbacks: Callback functions for events
            
        Returns:
            True if started successfully, False otherwise
        """
        if self.listener_id:
            logger.warning("User profile listener already started")
            return False
        
        self.user_id = user_id
        self.callbacks = callbacks
        
        def on_updated(doc: dict):
            """Handle profile updated."""
            if callbacks.on_updated:
                try:
                    callbacks.on_updated(doc)
                except Exception as e:
                    logger.error(f"Error in user profile on_updated callback: {e}")
            
            # Publish event
            event = DocumentUpdatedEvent(
                collection_path="user_profile",
                document_id=doc.get("document_id", ""),
                document_data=doc
            )
            firestore_event_bus.publish(event)
        
        # Watch specific document
        document_path = f"user_profile/{user_id}"
        self.listener_id = await self.watch_service.watch_document(
            document_path=document_path,
            on_updated=on_updated
        )
        
        if self.listener_id:
            logger.info(f"User profile listener started for user {user_id}")
            return True
        else:
            logger.error("Failed to start user profile listener")
            return False
    
    def stop(self) -> bool:
        """Stop the user profile listener."""
        if not self.listener_id or not self.watch_service:
            return False
        
        success = self.watch_service.stop_listener(self.listener_id)
        if success:
            self.listener_id = None
            self.user_id = None
            self.callbacks = None
            logger.info("User profile listener stopped")
        
        return success
    
    def is_active(self) -> bool:
        """Check if listener is active."""
        if not self.listener_id or not self.watch_service:
            return False
        return self.watch_service.is_listener_active(self.listener_id)


class LicenseListener:
    """Listener for user_licenses collection."""
    
    def __init__(self, watch_service: Optional[FirestoreWatchService] = None):
        """
        Initialize license listener.
        
        Args:
            watch_service: Optional watch service instance (uses global gRPC service if not provided, falls back to REST)
        """
        if watch_service:
            self.watch_service = watch_service
        else:
            # Check if watch services are enabled via configuration
            if not ENABLE_REALTIME_WATCH_SERVICES:
                # Watch services disabled - set to None (will use polling fallback)
                self.watch_service = None
                logger.debug("Real-time watch services disabled - will use polling fallback")
            else:
                # Try gRPC service first, fall back to REST API if not available
                if grpc_watch_service.is_available():
                    self.watch_service = grpc_watch_service
                else:
                    logger.warning("gRPC watch service not available, falling back to REST API")
                    self.watch_service = firestore_watch_service
        self.listener_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.callbacks: Optional[LicenseCallbacks] = None
    
    async def start(self, user_id: str, callbacks: LicenseCallbacks) -> bool:
        """
        Start listening for license changes.
        
        Args:
            user_id: User ID to watch
            callbacks: Callback functions for events
            
        Returns:
            True if started successfully, False otherwise
        """
        if self.listener_id:
            logger.warning("License listener already started")
            return False
        
        self.user_id = user_id
        self.callbacks = callbacks
        
        def on_updated(doc: dict):
            """Handle license updated."""
            if callbacks.on_updated:
                try:
                    callbacks.on_updated(doc)
                except Exception as e:
                    logger.error(f"Error in license on_updated callback: {e}")
            
            # Publish event
            event = DocumentUpdatedEvent(
                collection_path="user_licenses",
                document_id=doc.get("document_id", ""),
                document_data=doc
            )
            firestore_event_bus.publish(event)
        
        # Check if watch service is available
        if not self.watch_service:
            logger.debug("Watch service not available - will use polling fallback")
            return False
        
        # Watch specific document
        document_path = f"user_licenses/{user_id}"
        self.listener_id = await self.watch_service.watch_document(
            document_path=document_path,
            on_updated=on_updated
        )
        
        if self.listener_id:
            logger.info(f"License listener started for user {user_id}")
            return True
        else:
            logger.debug("Failed to start license listener - will use polling fallback")
            return False
    
    def stop(self) -> bool:
        """Stop the license listener."""
        if not self.listener_id or not self.watch_service:
            return False
        
        success = self.watch_service.stop_listener(self.listener_id)
        if success:
            self.listener_id = None
            self.user_id = None
            self.callbacks = None
            logger.info("License listener stopped")
        
        return success
    
    def is_active(self) -> bool:
        """Check if listener is active."""
        if not self.listener_id or not self.watch_service:
            return False
        return self.watch_service.is_listener_active(self.listener_id)


class AppUpdateListener:
    """Listener for app_updates collection."""
    
    def __init__(self, watch_service: Optional[FirestoreWatchService] = None):
        """
        Initialize app update listener.
        
        Args:
            watch_service: Optional watch service instance (uses global gRPC service if not provided, falls back to REST)
        """
        if watch_service:
            self.watch_service = watch_service
        else:
            # Check if watch services are enabled via configuration
            if not ENABLE_REALTIME_WATCH_SERVICES:
                # Watch services disabled - set to None (will use polling fallback)
                self.watch_service = None
                logger.debug("Real-time watch services disabled - will use polling fallback")
            else:
                # Try gRPC service first, fall back to REST API if not available
                if grpc_watch_service.is_available():
                    self.watch_service = grpc_watch_service
                else:
                    logger.warning("gRPC watch service not available, falling back to REST API")
                    self.watch_service = firestore_watch_service
        self.listener_id: Optional[str] = None
        self.callbacks: Optional[AppUpdateCallbacks] = None
    
    async def start(self, callbacks: AppUpdateCallbacks) -> bool:
        """
        Start listening for app update changes.
        
        Args:
            callbacks: Callback functions for events
            
        Returns:
            True if started successfully, False otherwise
        """
        if self.listener_id:
            logger.warning("App update listener already started")
            return False
        
        self.callbacks = callbacks
        
        def on_updated(doc: dict):
            """Handle app update updated."""
            if callbacks.on_updated:
                try:
                    callbacks.on_updated(doc)
                except Exception as e:
                    logger.error(f"Error in app update on_updated callback: {e}")
            
            # Publish event
            event = DocumentUpdatedEvent(
                collection_path=FIREBASE_APP_UPDATES_COLLECTION,
                document_id=doc.get("document_id", ""),
                document_data=doc
            )
            firestore_event_bus.publish(event)
        
        # Check if watch service is available
        if not self.watch_service:
            logger.debug("Watch service not available - will use polling fallback")
            return False
        
        # Watch specific document
        document_path = f"{FIREBASE_APP_UPDATES_COLLECTION}/{FIREBASE_APP_UPDATES_DOCUMENT}"
        self.listener_id = await self.watch_service.watch_document(
            document_path=document_path,
            on_updated=on_updated
        )
        
        if self.listener_id:
            logger.info("App update listener started")
            return True
        else:
            logger.debug("Failed to start app update listener - will use polling fallback")
            return False
    
    def stop(self) -> bool:
        """Stop the app update listener."""
        if not self.listener_id or not self.watch_service:
            return False
        
        success = self.watch_service.stop_listener(self.listener_id)
        if success:
            self.listener_id = None
            self.callbacks = None
            logger.info("App update listener stopped")
        
        return success
    
    def is_active(self) -> bool:
        """Check if listener is active."""
        if not self.listener_id or not self.watch_service:
            return False
        return self.watch_service.is_listener_active(self.listener_id)

