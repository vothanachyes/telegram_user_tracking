"""
Global fetch state manager for persistent fetch state across page navigations.
"""

import threading
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class FetchStateManager:
    """
    Singleton service to manage fetch state globally.
    Persists fetch progress across page navigations.
    """
    
    _instance: Optional['FetchStateManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize fetch state manager."""
        if self._initialized:
            return
        
        self._lock = threading.Lock()
        self._state: Dict[str, Any] = {
            'is_fetching': False,
            'processed_count': 0,
            'error_count': 0,
            'skipped_count': 0,
            'estimated_total': 0,
            'group_id': None,
            'group_name': None,
            'start_time': None,
            'last_update_time': None
        }
        self._initialized = True
        logger.debug("FetchStateManager initialized")
    
    def start_fetch(self, group_id: Optional[int] = None, group_name: Optional[str] = None):
        """
        Start a new fetch operation.
        
        Args:
            group_id: Optional group ID being fetched
            group_name: Optional group name being fetched
        """
        with self._lock:
            self._state['is_fetching'] = True
            self._state['processed_count'] = 0
            self._state['error_count'] = 0
            self._state['skipped_count'] = 0
            self._state['estimated_total'] = 0
            self._state['group_id'] = group_id
            self._state['group_name'] = group_name
            self._state['start_time'] = datetime.now()
            self._state['last_update_time'] = datetime.now()
            logger.info(f"Fetch started for group: {group_name} ({group_id})")
    
    def update_progress(
        self,
        processed_count: Optional[int] = None,
        error_count: Optional[int] = None,
        skipped_count: Optional[int] = None,
        estimated_total: Optional[int] = None
    ):
        """
        Update fetch progress.
        
        Args:
            processed_count: Number of messages processed
            error_count: Number of errors encountered
            skipped_count: Number of messages skipped
            estimated_total: Estimated total messages
        """
        with self._lock:
            if processed_count is not None:
                self._state['processed_count'] = processed_count
            if error_count is not None:
                self._state['error_count'] = error_count
            if skipped_count is not None:
                self._state['skipped_count'] = skipped_count
            if estimated_total is not None:
                self._state['estimated_total'] = estimated_total
            self._state['last_update_time'] = datetime.now()
    
    def increment_processed(self, count: int = 1):
        """Increment processed count."""
        with self._lock:
            self._state['processed_count'] += count
            self._state['last_update_time'] = datetime.now()
    
    def increment_error(self, count: int = 1):
        """Increment error count."""
        with self._lock:
            self._state['error_count'] += count
            self._state['last_update_time'] = datetime.now()
    
    def increment_skipped(self, count: int = 1):
        """Increment skipped count."""
        with self._lock:
            self._state['skipped_count'] += count
            self._state['last_update_time'] = datetime.now()
    
    def stop_fetch(self):
        """Stop the current fetch operation."""
        with self._lock:
            self._state['is_fetching'] = False
            logger.info("Fetch stopped")
    
    def reset(self):
        """Reset all fetch state to initial values."""
        with self._lock:
            self._state['is_fetching'] = False
            self._state['processed_count'] = 0
            self._state['error_count'] = 0
            self._state['skipped_count'] = 0
            self._state['estimated_total'] = 0
            self._state['group_id'] = None
            self._state['group_name'] = None
            self._state['start_time'] = None
            self._state['last_update_time'] = None
            logger.debug("Fetch state reset")
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get current fetch state (thread-safe copy).
        
        Returns:
            Dictionary containing current fetch state
        """
        with self._lock:
            return self._state.copy()
    
    @property
    def is_fetching(self) -> bool:
        """Check if fetch is in progress."""
        with self._lock:
            return self._state['is_fetching']
    
    @property
    def processed_count(self) -> int:
        """Get processed message count."""
        with self._lock:
            return self._state['processed_count']
    
    @property
    def error_count(self) -> int:
        """Get error count."""
        with self._lock:
            return self._state['error_count']
    
    @property
    def skipped_count(self) -> int:
        """Get skipped count."""
        with self._lock:
            return self._state['skipped_count']
    
    @property
    def estimated_total(self) -> int:
        """Get estimated total."""
        with self._lock:
            return self._state['estimated_total']
    
    @property
    def group_id(self) -> Optional[int]:
        """Get current group ID."""
        with self._lock:
            return self._state['group_id']
    
    @property
    def group_name(self) -> Optional[str]:
        """Get current group name."""
        with self._lock:
            return self._state['group_name']


# Global singleton instance
fetch_state_manager = FetchStateManager()

