"""
About page with app info and pricing.
"""

import flet as ft
import logging
from typing import Optional
from ui.theme import theme_manager
from services.auth_service import auth_service
from services.license_service import LicenseService
from database.db_manager import DatabaseManager
from config.settings import settings
from utils.constants import LICENSE_PRICING, LICENSE_TIER_SILVER, LICENSE_TIER_GOLD, LICENSE_TIER_PREMIUM

logger = logging.getLogger(__name__)


class AboutPage:
    """About page with About and Pricing tabs."""
    
    def __init__(self, page: ft.Page, db_manager: DatabaseManager):
        self.page = page
        self.db_manager = db_manager
        self.license_service = LicenseService(db_manager)
        
        # Get current license info
        self.license_info = self.license_service.get_license_info()
        
        # Create tabs
        self.about_tab = self._build_about_tab()
        self.pricing_tab = self._build_pricing_tab()
        
        self.tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(
                    text=theme_manager.t("about"),
                    content=self.about_tab
                ),
                ft.Tab(
                    text=theme_manager.t("pricing"),
                    content=self.pricing_tab
                )
            ],
            expand=True
        )
        
        self.container = ft.Container(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("about"),
                    size=32,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(height=20),
                self.tabs
            ], scroll=ft.ScrollMode.AUTO, spacing=10),
            padding=20,
            expand=True
        )
    
    def build(self) -> ft.Container:
        """Build and return the about page container."""
        return self.container
    
    def _build_about_tab(self) -> ft.Container:
        """Build About tab content."""
        return ft.Container(
            content=ft.Column([
                # App info card
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Text(
                            theme_manager.t("app_info"),
                            size=20,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        ft.Text(
                            theme_manager.t("app_description"),
                            size=14,
                            color=theme_manager.text_secondary_color
                        ),
                        ft.Container(height=20),
                        ft.Text(
                            theme_manager.t("features_overview"),
                            size=18,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Container(height=10),
                        self._create_feature_item(theme_manager.t("feature_track_messages")),
                        self._create_feature_item(theme_manager.t("feature_user_analytics")),
                        self._create_feature_item(theme_manager.t("feature_export_reports")),
                        self._create_feature_item(theme_manager.t("feature_media_download")),
                        self._create_feature_item(theme_manager.t("feature_reaction_tracking")),
                    ], spacing=15),
                    width=700
                ),
                
                ft.Container(height=20),
                
                # Developer info card
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Text(
                            theme_manager.t("developer_info"),
                            size=20,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        ft.Row([
                            ft.Icon(ft.Icons.INFO, color=theme_manager.primary_color),
                            ft.Column([
                                ft.Text(theme_manager.t("version"), size=12, color=theme_manager.text_secondary_color),
                                ft.Text(settings.app_version, size=16),
                            ], spacing=2)
                        ], spacing=10),
                        ft.Row([
                            ft.Icon(ft.Icons.PERSON, color=theme_manager.primary_color),
                            ft.Column([
                                ft.Text("Developer", size=12, color=theme_manager.text_secondary_color),
                                ft.Text(settings.developer_name, size=16),
                            ], spacing=2)
                        ], spacing=10),
                        ft.Row([
                            ft.Icon(ft.Icons.EMAIL, color=theme_manager.primary_color),
                            ft.Column([
                                ft.Text(theme_manager.t("email"), size=12, color=theme_manager.text_secondary_color),
                                ft.Text(settings.developer_email, size=16),
                            ], spacing=2)
                        ], spacing=10),
                        ft.Row([
                            ft.Icon(ft.Icons.PHONE, color=theme_manager.primary_color),
                            ft.Column([
                                ft.Text(theme_manager.t("contact"), size=12, color=theme_manager.text_secondary_color),
                                ft.Text(settings.developer_contact, size=16),
                            ], spacing=2)
                        ], spacing=10),
                    ], spacing=15),
                    width=700
                ),
                
                ft.Container(height=20),
                
                # License info card
                self._build_license_info_card()
                
            ], scroll=ft.ScrollMode.AUTO, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            expand=True
        )
    
    def _build_pricing_tab(self) -> ft.Container:
        """Build Pricing tab content."""
        pricing_cards = []
        
        for tier_key in [LICENSE_TIER_SILVER, LICENSE_TIER_GOLD, LICENSE_TIER_PREMIUM]:
            tier_info = LICENSE_PRICING[tier_key]
            is_current = self.license_info['tier'] == tier_key
            pricing_cards.append(self._create_pricing_card(tier_key, tier_info, is_current))
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("pricing"),
                    size=24,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(height=20),
                ft.Row(
                    pricing_cards,
                    spacing=20,
                    wrap=True,
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ], scroll=ft.ScrollMode.AUTO, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            expand=True
        )
    
    def _create_feature_item(self, text: str) -> ft.Row:
        """Create a feature list item with checkmark."""
        return ft.Row([
            ft.Icon(ft.Icons.CHECK_CIRCLE, color=theme_manager.success_color, size=20),
            ft.Text(text, size=14, color=theme_manager.text_color)
        ], spacing=10)
    
    def _build_license_info_card(self) -> ft.Container:
        """Build license information card."""
        tier = self.license_info['tier']
        tier_name = self.license_info['tier_name']
        is_active = self.license_info['is_active']
        expired = self.license_info['expired']
        expiration_date = self.license_info['expiration_date']
        days_remaining = self.license_info['days_until_expiration']
        current_devices = self.license_info['current_devices']
        max_devices = self.license_info['max_devices']
        current_groups = self.license_info['current_groups']
        max_groups = self.license_info['max_groups']
        
        # Tier color
        tier_colors = {
            LICENSE_TIER_SILVER: ft.Colors.GREY,
            LICENSE_TIER_GOLD: ft.Colors.AMBER,
            LICENSE_TIER_PREMIUM: ft.Colors.PURPLE
        }
        tier_color = tier_colors.get(tier, ft.Colors.GREY)
        
        # Status text
        if expired:
            status_text = ft.Text(
                theme_manager.t("license_expired"),
                color=ft.Colors.RED,
                weight=ft.FontWeight.BOLD
            )
        elif days_remaining is not None and days_remaining < 7:
            status_text = ft.Text(
                f"{theme_manager.t('license_expiring_soon')} ({days_remaining} {theme_manager.t('days_remaining')})",
                color=ft.Colors.ORANGE,
                weight=ft.FontWeight.BOLD
            )
        else:
            status_text = ft.Text(
                theme_manager.t("subscription"),
                color=theme_manager.success_color,
                weight=ft.FontWeight.BOLD
            )
        
        return theme_manager.create_card(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("current_plan"),
                    size=20,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(),
                ft.Row([
                    ft.Container(
                        content=ft.Text(
                            tier_name,
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE
                        ),
                        bgcolor=tier_color,
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        border_radius=theme_manager.corner_radius
                    ),
                    status_text
                ], spacing=10, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=10),
                ft.Row([
                    ft.Icon(ft.Icons.DEVICES, color=theme_manager.primary_color),
                    ft.Text(
                        f"{theme_manager.t('active_devices')}: {current_devices}/{max_devices}",
                        size=14
                    )
                ], spacing=10),
                ft.Row([
                    ft.Icon(ft.Icons.GROUP, color=theme_manager.primary_color),
                    ft.Text(
                        f"{theme_manager.t('groups_used')}: {current_groups}/{'∞' if max_groups == -1 else max_groups}",
                        size=14
                    )
                ], spacing=10),
                ft.Container(height=10),
                ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_TODAY, color=theme_manager.primary_color),
                    ft.Text(
                        f"{theme_manager.t('expires_on')}: {expiration_date.strftime('%Y-%m-%d') if expiration_date else 'N/A'}",
                        size=14
                    )
                ], spacing=10),
                ft.Container(height=10),
                ft.ElevatedButton(
                    theme_manager.t("view_pricing"),
                    icon=ft.Icons.ARROW_FORWARD,
                    on_click=lambda e: self._switch_to_pricing_tab(),
                    bgcolor=theme_manager.primary_color,
                    color=ft.Colors.WHITE
                )
            ], spacing=15),
            width=700
        )
    
    def _create_pricing_card(self, tier_key: str, tier_info: dict, is_current: bool) -> ft.Container:
        """Create a pricing card for a tier."""
        tier_name = tier_info['name']
        price_usd = tier_info['price_usd']
        price_khr = tier_info['price_khr']
        max_groups = tier_info['max_groups']
        max_devices = tier_info['max_devices']
        features = tier_info['features']
        
        # Tier colors
        tier_colors = {
            LICENSE_TIER_SILVER: ft.Colors.GREY,
            LICENSE_TIER_GOLD: ft.Colors.AMBER,
            LICENSE_TIER_PREMIUM: ft.Colors.PURPLE
        }
        tier_color = tier_colors.get(tier_key, ft.Colors.GREY)
        
        # Features list
        feature_items = []
        if max_groups == -1:
            feature_items.append(ft.Row([
                ft.Icon(ft.Icons.CHECK, color=theme_manager.success_color, size=16),
                ft.Text(theme_manager.t("feature_unlimited_groups"), size=12)
            ], spacing=5))
        else:
            feature_items.append(ft.Row([
                ft.Icon(ft.Icons.CHECK, color=theme_manager.success_color, size=16),
                ft.Text(f"{max_groups} {theme_manager.t('max_groups')}", size=12)
            ], spacing=5))
        
        feature_items.append(ft.Row([
            ft.Icon(ft.Icons.CHECK, color=theme_manager.success_color, size=16),
            ft.Text(f"{max_devices} {theme_manager.t('max_devices')}", size=12)
        ], spacing=5))
        
        if "priority_support" in features:
            feature_items.append(ft.Row([
                ft.Icon(ft.Icons.CHECK, color=theme_manager.success_color, size=16),
                ft.Text(theme_manager.t("feature_priority_support"), size=12)
            ], spacing=5))
        
        # Contact button
        contact_button = ft.ElevatedButton(
            theme_manager.t("contact_admin"),
            icon=ft.Icons.EMAIL,
            on_click=lambda e, t=tier_key: self._contact_admin(t),
            bgcolor=tier_color if not is_current else theme_manager.success_color,
            color=ft.Colors.WHITE,
            width=200
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            tier_name,
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE
                        ),
                        ft.Text(
                            f"${price_usd} / {price_khr:,} KHR",
                            size=16,
                            color=ft.Colors.WHITE
                        ),
                        ft.Text(
                            theme_manager.t("per_month"),
                            size=12,
                            color=ft.Colors.WHITE70
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    bgcolor=tier_color,
                    padding=20,
                    border_radius=ft.border_radius.only(
                        top_left=theme_manager.corner_radius,
                        top_right=theme_manager.corner_radius
                    )
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Container(height=10),
                        ft.Column(feature_items, spacing=8),
                        ft.Container(height=20),
                        contact_button,
                        ft.Container(height=10),
                        ft.Text(
                            theme_manager.t("current_plan") if is_current else "",
                            size=12,
                            color=theme_manager.success_color,
                            weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL
                        ) if is_current else ft.Container(height=0)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    padding=20,
                    bgcolor=theme_manager.surface_color,
                    border_radius=ft.border_radius.only(
                        bottom_left=theme_manager.corner_radius,
                        bottom_right=theme_manager.corner_radius
                    )
                )
            ], spacing=0),
            width=280,
            border=ft.border.all(2, tier_color if is_current else theme_manager.border_color),
            border_radius=theme_manager.corner_radius
        )
    
    def _switch_to_pricing_tab(self):
        """Switch to pricing tab."""
        self.tabs.selected_index = 1
        self.page.update()
    
    def _contact_admin(self, tier: str):
        """Open email client to contact admin for upgrade."""
        try:
            import webbrowser
            from urllib.parse import quote
            
            current_tier = self.license_info['tier']
            subject = theme_manager.t("upgrade_email_subject")
            body = theme_manager.t("upgrade_email_body").format(
                tier=tier,
                current_tier=current_tier,
                reason=""
            )
            
            email_url = f"mailto:{settings.developer_email}?subject={quote(subject)}&body={quote(body)}"
            webbrowser.open(email_url)
        except Exception as e:
            logger.error(f"Error opening email client: {e}")
            theme_manager.show_snackbar(
                self.page,
                f"Please contact {settings.developer_email} for upgrade",
                bgcolor=theme_manager.info_color
            )

