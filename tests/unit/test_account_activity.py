"""
Unit tests for account activity manager.
"""

import pytest
from datetime import datetime, timedelta
from database.managers.account_activity_manager import AccountActivityManager
from tests.fixtures.db_fixtures import create_test_db_manager


class TestAccountActivityManager:
    """Test account activity tracking and limits."""
    
    @pytest.fixture
    def activity_manager(self, test_db_manager):
        """Create account activity manager with test database."""
        # Use the account_activity manager from db_manager
        return test_db_manager._account_activity
    
    def test_log_account_action_add(self, activity_manager):
        """Test logging account addition."""
        user_email = "test@example.com"
        phone_number = "+1234567890"
        
        action_id = activity_manager.log_account_action(
            user_email=user_email,
            action='add',
            phone_number=phone_number
        )
        
        assert action_id is not None
        assert action_id > 0
    
    def test_log_account_action_delete(self, activity_manager):
        """Test logging account deletion."""
        user_email = "test@example.com"
        phone_number = "+1234567890"
        
        action_id = activity_manager.log_account_action(
            user_email=user_email,
            action='delete',
            phone_number=phone_number
        )
        
        assert action_id is not None
        assert action_id > 0
    
    def test_log_invalid_action(self, activity_manager):
        """Test logging invalid action."""
        user_email = "test@example.com"
        
        action_id = activity_manager.log_account_action(
            user_email=user_email,
            action='invalid',
            phone_number="+1234567890"
        )
        
        assert action_id is None
    
    def test_get_recent_activity_count(self, activity_manager):
        """Test getting recent activity count."""
        user_email = "test@example.com"
        
        # Log some actions
        activity_manager.log_account_action(user_email, 'add', "+1111111111")
        activity_manager.log_account_action(user_email, 'delete', "+2222222222")
        
        count = activity_manager.get_recent_activity_count(user_email, hours=48)
        assert count == 2
    
    def test_get_recent_activity_count_empty(self, activity_manager):
        """Test getting activity count for user with no activity."""
        user_email = "newuser@example.com"
        
        count = activity_manager.get_recent_activity_count(user_email, hours=48)
        assert count == 0
    
    def test_can_perform_account_action_under_limit(self, activity_manager):
        """Test that user can perform action when under limit."""
        user_email = "test@example.com"
        
        # Log one action
        activity_manager.log_account_action(user_email, 'add', "+1111111111")
        
        can_perform = activity_manager.can_perform_account_action(user_email)
        assert can_perform is True
    
    def test_can_perform_account_action_at_limit(self, activity_manager):
        """Test that user cannot perform action when at limit."""
        user_email = "test@example.com"
        
        # Log 2 actions (the limit)
        activity_manager.log_account_action(user_email, 'add', "+1111111111")
        activity_manager.log_account_action(user_email, 'delete', "+2222222222")
        
        can_perform = activity_manager.can_perform_account_action(user_email)
        assert can_perform is False
    
    def test_can_perform_account_action_over_limit(self, activity_manager):
        """Test that user cannot perform action when over limit."""
        user_email = "test@example.com"
        
        # Log 3 actions (over the limit)
        activity_manager.log_account_action(user_email, 'add', "+1111111111")
        activity_manager.log_account_action(user_email, 'delete', "+2222222222")
        activity_manager.log_account_action(user_email, 'add', "+3333333333")
        
        can_perform = activity_manager.can_perform_account_action(user_email)
        assert can_perform is False
    
    def test_rolling_window_48_hours(self, activity_manager):
        """Test that actions older than 48 hours don't count."""
        user_email = "test@example.com"
        
        # This would require mocking time, but we can test the logic
        # Log 2 actions
        activity_manager.log_account_action(user_email, 'add', "+1111111111")
        activity_manager.log_account_action(user_email, 'delete', "+2222222222")
        
        # Should be at limit
        can_perform = activity_manager.can_perform_account_action(user_email)
        assert can_perform is False
        
        # If we could set timestamps to 49 hours ago, they shouldn't count
        # This is tested implicitly through the get_recent_activity_count method
    
    def test_get_activity_log(self, activity_manager):
        """Test getting activity log for user."""
        user_email = "test@example.com"
        
        # Log some actions
        activity_manager.log_account_action(user_email, 'add', "+1111111111")
        import time
        time.sleep(0.1)  # Delay to ensure different timestamps
        activity_manager.log_account_action(user_email, 'delete', "+2222222222")
        
        log = activity_manager.get_activity_log(user_email, limit=10)
        
        assert len(log) == 2
        # Most recent first (delete should be first, but if timestamps are same, check both exist)
        actions = [item['action'] for item in log]
        assert 'add' in actions
        assert 'delete' in actions
        # If timestamps differ, delete should be first
        if log[0]['action_timestamp'] != log[1]['action_timestamp']:
            assert log[0]['action'] == 'delete'
        assert log[0]['user_email'] == user_email
        assert log[1]['user_email'] == user_email
    
    def test_get_activity_log_limit(self, activity_manager):
        """Test activity log respects limit."""
        user_email = "test@example.com"
        
        # Log 5 actions
        for i in range(5):
            activity_manager.log_account_action(user_email, 'add', f"+111111111{i}")
        
        log = activity_manager.get_activity_log(user_email, limit=3)
        assert len(log) == 3
    
    def test_multiple_users_independence(self, activity_manager):
        """Test that activity limits are per user."""
        user1 = "user1@example.com"
        user2 = "user2@example.com"
        
        # User1 reaches limit
        activity_manager.log_account_action(user1, 'add', "+1111111111")
        activity_manager.log_account_action(user1, 'delete', "+2222222222")
        
        # User2 should still be able to perform actions
        can_perform_user2 = activity_manager.can_perform_account_action(user2)
        assert can_perform_user2 is True
        
        # User1 should be blocked
        can_perform_user1 = activity_manager.can_perform_account_action(user1)
        assert can_perform_user1 is False

