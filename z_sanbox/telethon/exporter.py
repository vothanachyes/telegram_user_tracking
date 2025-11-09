"""
Main export logic for Telegram Group Exporter.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from telethon import TelegramClient, errors
from telethon.tl.types import Message
from tqdm import tqdm

from config import Config
from utils import extract_links, get_file_name, get_user_display_name, format_file_size


logger = logging.getLogger(__name__)


class DownloadProgress:
    """Progress bar for file downloads."""
    
    def __init__(self, message_id: int, total_bytes: int):
        self.pbar = tqdm(
            total=total_bytes,
            unit='B',
            unit_scale=True,
            desc=f"MSG-{message_id}",
            leave=False
        )
        self.last_received = 0
    
    def update(self, received_bytes: int, total_bytes: int, client=None) -> None:
        """Update progress bar."""
        self.pbar.total = total_bytes
        delta = received_bytes - self.last_received
        if delta > 0:
            self.pbar.update(delta)
            self.last_received = received_bytes
    
    def close(self) -> None:
        """Close progress bar."""
        self.pbar.close()


class TelegramExporter:
    """Main exporter class for Telegram group messages."""
    
    def __init__(self, config: type[Config]):
        self.config = config
        self.client: Optional[TelegramClient] = None
        self.total_files = 0
        self.total_skipped = 0
        self.total_errors = 0
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Connect to Telegram."""
        try:
            self.client = TelegramClient(
                self.config.SESSION_NAME,
                self.config.API_ID,
                self.config.API_HASH
            )
            await self.client.start(phone=self.config.PHONE_NUMBER)
            me = await self.client.get_me()
            logger.info(f"✅ Logged in as: {me.username or me.first_name} (ID: {me.id})")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Telegram."""
        if self.client:
            await self.client.disconnect()
            logger.info("Disconnected from Telegram")
    
    async def safe_download(
        self,
        message: Message,
        file_path: Path,
        max_retries: Optional[int] = None
    ) -> bool:
        """
        Download file with progress tracking and size limits.
        
        Args:
            message: Telegram message object
            file_path: Destination file path
            max_retries: Maximum retry attempts
            
        Returns:
            True if download successful, False otherwise
        """
        max_retries = max_retries or self.config.MAX_RETRIES
        
        # Size check
        if message.document:
            file_size_mb = message.document.size / (1024 * 1024)
            if file_size_mb > self.config.MAX_FILE_SIZE_MB:
                logger.warning(
                    f"⛔ Skipped {message.id} "
                    f"({file_size_mb:.1f}MB > {self.config.MAX_FILE_SIZE_MB}MB)"
                )
                self.total_skipped += 1
                return False
        
        # Check if file already exists
        if file_path.exists():
            logger.info(f"⏭️  File already exists: {file_path.name}")
            return True
        
        progress = None
        for attempt in range(max_retries):
            try:
                if message.document:
                    progress = DownloadProgress(message.id, message.document.size)
                elif message.photo:
                    # Photos don't have size in document, estimate
                    progress = DownloadProgress(message.id, 0)
                
                await message.download_media(
                    file=str(file_path),
                    progress_callback=progress.update if progress else None
                )
                
                if progress:
                    progress.close()
                
                return True
                
            except errors.FloodWaitError as e:
                wait = e.seconds + 5
                logger.warning(f"⏳ Flood wait: {wait}s")
                if progress:
                    progress.close()
                await asyncio.sleep(wait)
                
            except Exception as e:
                logger.error(f"⚠️ Attempt {attempt+1}/{max_retries} failed: {str(e)}")
                if progress:
                    progress.close()
                
                if attempt == max_retries - 1:
                    self.total_errors += 1
                    return False
                
                await asyncio.sleep(5)
        
        return False
    
    def create_metadata(
        self,
        message: Message,
        sender,
        file_name: Optional[str] = None
    ) -> dict:
        """Create metadata dictionary for a message."""
        metadata = {
            "sender_id": sender.id,
            "sender_name": get_user_display_name(sender),
            "message_id": message.id,
            "date": message.date.isoformat(),
            "caption": message.text,
            "links": extract_links(message.text),
        }
        
        if message.document:
            metadata["file_size_mb"] = round(
                message.document.size / (1024 * 1024), 2
            )
            metadata["file_type"] = message.document.mime_type or "unknown"
            if file_name:
                metadata["file_path"] = file_name
        elif message.photo:
            metadata["file_type"] = "photo"
            if file_name:
                metadata["file_path"] = file_name
        
        return metadata
    
    async def process_message(self, message: Message) -> bool:
        """
        Process a single message.
        
        Args:
            message: Telegram message object
            
        Returns:
            True if processed successfully, False otherwise
        """
        try:
            # Skip messages outside date range
            end_date = self.config.get_end_date()
            start_date = self.config.get_start_date()
            
            if message.date > end_date:
                return False
            
            if message.date < start_date:
                return False
            
            # Skip non-relevant messages
            if not (message.document or message.photo or extract_links(message.text)):
                return False
            
            # Get sender information
            sender = await message.get_sender()
            if not sender:
                logger.warning(f"Could not get sender for message {message.id}")
                return False
            
            username = get_user_display_name(sender)
            date_folder = message.date.strftime("%Y-%m-%d")
            user_folder = self.config.EXPORT_FOLDER / username / date_folder
            user_folder.mkdir(parents=True, exist_ok=True)
            
            file_name = None
            file_path = None
            
            # Handle file downloads
            if message.document or message.photo:
                file_name = get_file_name(message)
                if not file_name:
                    logger.warning(f"⚠️ Unsupported file type for message {message.id}")
                    return False
                
                file_path = user_folder / file_name
                
                if await self.safe_download(message, file_path):
                    self.total_files += 1
                    file_size = format_file_size(
                        message.document.size if message.document else 0
                    )
                    logger.info(
                        f"✓ [{self.total_files}] Downloaded: "
                        f"{username}/{date_folder}/{file_name} ({file_size})"
                    )
                else:
                    logger.error(f"Failed to download file for message {message.id}")
                    return False
            
            # Create and save metadata
            metadata = self.create_metadata(message, sender, file_name)
            meta_path = user_folder / f"meta_{message.id}.json"
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Rate limiting
            await asyncio.sleep(self.config.RATE_LIMIT)
            
            return True
            
        except Exception as e:
            logger.error(f"⚠️ Error processing message {message.id}: {str(e)}")
            self.total_errors += 1
            return False
    
    async def export_history(self) -> None:
        """Export group message history."""
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        try:
            group = await self.client.get_entity(self.config.GROUP_ID)
            start_date = self.config.get_start_date()
            end_date = self.config.get_end_date()
            
            logger.info(f"🚀 Exporting from: {group.title} (ID: {group.id})")
            logger.info(f"📅 Date range: {start_date.date()} to {end_date.date()}")
            logger.info(f"📦 File size limit: {self.config.MAX_FILE_SIZE_MB}MB")
            logger.info(f"⏱️  Rate limit: {self.config.RATE_LIMIT}s between downloads")
            
            processed_count = 0
            async for message in self.client.iter_messages(
                group,
                offset_date=start_date,
                reverse=True
            ):
                if await self.process_message(message):
                    processed_count += 1
                    
                    # Log progress every 10 messages
                    if processed_count % 10 == 0:
                        logger.info(
                            f"Progress: {processed_count} messages processed, "
                            f"{self.total_files} files downloaded"
                        )
                
        except Exception as e:
            logger.error(f"‼️ Critical error during export: {str(e)}")
            raise
    
    def print_summary(self) -> None:
        """Print export summary."""
        logger.info("\n" + "="*50)
        logger.info("✅ Export Summary")
        logger.info("="*50)
        logger.info(f"📁 Export folder: {self.config.EXPORT_FOLDER.absolute()}")
        logger.info(f"📦 Total files downloaded: {self.total_files}")
        logger.info(f"⏭️  Total skipped: {self.total_skipped}")
        logger.info(f"❌ Total errors: {self.total_errors}")
        logger.info("="*50)

