"""
Group Info Utility - Get Telegram group information by invite link, username, or ID.
"""
import asyncio
import json
import logging
import re
from typing import Optional, Dict, Any
from telethon import TelegramClient, errors
from telethon.tl.types import Channel, Chat, User
from config import Config

logger = logging.getLogger(__name__)


class GroupInfoFetcher:
    """Fetches group information from Telegram."""
    
    def __init__(self, client: TelegramClient):
        self.client = client
    
    def parse_input(self, user_input: str) -> Dict[str, Optional[str]]:
        """
        Parse user input to determine if it's an invite link, username, or ID.
        
        Args:
            user_input: User input string (invite link, username, or ID)
            
        Returns:
            Dictionary with parsed information
        """
        result = {
            'invite_link': None,
            'username': None,
            'group_id': None,
            'raw_input': user_input.strip()
        }
        
        user_input = user_input.strip()
        
        # Check if it's an invite link (joinchat or + format)
        invite_patterns = [
            r'(?:https?://)?(?:t\.me/joinchat/|t\.me/\+)([A-Za-z0-9_-]+)',
            r'(?:https?://)?(?:telegram\.me/joinchat/|telegram\.me/\+)([A-Za-z0-9_-]+)',
            r'joinchat/([A-Za-z0-9_-]+)',
            r'\+([A-Za-z0-9_-]+)',
        ]
        
        for pattern in invite_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                # Reconstruct full invite link
                invite_code = match.group(1)
                result['invite_link'] = f"https://t.me/joinchat/{invite_code}"
                return result
        
        # Check if it's a username (t.me/username format)
        username_patterns = [
            r'(?:https?://)?(?:t\.me/|telegram\.me/)([a-zA-Z0-9_]{5,32})(?:/.*)?$',
        ]
        
        for pattern in username_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                username = match.group(1)
                if username not in ['joinchat', '+']:
                    result['username'] = username
                    return result
        
        # Check if it's a username starting with @
        if user_input.startswith('@'):
            username = user_input[1:].strip()
            if re.match(r'^[a-zA-Z0-9_]{5,32}$', username):
                result['username'] = username
                return result
        
        # Check if it's a numeric ID (can be negative)
        cleaned_id = user_input.lstrip('-+')
        if cleaned_id.isdigit():
            result['group_id'] = int(user_input)
            return result
        
        # If no pattern matches, treat as username (if it looks like one)
        if re.match(r'^[a-zA-Z0-9_]{5,32}$', user_input):
            result['username'] = user_input
            return result
        
        return result
    
    async def get_group_by_invite_link(self, invite_link: str) -> Optional[Any]:
        """Get group entity by invite link."""
        try:
            entity = await self.client.get_entity(invite_link)
            return entity
        except Exception as e:
            logger.error(f"Error getting group by invite link: {e}")
            return None
    
    async def get_group_by_username(self, username: str) -> Optional[Any]:
        """Get group entity by username."""
        try:
            # Remove @ if present
            username = username.lstrip('@')
            entity = await self.client.get_entity(username)
            return entity
        except Exception as e:
            logger.error(f"Error getting group by username: {e}")
            return None
    
    async def get_group_by_id(self, group_id: int) -> Optional[Any]:
        """Get group entity by ID."""
        try:
            entity = await self.client.get_entity(group_id)
            return entity
        except Exception as e:
            logger.error(f"Error getting group by ID: {e}")
            return None
    
    async def fetch_group_info(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Fetch group information based on user input.
        
        Args:
            user_input: Invite link, username, or group ID
            
        Returns:
            Dictionary with group information or None if not found
        """
        parsed = self.parse_input(user_input)
        entity = None
        
        # Try to get entity based on parsed input
        if parsed['invite_link']:
            logger.info("🔗 Detected invite link, fetching group...")
            entity = await self.get_group_by_invite_link(parsed['invite_link'])
        elif parsed['username']:
            logger.info(f"👤 Detected username: @{parsed['username']}, fetching group...")
            entity = await self.get_group_by_username(parsed['username'])
        elif parsed['group_id']:
            logger.info(f"🆔 Detected group ID: {parsed['group_id']}, fetching group...")
            entity = await self.get_group_by_id(parsed['group_id'])
        else:
            logger.error("❌ Could not parse input. Please provide invite link, username, or group ID.")
            return None
        
        if not entity:
            logger.error("❌ Group not found or access denied.")
            return None
        
        # Extract group information
        info = {
            'id': entity.id,
            'title': getattr(entity, 'title', None),
            'username': getattr(entity, 'username', None),
            'access_hash': getattr(entity, 'access_hash', None),
            'type': type(entity).__name__,
        }
        
        # Add channel-specific information
        if isinstance(entity, Channel):
            info.update({
                'is_broadcast': entity.broadcast,
                'is_megagroup': entity.megagroup,
                'is_gigagroup': getattr(entity, 'gigagroup', False),
                'participants_count': getattr(entity, 'participants_count', None),
                'about': getattr(entity, 'about', None),
                'restricted': getattr(entity, 'restricted', False),
                'verified': getattr(entity, 'verified', False),
                'scam': getattr(entity, 'scam', False),
                'fake': getattr(entity, 'fake', False),
                'date': entity.date.isoformat() if hasattr(entity, 'date') and entity.date else None,
            })
            
            # Try to get more detailed info
            try:
                full_info = await self.client.get_entity(entity)
                if hasattr(full_info, 'full_chat'):
                    full_chat = full_info.full_chat
                    info['participants_count'] = getattr(full_chat, 'participants_count', info.get('participants_count'))
            except Exception as e:
                logger.debug(f"Could not fetch full chat info: {e}")
        
        elif isinstance(entity, Chat):
            info.update({
                'participants_count': getattr(entity, 'participants_count', None),
                'date': entity.date.isoformat() if hasattr(entity, 'date') and entity.date else None,
            })
        
        # Get invite link if available
        try:
            if isinstance(entity, Channel):
                export_result = await self.client.export_chat_invite_link(entity)
                if export_result:
                    if hasattr(export_result, 'link'):
                        info['invite_link'] = str(export_result.link)
                    elif isinstance(export_result, str):
                        info['invite_link'] = export_result
                    else:
                        info['invite_link'] = None
        except errors.ChatAdminRequiredError:
            info['invite_link'] = "Not available (admin required)"
        except errors.InviteHashExpiredError:
            info['invite_link'] = "Expired"
        except Exception as e:
            logger.debug(f"Could not get invite link: {e}")
            info['invite_link'] = None
        
        return info


async def get_group_info_async(user_input: str) -> Optional[Dict[str, Any]]:
    """
    Async function to get group info.
    
    Args:
        user_input: Invite link, username, or group ID
        
    Returns:
        Dictionary with group information or None
    """
    try:
        client = TelegramClient(
            Config.SESSION_NAME,
            Config.API_ID,
            Config.API_HASH
        )
        
        await client.start(phone=Config.PHONE_NUMBER)
        
        fetcher = GroupInfoFetcher(client)
        info = await fetcher.fetch_group_info(user_input)
        
        await client.disconnect()
        
        return info
        
    except Exception as e:
        logger.error(f"Error in get_group_info_async: {e}")
        return None

