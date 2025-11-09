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
            client: Telethon client instance
            group_id: Telegram group ID
            group_username: Optional group username for folder naming
            
        Returns:
            File path if successful, None otherwise
        """
        try:
            if not client:
                logger.error("Client is None")
                return None
            
            # Get entity to access photo
            entity = await client.get_entity(group_id)
            
            if not hasattr(entity, 'photo') or not entity.photo:
                logger.debug(f"No photo available for group {group_id}")
                return None
            
            # Create directory for group photos
            group_folder = Path(self.download_root_dir) / "groups" / str(group_id)
            group_folder.mkdir(parents=True, exist_ok=True)
            
            # Download photo - use download_profile_photo for chat/profile photos
            photo_path = group_folder / "photo.jpg"
            
            # Telethon's download_profile_photo downloads the profile/chat photo
            # It returns the downloaded file path
            downloaded_path = await client.download_profile_photo(
                entity,
                file=str(photo_path)
            )
            
            # download_profile_photo returns the path if successful, None otherwise
            if downloaded_path:
                # Verify the file exists
                if os.path.exists(downloaded_path):
                    logger.info(f"Downloaded group photo to {downloaded_path}")
                    return str(downloaded_path)
                else:
                    logger.warning(f"Photo download returned path but file doesn't exist: {downloaded_path}")
                    return None
            else:
                logger.debug(f"Photo download returned None for group {group_id} - photo may not be available")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading group photo for group {group_id}: {e}")
            return None

