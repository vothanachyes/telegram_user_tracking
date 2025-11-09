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
            telegram_user: Telethon user object
            
        Returns:
            TelegramUser object or None if failed/skipped
        """
        try:
            # Build full name
            first_name = getattr(telegram_user, 'first_name', None) or ""
            last_name = getattr(telegram_user, 'last_name', None) or ""
            full_name = f"{first_name} {last_name}".strip() or "Unknown User"
            
            user = TelegramUser(
                user_id=telegram_user.id,
                username=getattr(telegram_user, 'username', None),
                first_name=first_name,
                last_name=last_name if last_name else None,
                full_name=full_name,
                phone=getattr(telegram_user, 'phone', None)
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

