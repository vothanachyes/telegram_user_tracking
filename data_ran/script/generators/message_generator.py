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
    
    MESSAGE_TYPES = ['text', 'photo', 'video', 'sticker', 'document', 'audio', 'voice', 'poll', 'location']
    MEDIA_TYPES = ['photo', 'video', 'document', 'audio']
    STICKER_EMOJIS = ['👍', '❤️', '🔥', '🎉', '😊', '😄', '😍', '🤔', '✅', '❌']
    
    # Map UI checkbox names to actual message types
    TYPE_MAP = {
        'text': 'text',
        'voice': 'voice',
        'audio': 'audio',
        'photos': 'photo',
        'videos': 'video',
        'files': 'document',
        'sticker': 'sticker',
        'poll': 'poll',
        'location': 'location'
    }
    
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
        message_types = config.get('message_types', None)  # None = all types, or list of selected types
        
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
                
                # Get available message types based on selection
                available_types = self._get_available_types(message_types)
                
                # Determine message type from available types
                message_type = random.choice(available_types)
                
                # Initialize defaults
                has_media = False
                media_type = None
                media_count = 0
                content = None
                caption = None
                has_sticker = False
                sticker_emoji = None
                has_link = False
                has_mention = False
                tag_count = 0
                
                # Generate message based on type
                if message_type == 'text':
                    # Determine if we need tags (if 'tag' is selected, higher chance)
                    needs_tag = False
                    if message_types and 'tag' in message_types:
                        # If 'tag' is selected, 70% chance to have tags
                        needs_tag = random.random() < 0.7
                    
                    # Generate text message
                    if needs_tag:
                        tag_count = random.randint(
                            max(1, tag_config.get('min_tags', 1) if tag_config else 1),
                            tag_config.get('max_tags', 3) if tag_config else 3
                        )
                    else:
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
                    
                    # Check for link requirement
                    if message_types and 'link' in message_types:
                        if random.random() < 0.5:  # 50% chance to add link
                            content = (content or "") + " https://example.com"
                            has_link = True
                    elif content and ('http://' in content or 'https://' in content or 'www.' in content):
                        has_link = True
                    
                    # Check for mention requirement
                    if message_types and 'mention' in message_types:
                        if random.random() < 0.5:  # 50% chance to add mention
                            content = (content or "") + " @username"
                            has_mention = True
                    elif content and '@' in content:
                        has_mention = True
                
                elif message_type == 'sticker':
                    has_sticker = True
                    sticker_emoji = random.choice(self.STICKER_EMOJIS)
                
                elif message_type in ['photo', 'video', 'document', 'audio']:
                    has_media = True
                    media_type = message_type
                    media_count = 1
                    # Optionally add caption
                    if random.random() < 0.3:  # 30% chance for caption
                        if 'khmer' in languages and 'english' in languages:
                            lang = random.choice(['khmer', 'english'])
                        elif 'khmer' in languages:
                            lang = 'khmer'
                        else:
                            lang = 'english'
                        caption = self.ai_generator.generate_message(lang, include_tags=False, tag_count=0)
                        # Check for link in caption
                        if caption and ('http://' in caption or 'https://' in caption or 'www.' in caption):
                            has_link = True
                        # Check for mention in caption
                        if caption and '@' in caption:
                            has_mention = True
                
                elif message_type == 'voice':
                    message_type = 'voice'
                    has_media = True
                    media_type = 'voice'
                    media_count = 1
                
                elif message_type == 'poll':
                    message_type = 'poll'
                    content = "Poll: " + self.ai_generator.generate_message('english', include_tags=False, tag_count=0)
                
                elif message_type == 'location':
                    message_type = 'location'
                    content = "Location shared"
                
                # Handle tag requirement for non-text messages (if 'tag' is in selected types)
                # Text messages already handled above
                if message_types and 'tag' in message_types and message_type != 'text':
                    # For media messages with captions, add tags to caption
                    if message_type in ['photo', 'video', 'document', 'audio'] and caption:
                        tag_count = random.randint(1, tag_config.get('max_tags', 3) if tag_config else 3)
                        # Add tags to caption
                        tag_words = ['tech', 'news', 'update', 'important', 'announcement', 'event']
                        tags = ['#' + random.choice(tag_words) for _ in range(tag_count)]
                        caption = caption + " " + " ".join(tags)
                
                # Final check for links if not already set
                if not has_link and content and ('http://' in content or 'https://' in content or 'www.' in content):
                    has_link = True
                
                # Final check for mentions if not already set
                if not has_mention and content and '@' in content:
                    has_mention = True
                
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
                    'has_sticker': has_sticker,
                    'has_link': has_link,
                    'sticker_emoji': sticker_emoji,
                    'is_deleted': False,
                    'created_at': date_sent.isoformat(),
                    'updated_at': date_sent.isoformat()
                }
                messages.append(message)
                message_id_counter += 1
        
        return messages
    
    def _get_available_types(self, message_types: Any) -> List[str]:
        """
        Get available message types based on user selection.
        
        Args:
            message_types: None for all types, or list of selected types from UI
            
        Returns:
            List of available message type strings
        """
        if message_types is None:
            # All types selected - return all base types
            return self.MESSAGE_TYPES.copy()
        
        # Map UI checkbox names to actual message types
        available = []
        for ui_type in message_types:
            if ui_type in self.TYPE_MAP:
                mapped_type = self.TYPE_MAP[ui_type]
                if mapped_type not in available:
                    available.append(mapped_type)
        
        # If no valid types found, default to all types
        if not available:
            return self.MESSAGE_TYPES.copy()
        
        return available
    
    def get_dependencies(self) -> List[str]:
        """Messages depend on groups and users."""
        return ['groups', 'users']

