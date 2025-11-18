"""
Group generator for telegram_groups data.
"""

import random
from typing import Dict, Any, List
from datetime import datetime
from data_ran.pattern.base import BaseGenerator
from data_ran.script.ai_generator import AIContentGenerator


class GroupGenerator(BaseGenerator):
    """Generates telegram_groups data."""
    
    def __init__(self):
        """Initialize group generator."""
        self.ai_generator = AIContentGenerator()
    
    def generate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate groups data.
        
        Args:
            config: Configuration with:
                - num_groups: Number of groups to generate
                - date_range: Dict with 'start' and 'end' datetime
                - languages: List of languages ['khmer', 'english']
                
        Returns:
            List of group dictionaries
        """
        num_groups = config.get('num_groups', 3)
        date_range = config.get('date_range', {})
        languages = config.get('languages', ['english'])
        end_date = date_range.get('end', datetime.now())
        
        groups = []
        base_group_id = -1000000000000  # Negative for Telegram groups
        
        for i in range(num_groups):
            # Determine language for this group
            if 'khmer' in languages and 'english' in languages:
                lang = random.choice(['khmer', 'english', 'mixed'])
            elif 'khmer' in languages:
                lang = 'khmer'
            else:
                lang = 'english'
            
            group_name = self.ai_generator.generate_group_name(lang)
            group_username = f"{group_name.lower().replace(' ', '_').replace('/', '_')}_{random.randint(100, 999)}"
            
            group = {
                'group_id': base_group_id - i,
                'group_name': group_name,
                'group_username': group_username,
                'last_fetch_date': end_date.isoformat() if isinstance(end_date, datetime) else str(end_date),
                'total_messages': 0,  # Will be updated later
                'created_at': date_range.get('start', datetime.now()).isoformat() if isinstance(date_range.get('start'), datetime) else str(date_range.get('start', datetime.now())),
                'updated_at': end_date.isoformat() if isinstance(end_date, datetime) else str(end_date)
            }
            groups.append(group)
        
        return groups
    
    def get_dependencies(self) -> List[str]:
        """Groups have no dependencies."""
        return []

