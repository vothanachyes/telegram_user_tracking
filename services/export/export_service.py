"""
Export service facade for generating PDF and Excel reports.
"""

import logging
from typing import List
from database.db_manager import DatabaseManager
from database.models import Message, TelegramUser
from services.export.exporters.messages_exporter import MessagesExporter
from services.export.exporters.users_exporter import UsersExporter
from services.export.exporters.user_data_exporter import UserDataExporter

logger = logging.getLogger(__name__)


class ExportService:
    """Facade for exporting data to PDF and Excel formats."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.messages_exporter = MessagesExporter(db_manager)
        self.users_exporter = UsersExporter()
        self.user_data_exporter = UserDataExporter()
    
    def export_messages_to_excel(
        self,
        messages: List[Message],
        output_path: str,
        include_stats: bool = True
    ) -> bool:
        """
        Export messages to Excel file.
        Returns True if successful.
        """
        return self.messages_exporter.export_to_excel(messages, output_path, include_stats)
    
    def export_messages_to_pdf(
        self,
        messages: List[Message],
        output_path: str,
        title: str = "Messages Report",
        include_stats: bool = True
    ) -> bool:
        """
        Export messages to PDF file.
        Returns True if successful.
        """
        return self.messages_exporter.export_to_pdf(messages, output_path, title, include_stats)
    
    def export_users_to_excel(
        self,
        users: List[TelegramUser],
        output_path: str
    ) -> bool:
        """
        Export users to Excel file.
        Returns True if successful.
        """
        return self.users_exporter.export_to_excel(users, output_path)
    
    def export_users_to_pdf(
        self,
        users: List[TelegramUser],
        output_path: str,
        title: str = "Users Report"
    ) -> bool:
        """
        Export users to PDF file.
        Returns True if successful.
        """
        return self.users_exporter.export_to_pdf(users, output_path, title)
    
    def export_user_data_to_excel(
        self,
        user: TelegramUser,
        messages: List[Message],
        stats: dict,
        output_path: str
    ) -> bool:
        """
        Export user data (messages and statistics) to Excel file.
        Returns True if successful.
        """
        return self.user_data_exporter.export_to_excel(user, messages, stats, output_path)
    
    def export_user_data_to_pdf(
        self,
        user: TelegramUser,
        messages: List[Message],
        stats: dict,
        output_path: str
    ) -> bool:
        """
        Export user data (messages and statistics) to PDF file.
        Returns True if successful.
        """
        return self.user_data_exporter.export_to_pdf(user, messages, stats, output_path)

