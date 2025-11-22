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
    
    def get_users_with_group_counts(
        self,
        group_ids: Optional[List[int]] = None,
        search_query: Optional[str] = None
    ) -> List[dict]:
        """
        Get users with their group counts, optionally filtered by groups and search query.
        
        Args:
            group_ids: Optional list of group IDs to filter by
            search_query: Optional search query to filter users by name/username
            
        Returns:
            List of dictionaries with user_id, full_name, username, group_count
        """
        return self.db_manager.get_users_with_group_counts(group_ids, search_query)
    
    def get_user_groups(self, user_id: int) -> List[dict]:
        """
        Get all groups for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            List of group dictionaries with group_id, group_name, group_username
        """
        return self.db_manager.get_user_groups(user_id)
    
    def get_groups_with_user_counts(self, group_ids: Optional[List[int]] = None) -> List[dict]:
        """
        Get groups with user counts for filtering.
        
        Args:
            group_ids: Optional list of group IDs to filter by
            
        Returns:
            List of dictionaries with group_id, group_name, group_username, user_count
        """
        return self.db_manager.get_groups_with_user_counts(group_ids)

