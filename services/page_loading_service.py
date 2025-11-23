"""
Page loading service for async data loading with state management.
"""

import asyncio
import logging
from typing import Optional, Callable, Any, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class LoadingState(Enum):
    """Loading state enumeration."""
    IDLE = "idle"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


class PageLoadingService:
    """
    Base service for async page data loading.
    Provides loading state management, error handling, and cancellation support.
    """
    
    def __init__(self):
        """Initialize page loading service."""
        self.state = LoadingState.IDLE
        self.error: Optional[str] = None
        self._current_task: Optional[asyncio.Task] = None
        self._cancelled = False
    
    async def load_data(
        self,
        load_func: Callable[[], Any],
        on_success: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        use_cache: bool = True
    ) -> Any:
        """
        Load data asynchronously.
        
        Args:
            load_func: Function to load data (will be run in executor)
            on_success: Optional callback when data loads successfully
            on_error: Optional callback when error occurs
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Loaded data or None if error
        """
        # Cancel any existing task
        if self._current_task and not self._current_task.done():
            self._cancelled = True
            self._current_task.cancel()
            try:
                await self._current_task
            except asyncio.CancelledError:
                pass
        
        self._cancelled = False
        self.state = LoadingState.LOADING
        self.error = None
        
        try:
            # Run load function in executor to avoid blocking
            loop = asyncio.get_event_loop()
            self._current_task = loop.create_task(
                self._execute_load(load_func, loop)
            )
            
            data = await self._current_task
            
            if self._cancelled:
                return None
            
            self.state = LoadingState.LOADED
            self.error = None
            
            if on_success:
                on_success(data)
            
            return data
            
        except asyncio.CancelledError:
            self.state = LoadingState.IDLE
            return None
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error loading data: {error_msg}", exc_info=True)
            self.state = LoadingState.ERROR
            self.error = error_msg
            
            if on_error:
                on_error(error_msg)
            
            return None
    
    async def _execute_load(self, load_func: Callable[[], Any], loop: asyncio.AbstractEventLoop) -> Any:
        """Execute load function in thread pool executor."""
        return await loop.run_in_executor(None, load_func)
    
    def cancel(self):
        """Cancel current loading operation."""
        if self._current_task and not self._current_task.done():
            self._cancelled = True
            self._current_task.cancel()
            self.state = LoadingState.IDLE
    
    def reset(self):
        """Reset loading state."""
        self.cancel()
        self.state = LoadingState.IDLE
        self.error = None
        self._cancelled = False
    
    def is_loading(self) -> bool:
        """Check if currently loading."""
        return self.state == LoadingState.LOADING
    
    def is_loaded(self) -> bool:
        """Check if data is loaded."""
        return self.state == LoadingState.LOADED
    
    def has_error(self) -> bool:
        """Check if there's an error."""
        return self.state == LoadingState.ERROR

