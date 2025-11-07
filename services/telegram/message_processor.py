"""
Message processor for handling Telegram message data.
"""

import logging
import re
from typing import Optional

from database.models import Message
from utils.helpers import get_telegram_message_link

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
        telegram_msg: 'PyrogramMessage',
        group_id: int,
        group_username: Optional[str]
    ) -> Optional[Message]:
        """
        Process Telegram message and extract metadata.
        
        Args:
            telegram_msg: Pyrogram message object
            group_id: Group ID
            group_username: Group username (optional)
            
        Returns:
            Message object or None if failed
        """
        try:
            if not telegram_msg.from_user:
                return None
            
            # Determine media type and message type
            has_media = False
            media_type = None
            media_count = 0
            message_type = "text"
            has_sticker = False
            has_link = False
            sticker_emoji = None
            
            # Check for sticker
            if telegram_msg.sticker:
                has_sticker = True
                message_type = "sticker"
                if hasattr(telegram_msg.sticker, 'emoji') and telegram_msg.sticker.emoji:
                    sticker_emoji = telegram_msg.sticker.emoji
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
            # Check for video note
            elif telegram_msg.video_note:
                has_media = True
                media_type = "video_note"
                message_type = "video_note"
                media_count = 1
            # Check for animation (GIF)
            elif telegram_msg.animation:
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
            elif telegram_msg.location:
                message_type = "location"
            # Check for contact
            elif telegram_msg.contact:
                message_type = "contact"
            # Check for poll
            elif telegram_msg.poll:
                message_type = "poll"
            # Check for media group
            elif telegram_msg.media_group_id:
                has_media = True
                media_type = "media_group"
                message_type = "media_group"
            
            # Get message content
            content = telegram_msg.text or telegram_msg.caption or ""
            
            # Detect links in content
            if content and URL_PATTERN.search(content):
                has_link = True
                if message_type == "text":
                    message_type = "link"
            
            # Generate message link
            message_link = get_telegram_message_link(group_username, group_id, telegram_msg.id)
            
            message = Message(
                message_id=telegram_msg.id,
                group_id=group_id,
                user_id=telegram_msg.from_user.id,
                content=content,
                caption=telegram_msg.caption,
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

