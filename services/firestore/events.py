"""
Event system for Firestore real-time updates.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Type, Callable, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event type enumeration."""
    DOCUMENT_ADDED = "document_added"
    DOCUMENT_UPDATED = "document_updated"
    DOCUMENT_DELETED = "document_deleted"


@dataclass
class FirestoreEvent:
    """Base event class for Firestore document changes."""
    collection_path: str
    document_id: str
    document_data: dict
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: EventType = EventType.DOCUMENT_ADDED
    
    def __post_init__(self):
        """Ensure timestamp is datetime."""
        if isinstance(self.timestamp, str):
            try:
                from dateutil.parser import parse
                self.timestamp = parse(self.timestamp)
            except ImportError:
                # Fallback to datetime.fromisoformat if dateutil not available
                try:
                    self.timestamp = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
                except Exception:
                    self.timestamp = datetime.utcnow()


@dataclass
class DocumentAddedEvent(FirestoreEvent):
    """Event fired when a document is added to a collection."""
    event_type: EventType = field(default=EventType.DOCUMENT_ADDED, init=False)


@dataclass
class DocumentUpdatedEvent(FirestoreEvent):
    """Event fired when a document is updated in a collection."""
    event_type: EventType = field(default=EventType.DOCUMENT_UPDATED, init=False)
    old_data: Optional[dict] = None


@dataclass
class DocumentDeletedEvent(FirestoreEvent):
    """Event fired when a document is deleted from a collection."""
    event_type: EventType = field(default=EventType.DOCUMENT_DELETED, init=False)
    document_data: dict = field(default_factory=dict)


class FirestoreEventBus:
    """
    Event bus for decoupled communication between Firestore listeners and subscribers.
    Supports multiple subscribers per event type.
    """
    
    def __init__(self):
        """Initialize event bus with empty subscriber registry."""
        self._subscribers: Dict[Type[FirestoreEvent], List[Callable]] = {}
        self._logger = logging.getLogger(__name__)
    
    def subscribe(self, event_type: Type[FirestoreEvent], handler: Callable[[FirestoreEvent], None]) -> None:
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: Event class to subscribe to
            handler: Callback function that receives the event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            self._logger.debug(f"Subscribed handler to {event_type.__name__}")
        else:
            self._logger.warning(f"Handler already subscribed to {event_type.__name__}")
    
    def unsubscribe(self, event_type: Type[FirestoreEvent], handler: Callable[[FirestoreEvent], None]) -> None:
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: Event class to unsubscribe from
            handler: Callback function to remove
        """
        if event_type in self._subscribers:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
                self._logger.debug(f"Unsubscribed handler from {event_type.__name__}")
            else:
                self._logger.warning(f"Handler not found in subscribers for {event_type.__name__}")
    
    def publish(self, event: FirestoreEvent) -> None:
        """
        Publish an event to all subscribed handlers.
        
        Args:
            event: Event instance to publish
        """
        event_type = type(event)
        
        # Get all subscribers for this event type and its base classes
        handlers = []
        for cls in event_type.__mro__:
            if cls in self._subscribers:
                handlers.extend(self._subscribers[cls])
        
        if not handlers:
            self._logger.debug(f"No subscribers for {event_type.__name__}")
            return
        
        self._logger.debug(f"Publishing {event_type.__name__} to {len(handlers)} handler(s)")
        
        # Call all handlers
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                self._logger.error(f"Error in event handler for {event_type.__name__}: {e}", exc_info=True)
    
    def clear(self) -> None:
        """Clear all subscribers."""
        self._subscribers.clear()
        self._logger.debug("Event bus cleared")
    
    def get_subscriber_count(self, event_type: Type[FirestoreEvent]) -> int:
        """
        Get number of subscribers for an event type.
        
        Args:
            event_type: Event class to check
            
        Returns:
            Number of subscribers
        """
        return len(self._subscribers.get(event_type, []))


# Global event bus instance
firestore_event_bus = FirestoreEventBus()

