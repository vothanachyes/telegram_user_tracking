"""
View model for User Dashboard page - handles data fetching and business logic.
"""

from typing import Optional, List, Dict
from datetime import datetime
from database.db_manager import DatabaseManager
from database.models import TelegramUser


class UserDashboardViewModel:
    """View model for user dashboard data operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def search_users(self, query: str, limit: int = 10) -> List[TelegramUser]:
        """Search users by query."""
        if not query or len(query) < 2:
            return []
        return self.db_manager.search_users(query, limit=limit)
    
    def get_user_stats(
        self,
        user_id: int,
        group_id: Optional[int],
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict:
        """Get user activity statistics."""
        return self.db_manager.get_user_activity_stats(
            user_id=user_id,
            group_id=group_id,
            start_date=start_date,
            end_date=end_date
        )
    
    def get_user_messages(
        self,
        user_id: int,
        group_id: Optional[int],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        limit: int = 100
    ) -> List:
        """Get user messages with filters."""
        return self.db_manager.get_messages(
            group_id=group_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    
    def get_user_by_id(self, user_id: int) -> Optional[TelegramUser]:
        """Get user by ID."""
        return self.db_manager.get_user_by_id(user_id)
    
    def get_all_groups(self) -> List:
        """Get all groups."""
        return self.db_manager.get_all_groups()

