"""
Message fetcher for fetching messages from Telegram groups.
"""

import logging
import asyncio
from typing import Optional, Callable, Tuple
from datetime import datetime, timezone

try:
    from telethon.errors import FloodWaitError
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    FloodWaitError = None

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


def _normalize_to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Normalize a datetime to UTC timezone.
    If datetime is naive, assume it's in local timezone and convert to UTC.
    If datetime is timezone-aware, convert to UTC.
    
    Args:
        dt: Datetime to normalize (can be None)
        
    Returns:
        UTC timezone-aware datetime or None
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # Naive datetime - assume local timezone and convert to UTC
        # For date-only comparisons, we'll treat it as UTC midnight
        return dt.replace(tzinfo=timezone.utc)
    else:
        # Timezone-aware datetime - convert to UTC
        return dt.astimezone(timezone.utc)


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
        message_callback: Optional[Callable[[Message], None]] = None,
        delay_callback: Optional[Callable[[float, str], None]] = None
    ) -> Tuple[bool, int, Optional[str], int]:
        """
        Fetch messages from a group using temporary client (connect on demand).
        Returns (success, message_count, error_message, skipped_count)
        """
        # Check if device is revoked before starting fetch
        try:
            from services.device_manager_service import device_manager_service
            from services.auth_service import auth_service
            current_user = auth_service.get_current_user()
            if current_user:
                uid = current_user.get("uid")
                if uid:
                    is_revoked, error_msg = device_manager_service.check_device_status(uid)
                    if is_revoked:
                        logger.warning("Device is revoked, cannot fetch messages")
                        return False, 0, error_msg or "Device has been revoked. Please contact admin.", 0
        except Exception as e:
            logger.error(f"Error checking device status: {e}", exc_info=True)
            # Continue with fetch if check fails
        
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
            
            # Get account info (static copy to avoid losing reference if account deleted)
            account_full_name = None
            account_username = None
            try:
                me = await temp_client.get_me()
                if me:
                    account_full_name = f"{me.first_name or ''} {me.last_name or ''}".strip() or "Unknown"
                    account_username = me.username
            except Exception as e:
                logger.warning(f"Could not get account info: {e}")
            
            message_count = 0
            unique_users = set()  # Track unique users in this fetch
            media_count = 0  # Track media files in this fetch
            sticker_count = 0
            photo_count = 0
            video_count = 0
            document_count = 0
            audio_count = 0
            link_count = 0
            fetch_delay = settings.settings.fetch_delay_seconds
            
            # Normalize dates to UTC for comparison (fixes timezone-aware vs naive datetime issue)
            normalized_start_date = _normalize_to_utc(start_date)
            normalized_end_date = _normalize_to_utc(end_date)
            
            # Log fetch parameters for debugging
            logger.debug(f"Starting fetch for group {group_id} with start_date={start_date}, end_date={end_date}")
            if start_date:
                logger.debug(f"start_date timezone-aware: {start_date.tzinfo is not None}, normalized={normalized_start_date}")
            if end_date:
                logger.debug(f"end_date timezone-aware: {end_date.tzinfo is not None}, normalized={normalized_end_date}")
            
            # Get entity for iter_messages
            entity = await temp_client.get_entity(group_id)
            processed_count = 0
            skipped_count = 0
            
            # Use offset_date to start from start_date (more efficient than filtering all messages)
            iter_kwargs = {"reverse": True}
            if normalized_start_date:
                iter_kwargs["offset_date"] = normalized_start_date
            
            async for telegram_msg in temp_client.iter_messages(entity, **iter_kwargs):
                try:
                    processed_count += 1
                    
                    # Normalize message date to UTC for comparison
                    msg_date = telegram_msg.date
                    normalized_msg_date = _normalize_to_utc(msg_date)
                    
                    # Log datetime comparison details for debugging (first few messages only)
                    if processed_count <= 5 or (normalized_start_date or normalized_end_date):
                        logger.debug(
                            f"Message {telegram_msg.id}: date={msg_date}, "
                            f"normalized_date={normalized_msg_date}, "
                            f"start_date={normalized_start_date}, "
                            f"end_date={normalized_end_date}"
                        )
                    
                    # With reverse=True and offset_date, Telethon starts from start_date and goes forward
                    # We still need to check end_date and break when exceeded
                    if normalized_end_date:
                        if normalized_msg_date > normalized_end_date:
                            logger.debug(f"Message {telegram_msg.id} after end_date, breaking")
                            break
                    
                    # If we used offset_date, messages should already be >= start_date
                    # But keep this check as a safety net (shouldn't be needed with offset_date)
                    if normalized_start_date:
                        if normalized_msg_date < normalized_start_date:
                            logger.debug(f"Message {telegram_msg.id} before start_date, skipping (unexpected with offset_date)")
                            skipped_count += 1
                            continue
                    
                    if self.db_manager.is_message_deleted(telegram_msg.id, group_id):
                        continue
                    
                    # Check if message already exists in database
                    if self.db_manager.message_exists(telegram_msg.id, group_id):
                        skipped_count += 1
                        continue
                    
                    if telegram_msg.sender:
                        await self.user_processor.process_user(telegram_msg.sender)
                        unique_users.add(telegram_msg.sender.id)
                        
                        # Record user-group relationship
                        try:
                            self.db_manager.save_user_group(
                                user_id=telegram_msg.sender.id,
                                group_id=group_id,
                                group_name=group.group_name,
                                group_username=group.group_username
                            )
                        except Exception as e:
                            logger.warning(f"Failed to save user-group relationship: {e}")
                    
                    message = await self.message_processor.process_message(
                        telegram_msg,
                        group_id,
                        group.group_username
                    )
                    
                    if message:
                        self.db_manager.save_message(message)
                        message_count += 1
                        
                        # Count media files
                        if message.has_media:
                            media_files = self.db_manager.get_media_for_message(message.message_id)
                            media_count += len(media_files) if media_files else 0
                        
                        # Count message types (avoid double counting)
                        if message.has_sticker or (message.message_type and message.message_type == 'sticker'):
                            sticker_count += 1
                        if message.has_link:
                            link_count += 1
                        
                        # Count media types (prioritize media_type, fallback to message_type)
                        if message.media_type:
                            if message.media_type == 'photo':
                                photo_count += 1
                            elif message.media_type == 'video':
                                video_count += 1
                            elif message.media_type == 'document':
                                document_count += 1
                            elif message.media_type == 'audio':
                                audio_count += 1
                        elif message.message_type and not message.has_sticker:
                            # Fallback to message_type if media_type not set (skip if already counted as sticker)
                            if message.message_type == 'photo':
                                photo_count += 1
                            elif message.message_type == 'video':
                                video_count += 1
                            elif message.message_type == 'document':
                                document_count += 1
                            elif message.message_type in ('audio', 'voice'):
                                audio_count += 1
                        
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
                        # Show countdown if callback provided
                        if delay_callback:
                            await delay_callback(fetch_delay, "Rate limit delay")
                        else:
                            await asyncio.sleep(fetch_delay)
                    
                except FloodWaitError as e:
                    logger.warning(f"FloodWait: waiting {e.seconds} seconds")
                    # Show countdown for flood wait
                    if delay_callback:
                        await delay_callback(e.seconds, "Flood wait")
                    else:
                        await asyncio.sleep(e.seconds)
                except Exception as e:
                    logger.error(
                        f"Error processing message {telegram_msg.id}: {e}. "
                        f"Message date: {telegram_msg.date if hasattr(telegram_msg, 'date') else 'N/A'}"
                    )
                    continue
            
            logger.debug(
                f"Fetch iteration complete: processed={processed_count}, "
                f"saved={message_count}, skipped={skipped_count}, "
                f"unique_users={len(unique_users)}"
            )
            
            total_messages = self.db_manager.get_message_count(group_id)
            temp_group_manager.update_group_stats(group, total_messages)
            
            # Save fetch history with account info and summary
            if start_date and end_date:
                from database.models.telegram import GroupFetchHistory
                account_phone = credential.phone_number if credential else None
                fetch_history = GroupFetchHistory(
                    group_id=group_id,
                    start_date=start_date,
                    end_date=end_date,
                    message_count=message_count,
                    account_phone_number=account_phone,
                    account_full_name=account_full_name,
                    account_username=account_username,
                    total_users_fetched=len(unique_users),
                    total_media_fetched=media_count,
                    total_stickers=sticker_count,
                    total_photos=photo_count,
                    total_videos=video_count,
                    total_documents=document_count,
                    total_audio=audio_count,
                    total_links=link_count
                )
                self.db_manager.save_fetch_history(fetch_history)
            
            logger.info(f"Fetched {message_count} messages from group {group_id} (processed: {processed_count}, skipped: {skipped_count})")
            # Return (success, message_count, error_message, skipped_count)
            return True, message_count, None, skipped_count
            
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return False, 0, str(e), 0
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
        message_callback: Optional[Callable[[Message], None]] = None,
        delay_callback: Optional[Callable[[float, str], None]] = None
    ) -> Tuple[bool, int, Optional[str], int]:
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
            
            # Get account info (static copy to avoid losing reference if account deleted)
            account_full_name = None
            account_username = None
            try:
                me = await temp_client.get_me()
                if me:
                    account_full_name = f"{me.first_name or ''} {me.last_name or ''}".strip() or "Unknown"
                    account_username = me.username
            except Exception as e:
                logger.warning(f"Could not get account info: {e}")
            
            message_count = 0
            unique_users = set()  # Track unique users in this fetch
            media_count = 0  # Track media files in this fetch
            sticker_count = 0
            photo_count = 0
            video_count = 0
            document_count = 0
            audio_count = 0
            link_count = 0
            fetch_delay = settings.settings.fetch_delay_seconds
            
            # Normalize dates to UTC for comparison (fixes timezone-aware vs naive datetime issue)
            normalized_start_date = _normalize_to_utc(start_date)
            normalized_end_date = _normalize_to_utc(end_date)
            
            # Log fetch parameters for debugging
            logger.debug(
                f"Starting fetch for group {group_id} using account {credential.phone_number} "
                f"with start_date={start_date}, end_date={end_date}"
            )
            if start_date:
                logger.debug(f"start_date timezone-aware: {start_date.tzinfo is not None}, normalized={normalized_start_date}")
            if end_date:
                logger.debug(f"end_date timezone-aware: {end_date.tzinfo is not None}, normalized={normalized_end_date}")
            
            # Get entity for iter_messages
            entity = await temp_client.get_entity(group_id)
            logger.debug(f"Entity: {entity}")
            processed_count = 0
            skipped_count = 0
            
            # Use offset_date to start from start_date (more efficient than filtering all messages)
            iter_kwargs = {"reverse": True}
            if normalized_start_date:
                iter_kwargs["offset_date"] = normalized_start_date
            
            async for telegram_msg in temp_client.iter_messages(entity, **iter_kwargs):
                try:
                    processed_count += 1
                    
                    # Normalize message date to UTC for comparison
                    msg_date = telegram_msg.date
                    normalized_msg_date = _normalize_to_utc(msg_date)
                    
                    # Log datetime comparison details for debugging (first few messages only)
                    if processed_count <= 5 or (normalized_start_date or normalized_end_date):
                        logger.debug(
                            f"Message {telegram_msg.id}: date={msg_date}, "
                            f"normalized_date={normalized_msg_date}, "
                            f"start_date={normalized_start_date}, "
                            f"end_date={normalized_end_date}"
                        )
                    
                    # With reverse=True and offset_date, Telethon starts from start_date and goes forward
                    # We still need to check end_date and break when exceeded
                    if normalized_end_date:
                        if normalized_msg_date > normalized_end_date:
                            logger.debug(f"Message {telegram_msg.id} after end_date, breaking")
                            break
                    
                    # If we used offset_date, messages should already be >= start_date
                    # But keep this check as a safety net (shouldn't be needed with offset_date)
                    if normalized_start_date:
                        if normalized_msg_date < normalized_start_date:
                            logger.debug(f"Message {telegram_msg.id} before start_date, skipping (unexpected with offset_date)")
                            skipped_count += 1
                            continue
                    
                    if self.db_manager.is_message_deleted(telegram_msg.id, group_id):
                        continue
                    
                    # Check if message already exists in database
                    if self.db_manager.message_exists(telegram_msg.id, group_id):
                        skipped_count += 1
                        continue
                    
                    if telegram_msg.sender:
                        await self.user_processor.process_user(telegram_msg.sender)
                        unique_users.add(telegram_msg.sender.id)
                        
                        # Record user-group relationship
                        try:
                            self.db_manager.save_user_group(
                                user_id=telegram_msg.sender.id,
                                group_id=group_id,
                                group_name=group.group_name,
                                group_username=group.group_username
                            )
                        except Exception as e:
                            logger.warning(f"Failed to save user-group relationship: {e}")
                    
                    message = await self.message_processor.process_message(
                        telegram_msg,
                        group_id,
                        group.group_username
                    )
                    
                    if message:
                        self.db_manager.save_message(message)
                        message_count += 1
                        
                        # Count media files
                        if message.has_media:
                            media_files = self.db_manager.get_media_for_message(message.message_id)
                            media_count += len(media_files) if media_files else 0
                        
                        # Count message types (avoid double counting)
                        if message.has_sticker or (message.message_type and message.message_type == 'sticker'):
                            sticker_count += 1
                        if message.has_link:
                            link_count += 1
                        
                        # Count media types (prioritize media_type, fallback to message_type)
                        if message.media_type:
                            if message.media_type == 'photo':
                                photo_count += 1
                            elif message.media_type == 'video':
                                video_count += 1
                            elif message.media_type == 'document':
                                document_count += 1
                            elif message.media_type == 'audio':
                                audio_count += 1
                        elif message.message_type and not message.has_sticker:
                            # Fallback to message_type if media_type not set (skip if already counted as sticker)
                            if message.message_type == 'photo':
                                photo_count += 1
                            elif message.message_type == 'video':
                                video_count += 1
                            elif message.message_type == 'document':
                                document_count += 1
                            elif message.message_type in ('audio', 'voice'):
                                audio_count += 1
                        
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
                        # Show countdown if callback provided
                        if delay_callback:
                            await delay_callback(fetch_delay, "Rate limit delay")
                        else:
                            await asyncio.sleep(fetch_delay)
                    
                except FloodWaitError as e:
                    logger.warning(f"FloodWait: waiting {e.seconds} seconds")
                    # Show countdown for flood wait
                    if delay_callback:
                        await delay_callback(e.seconds, "Flood wait")
                    else:
                        await asyncio.sleep(e.seconds)
                except Exception as e:
                    logger.error(
                        f"Error processing message {telegram_msg.id}: {e}. "
                        f"Message date: {telegram_msg.date if hasattr(telegram_msg, 'date') else 'N/A'}"
                    )
                    continue
            
            logger.debug(
                f"Fetch iteration complete: processed={processed_count}, "
                f"saved={message_count}, skipped={skipped_count}, "
                f"unique_users={len(unique_users)}"
            )
            
            total_messages = self.db_manager.get_message_count(group_id)
            temp_group_manager.update_group_stats(group, total_messages)
            
            # Save fetch history with account info and summary
            if start_date and end_date:
                from database.models.telegram import GroupFetchHistory
                fetch_history = GroupFetchHistory(
                    group_id=group_id,
                    start_date=start_date,
                    end_date=end_date,
                    message_count=message_count,
                    account_phone_number=credential.phone_number,
                    account_full_name=account_full_name,
                    account_username=account_username,
                    total_users_fetched=len(unique_users),
                    total_media_fetched=media_count,
                    total_stickers=sticker_count,
                    total_photos=photo_count,
                    total_videos=video_count,
                    total_documents=document_count,
                    total_audio=audio_count,
                    total_links=link_count
                )
                self.db_manager.save_fetch_history(fetch_history)
            
            logger.info(f"Fetched {message_count} messages from group {group_id} using account {credential.phone_number} (processed: {processed_count}, skipped: {skipped_count})")
            # Return (success, message_count, error_message, skipped_count)
            return True, message_count, None, skipped_count
            
        except Exception as e:
            logger.error(f"Error fetching messages with account: {e}")
            return False, 0, str(e), 0
        finally:
            # Clean up temporary client
            if temp_client:
                try:
                    await temp_client.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting temporary client: {e}")

