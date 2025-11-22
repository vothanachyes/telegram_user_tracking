"""
Common groups fetcher service for discovering groups shared between authenticated account and selected users.
"""

import asyncio
import logging
from typing import Optional, Callable, Tuple, List
from datetime import datetime, timedelta

from database.db_manager import DatabaseManager
from database.models import TelegramCredential
from services.telegram.client_utils import ClientUtils
from services.telegram.group_manager import GroupManager
from telethon.errors import FloodWaitError
from telethon.tl.types import Channel, Chat

logger = logging.getLogger(__name__)


class CommonGroupsFetcher:
    """Fetches common groups between authenticated account and selected users."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        client_utils: ClientUtils
    ):
        self.db_manager = db_manager
        self.client_utils = client_utils
        self._cancelled = False
    
    def cancel(self):
        """Cancel the fetch operation."""
        self._cancelled = True
    
    async def fetch_common_groups(
        self,
        credential: TelegramCredential,
        user_ids: List[int],
        rate_limit: float = 1.0,
        time_limit_minutes: Optional[int] = None,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        cancellation_flag: Optional[Callable[[], bool]] = None
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Fetch common groups between authenticated account and selected users.
        
        Args:
            credential: Telegram credential for authenticated account
            user_ids: List of user IDs to check for common groups
            rate_limit: Delay in seconds between group checks
            time_limit_minutes: Maximum time in minutes (None = no limit)
            on_progress: Callback(processed_groups, found_groups, current_group_name)
            cancellation_flag: Callable that returns True if operation should be cancelled
            
        Returns:
            (success, fetched_count, error_message)
        """
        self._cancelled = False
        temp_client = None
        
        try:
            # Create temporary client
            temp_client = await self.client_utils.create_temporary_client(credential)
            if not temp_client:
                return False, 0, "Failed to connect or session expired"
            
            # Initialize counters
            processed_groups = 0
            found_groups = 0
            
            # Calculate end time if time limit is set
            end_time = None
            if time_limit_minutes:
                end_time = datetime.now() + timedelta(minutes=time_limit_minutes)
            
            # Get all dialogs (groups/channels) from authenticated account
            try:
                async for dialog in temp_client.iter_dialogs():
                    # Check cancellation
                    if self._cancelled or (cancellation_flag and cancellation_flag()):
                        logger.info("Common groups fetch cancelled by user")
                        break
                    
                    # Check time limit
                    if end_time and datetime.now() >= end_time:
                        logger.info("Common groups fetch stopped: time limit reached")
                        break
                    
                    # Only process groups/channels (not private chats)
                    entity = dialog.entity
                    if not isinstance(entity, (Channel, Chat)):
                        continue
                    
                    # Skip if it's not a group (broadcast channels don't have participants)
                    if isinstance(entity, Channel) and entity.broadcast:
                        continue
                    
                    # Get group info
                    group_id = abs(entity.id)
                    group_name = getattr(entity, 'title', None) or "Unknown Group"
                    group_username = getattr(entity, 'username', None)
                    
                    processed_groups += 1
                    
                    # Update progress
                    if on_progress:
                        on_progress(processed_groups, found_groups, group_name)
                    
                    # Check if any of the selected users are members of this group
                    try:
                        # Get participants for this group
                        participants = []
                        async for participant in temp_client.iter_participants(entity, limit=1000):
                            participants.append(participant.id)
                        
                        # Check if any selected user is in this group
                        common_users = [uid for uid in user_ids if uid in participants]
                        
                        if common_users:
                            # Save user-group relationships for all common users
                            for user_id in common_users:
                                try:
                                    self.db_manager.save_user_group(
                                        user_id=user_id,
                                        group_id=group_id,
                                        group_name=group_name,
                                        group_username=group_username
                                    )
                                except Exception as e:
                                    logger.warning(f"Failed to save user-group relationship for user {user_id} in group {group_id}: {e}")
                            
                            found_groups += 1
                            logger.debug(f"Found common group: {group_name} ({len(common_users)} users)")
                    
                    except Exception as e:
                        logger.warning(f"Error checking participants for group {group_name}: {e}")
                        # Continue with next group
                    
                    # Apply rate limiting
                    if rate_limit > 0:
                        await asyncio.sleep(rate_limit)
                
            except FloodWaitError as e:
                wait_time = e.seconds
                error_msg = f"Rate limit: wait {wait_time} seconds"
                logger.warning(error_msg)
                return False, found_groups, error_msg
            except Exception as e:
                logger.error(f"Error fetching common groups: {e}")
                return False, found_groups, str(e)
            
            return True, found_groups, None
            
        except Exception as e:
            logger.error(f"Error in fetch_common_groups: {e}")
            return False, 0, str(e)
        finally:
            # Always disconnect temporary client
            if temp_client:
                try:
                    await temp_client.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting temporary client: {e}")

