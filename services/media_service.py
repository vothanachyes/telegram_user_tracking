"""
Media download and management service.
"""

import logging
import asyncio
import os
from pathlib import Path
from typing import Optional, Callable, List
from datetime import datetime

try:
    from pyrogram import Client
    from pyrogram.types import Message as PyrogramMessage
    PYROGRAM_AVAILABLE = True
except ImportError:
    PYROGRAM_AVAILABLE = False

from PIL import Image

from database.db_manager import DatabaseManager
from database.models import MediaFile, Message, TelegramUser
from config.settings import settings
from utils.helpers import create_message_folder
from utils.validators import sanitize_filename

logger = logging.getLogger(__name__)


class MediaService:
    """Handles media file downloads and management."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def download_message_media(
        self,
        client: Client,
        telegram_msg: 'PyrogramMessage',
        message: Message,
        user: TelegramUser,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[MediaFile]:
        """
        Download all media from a message.
        Returns list of MediaFile objects.
        """
        media_files = []
        
        try:
            if not message.has_media:
                return media_files
            
            # Get settings
            app_settings = settings.settings
            
            if not app_settings.download_media:
                return media_files
            
            # Check media type settings
            if message.media_type == "photo" and not app_settings.download_photos:
                return media_files
            elif message.media_type == "video" and not app_settings.download_videos:
                return media_files
            elif message.media_type == "document" and not app_settings.download_documents:
                return media_files
            elif message.media_type == "audio" and not app_settings.download_audio:
                return media_files
            
            # Create message folder
            folder_path = create_message_folder(
                app_settings.download_root_dir,
                message.group_id,
                user.username or user.full_name,
                message.date_sent,
                message.message_id
            )
            
            # Download media based on type
            if telegram_msg.photo:
                media_file = await self._download_photo(
                    client, telegram_msg, folder_path, message, progress_callback
                )
                if media_file:
                    media_files.append(media_file)
            
            elif telegram_msg.video:
                media_file = await self._download_video(
                    client, telegram_msg, folder_path, message, app_settings.max_file_size_mb, progress_callback
                )
                if media_file:
                    media_files.append(media_file)
            
            elif telegram_msg.document:
                media_file = await self._download_document(
                    client, telegram_msg, folder_path, message, app_settings.max_file_size_mb, progress_callback
                )
                if media_file:
                    media_files.append(media_file)
            
            elif telegram_msg.audio or telegram_msg.voice:
                media_file = await self._download_audio(
                    client, telegram_msg, folder_path, message, app_settings.max_file_size_mb, progress_callback
                )
                if media_file:
                    media_files.append(media_file)
            
            # Save caption if present
            if telegram_msg.caption:
                caption_file = os.path.join(folder_path, "caption.txt")
                with open(caption_file, "w", encoding="utf-8") as f:
                    f.write(telegram_msg.caption)
            
            # Save media files to database
            for media_file in media_files:
                self.db_manager.save_media_file(media_file)
            
        except Exception as e:
            logger.error(f"Error downloading message media: {e}")
        
        return media_files
    
    async def _download_photo(
        self,
        client: Client,
        telegram_msg: 'PyrogramMessage',
        folder_path: str,
        message: Message,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Optional[MediaFile]:
        """Download photo."""
        try:
            file_name = f"photo_{message.message_id}.jpg"
            file_path = os.path.join(folder_path, file_name)
            
            # Download
            downloaded_path = await client.download_media(
                telegram_msg.photo,
                file_name=file_path,
                progress=self._create_progress_wrapper(progress_callback)
            )
            
            if not downloaded_path:
                return None
            
            # Get file info
            file_size = os.path.getsize(downloaded_path)
            
            # Create thumbnail
            thumbnail_path = await self._create_thumbnail(downloaded_path, folder_path)
            
            return MediaFile(
                message_id=message.message_id,
                file_path=downloaded_path,
                file_name=file_name,
                file_size_bytes=file_size,
                file_type="photo",
                mime_type="image/jpeg",
                thumbnail_path=thumbnail_path
            )
            
        except Exception as e:
            logger.error(f"Error downloading photo: {e}")
            return None
    
    async def _download_video(
        self,
        client: Client,
        telegram_msg: 'PyrogramMessage',
        folder_path: str,
        message: Message,
        max_size_mb: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Optional[MediaFile]:
        """Download video."""
        try:
            video = telegram_msg.video
            
            # Check file size
            if video.file_size > max_size_mb * 1024 * 1024:
                logger.warning(f"Video too large: {video.file_size} bytes")
                return None
            
            # Get file name
            file_name = video.file_name or f"video_{message.message_id}.mp4"
            file_name = sanitize_filename(file_name)
            file_path = os.path.join(folder_path, file_name)
            
            # Download
            downloaded_path = await client.download_media(
                video,
                file_name=file_path,
                progress=self._create_progress_wrapper(progress_callback)
            )
            
            if not downloaded_path:
                return None
            
            file_size = os.path.getsize(downloaded_path)
            
            return MediaFile(
                message_id=message.message_id,
                file_path=downloaded_path,
                file_name=file_name,
                file_size_bytes=file_size,
                file_type="video",
                mime_type=video.mime_type or "video/mp4"
            )
            
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None
    
    async def _download_document(
        self,
        client: Client,
        telegram_msg: 'PyrogramMessage',
        folder_path: str,
        message: Message,
        max_size_mb: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Optional[MediaFile]:
        """Download document."""
        try:
            document = telegram_msg.document
            
            # Check file size
            if document.file_size > max_size_mb * 1024 * 1024:
                logger.warning(f"Document too large: {document.file_size} bytes")
                return None
            
            # Get file name
            file_name = document.file_name or f"document_{message.message_id}"
            file_name = sanitize_filename(file_name)
            file_path = os.path.join(folder_path, file_name)
            
            # Download
            downloaded_path = await client.download_media(
                document,
                file_name=file_path,
                progress=self._create_progress_wrapper(progress_callback)
            )
            
            if not downloaded_path:
                return None
            
            file_size = os.path.getsize(downloaded_path)
            
            # Create thumbnail if image
            thumbnail_path = None
            if document.mime_type and document.mime_type.startswith("image/"):
                thumbnail_path = await self._create_thumbnail(downloaded_path, folder_path)
            
            return MediaFile(
                message_id=message.message_id,
                file_path=downloaded_path,
                file_name=file_name,
                file_size_bytes=file_size,
                file_type="document",
                mime_type=document.mime_type,
                thumbnail_path=thumbnail_path
            )
            
        except Exception as e:
            logger.error(f"Error downloading document: {e}")
            return None
    
    async def _download_audio(
        self,
        client: Client,
        telegram_msg: 'PyrogramMessage',
        folder_path: str,
        message: Message,
        max_size_mb: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Optional[MediaFile]:
        """Download audio."""
        try:
            audio = telegram_msg.audio or telegram_msg.voice
            
            # Check file size
            if audio.file_size > max_size_mb * 1024 * 1024:
                logger.warning(f"Audio too large: {audio.file_size} bytes")
                return None
            
            # Get file name
            if telegram_msg.audio:
                file_name = audio.file_name or f"audio_{message.message_id}.mp3"
            else:
                file_name = f"voice_{message.message_id}.ogg"
            
            file_name = sanitize_filename(file_name)
            file_path = os.path.join(folder_path, file_name)
            
            # Download
            downloaded_path = await client.download_media(
                audio,
                file_name=file_path,
                progress=self._create_progress_wrapper(progress_callback)
            )
            
            if not downloaded_path:
                return None
            
            file_size = os.path.getsize(downloaded_path)
            
            return MediaFile(
                message_id=message.message_id,
                file_path=downloaded_path,
                file_name=file_name,
                file_size_bytes=file_size,
                file_type="audio",
                mime_type=audio.mime_type or "audio/mpeg"
            )
            
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            return None
    
    async def _create_thumbnail(
        self, 
        image_path: str, 
        folder_path: str,
        size: tuple = (150, 150)
    ) -> Optional[str]:
        """Create thumbnail for image."""
        try:
            thumbnail_name = f"thumb_{Path(image_path).name}"
            thumbnail_path = os.path.join(folder_path, thumbnail_name)
            
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(thumbnail_path, "JPEG", quality=85)
            
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return None
    
    def _create_progress_wrapper(
        self, 
        callback: Optional[Callable[[int, int], None]]
    ) -> Optional[Callable]:
        """Create progress wrapper for Pyrogram download."""
        if not callback:
            return None
        
        async def progress(current, total):
            try:
                callback(current, total)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
        
        return progress
    
    def get_media_for_message(self, message_id: int) -> List[MediaFile]:
        """Get all media files for a message."""
        return self.db_manager.get_media_for_message(message_id)
    
    def delete_media_files(self, message_id: int) -> bool:
        """Delete all media files for a message."""
        try:
            media_files = self.get_media_for_message(message_id)
            
            for media in media_files:
                # Delete physical files
                if os.path.exists(media.file_path):
                    os.remove(media.file_path)
                
                if media.thumbnail_path and os.path.exists(media.thumbnail_path):
                    os.remove(media.thumbnail_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting media files: {e}")
            return False

