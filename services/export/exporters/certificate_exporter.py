"""
Certificate exporter for top users certificate in PDF and image formats.
"""

import logging
import os
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, KeepTogether, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from PIL import Image, ImageDraw, ImageFont
import io

from services.export.base_exporter import BaseExporter

logger = logging.getLogger(__name__)


class CertificateExporter(BaseExporter):
    """Exports top users certificate to PDF and image formats."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def export(
        self,
        data: List[Dict],
        output_path: str,
        format_type: str = 'pdf',
        **kwargs
    ) -> bool:
        """
        Export certificate to file.
        
        Args:
            data: List of user dictionaries
            output_path: Output file path
            format_type: 'pdf' or 'image'
            **kwargs: Additional options (group_name, date_range, title_en, title_km)
            
        Returns:
            True if successful
        """
        if format_type == 'pdf':
            return self.export_to_pdf(
                data,
                output_path,
                group_name=kwargs.get('group_name', ''),
                date_range=kwargs.get('date_range'),
                title_en=kwargs.get('title_en', 'Top Active Users Certificate'),
                title_km=kwargs.get('title_km', 'វិញ្ញាបនបត្រអ្នកប្រើប្រាស់សកម្មកំពូល')
            )
        elif format_type == 'image':
            return self.export_to_image(
                data,
                output_path,
                group_name=kwargs.get('group_name', ''),
                date_range=kwargs.get('date_range'),
                title_en=kwargs.get('title_en', 'Top Active Users Certificate'),
                title_km=kwargs.get('title_km', 'វិញ្ញាបនបត្រអ្នកប្រើប្រាស់សកម្មកំពូល'),
                image_size=kwargs.get('image_size', (1920, 1080))
            )
        else:
            logger.error(f"Unsupported format: {format_type}")
            return False
    
    def _get_gradient_colors_for_letter(self, letter: str) -> tuple:
        """Get consistent gradient colors based on first letter of name."""
        letter_num = ord(letter.upper()) - ord('A') if letter and letter.isalpha() else 0
        
        gradient_pairs = [
            ("#60A5FA", "#A78BFA"),  # Blue to Purple
            ("#F472B6", "#EF4444"),  # Pink to Red
            ("#34D399", "#14B8A6"),  # Green to Teal
            ("#FB923C", "#FBBF24"),  # Orange to Amber
            ("#22D3EE", "#3B82F6"),  # Cyan to Blue
            ("#818CF8", "#A78BFA"),  # Indigo to Purple
            ("#EF4444", "#F472B6"),  # Red to Pink
            ("#34D399", "#22D3EE"),  # Green to Cyan
            ("#A78BFA", "#F472B6"),  # Purple to Pink
            ("#22D3EE", "#2563EB"),  # Cyan to Blue
            ("#10B981", "#34D399"),  # Green
            ("#FCD34D", "#FB923C"),  # Yellow to Orange
            ("#EF4444", "#FB923C"),  # Red to Orange
            ("#A78BFA", "#6366F1"),  # Purple to Indigo
            ("#2563EB", "#06B6D4"),  # Blue to Cyan
            ("#14B8A6", "#34D399"),  # Teal to Green
            ("#FBBF24", "#FCD34D"),  # Amber to Yellow
            ("#F472B6", "#DC2626"),  # Pink to Red
            ("#6366F1", "#2563EB"),  # Indigo to Blue
            ("#10B981", "#14B8A6"),  # Green to Teal
            ("#FB923C", "#DC2626"),  # Orange to Red
            ("#A78BFA", "#F472B6"),  # Purple to Pink
            ("#06B6D4", "#2563EB"),  # Cyan to Blue
            ("#DC2626", "#FB923C"),  # Red to Orange
            ("#10B981", "#22D3EE"),  # Green to Cyan
            ("#A78BFA", "#2563EB"),  # Purple to Blue
        ]
        
        color_pair = gradient_pairs[letter_num % len(gradient_pairs)]
        return color_pair
    
    def _create_avatar_image(self, user: Dict, size: int = 100) -> Image.Image:
        """Create avatar image (photo or gradient with initial)."""
        profile_photo_path = user.get('profile_photo_path')
        full_name = user.get('full_name') or "Unknown"
        
        # Try to load profile photo
        if profile_photo_path and os.path.exists(profile_photo_path):
            try:
                img = Image.open(profile_photo_path)
                img = img.convert('RGB')
                img = img.resize((size, size), Image.Resampling.LANCZOS)
                
                # Create circular mask
                mask = Image.new('L', (size, size), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, size, size), fill=255)
                
                # Apply mask
                output = Image.new('RGB', (size, size), (255, 255, 255))
                output.paste(img, (0, 0), mask)
                return output
            except Exception as e:
                logger.warning(f"Failed to load profile photo: {e}")
        
        # Create gradient avatar with initial
        first_letter = full_name[0].upper() if full_name and len(full_name) > 0 else "?"
        gradient_colors = self._get_gradient_colors_for_letter(first_letter)
        
        # Create gradient image
        img = Image.new('RGB', (size, size))
        draw = ImageDraw.Draw(img)
        
        # Simple gradient (top-left to bottom-right)
        for i in range(size):
            ratio = i / size
            r1, g1, b1 = tuple(int(gradient_colors[0][j:j+2], 16) for j in (1, 3, 5))
            r2, g2, b2 = tuple(int(gradient_colors[1][j:j+2], 16) for j in (1, 3, 5))
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            draw.line([(i, 0), (i, size)], fill=(r, g, b))
        
        # Draw initial
        try:
            # Try to use a larger font
            font_size = size // 2
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.load_default()
            except:
                font = None
        
        # Get text bounding box
        if font:
            bbox = draw.textbbox((0, 0), first_letter, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = size // 3
            text_height = size // 3
        
        # Center text
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        draw.text((x, y), first_letter, fill=(255, 255, 255), font=font)
        
        return img
    
    def export_to_pdf(
        self,
        users: List[Dict],
        output_path: str,
        group_name: str = "",
        date_range: Optional[str] = None,
        title_en: str = "Top Active Users Certificate",
        title_km: str = "វិញ្ញាបនបត្រអ្នកប្រើប្រាស់សកម្មកំពូល"
    ) -> bool:
        """Export certificate to PDF."""
        try:
            if not self._validate_output_path(output_path):
                return False
            
            # Limit to top 5 users
            users = users[:5]
            
            if not users:
                logger.error("No users to export")
                return False
            
            # Create PDF document (A4 landscape for certificate)
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=40,
                leftMargin=40,
                topMargin=40,
                bottomMargin=40
            )
            
            elements = []
            
            # Title style
            title_style = ParagraphStyle(
                'CertificateTitle',
                parent=self.styles['Heading1'],
                fontSize=28,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=10,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            # Subtitle style
            subtitle_style = ParagraphStyle(
                'CertificateSubtitle',
                parent=self.styles['Normal'],
                fontSize=20,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=5,
                alignment=TA_CENTER,
                fontName='Helvetica'
            )
            
            # Header
            elements.append(Spacer(1, 0.5 * inch))
            elements.append(Paragraph(title_en, title_style))
            elements.append(Paragraph(title_km, subtitle_style))
            elements.append(Spacer(1, 0.2 * inch))
            
            if group_name:
                group_style = ParagraphStyle(
                    'GroupName',
                    parent=self.styles['Normal'],
                    fontSize=18,
                    textColor=colors.HexColor('#666666'),
                    spaceAfter=5,
                    alignment=TA_CENTER
                )
                elements.append(Paragraph(group_name, group_style))
            
            if date_range:
                date_style = ParagraphStyle(
                    'DateRange',
                    parent=self.styles['Normal'],
                    fontSize=14,
                    textColor=colors.HexColor('#888888'),
                    spaceAfter=20,
                    alignment=TA_CENTER
                )
                elements.append(Paragraph(date_range, date_style))
            
            elements.append(Spacer(1, 0.3 * inch))
            
            # User entries
            user_entries = []
            for idx, user in enumerate(users, 1):
                full_name = user.get('full_name') or "Unknown"
                message_count = user.get('message_count', 0)
                
                # Create avatar
                avatar_img = self._create_avatar_image(user, size=100)
                
                # Save avatar to bytes
                avatar_bytes = io.BytesIO()
                avatar_img.save(avatar_bytes, format='PNG')
                avatar_bytes.seek(0)
                
                # Rank badge colors
                rank_colors = {
                    1: ("#FFD700", "#FFA500"),  # Gold
                    2: ("#C0C0C0", "#808080"),  # Silver
                    3: ("#CD7F32", "#8B4513"),  # Bronze
                    4: ("#4169E1", "#1E90FF"),  # Blue
                    5: ("#4169E1", "#1E90FF"),  # Blue
                }
                colors_tuple = rank_colors.get(idx, ("#4169E1", "#1E90FF"))
                
                # User entry
                user_data = [
                    [RLImage(avatar_bytes, width=100, height=100)],
                    [Paragraph(f"<b>TOP {idx}</b>", ParagraphStyle(
                        'RankBadge',
                        parent=self.styles['Normal'],
                        fontSize=16,
                        textColor=colors.HexColor(colors_tuple[0]),
                        alignment=TA_CENTER,
                        fontName='Helvetica-Bold'
                    ))],
                    [Paragraph(full_name, ParagraphStyle(
                        'UserName',
                        parent=self.styles['Normal'],
                        fontSize=20,
                        textColor=colors.HexColor('#1a1a1a'),
                        alignment=TA_CENTER,
                        fontName='Helvetica-Bold'
                    ))],
                    [Paragraph(f"{message_count} Messages", ParagraphStyle(
                        'MessageCount',
                        parent=self.styles['Normal'],
                        fontSize=14,
                        textColor=colors.HexColor('#666666'),
                        alignment=TA_CENTER
                    ))],
                ]
                
                user_table = Table(user_data, colWidths=[2 * inch])
                user_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                
                user_entries.append(user_table)
            
            # Arrange users in 3 rows:
            # Row 1: TOP 1 (centered)
            # Row 2: TOP 2 and TOP 3 (justified/evenly spaced)
            # Row 3: TOP 4 and TOP 5 (justified/evenly spaced)
            
            if len(user_entries) > 0:
                # Row 1: TOP 1 (centered)
                if len(user_entries) >= 1:
                    row1_table = Table([[user_entries[0]]], colWidths=[2.2 * inch])
                    row1_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    elements.append(row1_table)
                    elements.append(Spacer(1, 0.2 * inch))
                
                # Row 2: TOP 2 and TOP 3 (horizontal)
                if len(user_entries) >= 3:
                    row2_table = Table([[user_entries[1], user_entries[2]]], colWidths=[2.2 * inch, 2.2 * inch])
                    row2_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    elements.append(row2_table)
                    elements.append(Spacer(1, 0.2 * inch))
                elif len(user_entries) == 2:
                    # Only 2 users, show TOP 2 in second row (centered)
                    row2_table = Table([[user_entries[1]]], colWidths=[2.2 * inch])
                    row2_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    elements.append(row2_table)
                    elements.append(Spacer(1, 0.2 * inch))
                
                # Row 3: TOP 4 and TOP 5 (horizontal)
                if len(user_entries) >= 5:
                    row3_table = Table([[user_entries[3], user_entries[4]]], colWidths=[2.2 * inch, 2.2 * inch])
                    row3_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    elements.append(row3_table)
                elif len(user_entries) == 4:
                    # Only 4 users, show TOP 4 in third row (centered)
                    row3_table = Table([[user_entries[3]]], colWidths=[2.2 * inch])
                    row3_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    elements.append(row3_table)
            
            elements.append(Spacer(1, 0.3 * inch))
            
            # Footer
            footer_style = ParagraphStyle(
                'Footer',
                parent=self.styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#888888'),
                alignment=TA_CENTER
            )
            footer_text = f"Generated on: {datetime.now().strftime('%B %d, %Y')}"
            elements.append(Paragraph(footer_text, footer_style))
            
            # Build PDF
            doc.build(elements)
            
            logger.info(f"Exported certificate to PDF: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting certificate to PDF: {e}", exc_info=True)
            return False
    
    def export_to_image(
        self,
        users: List[Dict],
        output_path: str,
        group_name: str = "",
        date_range: Optional[str] = None,
        title_en: str = "Top Active Users Certificate",
        title_km: str = "វិញ្ញាបនបត្រអ្នកប្រើប្រាស់សកម្មកំពូល",
        image_size: tuple = (1920, 1080)
    ) -> bool:
        """Export certificate to image (PNG/JPEG)."""
        try:
            if not self._validate_output_path(output_path):
                return False
            
            # Limit to top 5 users
            users = users[:5]
            
            if not users:
                logger.error("No users to export")
                return False
            
            # Create image
            width, height = image_size
            img = Image.new('RGB', (width, height), color='#E8F4F8')
            draw = ImageDraw.Draw(img)
            
            # Draw decorative border
            border_width = 15
            border_color = '#1E90FF'
            draw.rectangle(
                [(border_width, border_width), (width - border_width, height - border_width)],
                outline=border_color,
                width=border_width
            )
            
            # Inner border
            inner_border = border_width + 10
            draw.rectangle(
                [(inner_border, inner_border), (width - inner_border, height - inner_border)],
                outline='#4169E1',
                width=5
            )
            
            # Try to load fonts
            try:
                title_font = ImageFont.truetype("arial.ttf", 48)
                subtitle_font = ImageFont.truetype("arial.ttf", 32)
                name_font = ImageFont.truetype("arial.ttf", 36)
                count_font = ImageFont.truetype("arial.ttf", 24)
                footer_font = ImageFont.truetype("arial.ttf", 20)
            except:
                try:
                    title_font = ImageFont.load_default()
                    subtitle_font = ImageFont.load_default()
                    name_font = ImageFont.load_default()
                    count_font = ImageFont.load_default()
                    footer_font = ImageFont.load_default()
                except:
                    title_font = None
                    subtitle_font = None
                    name_font = None
                    count_font = None
                    footer_font = None
            
            y_offset = 80
            
            # Title
            title_bbox = draw.textbbox((0, 0), title_en, font=title_font) if title_font else (0, 0, 0, 0)
            title_width = title_bbox[2] - title_bbox[0] if title_font else len(title_en) * 20
            draw.text(
                ((width - title_width) // 2, y_offset),
                title_en,
                fill='#1a1a1a',
                font=title_font
            )
            y_offset += 60
            
            # Khmer subtitle
            subtitle_bbox = draw.textbbox((0, 0), title_km, font=subtitle_font) if subtitle_font else (0, 0, 0, 0)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0] if subtitle_font else len(title_km) * 15
            draw.text(
                ((width - subtitle_width) // 2, y_offset),
                title_km,
                fill='#1a1a1a',
                font=subtitle_font
            )
            y_offset += 50
            
            # Group name
            if group_name:
                group_bbox = draw.textbbox((0, 0), group_name, font=subtitle_font) if subtitle_font else (0, 0, 0, 0)
                group_width = group_bbox[2] - group_bbox[0] if subtitle_font else len(group_name) * 15
                draw.text(
                    ((width - group_width) // 2, y_offset),
                    group_name,
                    fill='#666666',
                    font=subtitle_font
                )
                y_offset += 40
            
            # Date range
            if date_range:
                date_bbox = draw.textbbox((0, 0), date_range, font=count_font) if count_font else (0, 0, 0, 0)
                date_width = date_bbox[2] - date_bbox[0] if count_font else len(date_range) * 10
                draw.text(
                    ((width - date_width) // 2, y_offset),
                    date_range,
                    fill='#888888',
                    font=count_font
                )
                y_offset += 50
            
            y_offset += 40
            
            # User entries arranged in 3 rows:
            # Row 1: TOP 1 (centered)
            # Row 2: TOP 2 and TOP 3 (justified/evenly spaced)
            # Row 3: TOP 4 and TOP 5 (justified/evenly spaced)
            
            avatar_size = 120
            row_spacing = 80
            user_spacing = 200  # Spacing between users in same row
            
            # Row 1: TOP 1 (centered)
            if len(users) >= 1:
                user = users[0]
                full_name = user.get('full_name') or "Unknown"
                message_count = user.get('message_count', 0)
                x_pos = width // 2
                
                # Create and paste avatar
                avatar_img = self._create_avatar_image(user, size=avatar_size)
                avatar_with_border = Image.new('RGB', (avatar_size + 10, avatar_size + 10), color='white')
                avatar_with_border.paste(avatar_img, (5, 5))
                img.paste(avatar_with_border, (x_pos - avatar_size // 2 - 5, y_offset))
                
                # Rank badge
                rank_text = "TOP 1"
                rank_color = "#FFD700"  # Gold
                rank_bbox = draw.textbbox((0, 0), rank_text, font=count_font) if count_font else (0, 0, 0, 0)
                rank_width = rank_bbox[2] - rank_bbox[0] if count_font else len(rank_text) * 12
                draw.text(
                    (x_pos - rank_width // 2, y_offset - 30),
                    rank_text,
                    fill=rank_color,
                    font=count_font
                )
                
                # Name
                name_bbox = draw.textbbox((0, 0), full_name, font=name_font) if name_font else (0, 0, 0, 0)
                name_width = name_bbox[2] - name_bbox[0] if name_font else len(full_name) * 18
                draw.text(
                    (x_pos - name_width // 2, y_offset + avatar_size + 20),
                    full_name,
                    fill='#1a1a1a',
                    font=name_font
                )
                
                # Message count
                count_text = f"{message_count} Messages"
                count_bbox = draw.textbbox((0, 0), count_text, font=count_font) if count_font else (0, 0, 0, 0)
                count_width = count_bbox[2] - count_bbox[0] if count_font else len(count_text) * 10
                draw.text(
                    (x_pos - count_width // 2, y_offset + avatar_size + 70),
                    count_text,
                    fill='#666666',
                    font=count_font
                )
                
                y_offset += avatar_size + 100 + row_spacing
            
            # Row 2: TOP 2 and TOP 3
            if len(users) >= 3:
                row2_x_positions = [width // 2 - user_spacing // 2, width // 2 + user_spacing // 2]
                for i, user_idx in enumerate([1, 2]):
                    user = users[user_idx]
                    full_name = user.get('full_name') or "Unknown"
                    message_count = user.get('message_count', 0)
                    x_pos = row2_x_positions[i]
                    
                    # Create and paste avatar
                    avatar_img = self._create_avatar_image(user, size=avatar_size)
                    avatar_with_border = Image.new('RGB', (avatar_size + 10, avatar_size + 10), color='white')
                    avatar_with_border.paste(avatar_img, (5, 5))
                    img.paste(avatar_with_border, (x_pos - avatar_size // 2 - 5, y_offset))
                    
                    # Rank badge
                    rank_text = f"TOP {user_idx + 1}"
                    rank_colors = {2: "#C0C0C0", 3: "#CD7F32"}  # Silver, Bronze
                    rank_color = rank_colors.get(user_idx + 1, "#4169E1")
                    rank_bbox = draw.textbbox((0, 0), rank_text, font=count_font) if count_font else (0, 0, 0, 0)
                    rank_width = rank_bbox[2] - rank_bbox[0] if count_font else len(rank_text) * 12
                    draw.text(
                        (x_pos - rank_width // 2, y_offset - 30),
                        rank_text,
                        fill=rank_color,
                        font=count_font
                    )
                    
                    # Name
                    name_bbox = draw.textbbox((0, 0), full_name, font=name_font) if name_font else (0, 0, 0, 0)
                    name_width = name_bbox[2] - name_bbox[0] if name_font else len(full_name) * 18
                    draw.text(
                        (x_pos - name_width // 2, y_offset + avatar_size + 20),
                        full_name,
                        fill='#1a1a1a',
                        font=name_font
                    )
                    
                    # Message count
                    count_text = f"{message_count} Messages"
                    count_bbox = draw.textbbox((0, 0), count_text, font=count_font) if count_font else (0, 0, 0, 0)
                    count_width = count_bbox[2] - count_bbox[0] if count_font else len(count_text) * 10
                    draw.text(
                        (x_pos - count_width // 2, y_offset + avatar_size + 70),
                        count_text,
                        fill='#666666',
                        font=count_font
                    )
                
                y_offset += avatar_size + 100 + row_spacing
            elif len(users) == 2:
                # Only 2 users, show TOP 2 in second row (centered)
                user = users[1]
                full_name = user.get('full_name') or "Unknown"
                message_count = user.get('message_count', 0)
                x_pos = width // 2
                
                # Create and paste avatar
                avatar_img = self._create_avatar_image(user, size=avatar_size)
                avatar_with_border = Image.new('RGB', (avatar_size + 10, avatar_size + 10), color='white')
                avatar_with_border.paste(avatar_img, (5, 5))
                img.paste(avatar_with_border, (x_pos - avatar_size // 2 - 5, y_offset))
                
                # Rank badge
                rank_text = "TOP 2"
                rank_color = "#C0C0C0"  # Silver
                rank_bbox = draw.textbbox((0, 0), rank_text, font=count_font) if count_font else (0, 0, 0, 0)
                rank_width = rank_bbox[2] - rank_bbox[0] if count_font else len(rank_text) * 12
                draw.text(
                    (x_pos - rank_width // 2, y_offset - 30),
                    rank_text,
                    fill=rank_color,
                    font=count_font
                )
                
                # Name
                name_bbox = draw.textbbox((0, 0), full_name, font=name_font) if name_font else (0, 0, 0, 0)
                name_width = name_bbox[2] - name_bbox[0] if name_font else len(full_name) * 18
                draw.text(
                    (x_pos - name_width // 2, y_offset + avatar_size + 20),
                    full_name,
                    fill='#1a1a1a',
                    font=name_font
                )
                
                # Message count
                count_text = f"{message_count} Messages"
                count_bbox = draw.textbbox((0, 0), count_text, font=count_font) if count_font else (0, 0, 0, 0)
                count_width = count_bbox[2] - count_bbox[0] if count_font else len(count_text) * 10
                draw.text(
                    (x_pos - count_width // 2, y_offset + avatar_size + 70),
                    count_text,
                    fill='#666666',
                    font=count_font
                )
                
                y_offset += avatar_size + 100 + row_spacing
            
            # Row 3: TOP 4 and TOP 5
            if len(users) >= 5:
                row3_x_positions = [width // 2 - user_spacing // 2, width // 2 + user_spacing // 2]
                for i, user_idx in enumerate([3, 4]):
                    user = users[user_idx]
                    full_name = user.get('full_name') or "Unknown"
                    message_count = user.get('message_count', 0)
                    x_pos = row3_x_positions[i]
                    
                    # Create and paste avatar
                    avatar_img = self._create_avatar_image(user, size=avatar_size)
                    avatar_with_border = Image.new('RGB', (avatar_size + 10, avatar_size + 10), color='white')
                    avatar_with_border.paste(avatar_img, (5, 5))
                    img.paste(avatar_with_border, (x_pos - avatar_size // 2 - 5, y_offset))
                    
                    # Rank badge
                    rank_text = f"TOP {user_idx + 1}"
                    rank_color = "#4169E1"  # Blue
                    rank_bbox = draw.textbbox((0, 0), rank_text, font=count_font) if count_font else (0, 0, 0, 0)
                    rank_width = rank_bbox[2] - rank_bbox[0] if count_font else len(rank_text) * 12
                    draw.text(
                        (x_pos - rank_width // 2, y_offset - 30),
                        rank_text,
                        fill=rank_color,
                        font=count_font
                    )
                    
                    # Name
                    name_bbox = draw.textbbox((0, 0), full_name, font=name_font) if name_font else (0, 0, 0, 0)
                    name_width = name_bbox[2] - name_bbox[0] if name_font else len(full_name) * 18
                    draw.text(
                        (x_pos - name_width // 2, y_offset + avatar_size + 20),
                        full_name,
                        fill='#1a1a1a',
                        font=name_font
                    )
                    
                    # Message count
                    count_text = f"{message_count} Messages"
                    count_bbox = draw.textbbox((0, 0), count_text, font=count_font) if count_font else (0, 0, 0, 0)
                    count_width = count_bbox[2] - count_bbox[0] if count_font else len(count_text) * 10
                    draw.text(
                        (x_pos - count_width // 2, y_offset + avatar_size + 70),
                        count_text,
                        fill='#666666',
                        font=count_font
                    )
            elif len(users) == 4:
                # Only 4 users, show TOP 4 in third row (centered)
                user = users[3]
                full_name = user.get('full_name') or "Unknown"
                message_count = user.get('message_count', 0)
                x_pos = width // 2
                
                # Create and paste avatar
                avatar_img = self._create_avatar_image(user, size=avatar_size)
                avatar_with_border = Image.new('RGB', (avatar_size + 10, avatar_size + 10), color='white')
                avatar_with_border.paste(avatar_img, (5, 5))
                img.paste(avatar_with_border, (x_pos - avatar_size // 2 - 5, y_offset))
                
                # Rank badge
                rank_text = "TOP 4"
                rank_color = "#4169E1"  # Blue
                rank_bbox = draw.textbbox((0, 0), rank_text, font=count_font) if count_font else (0, 0, 0, 0)
                rank_width = rank_bbox[2] - rank_bbox[0] if count_font else len(rank_text) * 12
                draw.text(
                    (x_pos - rank_width // 2, y_offset - 30),
                    rank_text,
                    fill=rank_color,
                    font=count_font
                )
                
                # Name
                name_bbox = draw.textbbox((0, 0), full_name, font=name_font) if name_font else (0, 0, 0, 0)
                name_width = name_bbox[2] - name_bbox[0] if name_font else len(full_name) * 18
                draw.text(
                    (x_pos - name_width // 2, y_offset + avatar_size + 20),
                    full_name,
                    fill='#1a1a1a',
                    font=name_font
                )
                
                # Message count
                count_text = f"{message_count} Messages"
                count_bbox = draw.textbbox((0, 0), count_text, font=count_font) if count_font else (0, 0, 0, 0)
                count_width = count_bbox[2] - count_bbox[0] if count_font else len(count_text) * 10
                draw.text(
                    (x_pos - count_width // 2, y_offset + avatar_size + 70),
                    count_text,
                    fill='#666666',
                    font=count_font
                )
            
            # Footer
            footer_text = f"Generated on: {datetime.now().strftime('%B %d, %Y')}"
            footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font) if footer_font else (0, 0, 0, 0)
            footer_width = footer_bbox[2] - footer_bbox[0] if footer_font else len(footer_text) * 10
            draw.text(
                ((width - footer_width) // 2, height - 60),
                footer_text,
                fill='#888888',
                font=footer_font
            )
            
            # Save image
            img.save(output_path, quality=95)
            
            logger.info(f"Exported certificate to image: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting certificate to image: {e}", exc_info=True)
            return False

