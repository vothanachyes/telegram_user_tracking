"""
Dashboard page with statistics and activity feed.
"""

import flet as ft
import asyncio
from typing import Optional
from datetime import datetime
from ui.theme import theme_manager
from ui.components import StatCard, DataTable
from database.db_manager import DatabaseManager
from utils.constants import format_bytes
from ui.pages.dashboard.sample_data import SampleDataGenerator
from utils.helpers import format_datetime, get_telegram_user_link


class DashboardPage(ft.Container):
    """Dashboard page with statistics."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.page: Optional[ft.Page] = None
        self.sample_data_generator = SampleDataGenerator(db_manager)
        
        # Generate sample data if database is empty
        self.sample_data_generator.ensure_sample_data()
        
        # Check if we're showing sample data
        self.is_sample_data = self.sample_data_generator.is_sample_data()
        
        # Get groups and set default selected group
        groups = self.db_manager.get_all_groups()
        self.selected_group_id = groups[0].group_id if groups else None
        self.selected_group_name = groups[0].group_name if groups else None
        
        # Create group dropdown
        group_options = [f"{g.group_name} ({g.group_id})" for g in groups]
        default_group_value = group_options[0] if group_options else None
        self.group_dropdown = theme_manager.create_dropdown(
            label=theme_manager.t("select_group"),
            options=group_options if group_options else ["No groups"],
            value=default_group_value,
            on_change=self._on_group_selected,
            width=250
        )
        
        # Create stat cards
        stats = self.db_manager.get_dashboard_stats()
        
        self.stat_cards = ft.Row([
            StatCard(
                title=theme_manager.t("total_messages"),
                value=str(stats['total_messages']),
                icon=ft.Icons.MESSAGE,
                color=theme_manager.primary_color
            ),
            StatCard(
                title=theme_manager.t("total_users"),
                value=str(stats['total_users']),
                icon=ft.Icons.PEOPLE,
                color=ft.Colors.BLUE
            ),
            StatCard(
                title=theme_manager.t("total_groups"),
                value=str(stats['total_groups']),
                icon=ft.Icons.GROUP,
                color=ft.Colors.GREEN
            ),
            StatCard(
                title=theme_manager.t("media_storage"),
                value=format_bytes(stats['total_media_size']),
                icon=ft.Icons.STORAGE,
                color=ft.Colors.ORANGE
            ),
        ], spacing=theme_manager.spacing_sm, wrap=True, run_spacing=theme_manager.spacing_sm)
        
        # Monthly stats
        self.monthly_stats = self._create_modern_card(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("statistics"),
                    size=theme_manager.font_size_section_title,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(),
                ft.Row([
                    ft.Column([
                        ft.Text(
                            theme_manager.t("messages_today"),
                            size=theme_manager.font_size_body,
                            color=theme_manager.text_secondary_color
                        ),
                        ft.Text(
                            str(stats['messages_today']),
                            size=theme_manager.font_size_large_number,
                            weight=ft.FontWeight.BOLD
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(),
                    ft.Column([
                        ft.Text(
                            theme_manager.t("messages_this_month"),
                            size=theme_manager.font_size_body,
                            color=theme_manager.text_secondary_color
                        ),
                        ft.Text(
                            str(stats['messages_this_month']),
                            size=theme_manager.font_size_large_number,
                            weight=ft.FontWeight.BOLD
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND, expand=True)
            ], spacing=theme_manager.spacing_sm)
        )
        
        # Recent activity
        self.recent_activity = self._create_modern_card(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        theme_manager.t("recent_activity"),
                        size=theme_manager.font_size_section_title,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip=theme_manager.t("refresh"),
                        on_click=self._refresh_data
                    )
                ]),
                ft.Divider(),
                self._get_recent_messages()
            ], spacing=theme_manager.spacing_sm)
        )
        
        # Top 10 active users table
        self.active_users_table = self._create_active_users_table()
        self.active_users_card = self._create_modern_card(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        theme_manager.t("top_active_users"),
                        size=theme_manager.font_size_section_title,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        text=theme_manager.t("all"),
                        icon=ft.Icons.ARROW_FORWARD,
                        on_click=self._navigate_to_reports,
                        disabled=self.selected_group_id is None
                    ),
                ]),
                ft.Divider(),
                ft.Container(
                    content=self.active_users_table,
                    height=400,
                    width=None
                ),
            ], spacing=theme_manager.spacing_sm)
        )
        
        # Build layout
        super().__init__(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        theme_manager.t("dashboard"),
                        size=theme_manager.font_size_page_title,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(expand=True),
                    self.group_dropdown,
                    self._create_sample_data_badge() if self.is_sample_data else ft.Container(),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=10),
                self.stat_cards,
                theme_manager.spacing_container("md"),
                ft.Row([
                    self.monthly_stats,
                    self.recent_activity,
                ], spacing=theme_manager.spacing_md, expand=True),
                theme_manager.spacing_container("md"),
                self.active_users_card,
            ], scroll=ft.ScrollMode.AUTO, spacing=theme_manager.spacing_md),
            padding=theme_manager.padding_lg,
            expand=True
        )
        
        # Load initial data
        self._refresh_active_users()
        
        # Trigger animations after page is mounted
        self._animation_initialized = False
    
    def _create_modern_card(self, content: ft.Control) -> ft.Container:
        """Create a modernized card with shadows, animations, and hover effects."""
        default_shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=8,
            color=ft.Colors.BLACK12 if not theme_manager.is_dark else ft.Colors.BLACK38,
            offset=ft.Offset(0, 2),
        )
        
        hover_shadow = ft.BoxShadow(
            spread_radius=2,
            blur_radius=15,
            color=ft.Colors.BLACK26 if not theme_manager.is_dark else ft.Colors.BLACK54,
            offset=ft.Offset(0, 4),
        )
        
        card = ft.Container(
            content=content,
            bgcolor=theme_manager.surface_color,
            border=ft.border.all(1, theme_manager.border_color),
            border_radius=theme_manager.corner_radius,
            padding=theme_manager.padding_md,
            shadow=[default_shadow],
            animate=ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT),
            animate_opacity=ft.Animation(duration=400, curve=ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT),
            opacity=0,
            scale=1.0,
            on_hover=lambda e: self._on_card_hover(e, card, default_shadow, hover_shadow)
        )
        
        return card
    
    def _on_card_hover(self, e: ft.ControlEvent, card: ft.Container, default_shadow: ft.BoxShadow, hover_shadow: ft.BoxShadow):
        """Handle card hover events."""
        is_hovered = e.data == "true"
        
        if is_hovered:
            card.scale = 1.01
            card.shadow = [hover_shadow]
        else:
            card.scale = 1.0
            card.shadow = [default_shadow]
        
        if self.page:
            self.page.update()
        else:
            card.update()
    
    async def _animate_dashboard(self):
        """Animate dashboard components with staggered delays."""
        if self._animation_initialized:
            return
        
        self._animation_initialized = True
        
        # Animate stat cards with staggered delay (100ms between each)
        for idx, card in enumerate(self.stat_cards.controls):
            await asyncio.sleep(0.1 * idx)  # 100ms delay between each card
            if hasattr(card, '_animate_in'):
                card._animate_in()
        
        # Animate monthly stats after stat cards (400ms total delay)
        await asyncio.sleep(0.1)
        self.monthly_stats.opacity = 1
        if self.page:
            self.page.update()
        
        # Animate recent activity (100ms after monthly stats)
        await asyncio.sleep(0.1)
        self.recent_activity.opacity = 1
        if self.page:
            self.page.update()
        
        # Animate active users card (100ms after recent activity)
        await asyncio.sleep(0.1)
        self.active_users_card.opacity = 1
        if self.page:
            self.page.update()
    
    def set_page(self, page: ft.Page):
        """Set page reference and trigger animations."""
        self.page = page
        
        # Set page reference for stat cards
        for card in self.stat_cards.controls:
            card.page = page
        
        # Trigger animations after a longer delay to ensure controls are added to page tree
        if page and hasattr(page, 'run_task'):
            async def start_animations():
                await asyncio.sleep(0.3)  # Longer delay to ensure page tree is built
                await self._animate_dashboard()
            
            page.run_task(start_animations)
        elif page:
            async def start_animations():
                await asyncio.sleep(0.3)  # Longer delay to ensure page tree is built
                await self._animate_dashboard()
            
            asyncio.create_task(start_animations())
    
    def _get_recent_messages(self) -> ft.Column:
        """Get recent messages list."""
        messages = self.db_manager.get_messages(limit=10)
        
        if not messages:
            return ft.Column([
                ft.Text(
                    theme_manager.t("no_data"),
                    color=theme_manager.text_secondary_color
                )
            ])
        
        message_items = []
        for msg in messages:
            user = self.db_manager.get_user_by_id(msg.user_id)
            user_name = user.full_name if user else "Unknown"
            
            message_items.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.MESSAGE, color=theme_manager.primary_color),
                    title=ft.Text(user_name, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(
                        msg.content[:100] + "..." if msg.content and len(msg.content) > 100 else msg.content or "",
                        max_lines=2
                    ),
                    trailing=ft.Text(
                        self._format_message_date(msg.date_sent),
                        size=theme_manager.font_size_small,
                        color=theme_manager.text_secondary_color
                    )
                )
            )
        
        return ft.Column(message_items, spacing=theme_manager.spacing_xs, scroll=ft.ScrollMode.AUTO, height=400)
    
    def _format_message_date(self, date_value) -> str:
        """Format message date, handling both string and datetime objects."""
        if not date_value:
            return ""
        
        # If it's already a string, parse it first
        if isinstance(date_value, str):
            try:
                # Try to parse ISO format datetime
                date_obj = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return date_obj.strftime("%Y-%m-%d %H:%M")
            except:
                # If parsing fails, return the string as-is (might already be formatted)
                return date_value[:16] if len(date_value) >= 16 else date_value
        
        # If it's a datetime object, format it
        if isinstance(date_value, datetime):
            return date_value.strftime("%Y-%m-%d %H:%M")
        
        return str(date_value)
    
    def _refresh_data(self, e):
        """Refresh dashboard data."""
        stats = self.db_manager.get_dashboard_stats()
        
        # Update stat cards
        cards = self.stat_cards.controls
        cards[0].update_value(str(stats['total_messages']))
        cards[1].update_value(str(stats['total_users']))
        cards[2].update_value(str(stats['total_groups']))
        cards[3].update_value(format_bytes(stats['total_media_size']))
        
        # Update monthly stats
        monthly_content = self.monthly_stats.content
        monthly_content.controls[2].controls[0].controls[1].value = str(stats['messages_today'])
        monthly_content.controls[2].controls[2].controls[1].value = str(stats['messages_this_month'])
        
        # Update recent activity
        activity_content = self.recent_activity.content
        activity_content.controls[2] = self._get_recent_messages()
        
        # Update active users
        self._refresh_active_users()
        
        self.update()
    
    
    def _on_group_selected(self, e):
        """Handle group selection."""
        if e.control.value and e.control.value != "No groups":
            group_str = e.control.value
            self.selected_group_id = int(group_str.split("(")[-1].strip(")"))
            groups = self.db_manager.get_all_groups()
            for group in groups:
                if group.group_id == self.selected_group_id:
                    self.selected_group_name = group.group_name
                    break
        else:
            self.selected_group_id = None
            self.selected_group_name = None
        
        # Update active users table
        self._refresh_active_users()
        
        # Update All button
        if hasattr(self, 'active_users_card'):
            content = self.active_users_card.content
            all_btn = content.controls[0].controls[2]
            all_btn.disabled = self.selected_group_id is None
        
        if self.page:
            self.page.update()
    
    def _create_active_users_table(self) -> DataTable:
        """Create top 10 active users table."""
        return DataTable(
            columns=["No", "Username", "Full Name", "Phone", "Messages"],
            rows=[],
            on_row_click=None,
            page_size=10,
            column_alignments=["center", "center", "left", "center", "center"],
            row_metadata=[],
            searchable=False
        )
    
    def _refresh_active_users(self):
        """Refresh active users table."""
        if not self.selected_group_id:
            self.active_users_table.refresh([], [])
            return
        
        users = self.db_manager.get_top_active_users_by_group(self.selected_group_id, limit=10)
        
        rows = []
        row_metadata = []
        for idx, user in enumerate(users, 1):
            username = user.get('username') or "-"
            full_name = user.get('full_name') or "-"
            phone = user.get('phone') or "-"
            message_count = user.get('message_count', 0)
            user_link = get_telegram_user_link(user.get('username'))
            
            rows.append([
                idx,
                username,
                full_name,
                phone,
                str(message_count),
            ])
            
            row_meta = {
                'cells': {}
            }
            if user_link and user.get('username'):
                row_meta['cells'][1] = {'link': user_link}
                row_meta['cells'][2] = {'link': user_link}
            row_metadata.append(row_meta)
        
        self.active_users_table.refresh(rows, row_metadata)
    
    def _navigate_to_reports(self, e):
        """Navigate to reports page."""
        if self.page and hasattr(self.page, 'data') and self.page.data:
            router = self.page.data.get('router')
            if router:
                router.navigate_to("reports")
    
    def _create_sample_data_badge(self) -> ft.Container:
        """Create a badge indicating sample data."""
        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.INFO_OUTLINED,
                    size=18,
                    color=ft.Colors.ORANGE_700 if theme_manager.is_dark else ft.Colors.ORANGE_600
                ),
                ft.Text(
                    "Sample Data",
                    size=theme_manager.font_size_small,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.ORANGE_700 if theme_manager.is_dark else ft.Colors.ORANGE_600
                )
            ], spacing=6, tight=True),
            bgcolor=ft.Colors.ORANGE_100 if not theme_manager.is_dark else ft.Colors.ORANGE_900,
            border=ft.border.all(1, ft.Colors.ORANGE_300 if not theme_manager.is_dark else ft.Colors.ORANGE_700),
            border_radius=20,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            tooltip="This dashboard is showing sample/demo data. Connect to Telegram to see real data."
        )

