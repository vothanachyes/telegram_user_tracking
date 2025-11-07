"""
Profile page showing current user and app info.
"""

import flet as ft
import logging
from typing import Callable, Optional
from ui.theme import theme_manager
from services.auth_service import auth_service
from services.license_service import LicenseService
from database.db_manager import DatabaseManager
from config.settings import settings
from utils.constants import LICENSE_PRICING

logger = logging.getLogger(__name__)


class ProfilePage:
    """Profile page with user info and logout."""
    
    def __init__(self, page: ft.Page, on_logout: Callable[[], None], db_manager: Optional[DatabaseManager] = None):
        self.page = page
        self.on_logout = on_logout
        self.logout_dialog: Optional[ft.AlertDialog] = None
        
        # Initialize license service if db_manager provided
        self.license_service = None
        if db_manager:
            self.license_service = LicenseService(db_manager)
        
        # Get current user
        current_user = auth_service.get_current_user()
        
        # Create logout button
        self.logout_button = theme_manager.create_button(
            text=theme_manager.t("logout"),
            icon=ft.Icons.LOGOUT,
            on_click=self._handle_logout,
            style="error"
        )
        
        # Build the container
        self.container = ft.Container(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("profile"),
                    size=32,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(height=20),
                
                # Profile card
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(
                                ft.Icons.ACCOUNT_CIRCLE,
                                size=80,
                                color=theme_manager.primary_color
                            ),
                            ft.Column([
                                ft.Text(
                                    current_user.get("display_name", "User") if current_user else "Guest",
                                    size=24,
                                    weight=ft.FontWeight.BOLD
                                ),
                                ft.Text(
                                    current_user.get("email", "") if current_user else "",
                                    size=14,
                                    color=theme_manager.text_secondary_color
                                ),
                            ], spacing=5)
                        ], spacing=20),
                        ft.Divider(),
                        self.logout_button,
                    ], spacing=15),
                    width=500
                ),
                
                ft.Container(height=20),
                
                # License status card
                self._build_license_status_card(),
                
                ft.Container(height=20),
                
                # App info card
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
                    width=500
                ),
                
            ], scroll=ft.ScrollMode.AUTO, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            expand=True
        )
    
    def build(self) -> ft.Container:
        """Build and return the profile page container."""
        return self.container
    
    def _handle_logout(self, e):
        """Handle logout button click."""
        logger.info("=== LOGOUT BUTTON CLICKED ===")
        logger.info(f"Page reference: {self.page}")
        
        # Confirm logout
        def confirm_logout(confirm_event):
            logger.info("=== CONFIRM LOGOUT CLICKED ===")
            try:
                # Close dialog first
                self.logout_dialog.open = False
                self.page.update()
                
                # Perform logout
                logger.info("Calling auth_service.logout()")
                logout_result = auth_service.logout()
                logger.info(f"Logout result: {logout_result}")
                
                # Show success message
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("logout_success"),
                    bgcolor=ft.Colors.GREEN
                )
                
                # Call logout callback
                logger.info("Calling on_logout callback")
                self.on_logout()
                logger.info("Logout complete")
            except Exception as ex:
                logger.error(f"Logout error: {ex}", exc_info=True)
        
        def cancel_logout(cancel_event):
            logger.info("=== CANCEL LOGOUT CLICKED ===")
            self.logout_dialog.open = False
            self.page.update()
        
        # Create and show confirmation dialog
        logger.info("Creating confirmation dialog")
        self.logout_dialog = ft.AlertDialog(
            title=ft.Text(theme_manager.t("logout")),
            content=ft.Text("Are you sure you want to logout?"),
            actions=[
                ft.TextButton(theme_manager.t("cancel"), on_click=cancel_logout),
                ft.TextButton(theme_manager.t("yes"), on_click=confirm_logout),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = self.logout_dialog
        self.logout_dialog.open = True
        self.page.update()
        logger.info("Dialog shown")
    
    def _build_license_status_card(self) -> ft.Container:
        """Build license status card."""
        if not self.license_service:
            return ft.Container(height=0)
        
        license_info = self.license_service.get_license_info()
        tier = license_info['tier']
        tier_name = license_info['tier_name']
        is_active = license_info['is_active']
        expired = license_info['expired']
        expiration_date = license_info['expiration_date']
        days_remaining = license_info['days_until_expiration']
        current_devices = license_info['current_devices']
        max_devices = license_info['max_devices']
        current_groups = license_info['current_groups']
        max_groups = license_info['max_groups']
        
        # Tier color
        tier_colors = {
            'silver': ft.Colors.GREY,
            'gold': ft.Colors.AMBER,
            'premium': ft.Colors.PURPLE
        }
        tier_color = tier_colors.get(tier, ft.Colors.GREY)
        
        # Status badge
        if expired:
            status_badge = ft.Container(
                content=ft.Text(
                    theme_manager.t("license_expired"),
                    color=ft.Colors.WHITE,
                    size=12,
                    weight=ft.FontWeight.BOLD
                ),
                bgcolor=ft.Colors.RED,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=theme_manager.corner_radius
            )
        elif days_remaining is not None and days_remaining < 7:
            status_badge = ft.Container(
                content=ft.Text(
                    f"{theme_manager.t('license_expiring_soon')} ({days_remaining} {theme_manager.t('days_remaining')})",
                    color=ft.Colors.WHITE,
                    size=12,
                    weight=ft.FontWeight.BOLD
                ),
                bgcolor=ft.Colors.ORANGE,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=theme_manager.corner_radius
            )
        else:
            status_badge = ft.Container(
                content=ft.Text(
                    theme_manager.t("subscription"),
                    color=ft.Colors.WHITE,
                    size=12,
                    weight=ft.FontWeight.BOLD
                ),
                bgcolor=theme_manager.success_color,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=theme_manager.corner_radius
            )
        
        return theme_manager.create_card(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        theme_manager.t("subscription"),
                        size=20,
                        weight=ft.FontWeight.BOLD
                    ),
                    status_badge
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
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
                ], spacing=10),
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
                    on_click=lambda e: self._navigate_to_pricing(),
                    bgcolor=theme_manager.primary_color,
                    color=ft.Colors.WHITE
                )
            ], spacing=15),
            width=500
        )
    
    def _navigate_to_pricing(self):
        """Navigate to About page, Pricing tab."""
        # This will be handled by the parent app's navigation
        # We'll use a callback or event
        if hasattr(self.page, 'route'):
            # Try to trigger navigation through page
            pass

