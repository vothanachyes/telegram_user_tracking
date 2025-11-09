"""
Group manager for Telegram group operations.
"""

import logging
from typing import Optional, Tuple
from datetime import datetime

from database.db_manager import DatabaseManager
from database.models import TelegramGroup
from services.telegram.group_photo_downloader import GroupPhotoDownloader

logger = logging.getLogger(__name__)


class GroupManager:
    """Manages Telegram group operations."""
    
    def __init__(self, db_manager: DatabaseManager, client, download_root_dir: str = "./downloads"):
        self.db_manager = db_manager
        self.client = client
        self.photo_downloader = GroupPhotoDownloader(download_root_dir)
    
    async def fetch_group_info(
        self,
        group_id: Optional[int] = None,
        invite_link: Optional[str] = None,
        username: Optional[str] = None,
        download_photo: bool = True
    ) -> Tuple[bool, Optional[TelegramGroup], Optional[str]]:
        """
        Fetch group information.
        
        Args:
            group_id: Group ID (optional if invite_link or username provided)
            invite_link: Invite link URL (optional if group_id or username provided)
            username: Group username without @ (optional if group_id or invite_link provided)
            download_photo: Whether to download group photo
            
        Returns:
            (success, group, error_message)
        """
        try:
            if not self.client:
                return False, None, "Not connected to Telegram"
            
            # Determine chat identifier - priority: invite_link > username > group_id
            # Telethon's get_entity accepts usernames (with or without @), invite links, and IDs
            if invite_link:
                chat_identifier = invite_link
            elif username:
                # Ensure username starts with @ for Telethon
                chat_identifier = username if username.startswith('@') else f"@{username}"
            elif group_id:
                chat_identifier = group_id
            else:
                return False, None, "Either group_id, invite_link, or username must be provided"

            logger.debug(f"Fetching group info with identifier: {chat_identifier} (type: {type(chat_identifier).__name__})")
            
            # Use the identifier directly - Telethon's get_entity() handles:
            # - Negative IDs like -1002529132546
            # - Invite links (https://t.me/joinchat/...)
            # - Usernames (@username or username)
            # 
            # IMPORTANT: For negative group IDs to work, the account must:
            # 1. Be a member of the group (not just accessed via invite link)
            # 2. Have the chat cached in Telethon's session
            # If get_entity() fails with "Peer id invalid", it means the account needs to join the group first
            
            # Handle positive integer IDs that might be group/channel IDs
            # Telethon treats positive integers as user IDs (PeerUser), so we need to try
            # converting to negative format for groups/channels
            entity = None
            if isinstance(chat_identifier, int) and chat_identifier > 0:
                # Try positive ID first (in case it's actually a user)
                try:
                    entity = await self.client.get_entity(chat_identifier)
                    # Check if it's actually a group/channel, not a user
                    from telethon.tl.types import User
                    if isinstance(entity, User):
                        # This is a user, not a group - try negative formats
                        logger.debug(f"Positive ID {chat_identifier} resolved to User, trying group/channel formats...")
                        entity = None
                except Exception as e:
                    error_str = str(e).lower()
                    if "peeruser" in error_str or "could not find the input entity for peeruser" in error_str:
                        # Telethon tried to resolve as user but failed - try group/channel formats
                        logger.debug(f"Positive ID {chat_identifier} was treated as PeerUser, trying group/channel formats...")
                    else:
                        raise
            
            # If entity is None, try alternative formats for group/channel IDs
            if entity is None and isinstance(chat_identifier, int) and chat_identifier > 0:
                # Try negative format for regular groups: -{id}
                try:
                    negative_id = -chat_identifier
                    logger.debug(f"Trying negative format: {negative_id}")
                    entity = await self.client.get_entity(negative_id)
                except Exception:
                    # Try supergroup/channel format: -100{id}
                    try:
                        supergroup_id = int(f"-100{chat_identifier}")
                        logger.debug(f"Trying supergroup format: {supergroup_id}")
                        entity = await self.client.get_entity(supergroup_id)
                    except Exception:
                        # If all formats fail, raise the original error
                        raise ValueError(
                            f"Could not resolve group ID {chat_identifier}. "
                            f"Telethon tried to resolve it as a user (PeerUser) but it doesn't exist. "
                            f"Please provide the group's invite link, username, or ensure the account is a member of the group."
                        )
            
            # If still None, try the original identifier (for negative IDs, usernames, links)
            if entity is None:
                entity = await self.client.get_entity(chat_identifier)
            
            # Determine the correct group ID format
            # Telethon returns entity.id which is already in the correct format
            # For channels/supergroups, Telethon returns negative IDs like -100{channel_id}
            # For regular groups, Telethon returns negative IDs like -{id}
            resolved_group_id = entity.id
            
            # Check if this is a channel or supergroup
            # Telethon uses type checking with telethon.tl.types
            is_channel_or_supergroup = False
            try:
                from telethon.tl.types import Channel, Chat
                is_channel_or_supergroup = isinstance(entity, Channel)
            except ImportError:
                # Fallback: check using hasattr
                is_channel_or_supergroup = (
                    hasattr(entity, 'broadcast') or 
                    hasattr(entity, 'megagroup') or
                    hasattr(entity, 'gigagroup')
                )
            
            # Telethon already returns IDs in the correct format
            # No conversion needed - entity.id is already in the correct format
            logger.debug(
                f"Group ID from Telethon: {resolved_group_id} "
                f"(type: {type(entity).__name__}, invite_link: {bool(invite_link)})"
            )
            
            # If we fetched via invite_link or username, try to ensure the group is accessible via group_id
            # by refreshing dialogs. This helps Telethon cache the group in its session
            # so the group_id can be used directly later
            if invite_link or username:
                fetch_method = "invite link" if invite_link else "username"
                logger.debug(
                    f"Group fetched via {fetch_method}. Resolved ID: {resolved_group_id} "
                    f"(entity.id: {entity.id}, is_supergroup: {is_channel_or_supergroup})"
                )
                try:
                    # Try to access the group using the resolved group_id to cache it
                    # This ensures Telethon recognizes the group_id for future use
                    test_entity = await self.client.get_entity(resolved_group_id)
                    logger.info(
                        f"Successfully cached group_id {resolved_group_id} in session. "
                        f"Entity type: {type(test_entity).__name__}"
                    )
                except Exception as cache_error:
                    # If direct access fails, try refreshing dialogs
                    logger.debug(
                        f"Direct access to group_id {resolved_group_id} failed: {cache_error}. "
                        f"Attempting to refresh dialogs to find group in session..."
                    )
                    try:
                        # Refresh dialogs to update session
                        # This ensures Telethon has the group in its dialog list
                        found_in_dialogs = False
                        async for dialog in self.client.iter_dialogs(limit=200):
                            # Check if this dialog matches our group
                            dialog_id = dialog.entity.id
                            if dialog_id == resolved_group_id:
                                logger.info(
                                    f"Group {resolved_group_id} found in dialogs! "
                                    f"Dialog ID: {dialog_id}, Chat: {dialog.name}"
                                )
                                found_in_dialogs = True
                                # Try to access it again after finding in dialogs
                                try:
                                    await self.client.get_entity(resolved_group_id)
                                    logger.info(f"Successfully accessed group {resolved_group_id} after dialog refresh")
                                except Exception as retry_error:
                                    logger.warning(f"Still cannot access group {resolved_group_id} after dialog refresh: {retry_error}")
                                break
                        
                        if not found_in_dialogs:
                            logger.warning(
                                f"Group {resolved_group_id} not found in dialogs. "
                                f"This may mean the account is not a member, or the group is not in the dialog list. "
                                f"Group_id may not work directly later - invite link may be needed."
                            )
                        else:
                            logger.debug(f"Refreshed dialogs and found group {resolved_group_id} in session")
                    except Exception as refresh_error:
                        logger.warning(
                            f"Could not refresh dialogs or cache group_id: {refresh_error}. "
                            f"Group was fetched via invite link but group_id may not work directly later."
                        )
            
            group = TelegramGroup(
                group_id=resolved_group_id,  # Use entity ID
                group_name=getattr(entity, 'title', None) or "Unknown Group",
                group_username=getattr(entity, 'username', None)
            )

            logger.debug(
                f"Created group: id={resolved_group_id}, name={group.group_name}, "
                f"username={group.group_username}, entity_id={entity.id}"
            )
            
            # Download group photo if requested
            if download_photo:
                photo_path = await self.photo_downloader.download_group_photo(
                    self.client,
                    resolved_group_id,  # Use converted ID
                    group.group_username
                )
                if photo_path:
                    group.group_photo_path = photo_path
            
            return True, group, None
            
        except Exception as e:
            error_str = str(e).lower()
            error_msg = str(e)
            
            # Handle specific Telethon errors
            if "peeruser" in error_str or "could not find the input entity for peeruser" in error_str:
                # Positive integer ID was treated as user ID but doesn't exist
                if group_id and group_id > 0:
                    error_msg = (
                        f"Group ID {group_id} was treated as a user ID. "
                        f"Please provide the group's invite link, username, or use the negative group ID format "
                        f"(e.g., -{group_id} or -100{group_id} for supergroups)."
                    )
                else:
                    error_msg = "Could not find the entity. Please provide an invite link, username, or ensure the account is a member."
                logger.warning(f"PeerUser error: {e}")
            elif "channel_invalid" in error_str:
                if invite_link:
                    error_msg = "Invalid invite link or account needs to join the group first. Please join the group using the invite link in Telegram, then try again."
                else:
                    error_msg = f"Account is not a member of this group. Please join the group first, then try again."
                logger.warning(f"Channel invalid error: {e}")
            elif "peer id invalid" in error_str:
                if invite_link:
                    error_msg = "Invalid invite link or account does not have access to this group"
                else:
                    error_msg = f"Invalid group ID or account does not have access to group {group_id}"
                logger.warning(f"Peer ID invalid error: {e}")
            elif "chat not found" in error_str or "not found" in error_str:
                error_msg = "Group not found or account is not a member"
            elif "forbidden" in error_str or "permission" in error_str:
                error_msg = "Permission denied. Account does not have access to this group"
            elif "unauthorized" in error_str or "expired" in error_str:
                error_msg = "Account session expired or invalid"
            
            logger.error(f"Error fetching group info: {e}")
            return False, None, error_msg
    
    def save_group(self, group: TelegramGroup):
        """Save group to database."""
        self.db_manager.save_group(group)
    
    def update_group_stats(self, group: TelegramGroup, message_count: int):
        """
        Update group statistics.
        
        Args:
            group: TelegramGroup object
            message_count: Total message count
        """
        group.last_fetch_date = datetime.now()
        group.total_messages = message_count
        self.db_manager.save_group(group)

