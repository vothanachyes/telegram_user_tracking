"""
Account activity manager for tracking add/delete operations.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from database.managers.base import BaseDatabaseManager, _parse_datetime
import logging

logger = logging.getLogger(__name__)


class AccountActivityManager(BaseDatabaseManager):
    """Manages account activity tracking operations."""
    
    def log_account_action(
        self,
        user_email: str,
        action: str,
        phone_number: Optional[str] = None
    ) -> Optional[int]:
        """
        Log an account action (add or delete).
        
        Args:
            user_email: Email of the user performing the action
            action: 'add' or 'delete'
            phone_number: Phone number of the account (optional)
            
        Returns:
            ID of the logged action or None if failed
        """
        # Handle edge case: user not logged in
        if not user_email:
            logger.warning("Cannot log account action: user email not provided")
            return None
        
        if action not in ('add', 'delete'):
            logger.error(f"Invalid action: {action}. Must be 'add' or 'delete'")
            return None
        
        try:
            encryption_service = self.get_encryption_service()
            
            # Encrypt sensitive fields
            encrypted_phone = encryption_service.encrypt_field(phone_number) if encryption_service else phone_number
            
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO account_activity_log 
                    (user_email, action, phone_number, action_timestamp)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_email, action, encrypted_phone))
                conn.commit()
                logger.info(f"Logged account action: {action} for user {user_email}")
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error logging account action: {e}")
            return None
    
    def get_recent_activity_count(
        self,
        user_email: str,
        hours: int = 48
    ) -> int:
        """
        Get count of account actions in the last N hours.
        
        Args:
            user_email: Email of the user
            hours: Number of hours to look back (default: 48)
            
        Returns:
            Count of actions in the time window
        """
        try:
            with self.get_connection() as conn:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                # SQLite timestamp comparison - use ISO format string
                cutoff_str = cutoff_time.strftime("%Y-%m-%d %H:%M:%S")
                cursor = conn.execute("""
                    SELECT COUNT(*) 
                    FROM account_activity_log
                    WHERE user_email = ? 
                    AND datetime(action_timestamp) >= datetime(?)
                """, (user_email, cutoff_str))
                count = cursor.fetchone()[0]
                return count
        except Exception as e:
            logger.error(f"Error getting recent activity count: {e}")
            return 0
    
    def can_perform_account_action(self, user_email: str, max_actions: int = 2) -> bool:
        """
        Check if user can perform account action (add/delete).
        
        Args:
            user_email: Email of the user
            max_actions: Maximum number of actions allowed (default: 2, can be from license)
            
        Returns:
            True if user can perform action, False otherwise
        """
        count = self.get_recent_activity_count(user_email, hours=48)
        can_perform = count < max_actions
        logger.debug(f"User {user_email} can perform action: {can_perform} (count: {count}/{max_actions})")
        return can_perform
    
    def get_earliest_activity_timestamp(self, user_email: str, hours: int = 48) -> Optional[datetime]:
        """
        Get the earliest activity timestamp in the last N hours.
        Used to calculate waiting time until next action is allowed.
        
        Args:
            user_email: Email of the user
            hours: Number of hours to look back (default: 48)
            
        Returns:
            Datetime of earliest activity in window, or None if no activities
        """
        try:
            with self.get_connection() as conn:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                cutoff_str = cutoff_time.strftime("%Y-%m-%d %H:%M:%S")
                cursor = conn.execute("""
                    SELECT MIN(datetime(action_timestamp)) as earliest_timestamp
                    FROM account_activity_log
                    WHERE user_email = ? 
                    AND datetime(action_timestamp) >= datetime(?)
                """, (user_email, cutoff_str))
                result = cursor.fetchone()
                if result and result['earliest_timestamp']:
                    return _parse_datetime(result['earliest_timestamp'])
                return None
        except Exception as e:
            logger.error(f"Error getting earliest activity timestamp: {e}")
            return None
    
    def get_waiting_time_hours(self, user_email: str, max_actions: int = 2, hours: int = 48) -> Optional[float]:
        """
        Calculate waiting time in hours until next action is allowed.
        
        Args:
            user_email: Email of the user
            max_actions: Maximum number of actions allowed
            hours: Time window in hours (default: 48)
            
        Returns:
            Hours remaining until earliest action expires from window, or None if action is allowed
        """
        count = self.get_recent_activity_count(user_email, hours=hours)
        if count < max_actions:
            return None  # Action is allowed, no waiting time
        
        earliest = self.get_earliest_activity_timestamp(user_email, hours=hours)
        if not earliest:
            return None  # No activities found, should be allowed
        
        # Calculate when the earliest activity will be outside the window
        window_end = earliest + timedelta(hours=hours)
        now = datetime.now()
        
        if window_end > now:
            # Calculate hours remaining
            delta = window_end - now
            return delta.total_seconds() / 3600.0
        else:
            # Window has already passed, should be allowed
            return None
    
    def get_activity_log(
        self,
        user_email: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent activity log for a user.
        
        Args:
            user_email: Email of the user
            limit: Maximum number of records to return
            
        Returns:
            List of activity records with keys: id, user_email, action, phone_number, action_timestamp
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, user_email, action, phone_number, action_timestamp
                    FROM account_activity_log
                    WHERE user_email = ?
                    ORDER BY action_timestamp DESC, id DESC
                    LIMIT ?
                """, (user_email, limit))
                
                encryption_service = self.get_encryption_service()
                
                results = []
                for row in cursor.fetchall():
                    # Decrypt sensitive fields
                    phone_number = encryption_service.decrypt_field(row['phone_number']) if encryption_service else row['phone_number']
                    
                    results.append({
                        'id': row['id'],
                        'user_email': row['user_email'],
                        'action': row['action'],
                        'phone_number': phone_number,
                        'action_timestamp': _parse_datetime(row['action_timestamp'])
                    })
                return results
        except Exception as e:
            logger.error(f"Error getting activity log: {e}")
            return []

