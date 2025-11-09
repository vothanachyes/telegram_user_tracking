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
        download_photo: bool = True
    ) -> Tuple[bool, Optional[TelegramGroup], Optional[str]]:
        """
        Fetch group information.
        
        Args:
            group_id: Group ID (optional if invite_link provided)
            invite_link: Invite link URL (optional if group_id provided)
            download_photo: Whether to download group photo
            
        Returns:
            (success, group, error_message)
        """
        try:
            if not self.client:
                return False, None, "Not connected to Telegram"
            
            # Use invite link or group_id - Pyrogram's get_chat accepts both
            chat_identifier = invite_link if invite_link else group_id

            logger.debug(f"Fetching group info with identifier: {chat_identifier} (type: {type(chat_identifier).__name__})")
            
            if not chat_identifier:
                return False, None, "Either group_id or invite_link must be provided"
            
            # Use the identifier directly - Pyrogram's get_chat() handles both formats
            # For negative IDs like -1002529132546, Pyrogram will extract the channel_id internally
            # For invite links, Pyrogram resolves them directly
            # 
            # IMPORTANT: For negative group IDs to work, the account must:
            # 1. Be a member of the group (not just accessed via invite link)
            # 2. Have the chat cached in Pyrogram's session
            # If get_chat() fails with "Peer id invalid", it means the account needs to join the group first
            chat = await self.client.get_chat(chat_identifier)
            
            # Determine the correct group ID format
            # For channels/supergroups, Pyrogram returns positive channel_id
            # but we need the full group ID format: -100{channel_id}
            # For regular groups, Pyrogram may return positive ID that needs to be negated
            resolved_group_id = chat.id
            
            # Check if this is a channel or supergroup
            # Pyrogram's Chat object has type attribute
            is_channel_or_supergroup = False
            try:
                from pyrogram.enums import ChatType
                is_channel_or_supergroup = (
                    chat.type == ChatType.CHANNEL or 
                    chat.type == ChatType.SUPERGROUP
                )
            except (ImportError, AttributeError):
                # Fallback: check using hasattr for older Pyrogram versions
                is_channel_or_supergroup = (
                    hasattr(chat, 'is_channel') and chat.is_channel
                ) or (
                    hasattr(chat, 'is_supergroup') and chat.is_supergroup
                )
            
            # Convert channel_id to full group ID format if needed
            if is_channel_or_supergroup and resolved_group_id > 0:
                # Convert: 2529132546 -> -1002529132546
                # Format: -100{channel_id} (string concatenation, not math)
                resolved_group_id = int(f"-100{resolved_group_id}")
                logger.debug(
                    f"Converted channel_id {chat.id} to full group ID {resolved_group_id} "
                    f"(type: {getattr(chat, 'type', 'unknown')}, invite_link: {bool(invite_link)})"
                )
            elif resolved_group_id > 0 and not is_channel_or_supergroup:
                # Regular group with positive ID - convert to negative format
                # Regular groups use -{id} format (NOT -100{id})
                # Example: 4703210976 -> -4703210976
                resolved_group_id = -resolved_group_id
                logger.debug(
                    f"Converted regular group ID {chat.id} to negative format {resolved_group_id} "
                    f"(type: {getattr(chat, 'type', 'unknown')}, invite_link: {bool(invite_link)})"
                )
            # If resolved_group_id is already negative, keep it as is
            # (could be -4703210976 for regular group or -1004703210976 for supergroup)
            
            # If we fetched via invite_link, try to ensure the group is accessible via group_id
            # by refreshing dialogs. This helps Pyrogram cache the group in its session
            # so the group_id can be used directly later (similar to how Telethon works)
            if invite_link:
                logger.debug(
                    f"Group fetched via invite link. Resolved ID: {resolved_group_id} "
                    f"(original chat.id: {chat.id}, is_supergroup: {is_channel_or_supergroup})"
                )
                try:
                    # Try to access the group using the resolved group_id to cache it
                    # This ensures Pyrogram recognizes the group_id for future use
                    test_chat = await self.client.get_chat(resolved_group_id)
                    logger.info(
                        f"Successfully cached group_id {resolved_group_id} in session. "
                        f"Chat type: {getattr(test_chat, 'type', 'unknown')}"
                    )
                except Exception as cache_error:
                    # If direct access fails, try refreshing dialogs
                    logger.debug(
                        f"Direct access to group_id {resolved_group_id} failed: {cache_error}. "
                        f"Attempting to refresh dialogs to find group in session..."
                    )
                    try:
                        # Refresh dialogs to update session (similar to Telethon's behavior)
                        # This ensures Pyrogram has the group in its dialog list
                        found_in_dialogs = False
                        async for dialog in self.client.get_dialogs(limit=200):
                            # Check if this dialog matches our group (handle both positive and negative IDs)
                            dialog_id = dialog.chat.id
                            if (dialog_id == resolved_group_id or 
                                abs(dialog_id) == abs(resolved_group_id) or
                                (resolved_group_id < 0 and dialog_id > 0 and abs(dialog_id) == abs(resolved_group_id))):
                                logger.info(
                                    f"Group {resolved_group_id} found in dialogs! "
                                    f"Dialog ID: {dialog_id}, Chat: {dialog.chat.title}"
                                )
                                found_in_dialogs = True
                                # Try to access it again after finding in dialogs
                                try:
                                    await self.client.get_chat(resolved_group_id)
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
                group_id=resolved_group_id,  # Use converted ID
                group_name=chat.title or "Unknown Group",
                group_username=chat.username
            )

            logger.debug(
                f"Created group: id={resolved_group_id}, name={group.group_name}, "
                f"username={group.group_username}, original_chat_id={chat.id}"
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
            
            # Handle specific Pyrogram errors
            if "channel_invalid" in error_str:
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

