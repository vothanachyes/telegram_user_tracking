"""
Message fetcher for fetching messages from Telegram groups.
"""

import logging
import asyncio
from typing import Optional, Callable, Tuple
from datetime import datetime

try:
    from pyrogram.errors import FloodWait
    PYROGRAM_AVAILABLE = True
except ImportError:
    PYROGRAM_AVAILABLE = False
    FloodWait = None

from database.db_manager import DatabaseManager
from database.models import TelegramCredential, Message
from config.settings import settings
from services.telegram.client_manager import ClientManager
from services.telegram.user_processor import UserProcessor
from services.telegram.message_processor import MessageProcessor
from services.telegram.reaction_processor import ReactionProcessor
from services.telegram.group_manager import GroupManager
from services.telegram.client_utils import ClientUtils

logger = logging.getLogger(__name__)


class MessageFetcher:
    """Handles fetching messages from Telegram groups."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        client_manager: ClientManager,
        user_processor: UserProcessor,
        message_processor: MessageProcessor,
        client_utils: ClientUtils
    ):
        self.db_manager = db_manager
        self.client_manager = client_manager
        self.user_processor = user_processor
        self.message_processor = message_processor
        self.client_utils = client_utils
    
    async def fetch_messages(
        self,
        group_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        message_callback: Optional[Callable[[Message], None]] = None
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Fetch messages from a group using temporary client (connect on demand).
        Returns (success, message_count, error_message)
        """
        temp_client = None
        try:
            # Get default credential
            credential = self.db_manager.get_default_credential()
            if not credential:
                return False, 0, "No Telegram account configured"
            
            # Create temporary client
            temp_client = await self.client_utils.create_temporary_client(credential)
            if not temp_client:
                return False, 0, "Failed to connect or session expired"
            
            # Create processors with temporary client
            temp_group_manager = GroupManager(self.db_manager, temp_client)
            temp_reaction_processor = ReactionProcessor(
                self.db_manager,
                temp_client,
                self.user_processor
            )
            
            # Fetch group info
            success, group, error = await temp_group_manager.fetch_group_info(group_id)
            if not success:
                return False, 0, error
            
            temp_group_manager.save_group(group)
            
            message_count = 0
            fetch_delay = settings.settings.fetch_delay_seconds
            
            async for telegram_msg in temp_client.get_chat_history(group_id):
                try:
                    if start_date and telegram_msg.date < start_date:
                        break
                    
                    if end_date and telegram_msg.date > end_date:
                        continue
                    
                    if self.db_manager.is_message_deleted(telegram_msg.id, group_id):
                        continue
                    
                    if telegram_msg.from_user:
                        await self.user_processor.process_user(telegram_msg.from_user)
                    
                    message = await self.message_processor.process_message(
                        telegram_msg,
                        group_id,
                        group.group_username
                    )
                    
                    if message:
                        self.db_manager.save_message(message)
                        message_count += 1
                        
                        if settings.settings.track_reactions:
                            await temp_reaction_processor.process_reactions(
                                telegram_msg,
                                group_id,
                                group.group_username,
                                message.message_link
                            )
                        
                        if message_callback:
                            message_callback(message)
                        
                        if progress_callback:
                            progress_callback(message_count, -1)
                    
                    if fetch_delay > 0:
                        await asyncio.sleep(fetch_delay)
                    
                except FloodWait as e:
                    logger.warning(f"FloodWait: waiting {e.value} seconds")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    logger.error(f"Error processing message {telegram_msg.id}: {e}")
                    continue
            
            total_messages = self.db_manager.get_message_count(group_id)
            temp_group_manager.update_group_stats(group, total_messages)
            
            logger.info(f"Fetched {message_count} messages from group {group_id}")
            return True, message_count, None
            
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return False, 0, str(e)
        finally:
            # Always disconnect temporary client
            if temp_client:
                try:
                    await temp_client.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting temporary client: {e}")
    
    async def fetch_messages_with_account(
        self,
        credential: TelegramCredential,
        group_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        message_callback: Optional[Callable[[Message], None]] = None
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Fetch messages using a specific account (temporary client).
        Keeps current session connected.
        
        Args:
            credential: TelegramCredential to use for fetching
            group_id: Group ID to fetch from
            start_date: Optional start date
            end_date: Optional end date
            progress_callback: Optional progress callback
            message_callback: Optional message callback
            
        Returns:
            (success, message_count, error_message)
        """
        temp_client = None
        try:
            # Create temporary client
            temp_client = await self.client_utils.create_temporary_client(credential)
            if not temp_client:
                return False, 0, "Failed to create temporary client or session expired"
            
            # Create processors with temporary client
            temp_group_manager = GroupManager(self.db_manager, temp_client)
            temp_reaction_processor = ReactionProcessor(
                self.db_manager,
                temp_client,
                self.user_processor
            )
            
            # Fetch group info
            success, group, error = await temp_group_manager.fetch_group_info(group_id)
            if not success:
                return False, 0, error
            
            temp_group_manager.save_group(group)
            
            message_count = 0
            fetch_delay = settings.settings.fetch_delay_seconds
            
            async for telegram_msg in temp_client.get_chat_history(group_id):
                try:
                    if start_date and telegram_msg.date < start_date:
                        break
                    
                    if end_date and telegram_msg.date > end_date:
                        continue
                    
                    if self.db_manager.is_message_deleted(telegram_msg.id, group_id):
                        continue
                    
                    if telegram_msg.from_user:
                        await self.user_processor.process_user(telegram_msg.from_user)
                    
                    message = await self.message_processor.process_message(
                        telegram_msg,
                        group_id,
                        group.group_username
                    )
                    
                    if message:
                        self.db_manager.save_message(message)
                        message_count += 1
                        
                        if settings.settings.track_reactions:
                            await temp_reaction_processor.process_reactions(
                                telegram_msg,
                                group_id,
                                group.group_username,
                                message.message_link
                            )
                        
                        if message_callback:
                            message_callback(message)
                        
                        if progress_callback:
                            progress_callback(message_count, -1)
                    
                    if fetch_delay > 0:
                        await asyncio.sleep(fetch_delay)
                    
                except FloodWait as e:
                    logger.warning(f"FloodWait: waiting {e.value} seconds")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    logger.error(f"Error processing message {telegram_msg.id}: {e}")
                    continue
            
            total_messages = self.db_manager.get_message_count(group_id)
            temp_group_manager.update_group_stats(group, total_messages)
            
            logger.info(f"Fetched {message_count} messages from group {group_id} using account {credential.phone_number}")
            return True, message_count, None
            
        except Exception as e:
            logger.error(f"Error fetching messages with account: {e}")
            return False, 0, str(e)
        finally:
            # Clean up temporary client
            if temp_client:
                try:
                    await temp_client.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting temporary client: {e}")

