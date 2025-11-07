"""
Excel formatting utilities.
"""

import logging
from typing import Dict, List, Optional
import xlsxwriter

logger = logging.getLogger(__name__)


class ExcelFormatter:
    """Handles Excel formatting (styles, columns, headers)."""
    
    # Default header format properties
    HEADER_BG_COLOR = '#082f49'
    HEADER_FONT_COLOR = 'white'
    
    def create_header_format(self, workbook: xlsxwriter.Workbook) -> xlsxwriter.Format:
        """
        Create header format for Excel worksheets.
        
        Args:
            workbook: xlsxwriter Workbook instance
            
        Returns:
            Formatted header style
        """
        return workbook.add_format({
            'bold': True,
            'bg_color': self.HEADER_BG_COLOR,
            'font_color': self.HEADER_FONT_COLOR,
            'border': 1
        })
    
    def create_cell_format(
        self,
        workbook: xlsxwriter.Workbook,
        text_wrap: bool = True,
        valign: str = 'top'
    ) -> xlsxwriter.Format:
        """
        Create cell format for Excel worksheets.
        
        Args:
            workbook: xlsxwriter Workbook instance
            text_wrap: Enable text wrapping
            valign: Vertical alignment ('top', 'middle', 'bottom')
            
        Returns:
            Formatted cell style
        """
        return workbook.add_format({
            'border': 1,
            'text_wrap': text_wrap,
            'valign': valign
        })
    
    def set_column_widths(
        self,
        worksheet: xlsxwriter.Worksheet,
        column_widths: Dict[str, float]
    ) -> None:
        """
        Set column widths for worksheet.
        
        Args:
            worksheet: xlsxwriter Worksheet instance
            column_widths: Dictionary mapping column letters to widths
        """
        for column, width in column_widths.items():
            worksheet.set_column(f'{column}:{column}', width)
    
    def apply_header_format(
        self,
        worksheet: xlsxwriter.Worksheet,
        header_format: xlsxwriter.Format,
        headers: List[str],
        start_row: int = 0
    ) -> None:
        """
        Apply header format to first row.
        
        Args:
            worksheet: xlsxwriter Worksheet instance
            header_format: Header format to apply
            headers: List of header names
            start_row: Starting row index (default: 0)
        """
        for col_num, value in enumerate(headers):
            worksheet.write(start_row, col_num, value, header_format)
    
    def add_autofilter(
        self,
        worksheet: xlsxwriter.Worksheet,
        first_row: int,
        first_col: int,
        last_row: int,
        last_col: int
    ) -> None:
        """
        Add auto-filter to worksheet.
        
        Args:
            worksheet: xlsxwriter Worksheet instance
            first_row: First row index
            first_col: First column index
            last_row: Last row index
            last_col: Last column index
        """
        worksheet.autofilter(first_row, first_col, last_row, last_col)

