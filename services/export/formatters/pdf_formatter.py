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
    
    # Color name to hex mapping for common colors
    COLOR_NAME_TO_HEX = {
        'grey': '#808080',
        'gray': '#808080',
        'lightgrey': '#D3D3D3',
        'lightgray': '#D3D3D3',
        'darkgrey': '#A9A9A9',
        'darkgray': '#A9A9A9',
        'silver': '#C0C0C0',
        'beige': '#F5F5DC',
    }
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def _parse_color(self, color: Any) -> Any:
        """
        Parse color value to ReportLab color object.
        
        Args:
            color: Color value (hex string, color name, or color object)
            
        Returns:
            ReportLab color object
        """
        # If already a color object, return as is
        if isinstance(color, colors.Color):
            return color
        
        # If None, return None
        if color is None:
            return None
        
        # If it's a string
        if isinstance(color, str):
            # If it's a hex string, use HexColor
            if color.startswith('#'):
                return colors.HexColor(color)
            
            # If it's a known color name, convert to hex
            color_lower = color.lower()
            if color_lower in self.COLOR_NAME_TO_HEX:
                return colors.HexColor(self.COLOR_NAME_TO_HEX[color_lower])
            
            # Try to get from colors module (for built-in colors like 'black', 'white', etc.)
            color_obj = getattr(colors, color_lower, None)
            if color_obj is not None and isinstance(color_obj, colors.Color):
                return color_obj
            
            # If not found, try HexColor anyway (might be a valid hex without #)
            try:
                return colors.HexColor(f"#{color}" if not color.startswith('#') else color)
            except (ValueError, AttributeError):
                # Fallback to grey if color cannot be parsed
                logger.warning(f"Could not parse color '{color}', using grey as fallback")
                return colors.HexColor('#808080')
        
        # For any other type, return as is (might be a valid color object)
        return color
    
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
        
        # Parse all color values
        parsed_header_bg = self._parse_color(header_bg_color)
        parsed_header_text = self._parse_color(header_text_color) or colors.whitesmoke
        parsed_body_bg = self._parse_color(body_bg_color) if body_bg_color is not None else colors.white
        parsed_grid = self._parse_color(grid_color) or colors.black
        
        return [
            ('BACKGROUND', (0, 0), (-1, 0), parsed_header_bg),
            ('TEXTCOLOR', (0, 0), (-1, 0), parsed_header_text),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), header_font_size),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), parsed_body_bg),
            ('GRID', (0, 0), (-1, -1), 1, parsed_grid),
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

