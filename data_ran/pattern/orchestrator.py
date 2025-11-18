"""
Data generator orchestrator that coordinates all generators and outputs nested JSON.
"""

import json
from typing import Dict, Any, List
from datetime import datetime
from data_ran.pattern.registry import FeatureRegistry


class DataGeneratorOrchestrator:
    """Orchestrates data generation and outputs nested JSON structure."""
    
    def __init__(self, registry: FeatureRegistry):
        """
        Initialize orchestrator.
        
        Args:
            registry: FeatureRegistry instance
        """
        self.registry = registry
        self.generated_data: Dict[str, Any] = {}
    
    def generate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate all data based on configuration.
        
        Args:
            config: Configuration dictionary with:
                - date_range: Dict with 'start' and 'end' datetime
                - num_groups: Number of groups
                - num_users: Number of users
                - messages_per_group: Number or range of messages per group
                - reactions_per_message: Dict with 'min' and 'max'
                - media_percentage: Percentage (0-100)
                - tag_config: Dict with 'min_tags' and 'max_tags'
                - deleted_percentage: Percentage (0-100)
                - languages: List of languages ['khmer', 'english']
                
        Returns:
            Nested JSON structure with all generated data
        """
        # Get generation order based on dependencies
        generation_order = self.registry.get_generation_order()
        
        # Prepare shared config
        shared_config = {
            'date_range': config.get('date_range', {}),
            'languages': config.get('languages', ['english']),
            'tag_config': config.get('tag_config', {'min_tags': 0, 'max_tags': 3}),
            'deleted_percentage': config.get('deleted_percentage', 5)
        }
        
        # Generate data in order
        for feature_name in generation_order:
            generator = self.registry.get_generator(feature_name)
            if not generator:
                continue
            
            # Prepare feature-specific config
            feature_config = shared_config.copy()
            
            if feature_name == 'groups':
                feature_config['num_groups'] = config.get('num_groups', 3)
            elif feature_name == 'users':
                feature_config['num_users'] = config.get('num_users', 10)
                feature_config['deleted_percentage'] = config.get('deleted_percentage', 5)
            elif feature_name == 'messages':
                feature_config['groups'] = self.generated_data.get('groups', [])
                feature_config['users'] = self.generated_data.get('users', [])
                feature_config['messages_per_group'] = config.get('messages_per_group', 100)
                feature_config['media_percentage'] = config.get('media_percentage', 30)
            elif feature_name == 'reactions':
                feature_config['messages'] = self.generated_data.get('messages', [])
                feature_config['users'] = self.generated_data.get('users', [])
                feature_config['reactions_per_message'] = config.get('reactions_per_message', {'min': 0, 'max': 5})
            elif feature_name == 'media':
                feature_config['messages'] = self.generated_data.get('messages', [])
            elif feature_name == 'tags':
                feature_config['messages'] = self.generated_data.get('messages', [])
            elif feature_name == 'deleted':
                feature_config['messages'] = self.generated_data.get('messages', [])
                feature_config['users'] = self.generated_data.get('users', [])
            
            # Generate data
            generated = generator.generate(feature_config)
            self.generated_data[feature_name] = generated
        
        # Build nested JSON structure
        return self._build_nested_structure(config)
    
    def _build_nested_structure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build nested JSON structure from flat generated data.
        
        Args:
            config: Original configuration
            
        Returns:
            Nested JSON structure
        """
        groups = self.generated_data.get('groups', [])
        users = self.generated_data.get('users', [])
        messages = self.generated_data.get('messages', [])
        reactions = self.generated_data.get('reactions', [])
        media_files = self.generated_data.get('media', [])
        tags = self.generated_data.get('tags', [])
        deleted_data = self.generated_data.get('deleted', {})
        settings = self.generated_data.get('settings', [])
        
        # Create user lookup
        user_lookup = {u['user_id']: u for u in users}
        
        # Create message lookup
        message_lookup = {m['message_id']: m for m in messages}
        
        # Group reactions by message_id
        reactions_by_message: Dict[int, List[Dict]] = {}
        for reaction in reactions:
            msg_id = reaction['message_id']
            if msg_id not in reactions_by_message:
                reactions_by_message[msg_id] = []
            reactions_by_message[msg_id].append(reaction)
        
        # Group media by message_id
        media_by_message: Dict[int, List[Dict]] = {}
        for media in media_files:
            msg_id = media['message_id']
            if msg_id not in media_by_message:
                media_by_message[msg_id] = []
            media_by_message[msg_id].append(media)
        
        # Group tags by message_id
        tags_by_message: Dict[int, List[Dict]] = {}
        for tag in tags:
            msg_id = tag['message_id']
            if msg_id not in tags_by_message:
                tags_by_message[msg_id] = []
            tags_by_message[msg_id].append(tag)
        
        # Group messages by group_id and user_id
        messages_by_group: Dict[int, List[Dict]] = {}
        messages_by_user: Dict[int, List[Dict]] = {}
        
        for message in messages:
            group_id = message['group_id']
            user_id = message['user_id']
            msg_id = message['message_id']
            
            # Add reactions, media, and tags to message
            message['reactions'] = reactions_by_message.get(msg_id, [])
            message['media_files'] = media_by_message.get(msg_id, [])
            message['tags'] = [t['tag'] for t in tags_by_message.get(msg_id, [])]
            
            if group_id not in messages_by_group:
                messages_by_group[group_id] = []
            messages_by_group[group_id].append(message)
            
            if user_id not in messages_by_user:
                messages_by_user[user_id] = []
            messages_by_user[user_id].append(message)
        
        # Build nested groups structure
        nested_groups = []
        for group in groups:
            group_id = group['group_id']
            group_messages = messages_by_group.get(group_id, [])
            
            # Group messages by user
            users_in_group = {}
            for message in group_messages:
                user_id = message['user_id']
                if user_id not in users_in_group:
                    user_data = user_lookup.get(user_id, {})
                    users_in_group[user_id] = {
                        **user_data,
                        'messages': []
                    }
                users_in_group[user_id]['messages'].append(message)
            
            nested_group = {
                **group,
                'users': list(users_in_group.values()),
                'total_messages': len(group_messages)
            }
            nested_groups.append(nested_group)
        
        # Build metadata
        date_range = config.get('date_range', {})
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'date_range': {
                'start': date_range.get('start', datetime.now()).isoformat() if isinstance(date_range.get('start'), datetime) else str(date_range.get('start', datetime.now())),
                'end': date_range.get('end', datetime.now()).isoformat() if isinstance(date_range.get('end'), datetime) else str(date_range.get('end', datetime.now()))
            },
            'config': {
                'num_groups': len(groups),
                'num_users': len(users),
                'num_messages': len(messages),
                'num_reactions': len(reactions),
                'num_media_files': len(media_files),
                'num_tags': len(tags),
                'languages': config.get('languages', ['english'])
            }
        }
        
        # Build final structure
        result = {
            'metadata': metadata,
            'telegram_groups': nested_groups,
            'app_settings': settings[0] if settings else None
        }
        
        # Add flat lists for database import (if needed)
        result['_flat_data'] = {
            'telegram_groups': groups,
            'telegram_users': users,
            'messages': messages,
            'reactions': reactions,
            'media_files': media_files,
            'message_tags': tags,
            'deleted_messages': deleted_data.get('deleted_messages', []),
            'deleted_users': deleted_data.get('deleted_users', []),
            'app_settings': settings
        }
        
        return result

