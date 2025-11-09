"""
Reaction processor for handling Telegram message reactions.
"""

import logging
import asyncio
from typing import Optional

try:
    from telethon.errors import FloodWaitError, BadRequestError
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

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
        telegram_msg: 'TelethonMessage',
        group_id: int,
        group_username: Optional[str],
        message_link: str
    ) -> int:
        """
        Process reactions for a message.
        
        Args:
            telegram_msg: Telethon message object
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
                        # Telethon stores reactions in message.reactions attribute
                        reacted_users = []
                        try:
                            # In Telethon, reactions are stored in message.reactions
                            # We need to get reaction users differently
                            if hasattr(telegram_msg, 'reactions') and telegram_msg.reactions:
                                # Telethon reactions structure is different
                                # reactions is a MessageReactions object with results list
                                reactions_obj = telegram_msg.reactions
                                if hasattr(reactions_obj, 'results'):
                                    for reaction_count in reactions_obj.results:
                                        # Check if this reaction matches our emoji
                                        reaction = reaction_count.reaction if hasattr(reaction_count, 'reaction') else None
                                        if reaction:
                                            reaction_emoji = None
                                            if hasattr(reaction, 'emoticon'):
                                                reaction_emoji = reaction.emoticon
                                            elif hasattr(reaction, 'document_id'):
                                                reaction_emoji = f"custom_{reaction.document_id}"
                                            
                                            if reaction_emoji == emoji:
                                                # Get users who reacted - Telethon doesn't have direct API for this
                                                # We'll need to use the count from reaction_count.count
                                                # For now, we'll process based on the reaction count
                                                # Note: Telethon doesn't provide easy access to individual reaction users
                                                # Note: Telethon's reaction API structure
                                                pass
                        except AttributeError:
                            logger.debug(f"Reactions not available for message {telegram_msg.id}")
                            continue
                        except BadRequestError as e:
                            logger.debug(f"Could not fetch reactions for message {telegram_msg.id}: {e}")
                            continue
                        except FloodWaitError as e:
                            logger.warning(f"FloodWait when fetching reactions: waiting {e.seconds} seconds")
                            await asyncio.sleep(e.seconds)
                            continue
                        
                        # Note: Telethon doesn't provide easy access to individual reaction users
                        # For now, we'll skip individual user reaction tracking
                        # The reaction counts are still available in message.reactions
                        # TODO: Implement reaction user fetching if needed via alternative methods
                        logger.debug(f"Reaction tracking for individual users not fully supported for message {telegram_msg.id}")
                    
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

