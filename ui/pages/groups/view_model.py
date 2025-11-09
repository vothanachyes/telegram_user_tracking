"""
View model for groups page.
"""

from typing import List, Optional
from database.db_manager import DatabaseManager
from database.models.telegram import TelegramGroup


class GroupsViewModel:
    """View model for groups page state."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.groups: List[TelegramGroup] = []
        self.selected_group: Optional[TelegramGroup] = None
        self.is_loading = False
    
    def load_groups(self):
        """Load all groups from database."""
        self.groups = self.db_manager.get_all_groups()
    
    def get_all_groups(self) -> List[TelegramGroup]:
        """Get all groups."""
        return self.groups
    
    def set_selected_group(self, group: Optional[TelegramGroup]):
        """Set selected group."""
        self.selected_group = group
    
    def get_selected_group(self) -> Optional[TelegramGroup]:
        """Get selected group."""
        return self.selected_group

