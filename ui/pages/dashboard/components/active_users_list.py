"""
Active users list component for dashboard.
"""

import flet as ft
from typing import List, Dict, Optional
from ui.theme import theme_manager


class ActiveUsersListComponent:
    """Component for displaying top active users."""
    
    def __init__(self):
        self.users_list = ft.Column(
            [], 
            spacing=theme_manager.spacing_xs, 
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        self.page: Optional[ft.Page] = None
    
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
    
    def _create_ranking_badge(self, rank: int) -> ft.Container:
        """Create ranking badge/icon for all users."""
        if rank == 1:
            return ft.Container(
                content=ft.Icon(ft.Icons.EMOJI_EVENTS, size=24, color=ft.Colors.AMBER_600),
                width=32, height=32,
                alignment=ft.alignment.center,
                tooltip="Rank #1"
            )
        elif rank == 2:
            return ft.Container(
                content=ft.Icon(ft.Icons.EMOJI_EVENTS, size=24, color=ft.Colors.GREY_600),
                width=32, height=32,
                alignment=ft.alignment.center,
                tooltip="Rank #2"
            )
        elif rank == 3:
            return ft.Container(
                content=ft.Icon(ft.Icons.EMOJI_EVENTS, size=24, color=ft.Colors.ORANGE_700),
                width=32, height=32,
                alignment=ft.alignment.center,
                tooltip="Rank #3"
            )
        else:
            # Show rank number for ranks 4-10
            return ft.Container(
                content=ft.Text(str(rank), size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                width=28, height=28,
                alignment=ft.alignment.center,
                bgcolor=theme_manager.primary_color,
                border_radius=14,
                tooltip=f"Rank #{rank}"
            )
    
    def update_users(self, users: List[Dict]):
        """Update the users list."""
        if not users:
            self.users_list.controls = [
                ft.Container(
                    content=ft.Text(
                        theme_manager.t("no_data"),
                        color=theme_manager.text_secondary_color
                    ),
                    padding=ft.padding.all(20),
                    alignment=ft.alignment.center
                )
            ]
            if self.page:
                self.page.update()
            return
        
        user_items = []
        for idx, user in enumerate(users, 1):
            full_name = user.get('full_name') or "Unknown"
            username = user.get('username') or None
            profile_photo_path = user.get('profile_photo_path')
            message_count = user.get('message_count', 0)
            
            # Create ranking badge
            ranking_badge = self._create_ranking_badge(idx)
            
            # Create avatar
            if profile_photo_path:
                avatar = ft.Container(
                    content=ft.Image(
                        src=profile_photo_path,
                        width=40, height=40,
                        fit=ft.ImageFit.COVER,
                        border_radius=20
                    ),
                    width=40, height=40,
                    border_radius=20,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                )
            else:
                first_letter = full_name[0].upper() if full_name and len(full_name) > 0 else "?"
                gradient_colors = self._get_gradient_colors_for_letter(first_letter)
                
                avatar = ft.Container(
                    content=ft.Text(first_letter, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=40, height=40,
                    border_radius=20,
                    alignment=ft.alignment.center,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=gradient_colors
                    ),
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                )
            
            # Create message count badge
            message_badge = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.MESSAGE, size=14, color=ft.Colors.WHITE),
                    ft.Text(str(message_count), size=theme_manager.font_size_small, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ], spacing=4, tight=True),
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                bgcolor=theme_manager.primary_color,
                border_radius=12,
            )
            
            # Create user item
            user_item = ft.Container(
                content=ft.Row([
                    ranking_badge,
                    avatar,
                    ft.Column([
                        ft.Text(full_name, size=theme_manager.font_size_body, weight=ft.FontWeight.W_500, color=theme_manager.text_color),
                        ft.Text(
                            f"@{username}" if username else (theme_manager.t("no_username") or "No username"),
                            size=theme_manager.font_size_small,
                            color=theme_manager.text_secondary_color
                        ),
                    ], spacing=2, tight=True, expand=True),
                    message_badge,
                ], spacing=theme_manager.spacing_sm, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(vertical=8, horizontal=12),
                clip_behavior=ft.ClipBehavior.NONE,
            )
            
            user_items.append(user_item)
        
        self.users_list.controls = user_items
        if self.page:
            self.page.update()
    
    def clear(self):
        """Clear the users list."""
        self.users_list.controls = []
        if self.page:
            self.page.update()
    
    def build(self) -> ft.Column:
        """Build and return the component."""
        return self.users_list
    
    def set_page(self, page: ft.Page):
        """Set page reference."""
        self.page = page

