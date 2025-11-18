"""
Database dumper for directly inserting generated data into database.
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from database.managers.db_manager import DatabaseManager
from database.models.telegram import TelegramGroup, TelegramUser
from database.models.message import Message, Reaction, MessageTag
from database.models.media import MediaFile
from database.models.deleted import DeletedMessage, DeletedUser
from database.models.app_settings import AppSettings
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseDumper:
    """Handles direct database insertion of generated data."""
    
    def __init__(self, db_path: str = "./data/app.db"):
        """
        Initialize database dumper.
        
        Args:
            db_path: Path to database file
        """
        self.db_path = db_path
        self.db_manager = DatabaseManager(db_path)
    
    def validate_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate generated data before insertion.
        
        Args:
            data: Generated data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        flat_data = data.get('_flat_data', {})
        
        # Check required tables
        required_tables = ['telegram_groups', 'telegram_users', 'messages']
        for table in required_tables:
            if table not in flat_data:
                errors.append(f"Missing required table: {table}")
        
        # Validate groups
        groups = flat_data.get('telegram_groups', [])
        if not groups:
            errors.append("No groups to insert")
        
        # Validate users
        users = flat_data.get('telegram_users', [])
        if not users:
            errors.append("No users to insert")
        
        # Validate messages reference existing groups and users
        messages = flat_data.get('messages', [])
        group_ids = {g['group_id'] for g in groups}
        user_ids = {u['user_id'] for u in users}
        
        for msg in messages:
            if msg.get('group_id') not in group_ids:
                errors.append(f"Message {msg.get('message_id')} references non-existent group {msg.get('group_id')}")
            if msg.get('user_id') not in user_ids:
                errors.append(f"Message {msg.get('message_id')} references non-existent user {msg.get('user_id')}")
        
        return len(errors) == 0, errors
    
    def dump_data(self, data: Dict[str, Any], clear_first: bool = False) -> bool:
        """
        Insert generated data into database.
        
        Args:
            data: Generated data dictionary (with _flat_data)
            clear_first: Whether to clear existing data first
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate data
            is_valid, errors = self.validate_data(data)
            if not is_valid:
                logger.error(f"Data validation failed: {errors}")
                return False
            
            flat_data = data.get('_flat_data', {})
            
            if clear_first:
                logger.info("Clearing existing data...")
                self._clear_data()
            
            # Insert in order (respecting foreign keys)
            logger.info("Inserting groups...")
            self.insert_groups(flat_data.get('telegram_groups', []))
            
            logger.info("Inserting users...")
            self.insert_users(flat_data.get('telegram_users', []))
            
            logger.info("Inserting messages...")
            self.insert_messages(flat_data.get('messages', []))
            
            logger.info("Inserting reactions...")
            self.insert_reactions(flat_data.get('reactions', []))
            
            logger.info("Inserting media files...")
            self.insert_media_files(flat_data.get('media_files', []))
            
            logger.info("Inserting tags...")
            self.insert_tags(flat_data.get('message_tags', []))
            
            logger.info("Inserting deleted items...")
            self.insert_deleted_messages(flat_data.get('deleted_messages', []))
            self.insert_deleted_users(flat_data.get('deleted_users', []))
            
            logger.info("Inserting app settings...")
            settings_list = flat_data.get('app_settings', [])
            if settings_list:
                self.insert_settings(settings_list[0])
            
            logger.info("Data dump completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error dumping data: {e}", exc_info=True)
            return False
    
    def _clear_data(self):
        """Clear existing data from database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                # Clear in reverse dependency order
                cursor.execute("DELETE FROM message_tags")
                cursor.execute("DELETE FROM reactions")
                cursor.execute("DELETE FROM media_files")
                cursor.execute("DELETE FROM deleted_messages")
                cursor.execute("DELETE FROM deleted_users")
                cursor.execute("DELETE FROM messages")
                cursor.execute("DELETE FROM telegram_users")
                cursor.execute("DELETE FROM telegram_groups")
                conn.commit()
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            raise
    
    def insert_groups(self, groups: List[Dict[str, Any]]) -> bool:
        """Insert groups into database."""
        try:
            for group_data in groups:
                group = TelegramGroup(
                    group_id=group_data['group_id'],
                    group_name=group_data['group_name'],
                    group_username=group_data.get('group_username'),
                    last_fetch_date=self._parse_datetime(group_data.get('last_fetch_date')),
                    total_messages=group_data.get('total_messages', 0),
                    created_at=self._parse_datetime(group_data.get('created_at')),
                    updated_at=self._parse_datetime(group_data.get('updated_at'))
                )
                self.db_manager.save_group(group)
            return True
        except Exception as e:
            logger.error(f"Error inserting groups: {e}")
            return False
    
    def insert_users(self, users: List[Dict[str, Any]]) -> bool:
        """Insert users into database."""
        try:
            for user_data in users:
                user = TelegramUser(
                    user_id=user_data['user_id'],
                    username=user_data.get('username'),
                    first_name=user_data.get('first_name'),
                    last_name=user_data.get('last_name'),
                    full_name=user_data.get('full_name', ''),
                    phone=user_data.get('phone'),
                    bio=user_data.get('bio'),
                    profile_photo_path=user_data.get('profile_photo_path'),
                    is_deleted=user_data.get('is_deleted', False),
                    created_at=self._parse_datetime(user_data.get('created_at')),
                    updated_at=self._parse_datetime(user_data.get('updated_at'))
                )
                self.db_manager.save_user(user)
            return True
        except Exception as e:
            logger.error(f"Error inserting users: {e}")
            return False
    
    def insert_messages(self, messages: List[Dict[str, Any]]) -> bool:
        """Insert messages into database."""
        try:
            for msg_data in messages:
                message = Message(
                    message_id=msg_data['message_id'],
                    group_id=msg_data['group_id'],
                    user_id=msg_data['user_id'],
                    content=msg_data.get('content'),
                    caption=msg_data.get('caption'),
                    date_sent=self._parse_datetime(msg_data.get('date_sent')),
                    has_media=msg_data.get('has_media', False),
                    media_type=msg_data.get('media_type'),
                    media_count=msg_data.get('media_count', 0),
                    message_link=msg_data.get('message_link'),
                    message_type=msg_data.get('message_type'),
                    has_sticker=msg_data.get('has_sticker', False),
                    has_link=msg_data.get('has_link', False),
                    sticker_emoji=msg_data.get('sticker_emoji'),
                    is_deleted=msg_data.get('is_deleted', False),
                    created_at=self._parse_datetime(msg_data.get('created_at')),
                    updated_at=self._parse_datetime(msg_data.get('updated_at'))
                )
                self.db_manager.save_message(message)
            return True
        except Exception as e:
            logger.error(f"Error inserting messages: {e}")
            return False
    
    def insert_reactions(self, reactions: List[Dict[str, Any]]) -> bool:
        """Insert reactions into database."""
        try:
            for reaction_data in reactions:
                reaction = Reaction(
                    message_id=reaction_data['message_id'],
                    group_id=reaction_data['group_id'],
                    user_id=reaction_data['user_id'],
                    emoji=reaction_data['emoji'],
                    message_link=reaction_data.get('message_link'),
                    reacted_at=self._parse_datetime(reaction_data.get('reacted_at')),
                    created_at=self._parse_datetime(reaction_data.get('created_at'))
                )
                self.db_manager.save_reaction(reaction)
            return True
        except Exception as e:
            logger.error(f"Error inserting reactions: {e}")
            return False
    
    def insert_media_files(self, media_files: List[Dict[str, Any]]) -> bool:
        """Insert media files into database."""
        try:
            for media_data in media_files:
                media = MediaFile(
                    message_id=media_data['message_id'],
                    file_path=media_data['file_path'],
                    file_name=media_data['file_name'],
                    file_size_bytes=media_data['file_size_bytes'],
                    file_type=media_data['file_type'],
                    mime_type=media_data.get('mime_type'),
                    thumbnail_path=media_data.get('thumbnail_path'),
                    created_at=self._parse_datetime(media_data.get('created_at'))
                )
                self.db_manager.save_media_file(media)
            return True
        except Exception as e:
            logger.error(f"Error inserting media files: {e}")
            return False
    
    def insert_tags(self, tags: List[Dict[str, Any]]) -> bool:
        """Insert tags into database."""
        try:
            # Group tags by message_id
            tags_by_message: Dict[tuple, List[str]] = {}
            for tag_data in tags:
                key = (tag_data['message_id'], tag_data['group_id'], tag_data['user_id'])
                date_sent = self._parse_datetime(tag_data.get('date_sent'))
                if key not in tags_by_message:
                    tags_by_message[key] = []
                tags_by_message[key].append(tag_data['tag'])
            
            # Save tags grouped by message
            for (message_id, group_id, user_id), tag_list in tags_by_message.items():
                # Get date_sent from first tag
                first_tag = next(t for t in tags if t['message_id'] == message_id)
                date_sent = self._parse_datetime(first_tag.get('date_sent'))
                self.db_manager.save_tags(message_id, group_id, user_id, tag_list, date_sent)
            return True
        except Exception as e:
            logger.error(f"Error inserting tags: {e}")
            return False
    
    def insert_deleted_messages(self, deleted_messages: List[Dict[str, Any]]) -> bool:
        """Insert deleted messages into database."""
        try:
            with self.db_manager.get_connection() as conn:
                for deleted_data in deleted_messages:
                    deleted_at = self._parse_datetime(deleted_data.get('deleted_at'))
                    conn.execute("""
                        INSERT OR IGNORE INTO deleted_messages (message_id, group_id, deleted_at)
                        VALUES (?, ?, ?)
                    """, (
                        deleted_data['message_id'],
                        deleted_data['group_id'],
                        deleted_at
                    ))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error inserting deleted messages: {e}")
            return False
    
    def insert_deleted_users(self, deleted_users: List[Dict[str, Any]]) -> bool:
        """Insert deleted users into database."""
        try:
            with self.db_manager.get_connection() as conn:
                for deleted_data in deleted_users:
                    deleted_at = self._parse_datetime(deleted_data.get('deleted_at'))
                    conn.execute("""
                        INSERT OR IGNORE INTO deleted_users (user_id, deleted_at)
                        VALUES (?, ?)
                    """, (
                        deleted_data['user_id'],
                        deleted_at
                    ))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error inserting deleted users: {e}")
            return False
    
    def insert_settings(self, settings_data: Dict[str, Any]) -> bool:
        """Insert app settings into database."""
        try:
            settings = AppSettings(
                theme=settings_data.get('theme', 'dark'),
                language=settings_data.get('language', 'en'),
                corner_radius=settings_data.get('corner_radius', 10),
                telegram_api_id=settings_data.get('telegram_api_id'),
                telegram_api_hash=settings_data.get('telegram_api_hash'),
                download_root_dir=settings_data.get('download_root_dir', './downloads'),
                download_media=settings_data.get('download_media', False),
                max_file_size_mb=settings_data.get('max_file_size_mb', 3),
                fetch_delay_seconds=settings_data.get('fetch_delay_seconds', 5.0),
                download_photos=settings_data.get('download_photos', False),
                download_videos=settings_data.get('download_videos', False),
                download_documents=settings_data.get('download_documents', False),
                download_audio=settings_data.get('download_audio', False),
                track_reactions=settings_data.get('track_reactions', True),
                reaction_fetch_delay=settings_data.get('reaction_fetch_delay', 0.5),
                pin_enabled=settings_data.get('pin_enabled', False),
                encrypted_pin=settings_data.get('encrypted_pin')
            )
            self.db_manager.update_settings(settings)
            return True
        except Exception as e:
            logger.error(f"Error inserting settings: {e}")
            return False
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object."""
        if not dt_str:
            return None
        if isinstance(dt_str, datetime):
            return dt_str
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except Exception:
            return None

