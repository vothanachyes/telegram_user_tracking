"""
Users exporter for Excel and PDF formats.
"""

import logging
from typing import List
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.pagesizes import A4

from database.models import TelegramUser
from services.export.base_exporter import BaseExporter
from services.export.formatters.excel_formatter import ExcelFormatter
from services.export.formatters.pdf_formatter import PDFFormatter
from services.export.formatters.data_formatter import DataFormatter

logger = logging.getLogger(__name__)


class UsersExporter(BaseExporter):
    """Exports users to Excel and PDF formats."""
    
    def __init__(self):
        self.excel_formatter = ExcelFormatter()
        self.pdf_formatter = PDFFormatter()
        self.data_formatter = DataFormatter()
    
    def export(
        self,
        data: List[TelegramUser],
        output_path: str,
        format_type: str = 'excel',
        **kwargs
    ) -> bool:
        """
        Export users to file.
        
        Args:
            data: List of TelegramUser objects
            output_path: Output file path
            format_type: 'excel' or 'pdf'
            **kwargs: Additional options (title)
            
        Returns:
            True if successful
        """
        if format_type == 'excel':
            return self.export_to_excel(data, output_path)
        elif format_type == 'pdf':
            title = kwargs.get('title', 'Users Report')
            return self.export_to_pdf(data, output_path, title)
        else:
            logger.error(f"Unsupported format: {format_type}")
            return False
    
    def export_to_excel(
        self,
        users: List[TelegramUser],
        output_path: str
    ) -> bool:
        """Export users to Excel file."""
        try:
            if not self._validate_output_path(output_path):
                return False
            
            # Format data
            data = self.data_formatter.format_users_for_excel(users)
            df = pd.DataFrame(data)
            
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Users', index=False)
                
                workbook = writer.book
                worksheet = writer.sheets['Users']
                
                # Apply formatting
                header_format = self.excel_formatter.create_header_format(workbook)
                self.excel_formatter.apply_header_format(worksheet, header_format, list(df.columns))
                
                # Set column widths
                self.excel_formatter.set_column_widths(worksheet, {
                    'A': 5,   # No
                    'B': 12,  # User ID
                    'C': 15,  # Username
                    'D': 20,  # Full Name
                    'E': 15,  # First Name
                    'F': 15,  # Last Name
                    'G': 15,  # Phone
                    'H': 30,  # Bio
                    'I': 20   # Created
                })
                
                # Add auto-filter
                self.excel_formatter.add_autofilter(worksheet, 0, 0, len(df), len(df.columns) - 1)
            
            logger.info(f"Exported {len(users)} users to Excel: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting users to Excel: {e}")
            return False
    
    def export_to_pdf(
        self,
        users: List[TelegramUser],
        output_path: str,
        title: str = "Users Report"
    ) -> bool:
        """Export users to PDF file."""
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
            elements.append(self.pdf_formatter.create_paragraph(title, title_style))
            elements.append(self.pdf_formatter.create_spacer(height=20))
            
            # Format users for PDF
            table_data = self.data_formatter.format_users_for_pdf(users, limit=100)
            
            # Create table
            user_table = self.pdf_formatter.create_table(
                table_data,
                col_widths=[0.5, 1.5, 2.5, 1.5],
                style=self.pdf_formatter.create_table_style(
                    grid_color='grey',
                    font_size=9,
                    header_font_size=10
                )
            )
            elements.append(user_table)
            
            # Add note if users were limited
            if len(users) > 100:
                elements.append(self.pdf_formatter.create_spacer())
                note = self.pdf_formatter.create_paragraph(
                    f"<i>Note: Showing first 100 of {len(users)} users. Export to Excel for full data.</i>"
                )
                elements.append(note)
            
            doc.build(elements)
            
            logger.info(f"Exported users to PDF: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting users to PDF: {e}")
            return False

