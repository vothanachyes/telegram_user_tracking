"""
User processor for handling Telegram user data.
"""

import logging
from typing import Optional

from database.db_manager import DatabaseManager
from database.models import TelegramUser

logger = logging.getLogger(__name__)


class UserProcessor:
    """Processes and saves Telegram users."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def process_user(self, telegram_user) -> Optional[TelegramUser]:
        """
        Process and save Telegram user.
        
        Args:
            telegram_user: Pyrogram user object
            
        Returns:
            TelegramUser object or None if failed/skipped
        """
        try:
            # Build full name
            full_name = telegram_user.first_name or ""
            if telegram_user.last_name:
                full_name += f" {telegram_user.last_name}"
            full_name = full_name.strip() or "Unknown User"
            
            user = TelegramUser(
                user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                full_name=full_name,
                phone=telegram_user.phone_number if hasattr(telegram_user, 'phone_number') else None
            )
            
            # Check if user is soft deleted
            existing = self.db_manager.get_user_by_id(telegram_user.id)
            if existing and existing.is_deleted:
                return None  # Skip deleted users
            
            self.db_manager.save_user(user)
            return user
            
        except Exception as e:
            logger.error(f"Error processing user: {e}")
            return None

