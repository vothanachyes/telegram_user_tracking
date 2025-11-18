"""
Reaction generator for reactions data.
"""

import random
from typing import Dict, Any, List
from datetime import datetime, timedelta
from data_ran.pattern.base import BaseGenerator


class ReactionGenerator(BaseGenerator):
    """Generates reactions data."""
    
    EMOJIS = ['👍', '❤️', '🔥', '🎉', '😊', '😄', '😍', '🤔', '✅', '👏', '💯', '🎯']
    
    def generate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate reactions data.
        
        Args:
            config: Configuration with:
                - messages: List of message dictionaries
                - users: List of user dictionaries (non-deleted)
                - reactions_per_message: Dict with 'min' and 'max' reactions per message
                
        Returns:
            List of reaction dictionaries
        """
        messages = config.get('messages', [])
        users = [u for u in config.get('users', []) if not u.get('is_deleted', False)]
        reactions_config = config.get('reactions_per_message', {'min': 0, 'max': 5})
        
        min_reactions = reactions_config.get('min', 0)
        max_reactions = reactions_config.get('max', 5)
        
        reactions = []
        
        for message in messages:
            message_id = message['message_id']
            group_id = message['group_id']
            date_sent_str = message['date_sent']
            
            # Parse date_sent
            if isinstance(date_sent_str, str):
                date_sent = datetime.fromisoformat(date_sent_str.replace('Z', '+00:00'))
            else:
                date_sent = date_sent_str
            
            # Number of reactions for this message
            num_reactions = random.randint(min_reactions, max_reactions)
            
            # Select random users to react (no duplicates per message)
            reacting_users = random.sample(users, min(num_reactions, len(users)))
            
            for user in reacting_users:
                emoji = random.choice(self.EMOJIS)
                reacted_at = date_sent + timedelta(seconds=random.randint(1, 3600))
                
                reaction = {
                    'message_id': message_id,
                    'group_id': group_id,
                    'user_id': user['user_id'],
                    'emoji': emoji,
                    'message_link': message.get('message_link'),
                    'reacted_at': reacted_at.isoformat(),
                    'created_at': reacted_at.isoformat()
                }
                reactions.append(reaction)
        
        return reactions
    
    def get_dependencies(self) -> List[str]:
        """Reactions depend on messages and users."""
        return ['messages', 'users']

