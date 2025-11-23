"""
Async query executor for non-blocking database operations.
"""

import asyncio
import logging
from typing import Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class AsyncQueryExecutor:
    """
    Executor for running synchronous database queries asynchronously.
    Prevents blocking the UI thread.
    """
    
    _instance: Optional['AsyncQueryExecutor'] = None
    _executor: Optional[ThreadPoolExecutor] = None
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize async query executor."""
        if self._initialized:
            return
        
        # Create thread pool executor for database operations
        # Use max_workers=5 to handle concurrent queries without overwhelming
        self._executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="db_query")
        self._initialized = True
        logger.debug("AsyncQueryExecutor initialized")
    
    async def execute(self, func: Callable[[], Any], *args, **kwargs) -> Any:
        """
        Execute a function asynchronously in thread pool.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Result of function execution
        """
        if not self._executor:
            raise RuntimeError("AsyncQueryExecutor not initialized")
        
        loop = asyncio.get_event_loop()
        
        # Wrap function with arguments
        def wrapped_func():
            return func(*args, **kwargs)
        
        try:
            result = await loop.run_in_executor(self._executor, wrapped_func)
            return result
        except Exception as e:
            logger.error(f"Error executing async query: {e}", exc_info=True)
            raise
    
    async def execute_with_timeout(
        self,
        func: Callable[[], Any],
        timeout: float = 30.0,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function asynchronously with timeout.
        
        Args:
            func: Function to execute
            timeout: Timeout in seconds (default: 30s)
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Result of function execution
            
        Raises:
            asyncio.TimeoutError: If execution exceeds timeout
        """
        try:
            result = await asyncio.wait_for(
                self.execute(func, *args, **kwargs),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.warning(f"Query execution timed out after {timeout}s")
            raise
    
    def shutdown(self, wait: bool = True):
        """
        Shutdown the thread pool executor.
        
        Args:
            wait: Whether to wait for pending tasks
        """
        if self._executor:
            self._executor.shutdown(wait=wait)
            self._executor = None
            logger.debug("AsyncQueryExecutor shut down")


# Global singleton instance
async_query_executor = AsyncQueryExecutor()

