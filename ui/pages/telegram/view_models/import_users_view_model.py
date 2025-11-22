"""
View model for import users feature.
"""

from typing import Optional


class ImportUsersViewModel:
    """Manages import users state and data tracking."""
    
    def __init__(self):
        self.is_importing = False
        self.fetched_count = 0
        self.skipped_exist_count = 0
        self.skipped_deleted_count = 0
        self.total_count = 0
        self.current_status = ""
        self.error_message: Optional[str] = None
    
    def reset(self):
        """Reset all state to initial values."""
        self.is_importing = False
        self.fetched_count = 0
        self.skipped_exist_count = 0
        self.skipped_deleted_count = 0
        self.total_count = 0
        self.current_status = ""
        self.error_message = None
    
    def get_actual_total(self) -> int:
        """Get actual total (sum of all categories)."""
        return self.fetched_count + self.skipped_exist_count + self.skipped_deleted_count
    
    def update_progress(
        self,
        fetched: int,
        skipped_exist: int,
        skipped_deleted: int,
        total: int
    ):
        """Update progress counters."""
        self.fetched_count = fetched
        self.skipped_exist_count = skipped_exist
        self.skipped_deleted_count = skipped_deleted
        self.total_count = total

