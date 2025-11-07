"""
User data exporter for Excel and PDF formats (user info + messages + stats).
"""

import logging
from typing import List, Dict, Any
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4

from database.models import TelegramUser, Message
from services.export.base_exporter import BaseExporter
from services.export.formatters.excel_formatter import ExcelFormatter
from services.export.formatters.pdf_formatter import PDFFormatter
from services.export.formatters.data_formatter import DataFormatter

logger = logging.getLogger(__name__)


class UserDataExporter(BaseExporter):
    """Exports user data (user info, messages, statistics) to Excel and PDF formats."""
    
    def __init__(self):
        self.excel_formatter = ExcelFormatter()
        self.pdf_formatter = PDFFormatter()
        self.data_formatter = DataFormatter()
    
    def export(
        self,
        data: Dict[str, Any],
        output_path: str,
        format_type: str = 'excel',
        **kwargs
    ) -> bool:
        """
        Export user data to file.
        
        Args:
            data: Dictionary with 'user', 'messages', 'stats' keys
            output_path: Output file path
            format_type: 'excel' or 'pdf'
            
        Returns:
            True if successful
        """
        if format_type == 'excel':
            return self.export_to_excel(
                data['user'],
                data['messages'],
                data['stats'],
                output_path
            )
        elif format_type == 'pdf':
            return self.export_to_pdf(
                data['user'],
                data['messages'],
                data['stats'],
                output_path
            )
        else:
            logger.error(f"Unsupported format: {format_type}")
            return False
    
    def export_to_excel(
        self,
        user: TelegramUser,
        messages: List[Message],
        stats: Dict[str, Any],
        output_path: str
    ) -> bool:
        """Export user data to Excel file."""
        try:
            if not self._validate_output_path(output_path):
                return False
            
            # Format data
            formatted_data = self.data_formatter.format_user_data_for_excel(user, messages, stats)
            
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                workbook = writer.book
                
                # User Information Sheet
                user_df = pd.DataFrame(formatted_data['user_info'])
                user_df.to_excel(writer, sheet_name='User Info', index=False)
                user_worksheet = writer.sheets['User Info']
                user_worksheet.set_column('A:A', 20)
                user_worksheet.set_column('B:B', 30)
                
                # Statistics Sheet
                stats_df = pd.DataFrame(formatted_data['statistics'])
                stats_df.to_excel(writer, sheet_name='Statistics', index=False)
                stats_worksheet = writer.sheets['Statistics']
                stats_worksheet.set_column('A:A', 25)
                stats_worksheet.set_column('B:B', 25)
                
                # Messages Sheet
                if formatted_data['messages']:
                    messages_df = pd.DataFrame(formatted_data['messages'])
                    messages_df.to_excel(writer, sheet_name='Messages', index=False)
                    messages_worksheet = writer.sheets['Messages']
                    
                    # Apply formatting
                    header_format = self.excel_formatter.create_header_format(workbook)
                    self.excel_formatter.apply_header_format(
                        messages_worksheet,
                        header_format,
                        list(messages_df.columns)
                    )
                    
                    # Set column widths
                    self.excel_formatter.set_column_widths(messages_worksheet, {
                        'A': 5,   # No
                        'B': 50,  # Message
                        'C': 20,  # Date
                        'D': 10,  # Has Media
                        'E': 12,  # Media Type
                        'F': 15,  # Message Type
                        'G': 12,  # Has Sticker
                        'H': 10,  # Has Link
                        'I': 40   # Link
                    })
                    
                    # Add auto-filter
                    self.excel_formatter.add_autofilter(
                        messages_worksheet,
                        0, 0,
                        len(messages_df),
                        len(messages_df.columns) - 1
                    )
            
            logger.info(f"Exported user data to Excel: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting user data to Excel: {e}")
            return False
    
    def export_to_pdf(
        self,
        user: TelegramUser,
        messages: List[Message],
        stats: Dict[str, Any],
        output_path: str
    ) -> bool:
        """Export user data to PDF file."""
        try:
            if not self._validate_output_path(output_path):
                return False
            
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )
            
            elements = []
            
            # Title
            title_style = self.pdf_formatter.create_title_style()
            elements.append(self.pdf_formatter.create_paragraph(
                f"User Report: {user.full_name}",
                title_style
            ))
            elements.append(self.pdf_formatter.create_spacer())
            
            # User Information
            heading_style = self.pdf_formatter.create_heading_style()
            elements.append(self.pdf_formatter.create_paragraph("User Information", heading_style))
            
            user_info_data = [
                ['Field', 'Value'],
                ['User ID', str(user.user_id)],
                ['Username', user.username or ''],
                ['Full Name', user.full_name],
                ['Phone', user.phone or ''],
                ['Bio', user.bio or ''],
            ]
            
            user_info_table = self.pdf_formatter.create_table(
                user_info_data,
                col_widths=[3, 4],
                style=self.pdf_formatter.create_table_style(body_bg_color='beige')
            )
            elements.append(user_info_table)
            elements.append(self.pdf_formatter.create_spacer(height=20))
            
            # Statistics
            elements.append(self.pdf_formatter.create_paragraph("Statistics", heading_style))
            stats_data = [
                ['Metric', 'Value'],
                ['Total Messages', str(stats.get('total_messages', 0))],
                ['Total Reactions', str(stats.get('total_reactions', 0))],
                ['Total Stickers', str(stats.get('total_stickers', 0))],
                ['Total Videos', str(stats.get('total_videos', 0))],
                ['Total Photos', str(stats.get('total_photos', 0))],
                ['Total Links', str(stats.get('total_links', 0))],
                ['Total Documents', str(stats.get('total_documents', 0))],
                ['Total Audio', str(stats.get('total_audio', 0))],
            ]
            
            stats_table = self.pdf_formatter.create_table(
                stats_data,
                col_widths=[3, 2],
                style=self.pdf_formatter.create_table_style(body_bg_color='beige')
            )
            elements.append(stats_table)
            elements.append(self.pdf_formatter.create_spacer(height=20))
            
            # Messages (limited to 100)
            if messages:
                elements.append(self.pdf_formatter.create_paragraph("Messages", heading_style))
                
                table_data = [['No', 'Message', 'Date', 'Media']]
                from utils.helpers import format_datetime
                for idx, msg in enumerate(messages[:100], 1):
                    message_text = msg.content or ''
                    if len(message_text) > 100:
                        message_text = message_text[:100] + '...'
                    
                    table_data.append([
                        str(idx),
                        message_text,
                        format_datetime(msg.date_sent, '%Y-%m-%d %H:%M'),
                        'Yes' if msg.has_media else 'No'
                    ])
                
                msg_table = self.pdf_formatter.create_table(
                    table_data,
                    col_widths=[0.4, 3.5, 1.3, 0.6],
                    style=self.pdf_formatter.create_table_style(
                        grid_color='grey',
                        font_size=8,
                        header_font_size=10
                    )
                )
                elements.append(msg_table)
                
                if len(messages) > 100:
                    elements.append(self.pdf_formatter.create_spacer())
                    note = self.pdf_formatter.create_paragraph(
                        f"<i>Note: Showing first 100 of {len(messages)} messages. Export to Excel for full data.</i>"
                    )
                    elements.append(note)
            
            doc.build(elements)
            
            logger.info(f"Exported user data to PDF: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting user data to PDF: {e}")
            return False

