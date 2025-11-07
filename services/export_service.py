"""
Export service for generating PDF and Excel reports.
"""

import logging
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import io

import pandas as pd
import xlsxwriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from database.db_manager import DatabaseManager
from database.models import Message, TelegramUser
from utils.constants import format_bytes, DATE_FORMAT, DATETIME_FORMAT
from utils.helpers import format_datetime

logger = logging.getLogger(__name__)


class ExportService:
    """Handles exporting data to PDF and Excel formats."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
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
        try:
            # Create DataFrame
            data = []
            for idx, msg in enumerate(messages, 1):
                user = self.db_manager.get_user_by_id(msg.user_id)
                
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
            
            df = pd.DataFrame(data)
            
            # Create Excel writer
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                # Write main data
                df.to_excel(writer, sheet_name='Messages', index=False)
                
                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Messages']
                
                # Define formats
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#082f49',
                    'font_color': 'white',
                    'border': 1
                })
                
                cell_format = workbook.add_format({
                    'border': 1,
                    'text_wrap': True,
                    'valign': 'top'
                })
                
                # Set column widths
                worksheet.set_column('A:A', 5)   # No
                worksheet.set_column('B:B', 20)  # Full Name
                worksheet.set_column('C:C', 15)  # Username
                worksheet.set_column('D:D', 15)  # Phone
                worksheet.set_column('E:E', 50)  # Message
                worksheet.set_column('F:F', 20)  # Date
                worksheet.set_column('G:G', 10)  # Has Media
                worksheet.set_column('H:H', 12)  # Media Type
                worksheet.set_column('I:I', 40)  # Link
                
                # Apply header format
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Add auto-filter
                worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
                
                # Add statistics sheet if requested
                if include_stats:
                    stats = self.db_manager.get_dashboard_stats()
                    
                    stats_data = pd.DataFrame([
                        ['Total Messages', stats['total_messages']],
                        ['Total Users', stats['total_users']],
                        ['Total Groups', stats['total_groups']],
                        ['Total Media Size', format_bytes(stats['total_media_size'])],
                        ['Messages Today', stats['messages_today']],
                        ['Messages This Month', stats['messages_this_month']],
                        ['Export Date', datetime.now().strftime(DATETIME_FORMAT)]
                    ], columns=['Metric', 'Value'])
                    
                    stats_data.to_excel(writer, sheet_name='Statistics', index=False)
                    
                    stats_worksheet = writer.sheets['Statistics']
                    stats_worksheet.set_column('A:A', 25)
                    stats_worksheet.set_column('B:B', 25)
            
            logger.info(f"Exported {len(messages)} messages to Excel: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return False
    
    def export_users_to_excel(
        self,
        users: List[TelegramUser],
        output_path: str
    ) -> bool:
        """
        Export users to Excel file.
        Returns True if successful.
        """
        try:
            data = []
            for idx, user in enumerate(users, 1):
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
            
            df = pd.DataFrame(data)
            
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Users', index=False)
                
                workbook = writer.book
                worksheet = writer.sheets['Users']
                
                # Format
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#082f49',
                    'font_color': 'white',
                    'border': 1
                })
                
                # Set column widths
                worksheet.set_column('A:A', 5)   # No
                worksheet.set_column('B:B', 12)  # User ID
                worksheet.set_column('C:C', 15)  # Username
                worksheet.set_column('D:D', 20)  # Full Name
                worksheet.set_column('E:E', 15)  # First Name
                worksheet.set_column('F:F', 15)  # Last Name
                worksheet.set_column('G:G', 15)  # Phone
                worksheet.set_column('H:H', 30)  # Bio
                worksheet.set_column('I:I', 20)  # Created
                
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
            
            logger.info(f"Exported {len(users)} users to Excel: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting users to Excel: {e}")
            return False
    
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
        try:
            # Create PDF
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )
            
            # Container for PDF elements
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#082f49'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#082f49'),
                spaceAfter=12
            )
            
            # Title
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 12))
            
            # Statistics
            if include_stats:
                stats = self.db_manager.get_dashboard_stats()
                
                elements.append(Paragraph("Statistics", heading_style))
                
                stats_data = [
                    ['Metric', 'Value'],
                    ['Total Messages', str(stats['total_messages'])],
                    ['Total Users', str(stats['total_users'])],
                    ['Total Groups', str(stats['total_groups'])],
                    ['Total Media Size', format_bytes(stats['total_media_size'])],
                    ['Export Date', datetime.now().strftime(DATETIME_FORMAT)]
                ]
                
                stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
                stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#082f49')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(stats_table)
                elements.append(Spacer(1, 20))
            
            # Messages
            elements.append(Paragraph("Messages", heading_style))
            
            # Prepare table data
            table_data = [['No', 'User', 'Message', 'Date', 'Media']]
            
            for idx, msg in enumerate(messages[:100], 1):  # Limit to 100 for PDF
                user = self.db_manager.get_user_by_id(msg.user_id)
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
            
            # Create table
            msg_table = Table(
                table_data,
                colWidths=[0.4*inch, 1.5*inch, 3*inch, 1.3*inch, 0.6*inch]
            )
            
            msg_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#082f49')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            elements.append(msg_table)
            
            # Add note if messages were limited
            if len(messages) > 100:
                elements.append(Spacer(1, 12))
                note = Paragraph(
                    f"<i>Note: Showing first 100 of {len(messages)} messages. Export to Excel for full data.</i>",
                    styles['Normal']
                )
                elements.append(note)
            
            # Build PDF
            doc.build(elements)
            
            logger.info(f"Exported messages to PDF: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {e}")
            return False
    
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
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )
            
            elements = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#082f49'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 20))
            
            # Table data
            table_data = [['No', 'Username', 'Full Name', 'Phone']]
            
            for idx, user in enumerate(users[:100], 1):
                table_data.append([
                    str(idx),
                    user.username or '-',
                    user.full_name,
                    user.phone or '-'
                ])
            
            user_table = Table(
                table_data,
                colWidths=[0.5*inch, 1.5*inch, 2.5*inch, 1.5*inch]
            )
            
            user_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#082f49')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            elements.append(user_table)
            
            if len(users) > 100:
                elements.append(Spacer(1, 12))
                note = Paragraph(
                    f"<i>Note: Showing first 100 of {len(users)} users. Export to Excel for full data.</i>",
                    styles['Normal']
                )
                elements.append(note)
            
            doc.build(elements)
            
            logger.info(f"Exported users to PDF: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting users to PDF: {e}")
            return False
    
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
        try:
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                workbook = writer.book
                
                # User Information Sheet
                user_data = pd.DataFrame([
                    ['User ID', user.user_id],
                    ['Username', user.username or ''],
                    ['Full Name', user.full_name],
                    ['First Name', user.first_name or ''],
                    ['Last Name', user.last_name or ''],
                    ['Phone', user.phone or ''],
                    ['Bio', user.bio or ''],
                    ['Created', format_datetime(user.created_at)],
                ], columns=['Field', 'Value'])
                
                user_data.to_excel(writer, sheet_name='User Info', index=False)
                user_worksheet = writer.sheets['User Info']
                user_worksheet.set_column('A:A', 20)
                user_worksheet.set_column('B:B', 30)
                
                # Statistics Sheet
                stats_data = pd.DataFrame([
                    ['Total Messages', stats.get('total_messages', 0)],
                    ['Total Reactions', stats.get('total_reactions', 0)],
                    ['Total Stickers', stats.get('total_stickers', 0)],
                    ['Total Videos', stats.get('total_videos', 0)],
                    ['Total Photos', stats.get('total_photos', 0)],
                    ['Total Links', stats.get('total_links', 0)],
                    ['Total Documents', stats.get('total_documents', 0)],
                    ['Total Audio', stats.get('total_audio', 0)],
                    ['Total Text Messages', stats.get('total_text_messages', 0)],
                    ['First Activity', format_datetime(stats.get('first_activity_date'))],
                    ['Last Activity', format_datetime(stats.get('last_activity_date'))],
                ], columns=['Metric', 'Value'])
                
                stats_data.to_excel(writer, sheet_name='Statistics', index=False)
                stats_worksheet = writer.sheets['Statistics']
                stats_worksheet.set_column('A:A', 25)
                stats_worksheet.set_column('B:B', 25)
                
                # Messages Sheet
                if messages:
                    messages_data = []
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
                    
                    messages_df = pd.DataFrame(messages_data)
                    messages_df.to_excel(writer, sheet_name='Messages', index=False)
                    messages_worksheet = writer.sheets['Messages']
                    
                    # Format
                    header_format = workbook.add_format({
                        'bold': True,
                        'bg_color': '#082f49',
                        'font_color': 'white',
                        'border': 1
                    })
                    
                    cell_format = workbook.add_format({
                        'border': 1,
                        'text_wrap': True,
                        'valign': 'top'
                    })
                    
                    # Set column widths
                    messages_worksheet.set_column('A:A', 5)   # No
                    messages_worksheet.set_column('B:B', 50)  # Message
                    messages_worksheet.set_column('C:C', 20)  # Date
                    messages_worksheet.set_column('D:D', 10)  # Has Media
                    messages_worksheet.set_column('E:E', 12)  # Media Type
                    messages_worksheet.set_column('F:F', 15)  # Message Type
                    messages_worksheet.set_column('G:G', 12)  # Has Sticker
                    messages_worksheet.set_column('H:H', 10)  # Has Link
                    messages_worksheet.set_column('I:I', 40)  # Link
                    
                    # Apply header format
                    for col_num, value in enumerate(messages_df.columns.values):
                        messages_worksheet.write(0, col_num, value, header_format)
                    
                    messages_worksheet.autofilter(0, 0, len(messages_df), len(messages_df.columns) - 1)
            
            logger.info(f"Exported user data to Excel: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting user data to Excel: {e}")
            return False
    
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
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )
            
            elements = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#082f49'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#082f49'),
                spaceAfter=12
            )
            
            # Title
            elements.append(Paragraph(f"User Report: {user.full_name}", title_style))
            elements.append(Spacer(1, 12))
            
            # User Information
            elements.append(Paragraph("User Information", heading_style))
            user_info_data = [
                ['Field', 'Value'],
                ['User ID', str(user.user_id)],
                ['Username', user.username or ''],
                ['Full Name', user.full_name],
                ['Phone', user.phone or ''],
                ['Bio', user.bio or ''],
            ]
            
            user_info_table = Table(user_info_data, colWidths=[3*inch, 4*inch])
            user_info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#082f49')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(user_info_table)
            elements.append(Spacer(1, 20))
            
            # Statistics
            elements.append(Paragraph("Statistics", heading_style))
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
            
            stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#082f49')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(stats_table)
            elements.append(Spacer(1, 20))
            
            # Messages (limited to 100)
            if messages:
                elements.append(Paragraph("Messages", heading_style))
                table_data = [['No', 'Message', 'Date', 'Media']]
                
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
                
                msg_table = Table(
                    table_data,
                    colWidths=[0.4*inch, 3.5*inch, 1.3*inch, 0.6*inch]
                )
                
                msg_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#082f49')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                
                elements.append(msg_table)
                
                if len(messages) > 100:
                    elements.append(Spacer(1, 12))
                    note = Paragraph(
                        f"<i>Note: Showing first 100 of {len(messages)} messages. Export to Excel for full data.</i>",
                        styles['Normal']
                    )
                    elements.append(note)
            
            doc.build(elements)
            
            logger.info(f"Exported user data to PDF: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting user data to PDF: {e}")
            return False

