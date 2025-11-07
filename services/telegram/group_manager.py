"""
Group manager for Telegram group operations.
"""

import logging
from typing import Optional, Tuple
from datetime import datetime

from database.db_manager import DatabaseManager
from database.models import TelegramGroup

logger = logging.getLogger(__name__)


class GroupManager:
    """Manages Telegram group operations."""
    
    def __init__(self, db_manager: DatabaseManager, client):
        self.db_manager = db_manager
        self.client = client
    
    async def fetch_group_info(
        self,
        group_id: int
    ) -> Tuple[bool, Optional[TelegramGroup], Optional[str]]:
        """
        Fetch group information.
        
        Args:
            group_id: Group ID
            
        Returns:
            (success, group, error_message)
        """
        try:
            if not self.client:
                return False, None, "Not connected to Telegram"
            
            chat = await self.client.get_chat(group_id)
            
            group = TelegramGroup(
                group_id=chat.id,
                group_name=chat.title or "Unknown Group",
                group_username=chat.username
            )
            
            return True, group, None
            
        except Exception as e:
            logger.error(f"Error fetching group info: {e}")
            return False, None, str(e)
    
    def save_group(self, group: TelegramGroup):
        """Save group to database."""
        self.db_manager.save_group(group)
    
    def update_group_stats(self, group: TelegramGroup, message_count: int):
        """
        Update group statistics.
        
        Args:
            group: TelegramGroup object
            message_count: Total message count
        """
        group.last_fetch_date = datetime.now()
        group.total_messages = message_count
        self.db_manager.save_group(group)

