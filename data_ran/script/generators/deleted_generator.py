"""
Deleted items generator for deleted_messages and deleted_users data.
"""

import random
from typing import Dict, Any, List
from datetime import datetime, timedelta
from data_ran.pattern.base import BaseGenerator


class DeletedGenerator(BaseGenerator):
    """Generates deleted_messages and deleted_users data."""
    
    def generate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate deleted items data.
        
        Args:
            config: Configuration with:
                - messages: List of message dictionaries
                - users: List of user dictionaries
                - deleted_percentage: Percentage of items to mark as deleted (0-100)
                
        Returns:
            Dictionary with 'deleted_messages' and 'deleted_users' lists
        """
        messages = config.get('messages', [])
        users = config.get('users', [])
        deleted_percentage = config.get('deleted_percentage', 5)
        
        deleted_messages = []
        deleted_users = []
        
        # Generate deleted messages
        num_deleted_messages = int(len(messages) * deleted_percentage / 100)
        messages_to_delete = random.sample(messages, min(num_deleted_messages, len(messages)))
        
        for message in messages_to_delete:
            date_sent_str = message.get('date_sent')
            if isinstance(date_sent_str, str):
                date_sent = datetime.fromisoformat(date_sent_str.replace('Z', '+00:00'))
            else:
                date_sent = date_sent_str if isinstance(date_sent_str, datetime) else datetime.now()
            
            # Deleted at some time after message was sent
            deleted_at = date_sent + timedelta(days=random.randint(1, 30))
            
            deleted_messages.append({
                'message_id': message['message_id'],
                'group_id': message['group_id'],
                'deleted_at': deleted_at.isoformat()
            })
        
        # Generate deleted users (already marked in users, but track in deleted_users table)
        deleted_user_list = [u for u in users if u.get('is_deleted', False)]
        
        for user in deleted_user_list:
            created_at_str = user.get('created_at')
            if isinstance(created_at_str, str):
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            else:
                created_at = created_at_str if isinstance(created_at_str, datetime) else datetime.now()
            
            # Deleted at some time after user was created
            deleted_at = created_at + timedelta(days=random.randint(1, 90))
            
            deleted_users.append({
                'user_id': user['user_id'],
                'deleted_at': deleted_at.isoformat()
            })
        
        return {
            'deleted_messages': deleted_messages,
            'deleted_users': deleted_users
        }
    
    def get_dependencies(self) -> List[str]:
        """Deleted items depend on messages and users."""
        return ['messages', 'users']

