"""
Pricing tab content for about page.
"""

import flet as ft
from ui.theme import theme_manager
from utils.constants import LICENSE_PRICING, LICENSE_TIER_BRONZE, LICENSE_TIER_SILVER, LICENSE_TIER_GOLD, LICENSE_TIER_PREMIUM
from services.license_service import LicenseService
from config.settings import settings


class PricingTab:
    """Pricing tab component."""
    
    def __init__(self, license_service: LicenseService):
        self.license_service = license_service
        self.license_info = license_service.get_license_info()
    
    def build(self) -> ft.Container:
        """Build Pricing tab content."""
        pricing_cards = []
        
        for tier_key in [LICENSE_TIER_BRONZE, LICENSE_TIER_SILVER, LICENSE_TIER_GOLD, LICENSE_TIER_PREMIUM]:
            tier_info = LICENSE_PRICING[tier_key]
            is_current = self.license_info['tier'] == tier_key
            pricing_cards.append(self._create_pricing_card(tier_key, tier_info, is_current))
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("pricing"),
                    size=theme_manager.font_size_page_title,
                    weight=ft.FontWeight.BOLD
                ),
                theme_manager.spacing_container("lg"),
                ft.Row(
                    pricing_cards,
                    spacing=theme_manager.spacing_lg,
                    wrap=True,
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ], scroll=ft.ScrollMode.AUTO, spacing=theme_manager.spacing_sm, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=theme_manager.padding_lg,
            expand=True
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
            LICENSE_TIER_BRONZE: ft.Colors.BROWN,
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
                ft.Text(theme_manager.t("feature_unlimited_groups"), size=theme_manager.font_size_small)
            ], spacing=theme_manager.spacing_xs))
        else:
            feature_items.append(ft.Row([
                ft.Icon(ft.Icons.CHECK, color=theme_manager.success_color, size=16),
                ft.Text(f"{max_groups} {theme_manager.t('max_groups')}", size=theme_manager.font_size_small)
            ], spacing=theme_manager.spacing_xs))
        
        feature_items.append(ft.Row([
            ft.Icon(ft.Icons.CHECK, color=theme_manager.success_color, size=16),
            ft.Text(f"{max_devices} {theme_manager.t('max_devices')}", size=theme_manager.font_size_small)
        ], spacing=theme_manager.spacing_xs))
        
        if "priority_support" in features:
            feature_items.append(ft.Row([
                ft.Icon(ft.Icons.CHECK, color=theme_manager.success_color, size=16),
                ft.Text(theme_manager.t("feature_priority_support"), size=theme_manager.font_size_small)
            ], spacing=theme_manager.spacing_xs))
        
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
                            size=theme_manager.font_size_page_title,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE
                        ),
                        ft.Text(
                            f"${price_usd} / {price_khr:,} KHR",
                            size=theme_manager.font_size_body,
                            color=ft.Colors.WHITE
                        ),
                        ft.Text(
                            theme_manager.t("per_month"),
                            size=theme_manager.font_size_small,
                            color=ft.Colors.WHITE70
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=theme_manager.spacing_xs),
                    bgcolor=tier_color,
                    padding=theme_manager.padding_lg,
                    border_radius=ft.border_radius.only(
                        top_left=theme_manager.corner_radius,
                        top_right=theme_manager.corner_radius
                    )
                ),
                ft.Container(
                    content=ft.Column([
                        theme_manager.spacing_container("sm"),
                        ft.Column(feature_items, spacing=theme_manager.spacing_sm),
                        theme_manager.spacing_container("lg"),
                        contact_button,
                        theme_manager.spacing_container("sm"),
                        ft.Text(
                            theme_manager.t("current_plan") if is_current else "",
                            size=theme_manager.font_size_small,
                            color=theme_manager.success_color,
                            weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL
                        ) if is_current else ft.Container(height=0)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=theme_manager.spacing_xs),
                    padding=theme_manager.padding_lg,
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
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error opening email client: {e}")
            theme_manager.show_snackbar(
                None,  # Page reference would need to be passed
                f"Please contact {settings.developer_email} for upgrade",
                bgcolor=theme_manager.info_color
            )

