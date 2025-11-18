"""
Message processor for handling Telegram message data.
"""

import logging
import re
from typing import Optional, List

from database.models import Message
from utils.helpers import get_telegram_message_link
from utils.tag_extractor import TagExtractor

logger = logging.getLogger(__name__)

# URL pattern for detecting links in messages
URL_PATTERN = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)


class MessageProcessor:
    """Processes Telegram messages and extracts metadata."""
    
    def __init__(self):
        pass
    
    async def process_message(
        self,
        telegram_msg: 'TelethonMessage',
        group_id: int,
        group_username: Optional[str]
    ) -> Optional[Message]:
        """
        Process Telegram message and extract metadata.
        
        Args:
            telegram_msg: Telethon message object
            group_id: Group ID
            group_username: Group username (optional)
            
        Returns:
            Message object or None if failed
        """
        try:
            if not telegram_msg.sender:
                return None
            
            # Determine media type and message type
            has_media = False
            media_type = None
            media_count = 0
            message_type = "text"
            has_sticker = False
            has_link = False
            sticker_emoji = None
            
            # Check for sticker (Telethon uses message.media)
            if telegram_msg.sticker:
                has_sticker = True
                message_type = "sticker"
                if hasattr(telegram_msg.sticker, 'alt') and telegram_msg.sticker.alt:
                    sticker_emoji = telegram_msg.sticker.alt
                has_media = True
                media_type = "sticker"
                media_count = 1
            # Check for photo
            elif telegram_msg.photo:
                has_media = True
                media_type = "photo"
                message_type = "photo"
                media_count = 1
            # Check for video
            elif telegram_msg.video:
                has_media = True
                media_type = "video"
                message_type = "video"
                media_count = 1
            # Check for video note (round video)
            elif telegram_msg.video_note:
                has_media = True
                media_type = "video_note"
                message_type = "video_note"
                media_count = 1
            # Check for animation (GIF)
            elif telegram_msg.gif:
                has_media = True
                media_type = "animation"
                message_type = "animation"
                media_count = 1
            # Check for document
            elif telegram_msg.document:
                has_media = True
                media_type = "document"
                message_type = "document"
                media_count = 1
            # Check for audio
            elif telegram_msg.audio:
                has_media = True
                media_type = "audio"
                message_type = "audio"
                media_count = 1
            # Check for voice
            elif telegram_msg.voice:
                has_media = True
                media_type = "voice"
                message_type = "voice"
                media_count = 1
            # Check for location
            elif telegram_msg.geo:
                message_type = "location"
            # Check for contact
            elif telegram_msg.contact:
                message_type = "contact"
            # Check for poll
            elif telegram_msg.poll:
                message_type = "poll"
            # Check for media group (grouped_id in Telethon)
            elif telegram_msg.grouped_id:
                has_media = True
                media_type = "media_group"
                message_type = "media_group"
            
            # Get message content (Telethon uses 'message' attribute for text)
            content = getattr(telegram_msg, 'message', None) or ""
            
            # Detect links in content
            if content and URL_PATTERN.search(content):
                has_link = True
                if message_type == "text":
                    message_type = "link"
            
            # Generate message link
            message_link = get_telegram_message_link(group_username, group_id, telegram_msg.id)
            
            # Extract caption (for media messages)
            caption = getattr(telegram_msg, 'message', None) or ""
            
            message = Message(
                message_id=telegram_msg.id,
                group_id=group_id,
                user_id=telegram_msg.sender.id if telegram_msg.sender else 0,
                content=content,
                caption=caption,
                date_sent=telegram_msg.date,
                has_media=has_media,
                media_type=media_type,
                media_count=media_count,
                message_link=message_link,
                message_type=message_type,
                has_sticker=has_sticker,
                has_link=has_link,
                sticker_emoji=sticker_emoji
            )
            
            return message
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return None
    
    def extract_tags(self, content: str = None, caption: str = None) -> List[str]:
        """
        Extract tags from message content and caption.
        
        Args:
            content: Message content text
            caption: Message caption text
            
        Returns:
            List of normalized tags (without # prefix)
        """
        return TagExtractor.extract_tags_from_content_and_caption(content, caption)

