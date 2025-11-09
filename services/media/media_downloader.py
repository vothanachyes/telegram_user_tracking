"""
Media downloader for downloading different types of media files.
"""

import logging
import os
from typing import Optional, Callable, List

try:
    from pyrogram import Client
    from pyrogram.types import Message as PyrogramMessage
    PYROGRAM_AVAILABLE = True
except ImportError:
    PYROGRAM_AVAILABLE = False

from database.models import MediaFile, Message
from config.settings import settings
from utils.helpers import create_message_folder
from utils.validators import sanitize_filename
from services.media.thumbnail_creator import ThumbnailCreator

logger = logging.getLogger(__name__)


class MediaDownloader:
    """Handles downloading different types of media files."""
    
    def __init__(self):
        self.thumbnail_creator = ThumbnailCreator()
    
    async def download_message_media(
        self,
        client: Client,
        telegram_msg: 'PyrogramMessage',
        message: Message,
        user,
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
                progress=self.thumbnail_creator.create_progress_wrapper(progress_callback)
            )
            
            if not downloaded_path:
                return None
            
            # Get file info
            file_size = os.path.getsize(downloaded_path)
            
            # Create thumbnail
            thumbnail_path = await self.thumbnail_creator.create_thumbnail(downloaded_path, folder_path)
            
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
                progress=self.thumbnail_creator.create_progress_wrapper(progress_callback)
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
                progress=self.thumbnail_creator.create_progress_wrapper(progress_callback)
            )
            
            if not downloaded_path:
                return None
            
            file_size = os.path.getsize(downloaded_path)
            
            # Create thumbnail if image
            thumbnail_path = None
            if document.mime_type and document.mime_type.startswith("image/"):
                thumbnail_path = await self.thumbnail_creator.create_thumbnail(downloaded_path, folder_path)
            
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
                progress=self.thumbnail_creator.create_progress_wrapper(progress_callback)
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

