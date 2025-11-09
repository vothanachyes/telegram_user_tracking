"""
Update downloader for downloading and verifying updates.
"""

import logging
import hashlib
import platform
from pathlib import Path
from typing import Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("requests library not installed")

from utils.constants import (
    UPDATES_DIR_NAME,
    USER_DATA_DIR
)

logger = logging.getLogger(__name__)


class UpdateDownloader:
    """Handles downloading and verifying update files."""
    
    def __init__(self):
        self._updates_dir = Path(USER_DATA_DIR) / UPDATES_DIR_NAME
        self._updates_dir.mkdir(parents=True, exist_ok=True)
    
    async def download_update(
        self,
        url: str,
        version: str,
        expected_checksum: Optional[str] = None,
        expected_size: Optional[int] = None
    ) -> Optional[Path]:
        """
        Download update file.
        
        Args:
            url: Download URL
            version: Version string
            expected_checksum: Expected SHA256 checksum
            expected_size: Expected file size in bytes
        
        Returns:
            Path to downloaded file or None if failed
        """
        if not REQUESTS_AVAILABLE:
            logger.error("requests library not available for downloading updates")
            return None
        
        try:
            # Determine file extension based on platform
            system = platform.system()
            if system == "Windows":
                ext = ".exe"
            elif system == "Darwin":
                ext = ".dmg"
            else:
                ext = ""
            
            filename = f"TelegramUserTracking-v{version}{ext}"
            download_path = self._updates_dir / filename
            
            # Skip if already downloaded and verified
            if download_path.exists():
                if expected_checksum:
                    if self.verify_checksum(download_path, expected_checksum):
                        logger.info(f"Update already downloaded: {download_path}")
                        return download_path
                    else:
                        # Corrupted file, delete and re-download
                        logger.warning(f"Corrupted download detected, re-downloading: {download_path}")
                        download_path.unlink()
            
            logger.info(f"Downloading update from {url}")
            
            # Download file
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Check file size if provided
            if expected_size:
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) != expected_size:
                    logger.warning(
                        f"File size mismatch: expected {expected_size}, got {content_length}"
                    )
            
            # Write file
            total_size = 0
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
            
            logger.info(f"Downloaded {total_size} bytes to {download_path}")
            
            # Verify checksum if provided
            if expected_checksum:
                if not self.verify_checksum(download_path, expected_checksum):
                    logger.error("Checksum verification failed")
                    download_path.unlink()
                    return None
                logger.info("Checksum verification passed")
            
            return download_path
            
        except Exception as e:
            logger.error(f"Error downloading update: {e}", exc_info=True)
            return None
    
    def verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """
        Verify file SHA256 checksum.
        
        Args:
            file_path: Path to file
            expected_checksum: Expected SHA256 checksum (hex string)
        
        Returns:
            True if checksum matches, False otherwise
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)
            
            actual_checksum = sha256_hash.hexdigest()
            matches = actual_checksum.lower() == expected_checksum.lower()
            
            if not matches:
                logger.warning(
                    f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}"
                )
            
            return matches
        except Exception as e:
            logger.error(f"Error verifying checksum: {e}")
            return False

