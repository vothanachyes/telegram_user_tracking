"""
Sample data generation for dashboard.
"""

import logging
from datetime import datetime, timedelta
from random import randint, choice
from database.models import TelegramUser, TelegramGroup, Message
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class SampleDataGenerator:
    """Generates sample data for dashboard demonstration."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def ensure_sample_data(self):
        """Generate sample data if database is empty."""
        stats = self.db_manager.get_dashboard_stats()
        
        # Check if we have any data
        if stats['total_messages'] == 0 and stats['total_users'] == 0:
            self._generate_sample_data()
    
    def is_sample_data(self) -> bool:
        """Check if current data is sample data."""
        users = self.db_manager.get_all_users()
        groups = self.db_manager.get_all_groups()
        
        if not users or not groups:
            return False
        
        # Check if we have sample data by checking user IDs
        # Sample users have IDs 1000-1007, sample groups have IDs 2000-2003
        sample_user_count = sum(1 for user in users if 1000 <= user.user_id < 1010)
        sample_group_count = sum(1 for group in groups if 2000 <= group.group_id < 2010)
        
        # If we have sample data and it's the majority/all of the data, show badge
        total_users = len(users)
        total_groups = len(groups)
        
        # Show badge if all or majority of data is sample data
        return (sample_user_count == total_users and sample_group_count == total_groups) or \
               (sample_user_count >= 5 and sample_group_count >= 2)
    
    def _generate_sample_data(self):
        """Generate sample data for demonstration."""
        # Sample user names
        sample_users = [
            {"first_name": "John", "last_name": "Doe", "username": "johndoe", "phone": "+1234567890"},
            {"first_name": "Jane", "last_name": "Smith", "username": "janesmith", "phone": "+1234567891"},
            {"first_name": "Alice", "last_name": "Johnson", "username": "alicej", "phone": "+1234567892"},
            {"first_name": "Bob", "last_name": "Williams", "username": "bobw", "phone": "+1234567893"},
            {"first_name": "Charlie", "last_name": "Brown", "username": "charlieb", "phone": "+1234567894"},
            {"first_name": "Diana", "last_name": "Davis", "username": "dianad", "phone": "+1234567895"},
            {"first_name": "Eve", "last_name": "Miller", "username": "evem", "phone": "+1234567896"},
            {"first_name": "Frank", "last_name": "Wilson", "username": "frankw", "phone": "+1234567897"},
        ]
        
        # Sample group names
        sample_groups = [
            {"name": "Project Team", "username": "projectteam"},
            {"name": "Marketing Group", "username": "marketing"},
            {"name": "Development Chat", "username": "devchat"},
            {"name": "General Discussion", "username": None},
        ]
        
        # Sample messages
        sample_messages = [
            "Hello everyone! How's the project going?",
            "I've completed the first phase of the design.",
            "Can we schedule a meeting for next week?",
            "The new feature is ready for testing.",
            "Great work on the latest update!",
            "I have a question about the API integration.",
            "Let's discuss the roadmap for Q2.",
            "The bug has been fixed and deployed.",
            "Thanks for all your hard work!",
            "I'll send the report by end of day.",
            "The presentation is ready for review.",
            "Can someone help with the database migration?",
            "The client feedback has been positive.",
            "We need to update the documentation.",
            "The new version is now live!",
            "I've added the requested features.",
            "Let's celebrate the milestone!",
            "The code review is complete.",
            "I'll prepare the summary report.",
            "The meeting notes are in the shared folder.",
        ]
        
        # Create sample users
        created_users = []
        for i, user_data in enumerate(sample_users):
            user = TelegramUser(
                user_id=1000 + i,
                username=user_data["username"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                full_name=f"{user_data['first_name']} {user_data['last_name']}",
                phone=user_data["phone"],
                bio=f"Sample user {i+1}",
                created_at=datetime.now() - timedelta(days=30)
            )
            self.db_manager.save_user(user)
            created_users.append(user)
        
        # Create sample groups
        created_groups = []
        for i, group_data in enumerate(sample_groups):
            group = TelegramGroup(
                group_id=2000 + i,
                group_name=group_data["name"],
                group_username=group_data["username"],
                last_fetch_date=datetime.now() - timedelta(days=randint(0, 7)),
                total_messages=0,
                created_at=datetime.now() - timedelta(days=30)
            )
            self.db_manager.save_group(group)
            created_groups.append(group)
        
        # Create sample messages
        # Generate messages over the last 30 days, with more recent activity
        base_date = datetime.now() - timedelta(days=30)
        message_id = 1
        
        for day in range(30):
            # Generate more messages for recent days (last 7 days get more activity)
            if day >= 23:  # Last 7 days
                messages_per_day = randint(10, 20)
            elif day >= 15:  # Days 15-22
                messages_per_day = randint(8, 15)
            else:  # Older days
                messages_per_day = randint(3, 10)
            
            for msg_num in range(messages_per_day):
                user = choice(created_users)
                group = choice(created_groups)
                
                # Create message date (spread throughout the day)
                hours = randint(8, 20)
                minutes = randint(0, 59)
                seconds = randint(0, 59)
                message_date = base_date + timedelta(days=day, hours=hours, minutes=minutes, seconds=seconds)
                
                # Ensure we have some messages from today
                if day == 29:  # Today
                    message_date = datetime.now() - timedelta(hours=randint(0, 12), minutes=randint(0, 59))
                
                # Randomly decide if message has media
                has_media = randint(1, 10) <= 3  # 30% chance
                media_type = None
                media_count = 0
                
                if has_media:
                    media_type = choice(["photo", "video", "document", "audio"])
                    media_count = randint(1, 3)
                
                message = Message(
                    message_id=message_id,
                    group_id=group.group_id,
                    user_id=user.user_id,
                    content=choice(sample_messages),
                    date_sent=message_date,
                    has_media=has_media,
                    media_type=media_type,
                    media_count=media_count,
                    created_at=message_date
                )
                self.db_manager.save_message(message)
                message_id += 1
        
        # Update group message counts
        for group in created_groups:
            count = self.db_manager.get_message_count(group_id=group.group_id)
            group.total_messages = count
            self.db_manager.save_group(group)

