"""
Firestore real-time listener system for generic collection watching.
"""

from services.firestore.watch_service import FirestoreWatchService
from services.firestore.grpc_watch_service import FirestoreGRPCWatchService, grpc_watch_service
from services.firestore.events import (
    FirestoreEvent,
    DocumentAddedEvent,
    DocumentUpdatedEvent,
    DocumentDeletedEvent,
    FirestoreEventBus,
    firestore_event_bus
)
from services.firestore.collection_listeners import (
    NotificationListener,
    UserProfileListener,
    LicenseListener,
    AppUpdateListener
)

__all__ = [
    "FirestoreWatchService",
    "FirestoreGRPCWatchService",
    "grpc_watch_service",
    "FirestoreEvent",
    "DocumentAddedEvent",
    "DocumentUpdatedEvent",
    "DocumentDeletedEvent",
    "FirestoreEventBus",
    "firestore_event_bus",
    "NotificationListener",
    "UserProfileListener",
    "LicenseListener",
    "AppUpdateListener",
]

