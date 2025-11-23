"""
Pricing tab content for about page.
"""

import flet as ft
from ui.theme import theme_manager
from services.license_service import LicenseService
from services.license.license_tier_service import license_tier_service
from config.settings import settings


class PricingTab:
    """Pricing tab component."""
    
    def __init__(self, license_service: LicenseService):
        self.license_service = license_service
        self.license_info = None  # Will be loaded asynchronously
    
    def build(self) -> ft.Container:
        """Build Pricing tab content (synchronous version - loads tiers synchronously)."""
        # Load license info if not loaded
        if self.license_info is None:
            self.license_info = self.license_service.get_license_info()
        
        # Fetch tiers from Firestore (synchronous - for backward compatibility)
        tiers = license_tier_service.get_all_tiers()
        
        return self.build_with_tiers(tiers)
    
    def build_with_tiers(self, tiers: list) -> ft.Container:
        """Build Pricing tab content with pre-loaded tiers."""
        pricing_cards = []
        
        # Load license info if not loaded
        if self.license_info is None:
            self.license_info = self.license_service.get_license_info()
        
        # If no tiers found, show empty state
        if not tiers:
            return ft.Container(
                content=ft.Column([
                    ft.Text(
                        theme_manager.t("pricing"),
                        size=theme_manager.font_size_page_title,
                        weight=ft.FontWeight.BOLD
                    ),
                    theme_manager.spacing_container("lg"),
                    ft.Text(
                        "No pricing tiers available. Please contact admin.",
                        size=theme_manager.font_size_body,
                        color=theme_manager.text_secondary_color
                    )
                ], scroll=ft.ScrollMode.AUTO, spacing=theme_manager.spacing_sm, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=theme_manager.padding_lg,
                expand=True
            )
        
        # Create pricing cards for each tier
        for tier_info in tiers:
            tier_key = tier_info.get('tier_key', '')
            is_current = self.license_info.get('tier') == tier_key if self.license_info else False
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
        tier_name = tier_info.get('name', tier_key.capitalize())
        price_usd = tier_info.get('price_usd', 0)
        price_khr = tier_info.get('price_khr', 0)
        max_groups = tier_info.get('max_groups', 1)
        max_devices = tier_info.get('max_devices', 1)
        features = tier_info.get('features', [])
        
        # Handle features if it's a string (comma-separated)
        if isinstance(features, str):
            features = [f.strip() for f in features.split(',') if f.strip()]
        
        # Tier colors - dynamic mapping based on tier_key
        tier_colors = {
            'bronze': ft.Colors.BROWN,
            'silver': ft.Colors.GREY,
            'gold': ft.Colors.AMBER,
            'premium': ft.Colors.PURPLE,
            'custom': ft.Colors.BLUE_GREY
        }
        tier_color = tier_colors.get(tier_key.lower(), ft.Colors.GREY)
        
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
            
            # Load license info if not loaded
            if self.license_info is None:
                self.license_info = self.license_service.get_license_info()
            
            current_tier = self.license_info.get('tier', 'unknown') if self.license_info else 'unknown'
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

