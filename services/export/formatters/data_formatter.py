"""
Data transformation utilities for exports.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from database.models import Message, TelegramUser
from utils.helpers import format_datetime
from utils.constants import DATETIME_FORMAT, format_bytes

logger = logging.getLogger(__name__)


class DataFormatter:
    """Handles data transformation for exports."""
    
    @staticmethod
    def format_messages_for_excel(
        messages: List[Message],
        db_manager,
        start_index: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Format messages for Excel export.
        
        Args:
            messages: List of Message objects
            db_manager: DatabaseManager instance
            start_index: Starting row number
            
        Returns:
            List of dictionaries with formatted message data
        """
        data = []
        for idx, msg in enumerate(messages, start_index):
            user = db_manager.get_user_by_id(msg.user_id)
            
            data.append({
                'No': idx,
                'Full Name': user.full_name if user else 'Unknown',
                'Username': user.username if user else '',
                'Phone': user.phone if user else '',
                'Message': msg.content or '',
                'Date Sent': format_datetime(msg.date_sent),
                'Has Media': 'Yes' if msg.has_media else 'No',
                'Media Type': msg.media_type or '',
                'Message Link': msg.message_link or ''
            })
        
        return data
    
    @staticmethod
    def format_messages_for_pdf(
        messages: List[Message],
        db_manager,
        limit: int = 100,
        start_index: int = 1
    ) -> List[List[str]]:
        """
        Format messages for PDF export.
        
        Args:
            messages: List of Message objects
            db_manager: DatabaseManager instance
            limit: Maximum number of messages to include
            start_index: Starting row number
            
        Returns:
            List of rows (each row is a list of strings)
        """
        table_data = [['No', 'User', 'Message', 'Date', 'Media']]
        
        for idx, msg in enumerate(messages[:limit], start_index):
            user = db_manager.get_user_by_id(msg.user_id)
            user_name = user.full_name if user else 'Unknown'
            
            # Truncate message
            message_text = msg.content or ''
            if len(message_text) > 100:
                message_text = message_text[:100] + '...'
            
            table_data.append([
                str(idx),
                user_name,
                message_text,
                format_datetime(msg.date_sent, '%Y-%m-%d %H:%M'),
                'Yes' if msg.has_media else 'No'
            ])
        
        return table_data
    
    @staticmethod
    def format_users_for_excel(
        users: List[TelegramUser],
        start_index: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Format users for Excel export.
        
        Args:
            users: List of TelegramUser objects
            start_index: Starting row number
            
        Returns:
            List of dictionaries with formatted user data
        """
        data = []
        for idx, user in enumerate(users, start_index):
            data.append({
                'No': idx,
                'User ID': user.user_id,
                'Username': user.username or '',
                'Full Name': user.full_name,
                'First Name': user.first_name or '',
                'Last Name': user.last_name or '',
                'Phone': user.phone or '',
                'Bio': user.bio or '',
                'Created': format_datetime(user.created_at)
            })
        
        return data
    
    @staticmethod
    def format_users_for_pdf(
        users: List[TelegramUser],
        limit: int = 100,
        start_index: int = 1
    ) -> List[List[str]]:
        """
        Format users for PDF export.
        
        Args:
            users: List of TelegramUser objects
            limit: Maximum number of users to include
            start_index: Starting row number
            
        Returns:
            List of rows (each row is a list of strings)
        """
        table_data = [['No', 'Username', 'Full Name', 'Phone']]
        
        for idx, user in enumerate(users[:limit], start_index):
            table_data.append([
                str(idx),
                user.username or '-',
                user.full_name,
                user.phone or '-'
            ])
        
        return table_data
    
    @staticmethod
    def format_user_data_for_excel(
        user: TelegramUser,
        messages: List[Message],
        stats: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Format user data for Excel export (multiple sheets).
        
        Args:
            user: TelegramUser object
            messages: List of Message objects
            stats: Statistics dictionary
            
        Returns:
            Dictionary with sheet names as keys and data as values
        """
        # User Information
        user_data = [
            {'Field': 'User ID', 'Value': user.user_id},
            {'Field': 'Username', 'Value': user.username or ''},
            {'Field': 'Full Name', 'Value': user.full_name},
            {'Field': 'First Name', 'Value': user.first_name or ''},
            {'Field': 'Last Name', 'Value': user.last_name or ''},
            {'Field': 'Phone', 'Value': user.phone or ''},
            {'Field': 'Bio', 'Value': user.bio or ''},
            {'Field': 'Created', 'Value': format_datetime(user.created_at)},
        ]
        
        # Statistics
        stats_data = [
            {'Metric': 'Total Messages', 'Value': stats.get('total_messages', 0)},
            {'Metric': 'Total Reactions', 'Value': stats.get('total_reactions', 0)},
            {'Metric': 'Total Stickers', 'Value': stats.get('total_stickers', 0)},
            {'Metric': 'Total Videos', 'Value': stats.get('total_videos', 0)},
            {'Metric': 'Total Photos', 'Value': stats.get('total_photos', 0)},
            {'Metric': 'Total Links', 'Value': stats.get('total_links', 0)},
            {'Metric': 'Total Documents', 'Value': stats.get('total_documents', 0)},
            {'Metric': 'Total Audio', 'Value': stats.get('total_audio', 0)},
            {'Metric': 'Total Text Messages', 'Value': stats.get('total_text_messages', 0)},
            {'Metric': 'First Activity', 'Value': format_datetime(stats.get('first_activity_date'))},
            {'Metric': 'Last Activity', 'Value': format_datetime(stats.get('last_activity_date'))},
        ]
        
        # Messages
        messages_data = []
        if messages:
            for idx, msg in enumerate(messages, 1):
                messages_data.append({
                    'No': idx,
                    'Message': msg.content or '',
                    'Date Sent': format_datetime(msg.date_sent),
                    'Has Media': 'Yes' if msg.has_media else 'No',
                    'Media Type': msg.media_type or '',
                    'Message Type': msg.message_type or '',
                    'Has Sticker': 'Yes' if msg.has_sticker else 'No',
                    'Has Link': 'Yes' if msg.has_link else 'No',
                    'Message Link': msg.message_link or ''
                })
        
        return {
            'user_info': user_data,
            'statistics': stats_data,
            'messages': messages_data
        }
    
    @staticmethod
    def format_stats_for_excel(
        stats: Dict[str, Any],
        include_export_date: bool = True
    ) -> List[List[str]]:
        """
        Format statistics for Excel export.
        
        Args:
            stats: Statistics dictionary
            include_export_date: Whether to include export date
            
        Returns:
            List of rows (each row is [metric, value])
        """
        stats_data = [
            ['Total Messages', str(stats.get('total_messages', 0))],
            ['Total Users', str(stats.get('total_users', 0))],
            ['Total Groups', str(stats.get('total_groups', 0))],
            ['Total Media Size', format_bytes(stats.get('total_media_size', 0))],
            ['Messages Today', str(stats.get('messages_today', 0))],
            ['Messages This Month', str(stats.get('messages_this_month', 0))],
        ]
        
        if include_export_date:
            stats_data.append(['Export Date', datetime.now().strftime(DATETIME_FORMAT)])
        
        return stats_data

