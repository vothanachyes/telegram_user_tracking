"""
View model for Telegram page - handles data operations.
"""

from typing import Optional, List
from datetime import datetime
from database.db_manager import DatabaseManager


class TelegramViewModel:
    """View model for telegram page data operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_messages(
        self,
        group_id: Optional[int],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        limit: int = 100,
        tags: Optional[List[str]] = None,
        message_type_filter: Optional[str] = None
    ) -> List:
        """Get messages with filters."""
        return self.db_manager.get_messages(
            group_id=group_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            tags=tags,
            message_type_filter=message_type_filter
        )
    
    def get_users_by_group(self, group_id: int, include_all: bool = False) -> List:
        """
        Get users by group.
        
        Args:
            group_id: Group ID
            include_all: If True, include all users (even those without messages). 
                       If False, only users who have sent messages.
        """
        if include_all:
            return self.db_manager.get_all_users_in_group(group_id)
        return self.db_manager.get_users_by_group(group_id)
    
    def get_all_groups(self) -> List:
        """Get all groups."""
        return self.db_manager.get_all_groups()
    
    def get_user_by_id(self, user_id: int):
        """Get user by ID."""
        return self.db_manager.get_user_by_id(user_id)
    
    def get_all_users(self):
        """Get all users."""
        return self.db_manager.get_all_users()

