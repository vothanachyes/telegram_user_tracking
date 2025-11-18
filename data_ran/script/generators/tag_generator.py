"""
Tag generator for message_tags data.
"""

from typing import Dict, Any, List
from datetime import datetime
from data_ran.pattern.base import BaseGenerator
from utils.tag_extractor import TagExtractor


class TagGenerator(BaseGenerator):
    """Generates message_tags data."""
    
    def generate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate message_tags data by extracting tags from messages.
        
        Args:
            config: Configuration with:
                - messages: List of message dictionaries
                
        Returns:
            List of tag dictionaries
        """
        messages = config.get('messages', [])
        tags = []
        
        for message in messages:
            message_id = message['message_id']
            group_id = message['group_id']
            user_id = message['user_id']
            date_sent_str = message.get('date_sent')
            
            # Parse date_sent
            if isinstance(date_sent_str, str):
                date_sent = datetime.fromisoformat(date_sent_str.replace('Z', '+00:00'))
            else:
                date_sent = date_sent_str if isinstance(date_sent_str, datetime) else datetime.now()
            
            # Extract tags from content and caption
            content = message.get('content', '')
            caption = message.get('caption', '')
            
            extracted_tags = TagExtractor.extract_tags_from_content_and_caption(content, caption)
            
            for tag in extracted_tags:
                tag_entry = {
                    'message_id': message_id,
                    'group_id': group_id,
                    'user_id': user_id,
                    'tag': tag,
                    'date_sent': date_sent.isoformat(),
                    'created_at': date_sent.isoformat()
                }
                tags.append(tag_entry)
        
        return tags
    
    def get_dependencies(self) -> List[str]:
        """Tags depend on messages."""
        return ['messages']

