"""
Base polling service for background periodic data fetching.
Provides a reusable foundation for implementing polling services.
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Callable
from config.settings import (
    ENABLE_NOTIFICATION_POLLING,
    ENABLE_UPDATE_POLLING
)

logger = logging.getLogger(__name__)


class BasePollingService(ABC):
    """
    Abstract base class for background polling services.
    
    Provides common functionality for periodic data fetching:
    - Start/stop control
    - Configurable polling interval
    - Error handling and retry logic
    - Condition checks before polling
    - Pluggable enable/disable via configuration
    """
    
    def __init__(
        self,
        interval_seconds: float,
        enabled: bool = True,
        name: Optional[str] = None
    ):
        """
        Initialize base polling service.
        
        Args:
            interval_seconds: Polling interval in seconds
            enabled: Whether polling is enabled (can be overridden by config)
            name: Optional service name for logging
        """
        self._interval = interval_seconds
        self._enabled = enabled
        self._name = name or self.__class__.__name__
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._condition_check: Optional[Callable[[], bool]] = None
    
    @property
    def interval(self) -> float:
        """Get current polling interval in seconds."""
        return self._interval
    
    @property
    def is_running(self) -> bool:
        """Check if polling service is running."""
        return self._running
    
    @property
    def is_enabled(self) -> bool:
        """Check if polling service is enabled."""
        return self._enabled and self._check_config_enabled()
    
    def set_interval(self, seconds: float) -> None:
        """
        Set polling interval.
        
        Args:
            seconds: New interval in seconds
        """
        if seconds <= 0:
            raise ValueError("Interval must be greater than 0")
        self._interval = seconds
        logger.debug(f"{self._name}: Polling interval set to {seconds} seconds")
    
    def set_condition_check(self, condition: Callable[[], bool]) -> None:
        """
        Set condition check function that must return True before polling.
        
        Args:
            condition: Function that returns True if polling should proceed
        """
        self._condition_check = condition
    
    def enable(self) -> None:
        """Enable polling service."""
        self._enabled = True
        logger.debug(f"{self._name}: Polling enabled")
    
    def disable(self) -> None:
        """Disable polling service."""
        self._enabled = False
        logger.debug(f"{self._name}: Polling disabled")
        # Stop if currently running (fire and forget)
        if self._running:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.stop())
                else:
                    asyncio.run(self.stop())
            except RuntimeError:
                # No event loop, create task in new loop
                asyncio.create_task(self.stop())
    
    def _check_config_enabled(self) -> bool:
        """
        Check if service is enabled via configuration.
        Override in subclasses to check specific config flags.
        
        Returns:
            True if enabled via config, False otherwise
        """
        # Default: check general polling flags
        # Subclasses can override for specific checks
        return True
    
    async def start(self) -> bool:
        """
        Start the polling service.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self._running:
            logger.warning(f"{self._name}: Polling service already running")
            return False
        
        if not self.is_enabled:
            logger.debug(f"{self._name}: Polling service is disabled")
            return False
        
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"{self._name}: Polling service started (interval: {self._interval}s)")
        return True
    
    async def stop(self) -> None:
        """Stop the polling service."""
        if not self._running:
            return
        
        self._running = False
        
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        self._task = None
        logger.info(f"{self._name}: Polling service stopped")
    
    async def _poll_loop(self) -> None:
        """
        Main polling loop.
        Handles interval timing, condition checks, and error handling.
        """
        logger.debug(f"{self._name}: Polling loop started")
        
        while self._running:
            try:
                # Check if still enabled
                if not self.is_enabled:
                    logger.debug(f"{self._name}: Polling disabled, stopping")
                    break
                
                # Check condition before polling
                if self._condition_check and not self._condition_check():
                    logger.debug(f"{self._name}: Condition check failed, skipping poll")
                    await asyncio.sleep(self._interval)
                    continue
                
                # Perform polling
                try:
                    await self._poll()
                except Exception as e:
                    logger.error(f"{self._name}: Error during poll: {e}", exc_info=True)
                    # Continue polling even on error (with interval delay)
                
                # Wait for next interval
                await asyncio.sleep(self._interval)
                
            except asyncio.CancelledError:
                logger.debug(f"{self._name}: Polling loop cancelled")
                break
            except Exception as e:
                logger.error(f"{self._name}: Unexpected error in polling loop: {e}", exc_info=True)
                # Wait before retrying to avoid tight error loop
                await asyncio.sleep(min(self._interval, 60))
        
        self._running = False
        logger.debug(f"{self._name}: Polling loop ended")
    
    @abstractmethod
    async def _poll(self) -> None:
        """
        Perform the actual polling operation.
        Must be implemented by subclasses.
        
        This method is called periodically based on the interval.
        """
        pass

