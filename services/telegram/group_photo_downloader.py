"""
Group photo downloader service.
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class GroupPhotoDownloader:
    """Service for downloading group profile photos."""
    
    def __init__(self, download_root_dir: str = "./downloads"):
        """
        Initialize group photo downloader.
        
        Args:
            download_root_dir: Root directory for downloads
        """
        self.download_root_dir = download_root_dir
    
    async def download_group_photo(
        self,
        client,
        group_id: int,
        group_username: Optional[str] = None
    ) -> Optional[str]:
        """
        Download group photo from Telegram.
        
        Args:
            client: Pyrogram client instance
            group_id: Telegram group ID
            group_username: Optional group username for folder naming
            
        Returns:
            File path if successful, None otherwise
        """
        try:
            if not client:
                logger.error("Client is None")
                return None
            
            # Get chat to access photo
            chat = await client.get_chat(group_id)
            
            if not chat.photo:
                logger.debug(f"No photo available for group {group_id}")
                return None
            
            # Create directory for group photos
            group_folder = Path(self.download_root_dir) / "groups" / str(group_id)
            group_folder.mkdir(parents=True, exist_ok=True)
            
            # Download photo
            photo_path = group_folder / "photo.jpg"
            
            downloaded_path = await client.download_media(
                chat.photo.big_file_id,
                file_name=str(photo_path)
            )
            
            if downloaded_path and os.path.exists(downloaded_path):
                logger.info(f"Downloaded group photo to {downloaded_path}")
                return str(downloaded_path)
            else:
                logger.warning(f"Photo download returned path but file doesn't exist: {downloaded_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading group photo for group {group_id}: {e}")
            return None

