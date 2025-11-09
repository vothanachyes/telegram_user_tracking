"""
View model for fetch data page - manages state and data tracking.
"""

from typing import Optional, Dict, List
from datetime import datetime
from database.models import Message, TelegramUser


class FetchViewModel:
    """Manages fetch state and data tracking."""
    
    def __init__(self):
        self.is_fetching = False
        self.processed_count = 0
        self.error_count = 0
        self.estimated_total = 0
        self.current_message: Optional[Message] = None
        self.current_user: Optional[TelegramUser] = None
        self.current_error: Optional[str] = None
        
        # User summary data: {user_id: {messages: count, reactions: count, media: count}}
        self.user_summary: Dict[int, Dict[str, int]] = {}
        
        # Message queue for animation (previous, current, next)
        self.message_queue: List[Optional[Message]] = [None, None, None]
        self.user_queue: List[Optional[TelegramUser]] = [None, None, None]
        self.error_queue: List[Optional[str]] = [None, None, None]
    
    def reset(self):
        """Reset all state to initial values."""
        self.is_fetching = False
        self.processed_count = 0
        self.error_count = 0
        self.estimated_total = 0
        self.current_message = None
        self.current_user = None
        self.current_error = None
        self.user_summary.clear()
        self.message_queue = [None, None, None]
        self.user_queue = [None, None, None]
        self.error_queue = [None, None, None]
    
    def add_message(self, message: Message, user: Optional[TelegramUser] = None, error: Optional[str] = None):
        """Add a new message to the queue and update state."""
        # Shift queue: previous -> left, current -> previous, new -> current
        self.message_queue[0] = self.message_queue[1]  # previous -> left
        self.message_queue[1] = self.message_queue[2]  # current -> previous
        self.message_queue[2] = message  # new -> current
        
        self.user_queue[0] = self.user_queue[1]
        self.user_queue[1] = self.user_queue[2]
        self.user_queue[2] = user
        
        self.error_queue[0] = self.error_queue[1]
        self.error_queue[1] = self.error_queue[2]
        self.error_queue[2] = error
        
        self.current_message = message
        self.current_user = user
        self.current_error = error
        
        if error:
            self.error_count += 1
        else:
            self.processed_count += 1
            # Update user summary
            if message.user_id not in self.user_summary:
                self.user_summary[message.user_id] = {
                    'messages': 0,
                    'reactions': 0,
                    'media': 0
                }
            self.user_summary[message.user_id]['messages'] += 1
            if message.has_media:
                self.user_summary[message.user_id]['media'] += 1
    
    def get_summary_data(self) -> List[Dict]:
        """Get summary data as list of dictionaries for table display."""
        summary_list = []
        for user_id, stats in self.user_summary.items():
            summary_list.append({
                'user_id': user_id,
                'messages': stats['messages'],
                'reactions': stats['reactions'],
                'media': stats['media']
            })
        # Sort by message count descending
        summary_list.sort(key=lambda x: x['messages'], reverse=True)
        return summary_list

