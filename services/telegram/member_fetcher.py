"""
Member fetcher service for importing Telegram group members.
"""

import asyncio
import logging
from typing import Optional, Callable, Tuple
from datetime import datetime, timedelta

from database.db_manager import DatabaseManager
from database.models import TelegramCredential, TelegramUser
from services.telegram.client_utils import ClientUtils
from services.telegram.user_processor import UserProcessor
from services.telegram.group_manager import GroupManager
from telethon.errors import FloodWaitError

logger = logging.getLogger(__name__)


class MemberFetcher:
    """Fetches and imports Telegram group members."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        client_utils: ClientUtils
    ):
        self.db_manager = db_manager
        self.client_utils = client_utils
        self.user_processor = UserProcessor(db_manager)
        self._cancelled = False
    
    def cancel(self):
        """Cancel the fetch operation."""
        self._cancelled = True
    
    async def fetch_members(
        self,
        group_id: int,
        rate_limit: float = 1.0,
        fetch_limit: Optional[int] = None,
        time_limit_minutes: Optional[int] = None,
        skip_deleted: bool = True,
        on_progress: Optional[Callable[[int, int, int, int], None]] = None,
        on_member: Optional[Callable[[object, str], None]] = None,
        cancellation_flag: Optional[Callable[[], bool]] = None
    ) -> Tuple[bool, int, int, int, Optional[str]]:
        """
        Fetch all members from a Telegram group.
        
        Args:
            group_id: Telegram group ID
            rate_limit: Delay in seconds between fetches
            fetch_limit: Maximum number of members to fetch (None = no limit)
            time_limit_minutes: Maximum time in minutes (None = no limit)
            skip_deleted: Skip users that are marked as deleted
            on_progress: Callback(fetched_count, skipped_exist_count, skipped_deleted_count, total_count)
            on_member: Callback(telegram_user, status) where status is 'fetched', 'skipped_exist', 'skipped_deleted'
            
        Returns:
            (success, fetched_count, skipped_exist_count, skipped_deleted_count, error_message)
        """
        self._cancelled = False
        temp_client = None
        
        try:
            # Get default credential
            credential = self.db_manager.get_default_credential()
            if not credential:
                return False, 0, 0, 0, "No Telegram account configured"
            
            # Create temporary client
            temp_client = await self.client_utils.create_temporary_client(credential)
            if not temp_client:
                return False, 0, 0, 0, "Failed to connect or session expired"
            
            # Get group entity
            group_manager = GroupManager(self.db_manager, temp_client)
            success, group, error = await group_manager.fetch_group_info(group_id=group_id)
            if not success:
                return False, 0, 0, 0, error or "Failed to fetch group info"
            
            # Get group entity for iter_participants
            try:
                entity = await temp_client.get_entity(group_id)
            except Exception as e:
                logger.error(f"Error getting group entity: {e}")
                return False, 0, 0, 0, f"Failed to access group: {str(e)}"
            
            # Initialize counters
            fetched_count = 0
            skipped_exist_count = 0
            skipped_deleted_count = 0
            total_count = 0
            
            # Calculate end time if time limit is set
            end_time = None
            if time_limit_minutes:
                end_time = datetime.now() + timedelta(minutes=time_limit_minutes)
            
            # Fetch members using iter_participants with aggressive mode
            try:
                async for user in temp_client.iter_participants(entity, aggressive=True):
                    # Check cancellation
                    if self._cancelled or (cancellation_flag and cancellation_flag()):
                        logger.info("Member fetch cancelled by user")
                        break
                    
                    # Check time limit
                    if end_time and datetime.now() >= end_time:
                        logger.info("Member fetch stopped: time limit reached")
                        break
                    
                    # Check fetch limit
                    if fetch_limit and total_count >= fetch_limit:
                        logger.info("Member fetch stopped: fetch limit reached")
                        break
                    
                    total_count += 1
                    
                    # Skip bots (optional - you can make this configurable)
                    if getattr(user, 'bot', False):
                        continue
                    
                    # Process user
                    existing = self.db_manager.get_user_by_id(user.id)
                    
                    # Check if user is deleted
                    user_was_deleted = False
                    if existing and existing.is_deleted:
                        if skip_deleted:
                            skipped_deleted_count += 1
                            if on_member:
                                on_member(user, 'skipped_deleted')
                            if on_progress:
                                on_progress(fetched_count, skipped_exist_count, skipped_deleted_count, total_count)
                            # Apply rate limit
                            if rate_limit > 0:
                                await asyncio.sleep(rate_limit)
                            continue
                        else:
                            # Mark that we need to restore this user
                            user_was_deleted = True
                    
                    # Check if user already exists (and not deleted) - skip if already exists and not deleted
                    if existing and not existing.is_deleted and not user_was_deleted:
                        skipped_exist_count += 1
                        if on_member:
                            on_member(user, 'skipped_exist')
                    else:
                        # Process and save new user (or update existing/restored user)
                        try:
                            # Build full name
                            first_name = getattr(user, 'first_name', None) or ""
                            last_name = getattr(user, 'last_name', None) or ""
                            full_name = f"{first_name} {last_name}".strip() or "Unknown User"
                            
                            telegram_user = TelegramUser(
                                user_id=user.id,
                                username=getattr(user, 'username', None),
                                first_name=first_name,
                                last_name=last_name if last_name else None,
                                full_name=full_name,
                                phone=getattr(user, 'phone', None),
                                bio=getattr(user, 'about', None)
                            )
                            
                            # Save or update user
                            result = self.db_manager.save_user(telegram_user)
                            if result:
                                # If user was deleted, restore it
                                if user_was_deleted:
                                    with self.db_manager.get_connection() as conn:
                                        conn.execute(
                                            "UPDATE telegram_users SET is_deleted = 0 WHERE user_id = ?",
                                            (user.id,)
                                        )
                                        conn.commit()
                                    logger.debug(f"Restored and saved user {user.id}: {full_name}")
                                
                                # Record user-group relationship
                                try:
                                    self.db_manager.save_user_group(
                                        user_id=user.id,
                                        group_id=group.group_id,
                                        group_name=group.group_name,
                                        group_username=group.group_username
                                    )
                                except Exception as e:
                                    logger.warning(f"Failed to save user-group relationship: {e}")
                                else:
                                    logger.debug(f"Saved user {user.id}: {full_name}")
                                
                                fetched_count += 1
                            else:
                                logger.warning(f"Failed to save user {user.id}: {full_name}")
                            
                            if on_member:
                                on_member(user, 'fetched')
                        except Exception as e:
                            logger.error(f"Error processing member {user.id}: {e}", exc_info=True)
                            # Continue with next user
                    
                    # Update progress
                    if on_progress:
                        on_progress(fetched_count, skipped_exist_count, skipped_deleted_count, total_count)
                    
                    # Apply rate limiting
                    if rate_limit > 0:
                        await asyncio.sleep(rate_limit)
                
            except FloodWaitError as e:
                wait_time = e.seconds
                error_msg = f"Rate limit: wait {wait_time} seconds"
                logger.warning(error_msg)
                return False, fetched_count, skipped_exist_count, skipped_deleted_count, error_msg
            except Exception as e:
                logger.error(f"Error fetching members: {e}")
                return False, fetched_count, skipped_exist_count, skipped_deleted_count, str(e)
            
            return True, fetched_count, skipped_exist_count, skipped_deleted_count, None
            
        except Exception as e:
            logger.error(f"Error in fetch_members: {e}")
            return False, 0, 0, 0, str(e)
        finally:
            # Always disconnect temporary client
            if temp_client:
                try:
                    await temp_client.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting temporary client: {e}")

