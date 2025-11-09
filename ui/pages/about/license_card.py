"""
License information card component.
"""

import flet as ft
from ui.theme import theme_manager
from utils.constants import LICENSE_TIER_BRONZE, LICENSE_TIER_SILVER, LICENSE_TIER_GOLD, LICENSE_TIER_PREMIUM


class LicenseInfoCard:
    """License information card component."""
    
    def __init__(self, license_info: dict):
        self.license_info = license_info
    
    def build(self) -> ft.Container:
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
            LICENSE_TIER_BRONZE: ft.Colors.BROWN,
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
                    size=theme_manager.font_size_section_title,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(),
                ft.Row([
                    ft.Container(
                        content=ft.Text(
                            tier_name,
                            size=theme_manager.font_size_subsection_title,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE
                        ),
                        bgcolor=tier_color,
                        padding=ft.padding.symmetric(horizontal=theme_manager.padding_sm, vertical=theme_manager.spacing_xs),
                        border_radius=theme_manager.corner_radius
                    ),
                    status_text
                ], spacing=theme_manager.spacing_sm, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                theme_manager.spacing_container("sm"),
                ft.Row([
                    ft.Icon(ft.Icons.DEVICES, color=theme_manager.primary_color),
                    ft.Text(
                        f"{theme_manager.t('active_devices')}: {current_devices}/{max_devices}",
                        size=theme_manager.font_size_body
                    )
                ], spacing=theme_manager.spacing_sm),
                ft.Row([
                    ft.Icon(ft.Icons.GROUP, color=theme_manager.primary_color),
                    ft.Text(
                        f"{theme_manager.t('groups_used')}: {current_groups}/{'∞' if max_groups == -1 else max_groups}",
                        size=theme_manager.font_size_body
                    )
                ], spacing=theme_manager.spacing_sm),
                theme_manager.spacing_container("sm"),
                ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_TODAY, color=theme_manager.primary_color),
                    ft.Text(
                        f"{theme_manager.t('expires_on')}: {expiration_date.strftime('%Y-%m-%d') if expiration_date else 'N/A'}",
                        size=theme_manager.font_size_body
                    )
                ], spacing=theme_manager.spacing_sm),
                # Show remaining days prominently
                ft.Container(
                    content=ft.Row([
                        ft.Icon(
                            ft.Icons.ACCESS_TIME,
                            color=ft.Colors.WHITE,
                            size=20
                        ),
                        ft.Text(
                            f"{days_remaining} {theme_manager.t('days_remaining')}" if days_remaining is not None else theme_manager.t("no_expiration"),
                            size=theme_manager.font_size_body,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE
                        )
                    ], spacing=theme_manager.spacing_sm, alignment=ft.MainAxisAlignment.CENTER),
                    bgcolor=ft.Colors.BLUE_700 if days_remaining is not None and days_remaining > 7 else (ft.Colors.ORANGE_700 if days_remaining is not None and days_remaining > 0 else ft.Colors.RED_700),
                    padding=ft.padding.symmetric(horizontal=theme_manager.spacing_lg, vertical=theme_manager.spacing_sm),
                    border_radius=theme_manager.corner_radius,
                    width=700
                ) if days_remaining is not None or expiration_date is None else ft.Container(height=0),
                theme_manager.spacing_container("sm"),
                ft.ElevatedButton(
                    theme_manager.t("view_pricing"),
                    icon=ft.Icons.ARROW_FORWARD,
                    on_click=lambda e: self._switch_to_pricing_tab(),
                    bgcolor=theme_manager.primary_color,
                    color=ft.Colors.WHITE
                )
            ], spacing=theme_manager.spacing_md),
            width=700
        )
    
    def _switch_to_pricing_tab(self):
        """Switch to pricing tab - this will be handled by the parent page."""
        # This callback will be set by the parent page
        if hasattr(self, 'on_switch_to_pricing'):
            self.on_switch_to_pricing()

