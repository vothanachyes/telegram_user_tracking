"""
Top Users Certificate component for displaying top 5 active users in certificate style.
"""

import flet as ft
from typing import List, Dict, Optional
from datetime import datetime
from ui.theme import theme_manager


class TopUsersCertificate(ft.Container):
    """Certificate-style display for top 5 active users."""
    
    def __init__(
        self,
        group_name: str = "",
        date_range: Optional[str] = None
    ):
        self.group_name = group_name
        self.date_range = date_range
        self.users: List[Dict] = []
        
        # Main content container
        self.content_container = ft.Container()
        
        super().__init__(
            content=self.content_container,
            padding=ft.padding.all(40),
            expand=True
        )
    
    def _get_gradient_colors_for_letter(self, letter: str) -> tuple:
        """Get consistent gradient colors based on first letter of name."""
        letter_num = ord(letter.upper()) - ord('A') if letter and letter.isalpha() else 0
        
        gradient_pairs = [
            (ft.Colors.BLUE_400, ft.Colors.PURPLE_400),
            (ft.Colors.PINK_400, ft.Colors.RED_400),
            (ft.Colors.GREEN_400, ft.Colors.TEAL_400),
            (ft.Colors.ORANGE_400, ft.Colors.AMBER_400),
            (ft.Colors.CYAN_400, ft.Colors.BLUE_400),
            (ft.Colors.INDIGO_400, ft.Colors.PURPLE_400),
            (ft.Colors.RED_400, ft.Colors.PINK_400),
            (ft.Colors.GREEN_400, ft.Colors.CYAN_400),
            (ft.Colors.PURPLE_400, ft.Colors.PINK_400),
            (ft.Colors.CYAN_400, ft.Colors.BLUE_500),
            (ft.Colors.GREEN_500, ft.Colors.GREEN_400),
            (ft.Colors.YELLOW_400, ft.Colors.ORANGE_400),
            (ft.Colors.RED_400, ft.Colors.ORANGE_400),
            (ft.Colors.PURPLE_400, ft.Colors.INDIGO_400),
            (ft.Colors.BLUE_500, ft.Colors.CYAN_500),
            (ft.Colors.TEAL_400, ft.Colors.GREEN_400),
            (ft.Colors.AMBER_400, ft.Colors.YELLOW_400),
            (ft.Colors.PINK_400, ft.Colors.RED_500),
            (ft.Colors.INDIGO_500, ft.Colors.BLUE_500),
            (ft.Colors.GREEN_500, ft.Colors.TEAL_500),
            (ft.Colors.ORANGE_500, ft.Colors.RED_500),
            (ft.Colors.PURPLE_500, ft.Colors.PINK_500),
            (ft.Colors.CYAN_500, ft.Colors.BLUE_500),
            (ft.Colors.RED_500, ft.Colors.ORANGE_500),
            (ft.Colors.GREEN_500, ft.Colors.CYAN_500),
            (ft.Colors.PURPLE_500, ft.Colors.BLUE_500),
        ]
        
        color_pair = gradient_pairs[letter_num % len(gradient_pairs)]
        return color_pair
    
    def _create_rank_badge(self, rank: int) -> ft.Container:
        """Create rank badge (TOP 1, TOP 2, etc.)."""
        badge_colors = {
            1: ("#FFD700", "#FFA500"),  # Gold
            2: ("#C0C0C0", "#808080"),  # Silver
            3: ("#CD7F32", "#8B4513"),  # Bronze
            4: ("#4169E1", "#1E90FF"),  # Blue
            5: ("#4169E1", "#1E90FF"),  # Blue
        }
        
        colors = badge_colors.get(rank, ("#4169E1", "#1E90FF"))
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "TOP",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE
                ),
                ft.Text(
                    str(rank),
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE
                ),
            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=60,
            height=60,
            bgcolor=colors[0],
            border_radius=30,
            alignment=ft.alignment.center,
            border=ft.border.all(3, colors[1]),
        )
    
    def _create_user_avatar(self, user: Dict) -> ft.Container:
        """Create user avatar (photo or gradient with initial)."""
        profile_photo_path = user.get('profile_photo_path')
        full_name = user.get('full_name') or "Unknown"
        
        if profile_photo_path:
            try:
                return ft.Container(
                    content=ft.Image(
                        src=profile_photo_path,
                        width=100,
                        height=100,
                        fit=ft.ImageFit.COVER,
                        border_radius=50
                    ),
                    width=100,
                    height=100,
                    border_radius=50,
                    border=ft.border.all(4, ft.Colors.WHITE),
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                )
            except Exception:
                pass  # Fallback to avatar
        
        # Create gradient avatar with initial
        first_letter = full_name[0].upper() if full_name and len(full_name) > 0 else "?"
        gradient_colors = self._get_gradient_colors_for_letter(first_letter)
        
        return ft.Container(
            content=ft.Text(
                first_letter,
                size=40,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE
            ),
            width=100,
            height=100,
            border_radius=50,
            border=ft.border.all(4, ft.Colors.WHITE),
            alignment=ft.alignment.center,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=gradient_colors
            ),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS
        )
    
    def _create_user_entry(self, user: Dict, rank: int) -> ft.Container:
        """Create a single user entry for the certificate."""
        full_name = user.get('full_name') or "Unknown"
        message_count = user.get('message_count', 0)
        
        # Rank badge
        rank_badge = self._create_rank_badge(rank)
        
        # Avatar
        avatar = self._create_user_avatar(user)
        
        # User info
        name_text = ft.Text(
            full_name,
            size=24,
            weight=ft.FontWeight.BOLD,
            color="#1a1a1a" if not theme_manager.is_dark else "#ffffff",
            text_align=ft.TextAlign.CENTER
        )
        
        message_text = ft.Text(
            f"{message_count} {theme_manager.t('messages_sent') or 'Messages Sent'}",
            size=16,
            color="#666666" if not theme_manager.is_dark else "#cccccc",
            text_align=ft.TextAlign.CENTER
        )
        
        user_entry = ft.Container(
            content=ft.Column([
                rank_badge,
                ft.Container(height=10),
                avatar,
                ft.Container(height=15),
                name_text,
                ft.Container(height=5),
                message_text,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            padding=ft.padding.all(20),
            width=200,
        )
        
        return user_entry
    
    def update_users(
        self,
        users: List[Dict],
        group_name: str = "",
        date_range: Optional[str] = None
    ):
        """Update certificate with new user data."""
        self.users = users[:5]  # Limit to top 5
        self.group_name = group_name
        self.date_range = date_range
        
        # Certificate background color (light blue/white for certificate feel)
        bg_color = "#E8F4F8" if not theme_manager.is_dark else "#1a1a2e"
        border_color = "#1E90FF" if not theme_manager.is_dark else "#4169E1"
        
        # Header
        title_en = theme_manager.t("certificate_title") or "Top Active Users Certificate"
        title_km = "វិញ្ញាបនបត្រអ្នកប្រើប្រាស់សកម្មកំពូល"
        
        header = ft.Column([
            ft.Text(
                title_en,
                size=28,
                weight=ft.FontWeight.BOLD,
                color="#1a1a1a" if not theme_manager.is_dark else "#ffffff",
                text_align=ft.TextAlign.CENTER
            ),
            ft.Text(
                title_km,
                size=20,
                weight=ft.FontWeight.W_500,
                color="#1a1a1a" if not theme_manager.is_dark else "#ffffff",
                text_align=ft.TextAlign.CENTER
            ),
            ft.Container(height=10),
            ft.Text(
                group_name or "",
                size=18,
                color="#666666" if not theme_manager.is_dark else "#cccccc",
                text_align=ft.TextAlign.CENTER
            ),
            ft.Container(height=5),
            ft.Text(
                date_range or "",
                size=14,
                color="#888888" if not theme_manager.is_dark else "#aaaaaa",
                text_align=ft.TextAlign.CENTER
            ) if date_range else ft.Container(),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        
        # User entries
        if not self.users:
            content = ft.Column([
                header,
                ft.Container(height=40),
                ft.Text(
                    theme_manager.t("no_data") or "No data available",
                    size=18,
                    color="#666666" if not theme_manager.is_dark else "#cccccc",
                    text_align=ft.TextAlign.CENTER
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        else:
            user_entries = []
            for idx, user in enumerate(self.users, 1):
                user_entries.append(self._create_user_entry(user, idx))
            
            # Arrange users in 3 rows:
            # Row 1: TOP 1 (centered)
            # Row 2: TOP 2 and TOP 3 (justified/evenly spaced)
            # Row 3: TOP 4 and TOP 5 (justified/evenly spaced)
            
            rows = []
            
            # Row 1: TOP 1 (centered)
            if len(user_entries) > 0:
                rows.append(
                    ft.Row(
                        [user_entries[0]],
                        spacing=0,
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                )
            
            # Row 2: TOP 2 and TOP 3 (justified/evenly spaced)
            if len(user_entries) >= 3:
                rows.append(
                    ft.Row(
                        user_entries[1:3],
                        spacing=60,
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                )
            elif len(user_entries) == 2:
                # Only 2 users, show both in second row
                rows.append(
                    ft.Row(
                        [user_entries[1]],
                        spacing=0,
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                )
            
            # Row 3: TOP 4 and TOP 5 (justified/evenly spaced)
            if len(user_entries) >= 5:
                rows.append(
                    ft.Row(
                        user_entries[3:5],
                        spacing=60,
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                )
            elif len(user_entries) == 4:
                # Only 4 users, show TOP 4 in third row
                rows.append(
                    ft.Row(
                        [user_entries[3]],
                        spacing=0,
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                )
            
            users_column = ft.Column(
                rows,
                spacing=40,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            
            content = ft.Column([
                header,
                ft.Container(height=40),
                users_column,
                ft.Container(height=40),
                # Footer
                ft.Text(
                    f"{theme_manager.t('generated_on') or 'Generated on'}: {datetime.now().strftime('%B %d, %Y')}",
                    size=12,
                    color="#888888" if not theme_manager.is_dark else "#aaaaaa",
                    text_align=ft.TextAlign.CENTER
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        
        # Decorative border
        border_width = 8
        
        # Create certificate container with decorative border
        certificate_content = ft.Container(
            content=ft.Container(
                content=content,
                padding=ft.padding.all(40),
                bgcolor=bg_color,
            ),
            border=ft.border.all(border_width, border_color),
            border_radius=10,
            padding=ft.padding.all(20),
            bgcolor="#ffffff" if not theme_manager.is_dark else "#2a2a3e",
        )
        
        self.content_container.content = certificate_content
        self.content_container.alignment = ft.alignment.center
        
        # Update if page is set
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def set_page(self, page: ft.Page):
        """Set page reference."""
        self.page = page

