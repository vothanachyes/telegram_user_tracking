"""
Utility functions for Telegram Group Exporter.
"""
import re
from pathlib import Path
from typing import Optional
from telethon.tl.types import (
    DocumentAttributeFilename,
    DocumentAttributeVideo,
    DocumentAttributeAudio,
    DocumentAttributeImageSize,
    DocumentAttributeSticker,
    Message,
)


def extract_links(text: Optional[str]) -> list[str]:
    """Extract URLs from text."""
    if not text:
        return []
    url_pattern = re.compile(r'https?://\S+')
    return url_pattern.findall(text)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove invalid characters."""
    # Remove invalid characters for Windows/Linux/Mac
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    return filename


def get_file_name(message: Message) -> Optional[str]:
    """
    Extract filename from message for all file types.
    
    Args:
        message: Telegram message object
        
    Returns:
        Filename or None if unsupported
    """
    if message.document:
        # Check for filename attribute first
        for attr in message.document.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                return sanitize_filename(attr.file_name)
        
        # Video files
        if any(isinstance(attr, DocumentAttributeVideo) for attr in message.document.attributes):
            return f"video_{message.id}.mp4"
            
        # Audio files
        if any(isinstance(attr, DocumentAttributeAudio) for attr in message.document.attributes):
            return f"audio_{message.id}.mp3"
            
        # Images (without filename attribute)
        if any(isinstance(attr, DocumentAttributeImageSize) for attr in message.document.attributes):
            return f"image_{message.id}.jpg"
            
        # Stickers
        if any(isinstance(attr, DocumentAttributeSticker) for attr in message.document.attributes):
            return f"sticker_{message.id}.webp"
            
        # Fallback for other documents
        if message.document.mime_type:
            ext = message.document.mime_type.split('/')[-1]
        else:
            ext = 'bin'
        return f"document_{message.id}.{ext}"
        
    elif message.photo:
        return f"photo_{message.id}.jpg"
        
    return None


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def get_user_display_name(sender) -> str:
    """Get display name for a user."""
    if sender.username:
        return sender.username
    if sender.first_name:
        name = sender.first_name
        if sender.last_name:
            name += f" {sender.last_name}"
        return name
    return f"user_{sender.id}"

