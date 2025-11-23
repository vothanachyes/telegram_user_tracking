"""
Background service for executing scheduled user deletions.
"""

import logging
import threading
import time
from typing import Optional
from admin.services.admin_user_service import admin_user_service

logger = logging.getLogger(__name__)


class ScheduledDeletionService:
    """Background service to periodically check and execute scheduled user deletions."""
    
    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._check_interval = 3600  # Check every hour (3600 seconds)
    
    def start(self):
        """Start the background deletion checker service."""
        if self._running:
            logger.warning("Scheduled deletion service already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Scheduled deletion service started")
    
    def stop(self):
        """Stop the background deletion checker service."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Scheduled deletion service stopped")
    
    def _run_loop(self):
        """Background loop to check and execute scheduled deletions."""
        while self._running:
            try:
                # Execute scheduled deletions
                deleted_count = admin_user_service.execute_scheduled_deletions()
                
                if deleted_count > 0:
                    logger.info(f"Executed {deleted_count} scheduled user deletions")
                
                # Sleep for check interval
                time.sleep(self._check_interval)
            
            except Exception as e:
                logger.error(f"Error in scheduled deletion service loop: {e}", exc_info=True)
                # Wait 5 minutes before retrying on error
                time.sleep(300)
    
    def check_now(self) -> int:
        """
        Manually trigger a check for scheduled deletions.
        Useful for testing or immediate execution.
        
        Returns:
            Number of users deleted
        """
        try:
            return admin_user_service.execute_scheduled_deletions()
        except Exception as e:
            logger.error(f"Error in manual scheduled deletion check: {e}", exc_info=True)
            return 0


# Global scheduled deletion service instance
scheduled_deletion_service = ScheduledDeletionService()

