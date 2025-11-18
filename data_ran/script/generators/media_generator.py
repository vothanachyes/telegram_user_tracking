"""
Media generator for media_files data.
"""

import random
from typing import Dict, Any, List
from datetime import datetime
from data_ran.pattern.base import BaseGenerator


class MediaGenerator(BaseGenerator):
    """Generates media_files data."""
    
    MIME_TYPES = {
        'photo': 'image/jpeg',
        'video': 'video/mp4',
        'document': 'application/pdf',
        'audio': 'audio/mpeg'
    }
    
    FILE_EXTENSIONS = {
        'photo': '.jpg',
        'video': '.mp4',
        'document': '.pdf',
        'audio': '.mp3'
    }
    
    def generate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate media_files data.
        
        Args:
            config: Configuration with:
                - messages: List of message dictionaries (only those with has_media=True)
                
        Returns:
            List of media file dictionaries
        """
        messages = config.get('messages', [])
        media_messages = [m for m in messages if m.get('has_media', False)]
        
        media_files = []
        
        for message in media_messages:
            message_id = message['message_id']
            media_type = message.get('media_type')
            group_id = message['group_id']
            
            if not media_type:
                continue
            
            # Generate file info
            file_name = f"{media_type}_{message_id}{self.FILE_EXTENSIONS.get(media_type, '.bin')}"
            file_path = f"./downloads/groups/{group_id}/{file_name}"
            
            # Generate file size (realistic ranges)
            if media_type == 'photo':
                file_size = random.randint(50000, 5000000)  # 50KB - 5MB
            elif media_type == 'video':
                file_size = random.randint(1000000, 100000000)  # 1MB - 100MB
            elif media_type == 'document':
                file_size = random.randint(100000, 10000000)  # 100KB - 10MB
            else:  # audio
                file_size = random.randint(50000, 5000000)  # 50KB - 5MB
            
            date_sent_str = message.get('date_sent')
            if isinstance(date_sent_str, str):
                created_at = datetime.fromisoformat(date_sent_str.replace('Z', '+00:00'))
            else:
                created_at = date_sent_str if isinstance(date_sent_str, datetime) else datetime.now()
            
            media_file = {
                'message_id': message_id,
                'file_path': file_path,
                'file_name': file_name,
                'file_size_bytes': file_size,
                'file_type': media_type,
                'mime_type': self.MIME_TYPES.get(media_type, 'application/octet-stream'),
                'thumbnail_path': f"./downloads/groups/{group_id}/{file_name}_thumb.jpg" if media_type in ['photo', 'video'] else None,
                'created_at': created_at.isoformat()
            }
            media_files.append(media_file)
        
        return media_files
    
    def get_dependencies(self) -> List[str]:
        """Media files depend on messages."""
        return ['messages']

