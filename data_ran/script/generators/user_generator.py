"""
User generator for telegram_users data.
"""

import random
from typing import Dict, Any, List
from datetime import datetime
from data_ran.pattern.base import BaseGenerator
from data_ran.script.ai_generator import AIContentGenerator


class UserGenerator(BaseGenerator):
    """Generates telegram_users data."""
    
    def __init__(self):
        """Initialize user generator."""
        self.ai_generator = AIContentGenerator()
    
    def generate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate users data.
        
        Args:
            config: Configuration with:
                - num_users: Number of users to generate
                - deleted_percentage: Percentage of deleted users (0-100)
                - languages: List of languages ['khmer', 'english']
                
        Returns:
            List of user dictionaries
        """
        num_users = config.get('num_users', 10)
        deleted_percentage = config.get('deleted_percentage', 5)
        languages = config.get('languages', ['english'])
        date_range = config.get('date_range', {})
        start_date = date_range.get('start', datetime.now())
        
        users = []
        base_user_id = 100000000
        
        num_deleted = int(num_users * deleted_percentage / 100)
        
        for i in range(num_users):
            is_deleted = i < num_deleted
            
            # Determine language for this user
            if 'khmer' in languages and 'english' in languages:
                lang = random.choice(['khmer', 'english'])
            elif 'khmer' in languages:
                lang = 'khmer'
            else:
                lang = 'english'
            
            if lang == 'khmer':
                name_data = self.ai_generator.generate_khmer_name()
            else:
                name_data = self.ai_generator.generate_english_name()
            
            phone = f"+{random.randint(1, 999)}{random.randint(100000000, 999999999)}"
            bio = f"User bio {i+1}" if not is_deleted else None
            
            user = {
                'user_id': base_user_id + i,
                'username': name_data['username'],
                'first_name': name_data['first_name'],
                'last_name': name_data['last_name'],
                'full_name': name_data['full_name'],
                'phone': phone if not is_deleted else None,
                'bio': bio,
                'profile_photo_path': f"./downloads/profiles/user_{base_user_id + i}.jpg" if not is_deleted else None,
                'is_deleted': is_deleted,
                'created_at': start_date.isoformat() if isinstance(start_date, datetime) else str(start_date),
                'updated_at': start_date.isoformat() if isinstance(start_date, datetime) else str(start_date)
            }
            users.append(user)
        
        return users
    
    def get_dependencies(self) -> List[str]:
        """Users have no dependencies."""
        return []

