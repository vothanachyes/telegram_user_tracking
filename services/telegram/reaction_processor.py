"""
Reaction processor for handling Telegram message reactions.
"""

import logging
import asyncio
from typing import Optional

try:
    from pyrogram.errors import FloodWait, BadRequest
    PYROGRAM_AVAILABLE = True
except ImportError:
    PYROGRAM_AVAILABLE = False

from database.db_manager import DatabaseManager
from database.models import Reaction
from config.settings import settings

logger = logging.getLogger(__name__)


class ReactionProcessor:
    """Processes Telegram message reactions."""
    
    def __init__(self, db_manager: DatabaseManager, client, user_processor):
        self.db_manager = db_manager
        self.client = client
        self.user_processor = user_processor
    
    async def process_reactions(
        self,
        telegram_msg: 'PyrogramMessage',
        group_id: int,
        group_username: Optional[str],
        message_link: str
    ) -> int:
        """
        Process reactions for a message.
        
        Args:
            telegram_msg: Pyrogram message object
            group_id: Group ID
            group_username: Group username (optional)
            message_link: Message link
            
        Returns:
            Number of reactions processed
        """
        if not settings.settings.track_reactions:
            return 0
        
        if not self.client:
            return 0
        
        try:
            # Check if message has reactions
            if not hasattr(telegram_msg, 'reactions') or not telegram_msg.reactions:
                return 0
            
            reaction_count = 0
            reaction_delay = settings.settings.reaction_fetch_delay
            
            # Get the actual list of reactions from MessageReactions object
            # MessageReactions has a 'reactions' attribute (or 'results' in some versions)
            reactions_list = None
            if hasattr(telegram_msg.reactions, 'reactions'):
                reactions_list = telegram_msg.reactions.reactions
            elif hasattr(telegram_msg.reactions, 'results'):
                reactions_list = telegram_msg.reactions.results
            elif isinstance(telegram_msg.reactions, list):
                # Already a list (shouldn't happen, but handle it)
                reactions_list = telegram_msg.reactions
            else:
                logger.warning(f"Could not extract reactions list from MessageReactions object for message {telegram_msg.id}")
                return 0
            
            if not reactions_list:
                return 0
            
            # Process each reaction type
            for reaction_obj in reactions_list:
                try:
                    # Get emoji from reaction object
                    # ReactionCount objects have a 'reaction' attribute with the actual reaction
                    emoji = "👍"  # Default
                    
                    # Try to get the actual reaction object (might be nested in ReactionCount)
                    actual_reaction = reaction_obj
                    if hasattr(reaction_obj, 'reaction'):
                        actual_reaction = reaction_obj.reaction
                    
                    # Extract emoji from the reaction
                    if hasattr(actual_reaction, 'emoticon'):
                        emoji = actual_reaction.emoticon
                    elif hasattr(actual_reaction, 'emoji'):
                        emoji = actual_reaction.emoji
                    elif hasattr(actual_reaction, 'custom_emoji_id'):
                        # Custom emoji - store the ID as string
                        emoji = f"custom_{actual_reaction.custom_emoji_id}"
                    elif hasattr(reaction_obj, 'emoji'):
                        # Fallback: try direct attribute
                        emoji = reaction_obj.emoji
                    elif hasattr(reaction_obj, 'custom_emoji_id'):
                        # Fallback: try direct attribute
                        emoji = f"custom_{reaction_obj.custom_emoji_id}"
                    
                    # Try to get users who reacted with this emoji
                    try:
                        # Get all reactions for this message
                        reacted_users = []
                        try:
                            reactions_result = await self.client.get_reactions(
                                group_id,
                                telegram_msg.id
                            )
                            
                            # Handle different return types
                            if isinstance(reactions_result, list):
                                for item in reactions_result:
                                    # Check if this reaction matches our emoji
                                    item_emoji = None
                                    if hasattr(item, 'emoji'):
                                        item_emoji = item.emoji
                                    elif hasattr(item, 'custom_emoji_id'):
                                        item_emoji = f"custom_{item.custom_emoji_id}"
                                    
                                    if item_emoji == emoji:
                                        # Extract user from reaction
                                        if hasattr(item, 'user_id'):
                                            user_id = item.user_id
                                            try:
                                                user = await self.client.get_users(user_id)
                                                if user:
                                                    reacted_users.append(user)
                                            except:
                                                pass
                                        elif hasattr(item, 'user'):
                                            reacted_users.append(item.user)
                        except AttributeError:
                            logger.debug(f"get_reactions method not available, skipping reaction user fetch")
                            continue
                        except BadRequest as e:
                            logger.debug(f"Could not fetch reactions for message {telegram_msg.id}: {e}")
                            continue
                        except FloodWait as e:
                            logger.warning(f"FloodWait when fetching reactions: waiting {e.value} seconds")
                            await asyncio.sleep(e.value)
                            continue
                        
                        # Save each reaction
                        for user in reacted_users:
                            # Process user first to ensure they exist in database
                            if user:
                                await self.user_processor.process_user(user)
                                
                                reaction = Reaction(
                                    message_id=telegram_msg.id,
                                    group_id=group_id,
                                    user_id=user.id,
                                    emoji=emoji,
                                    message_link=message_link,
                                    reacted_at=telegram_msg.date  # Use message date as proxy
                                )
                                
                                self.db_manager.save_reaction(reaction)
                                reaction_count += 1
                                
                                # Rate limiting between reaction saves
                                if reaction_delay > 0:
                                    await asyncio.sleep(reaction_delay)
                    
                    except Exception as e:
                        logger.warning(f"Error fetching reactions for message {telegram_msg.id}: {e}")
                        continue
                
                except Exception as e:
                    logger.warning(f"Error processing reaction: {e}")
                    continue
            
            return reaction_count
            
        except Exception as e:
            logger.error(f"Error processing reactions for message {telegram_msg.id}: {e}")
            return 0

