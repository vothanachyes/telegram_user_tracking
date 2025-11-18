"""
Message generator for messages data.
"""

import random
from typing import Dict, Any, List
from datetime import datetime, timedelta
from data_ran.pattern.base import BaseGenerator
from data_ran.script.ai_generator import AIContentGenerator


class MessageGenerator(BaseGenerator):
    """Generates messages data."""
    
    MESSAGE_TYPES = ['text', 'photo', 'video', 'sticker', 'document', 'audio']
    MEDIA_TYPES = ['photo', 'video', 'document', 'audio']
    STICKER_EMOJIS = ['👍', '❤️', '🔥', '🎉', '😊', '😄', '😍', '🤔', '✅', '❌']
    
    def __init__(self):
        """Initialize message generator."""
        self.ai_generator = AIContentGenerator()
    
    def generate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate messages data.
        
        Args:
            config: Configuration with:
                - groups: List of group dictionaries
                - users: List of user dictionaries (non-deleted)
                - messages_per_group: Number of messages per group (or range)
                - media_percentage: Percentage of messages with media (0-100)
                - date_range: Dict with 'start' and 'end' datetime
                - languages: List of languages ['khmer', 'english']
                
        Returns:
            List of message dictionaries
        """
        groups = config.get('groups', [])
        users = [u for u in config.get('users', []) if not u.get('is_deleted', False)]
        messages_per_group = config.get('messages_per_group', 100)
        media_percentage = config.get('media_percentage', 30)
        date_range = config.get('date_range', {})
        languages = config.get('languages', ['english'])
        tag_config = config.get('tag_config', {})
        
        if isinstance(messages_per_group, dict):
            min_msg = messages_per_group.get('min', 50)
            max_msg = messages_per_group.get('max', 200)
        else:
            min_msg = max_msg = messages_per_group
        
        start_date = date_range.get('start', datetime.now() - timedelta(days=30))
        end_date = date_range.get('end', datetime.now())
        
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        messages = []
        message_id_counter = 1000
        
        for group in groups:
            group_id = group['group_id']
            num_messages = random.randint(min_msg, max_msg)
            
            # Distribute messages across date range
            time_span = (end_date - start_date).total_seconds()
            
            for i in range(num_messages):
                # Random timestamp within date range
                random_seconds = random.randint(0, int(time_span))
                date_sent = start_date + timedelta(seconds=random_seconds)
                
                # Random user from available users
                user = random.choice(users) if users else None
                if not user:
                    continue
                
                user_id = user['user_id']
                
                # Determine message type
                has_media = random.randint(1, 100) <= media_percentage
                
                if has_media:
                    message_type = random.choice(self.MEDIA_TYPES)
                    media_type = message_type
                    media_count = 1
                    content = None
                    caption = None
                else:
                    # Text or sticker
                    if random.random() < 0.1:  # 10% stickers
                        message_type = 'sticker'
                        media_type = None
                        media_count = 0
                        content = None
                        caption = None
                        has_sticker = True
                        sticker_emoji = random.choice(self.STICKER_EMOJIS)
                    else:
                        message_type = 'text'
                        media_type = None
                        media_count = 0
                        has_sticker = False
                        sticker_emoji = None
                        
                        # Generate message content
                        tag_count = random.randint(
                            tag_config.get('min_tags', 0),
                            tag_config.get('max_tags', 3)
                        ) if tag_config else 0
                        
                        # Determine language
                        if 'khmer' in languages and 'english' in languages:
                            lang = random.choice(['khmer', 'english', 'mixed'])
                        elif 'khmer' in languages:
                            lang = 'khmer'
                        else:
                            lang = 'english'
                        
                        content = self.ai_generator.generate_message(
                            lang, 
                            include_tags=tag_count > 0,
                            tag_count=tag_count
                        )
                        caption = None
                
                # Check for links in content
                has_link = False
                if content and ('http://' in content or 'https://' in content or 'www.' in content):
                    has_link = True
                
                # Generate message link
                group_username = group.get('group_username', 'group')
                message_link = f"https://t.me/{group_username}/{message_id_counter}"
                
                message = {
                    'message_id': message_id_counter,
                    'group_id': group_id,
                    'user_id': user_id,
                    'content': content,
                    'caption': caption,
                    'date_sent': date_sent.isoformat(),
                    'has_media': has_media,
                    'media_type': media_type,
                    'media_count': media_count,
                    'message_link': message_link,
                    'message_type': message_type,
                    'has_sticker': has_sticker if 'has_sticker' in locals() else False,
                    'has_link': has_link,
                    'sticker_emoji': sticker_emoji if 'sticker_emoji' in locals() else None,
                    'is_deleted': False,
                    'created_at': date_sent.isoformat(),
                    'updated_at': date_sent.isoformat()
                }
                messages.append(message)
                message_id_counter += 1
        
        return messages
    
    def get_dependencies(self) -> List[str]:
        """Messages depend on groups and users."""
        return ['groups', 'users']

