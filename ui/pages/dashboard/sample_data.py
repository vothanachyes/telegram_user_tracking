"""
Sample data generator for dashboard demonstration.
Generates sample data if the database is empty.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class SampleDataGenerator:
    """Generates sample data for dashboard demonstration."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize sample data generator.
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
        self._is_sample_data = False
    
    def ensure_sample_data(self):
        """Generate sample data if database is empty."""
        try:
            # Check if database has any groups
            groups = self.db_manager.get_all_groups()
            
            if not groups:
                logger.info("Database is empty, generating sample data...")
                self._generate_sample_data()
                self._is_sample_data = True
            else:
                # Check if this looks like sample data (simple heuristic)
                # You can enhance this to check for specific markers
                self._is_sample_data = False
                
        except Exception as e:
            logger.error(f"Error checking/generating sample data: {e}", exc_info=True)
            self._is_sample_data = False
    
    def is_sample_data(self) -> bool:
        """
        Check if current data is sample data.
        
        Returns:
            True if sample data exists, False otherwise
        """
        return self._is_sample_data
    
    def _generate_sample_data(self):
        """Generate basic sample data for demonstration."""
        try:
            # Generate sample groups
            sample_groups = [
                {
                    'group_id': 1001,
                    'group_name': 'Sample Tech Group',
                    'group_username': 'sample_tech',
                    'last_fetch_date': datetime.now(),
                    'total_messages': 0
                },
                {
                    'group_id': 1002,
                    'group_name': 'Sample Marketing Team',
                    'group_username': 'sample_marketing',
                    'last_fetch_date': datetime.now(),
                    'total_messages': 0
                }
            ]
            
            # Generate sample users
            sample_users = [
                {
                    'user_id': 2001,
                    'username': 'sample_user1',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'full_name': 'John Doe',
                    'phone': '+1234567890',
                    'bio': 'Sample user',
                    'profile_photo_path': None,
                    'is_deleted': False
                },
                {
                    'user_id': 2002,
                    'username': 'sample_user2',
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'full_name': 'Jane Smith',
                    'phone': '+1234567891',
                    'bio': 'Sample user',
                    'profile_photo_path': None,
                    'is_deleted': False
                }
            ]
            
            # Insert sample groups
            for group in sample_groups:
                try:
                    self.db_manager.add_group(
                        group_id=group['group_id'],
                        group_name=group['group_name'],
                        group_username=group['group_username'],
                        last_fetch_date=group['last_fetch_date']
                    )
                except Exception as e:
                    logger.warning(f"Could not add sample group {group['group_name']}: {e}")
            
            # Insert sample users
            for user in sample_users:
                try:
                    self.db_manager.add_user(
                        user_id=user['user_id'],
                        username=user['username'],
                        first_name=user['first_name'],
                        last_name=user['last_name'],
                        full_name=user['full_name'],
                        phone=user['phone'],
                        bio=user['bio'],
                        profile_photo_path=user['profile_photo_path'],
                        is_deleted=user['is_deleted']
                    )
                except Exception as e:
                    logger.warning(f"Could not add sample user {user['username']}: {e}")
            
            # Generate some sample messages
            now = datetime.now()
            for i in range(5):
                try:
                    message_date = now - timedelta(days=i)
                    self.db_manager.add_message(
                        message_id=3000 + i,
                        group_id=1001,
                        user_id=2001 if i % 2 == 0 else 2002,
                        content=f'Sample message {i + 1}',
                        date_sent=message_date,
                        has_media=False,
                        message_type='text'
                    )
                except Exception as e:
                    logger.warning(f"Could not add sample message {i}: {e}")
            
            logger.info("Sample data generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating sample data: {e}", exc_info=True)
            raise

