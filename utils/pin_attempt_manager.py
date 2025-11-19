"""
PIN attempt tracking and lockout management.
"""

import logging
from datetime import datetime, timedelta
from typing import Tuple, Optional
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

# Progressive wait times in milliseconds (matching user's specification)
WAIT_TIMES = [
    1 * 60 * 1000,      # 5 attempts → 1 min
    5 * 60 * 1000,      # 10 attempts → 5 min
    10 * 60 * 1000,     # 15 attempts → 10 min
    60 * 60 * 1000,     # 20 attempts → 1h
    2 * 60 * 60 * 1000, # 25 attempts → 2h
    5 * 60 * 60 * 1000, # 30 attempts → 5h
    10 * 60 * 60 * 1000, # 35 attempts → 10h
    24 * 60 * 60 * 1000, # 40 attempts → 24h
    5 * 24 * 60 * 60 * 1000, # 45 attempts → 5 days
]

# Thresholds for when each wait time applies
ATTEMPT_THRESHOLDS = [5, 10, 15, 20, 25, 30, 35, 40, 45]


class PinAttemptManager:
    """Manages PIN attempt tracking and lockout logic."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize PIN attempt manager.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def get_wait_time_ms(self, attempt_count: int) -> int:
        """
        Get wait time in milliseconds based on attempt count.
        
        Args:
            attempt_count: Number of failed attempts
            
        Returns:
            Wait time in milliseconds
        """
        for i, threshold in enumerate(ATTEMPT_THRESHOLDS):
            if attempt_count >= threshold:
                return WAIT_TIMES[i]
        return 0  # No wait time for attempts < 5
    
    def is_locked_out(self) -> Tuple[bool, Optional[datetime], Optional[int]]:
        """
        Check if PIN entry is currently locked out.
        
        Returns:
            Tuple of (is_locked, lockout_until, remaining_seconds)
            - is_locked: True if currently locked out
            - lockout_until: Timestamp when lockout expires (None if not locked)
            - remaining_seconds: Seconds remaining in lockout (None if not locked)
        """
        try:
            settings = self.db_manager.get_settings()
            
            # Check if lockout timestamp exists and is in the future
            if settings.pin_lockout_until:
                now = datetime.now()
                if settings.pin_lockout_until > now:
                    remaining = (settings.pin_lockout_until - now).total_seconds()
                    return True, settings.pin_lockout_until, int(remaining)
                else:
                    # Lockout expired, clear it
                    self._clear_lockout()
                    return False, None, None
            
            return False, None, None
        except Exception as e:
            logger.error(f"Error checking lockout status: {e}")
            return False, None, None
    
    def record_failed_attempt(self) -> Tuple[int, Optional[int]]:
        """
        Record a failed PIN attempt and apply lockout if needed.
        
        Returns:
            Tuple of (attempt_count, wait_time_ms)
            - attempt_count: New total attempt count
            - wait_time_ms: Wait time in milliseconds if locked out, None otherwise
        """
        try:
            settings = self.db_manager.get_settings()
            new_count = settings.pin_attempt_count + 1
            
            # Get wait time for this attempt count
            wait_time_ms = self.get_wait_time_ms(new_count)
            
            # Update attempt count
            settings.pin_attempt_count = new_count
            
            # If wait time is needed, set lockout timestamp
            if wait_time_ms > 0:
                lockout_until = datetime.now() + timedelta(milliseconds=wait_time_ms)
                settings.pin_lockout_until = lockout_until
                logger.info(f"PIN lockout applied: {new_count} attempts, wait {wait_time_ms}ms until {lockout_until}")
            else:
                settings.pin_lockout_until = None
            
            # Save to database
            self.db_manager.update_settings(settings)
            
            return new_count, wait_time_ms if wait_time_ms > 0 else None
        except Exception as e:
            logger.error(f"Error recording failed attempt: {e}")
            return 0, None
    
    def reset_attempts(self):
        """Reset PIN attempt count and clear lockout."""
        try:
            settings = self.db_manager.get_settings()
            settings.pin_attempt_count = 0
            settings.pin_lockout_until = None
            self.db_manager.update_settings(settings)
            logger.info("PIN attempts reset")
        except Exception as e:
            logger.error(f"Error resetting attempts: {e}")
    
    def _clear_lockout(self):
        """Clear expired lockout (internal method)."""
        try:
            settings = self.db_manager.get_settings()
            settings.pin_lockout_until = None
            self.db_manager.update_settings(settings)
        except Exception as e:
            logger.error(f"Error clearing lockout: {e}")
    
    def format_wait_time(self, seconds: int) -> str:
        """
        Format wait time in a human-readable format.
        
        Args:
            seconds: Seconds to wait
            
        Returns:
            Formatted string (e.g., "5 minutes", "2 hours", "3 days")
        """
        if seconds < 60:
            return f"{seconds} second{'s' if seconds != 1 else ''}"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            days = seconds // 86400
            return f"{days} day{'s' if days != 1 else ''}"

