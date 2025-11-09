"""
Thumbnail creator for creating image thumbnails.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Callable

from PIL import Image

logger = logging.getLogger(__name__)


class ThumbnailCreator:
    """Handles thumbnail creation and progress wrapper utilities."""
    
    async def create_thumbnail(
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
    
    def create_progress_wrapper(
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

