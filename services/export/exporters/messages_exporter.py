"""
Messages exporter for Excel and PDF formats.
"""

import logging
from typing import List
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4

from database.models import Message
from database.db_manager import DatabaseManager
from services.export.base_exporter import BaseExporter
from services.export.formatters.excel_formatter import ExcelFormatter
from services.export.formatters.pdf_formatter import PDFFormatter
from services.export.formatters.data_formatter import DataFormatter
from utils.constants import DATETIME_FORMAT
from datetime import datetime

logger = logging.getLogger(__name__)


class MessagesExporter(BaseExporter):
    """Exports messages to Excel and PDF formats."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.excel_formatter = ExcelFormatter()
        self.pdf_formatter = PDFFormatter()
        self.data_formatter = DataFormatter()
    
    def export(
        self,
        data: List[Message],
        output_path: str,
        format_type: str = 'excel',
        **kwargs
    ) -> bool:
        """
        Export messages to file.
        
        Args:
            data: List of Message objects
            output_path: Output file path
            format_type: 'excel' or 'pdf'
            **kwargs: Additional options (include_stats, title)
            
        Returns:
            True if successful
        """
        if format_type == 'excel':
            return self.export_to_excel(data, output_path, **kwargs)
        elif format_type == 'pdf':
            return self.export_to_pdf(data, output_path, **kwargs)
        else:
            logger.error(f"Unsupported format: {format_type}")
            return False
    
    def export_to_excel(
        self,
        messages: List[Message],
        output_path: str,
        include_stats: bool = True
    ) -> bool:
        """Export messages to Excel file."""
        try:
            if not self._validate_output_path(output_path):
                return False
            
            # Format data
            data = self.data_formatter.format_messages_for_excel(messages, self.db_manager)
            df = pd.DataFrame(data)
            
            # Create Excel writer
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                # Write main data
                df.to_excel(writer, sheet_name='Messages', index=False)
                
                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Messages']
                
                # Apply formatting
                header_format = self.excel_formatter.create_header_format(workbook)
                self.excel_formatter.apply_header_format(worksheet, header_format, list(df.columns))
                
                # Set column widths
                self.excel_formatter.set_column_widths(worksheet, {
                    'A': 5,   # No
                    'B': 20,  # Full Name
                    'C': 15,  # Username
                    'D': 15,  # Phone
                    'E': 50,  # Message
                    'F': 20,  # Date
                    'G': 10,  # Has Media
                    'H': 12,  # Media Type
                    'I': 40   # Link
                })
                
                # Add auto-filter
                self.excel_formatter.add_autofilter(worksheet, 0, 0, len(df), len(df.columns) - 1)
                
                # Add statistics sheet if requested
                if include_stats:
                    stats = self.db_manager.get_dashboard_stats()
                    stats_data = self.data_formatter.format_stats_for_excel(stats)
                    
                    stats_df = pd.DataFrame(stats_data, columns=['Metric', 'Value'])
                    stats_df.to_excel(writer, sheet_name='Statistics', index=False)
                    
                    stats_worksheet = writer.sheets['Statistics']
                    stats_worksheet.set_column('A:A', 25)
                    stats_worksheet.set_column('B:B', 25)
            
            logger.info(f"Exported {len(messages)} messages to Excel: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting messages to Excel: {e}", exc_info=True)
            return False
    
    def export_to_pdf(
        self,
        messages: List[Message],
        output_path: str,
        title: str = "Messages Report",
        include_stats: bool = True
    ) -> bool:
        """Export messages to PDF file."""
        try:
            if not self._validate_output_path(output_path):
                return False
            
            # Create PDF
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
            elements.append(self.pdf_formatter.create_paragraph(title, title_style))
            elements.append(self.pdf_formatter.create_spacer())
            
            # Statistics
            if include_stats:
                stats = self.db_manager.get_dashboard_stats()
                heading_style = self.pdf_formatter.create_heading_style()
                elements.append(self.pdf_formatter.create_paragraph("Statistics", heading_style))
                
                from utils.constants import format_bytes
                stats_data = [
                    ['Metric', 'Value'],
                    ['Total Messages', str(stats['total_messages'])],
                    ['Total Users', str(stats['total_users'])],
                    ['Total Groups', str(stats['total_groups'])],
                    ['Total Media Size', format_bytes(stats['total_media_size'])],
                    ['Export Date', datetime.now().strftime(DATETIME_FORMAT)]
                ]
                
                stats_table = self.pdf_formatter.create_table(
                    stats_data,
                    col_widths=[3, 2],
                    style=self.pdf_formatter.create_table_style(body_bg_color='beige')
                )
                elements.append(stats_table)
                elements.append(self.pdf_formatter.create_spacer(height=20))
            
            # Messages
            heading_style = self.pdf_formatter.create_heading_style()
            elements.append(self.pdf_formatter.create_paragraph("Messages", heading_style))
            
            # Format messages for PDF
            table_data = self.data_formatter.format_messages_for_pdf(messages, self.db_manager, limit=100)
            
            # Create table
            msg_table = self.pdf_formatter.create_table(
                table_data,
                col_widths=[0.4, 1.5, 3, 1.3, 0.6],
                style=self.pdf_formatter.create_table_style(
                    grid_color='grey',
                    font_size=8,
                    header_font_size=10
                )
            )
            elements.append(msg_table)
            
            # Add note if messages were limited
            if len(messages) > 100:
                elements.append(self.pdf_formatter.create_spacer())
                note = self.pdf_formatter.create_paragraph(
                    f"<i>Note: Showing first 100 of {len(messages)} messages. Export to Excel for full data.</i>"
                )
                elements.append(note)
            
            # Build PDF
            doc.build(elements)
            
            logger.info(f"Exported messages to PDF: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting messages to PDF: {e}", exc_info=True)
            return False

