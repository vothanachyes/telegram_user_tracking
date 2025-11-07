"""
PDF formatting utilities.
"""

import logging
from typing import List, Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT

logger = logging.getLogger(__name__)


class PDFFormatter:
    """Handles PDF formatting (styles, tables, paragraphs)."""
    
    # Default color scheme
    PRIMARY_COLOR = '#082f49'
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def create_title_style(
        self,
        font_size: int = 24,
        alignment: str = TA_CENTER
    ) -> ParagraphStyle:
        """
        Create title style for PDF.
        
        Args:
            font_size: Font size for title
            alignment: Text alignment
            
        Returns:
            ParagraphStyle for titles
        """
        return ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=font_size,
            textColor=colors.HexColor(self.PRIMARY_COLOR),
            spaceAfter=30,
            alignment=alignment
        )
    
    def create_heading_style(
        self,
        font_size: int = 14
    ) -> ParagraphStyle:
        """
        Create heading style for PDF.
        
        Args:
            font_size: Font size for heading
            
        Returns:
            ParagraphStyle for headings
        """
        return ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=font_size,
            textColor=colors.HexColor(self.PRIMARY_COLOR),
            spaceAfter=12
        )
    
    def create_table_style(
        self,
        header_bg_color: str = None,
        header_text_color: str = 'whitesmoke',
        body_bg_color: str = None,
        grid_color: str = 'black',
        font_size: int = 10,
        header_font_size: int = 12
    ) -> List[tuple]:
        """
        Create table style for PDF tables.
        
        Args:
            header_bg_color: Header background color (default: PRIMARY_COLOR)
            header_text_color: Header text color
            body_bg_color: Body background color (default: white)
            grid_color: Grid line color
            font_size: Body font size
            header_font_size: Header font size
            
        Returns:
            List of TableStyle tuples
        """
        if header_bg_color is None:
            header_bg_color = self.PRIMARY_COLOR
        if body_bg_color is None:
            body_bg_color = colors.white
        
        return [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_bg_color)),
            ('TEXTCOLOR', (0, 0), (-1, 0), getattr(colors, header_text_color, colors.whitesmoke)),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), header_font_size),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), body_bg_color),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(grid_color) if isinstance(grid_color, str) else grid_color),
            ('FONTSIZE', (0, 1), (-1, -1), font_size),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]
    
    def create_table(
        self,
        data: List[List[str]],
        col_widths: List[float],
        style: List[tuple] = None
    ) -> Table:
        """
        Create a formatted table.
        
        Args:
            data: Table data (list of rows)
            col_widths: Column widths in inches
            style: Custom table style (uses default if None)
            
        Returns:
            Formatted Table object
        """
        table = Table(data, colWidths=[w * inch for w in col_widths])
        
        if style is None:
            style = self.create_table_style()
        
        table.setStyle(TableStyle(style))
        return table
    
    def create_paragraph(
        self,
        text: str,
        style: ParagraphStyle = None
    ) -> Paragraph:
        """
        Create a paragraph element.
        
        Args:
            text: Text content
            style: Paragraph style (uses Normal if None)
            
        Returns:
            Paragraph object
        """
        if style is None:
            style = self.styles['Normal']
        return Paragraph(text, style)
    
    def create_spacer(self, width: float = 1, height: float = 12) -> Spacer:
        """
        Create a spacer element.
        
        Args:
            width: Width in inches
            height: Height in points
            
        Returns:
            Spacer object
        """
        return Spacer(width, height)

