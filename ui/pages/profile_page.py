"""
Profile page showing current user and app info.
"""

import flet as ft
import logging
from typing import Callable, Optional
from ui.theme import theme_manager
from ui.dialogs import dialog_manager
from services.auth_service import auth_service
from services.license_service import LicenseService
from database.db_manager import DatabaseManager
from config.settings import settings
from config.app_config import app_config

logger = logging.getLogger(__name__)


class ProfilePage:
    """Profile page with user info and logout."""
    
    def __init__(self, page: ft.Page, on_logout: Callable[[], None], db_manager: Optional[DatabaseManager] = None):
        self.page = page
        self.on_logout = on_logout
        
        # Initialize license service if db_manager provided
        self.license_service = None
        if db_manager:
            self.license_service = LicenseService(db_manager)
        
        # Create logout button (disabled in sample_db mode)
        is_sample_mode = app_config.is_sample_db_mode()
        self.logout_button = theme_manager.create_button(
            text=theme_manager.t("logout"),
            icon=ft.Icons.LOGOUT,
            on_click=self._handle_logout,
            style="error",
            disabled=is_sample_mode  # Disable in sample_db mode
        )
    
    def _build_profile_card(self) -> ft.Container:
        """Build profile card with current user info."""
        # Get current user info fresh
        current_user = auth_service.get_current_user()
        
        if current_user:
            display_name = current_user.get("display_name") or current_user.get("email", "User")
            email = current_user.get("email", "")
        else:
            display_name = "Guest"
            email = ""
        
        return theme_manager.create_card(
            content=ft.Column([
                ft.Row([
                    ft.Icon(
                        ft.Icons.ACCOUNT_CIRCLE,
                        size=80,
                        color=theme_manager.primary_color
                    ),
                    ft.Column([
                        ft.Text(
                            display_name,
                            size=theme_manager.font_size_page_title,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(
                            email,
                            size=theme_manager.font_size_body,
                            color=theme_manager.text_secondary_color
                        ),
                    ], spacing=theme_manager.spacing_xs)
                ], spacing=theme_manager.spacing_lg),
                ft.Divider(),
                self.logout_button,
                ft.Text(
                    "Logout is disabled in sample database mode.",
                    size=12,
                    color=theme_manager.text_secondary_color,
                    visible=app_config.is_sample_db_mode()
                ) if app_config.is_sample_db_mode() else ft.Container(),
            ], spacing=theme_manager.spacing_md),
            width=500
        )
    
    def build(self) -> ft.Container:
        """Build and return the profile page container, refreshing user info."""
        # Build the container with fresh user info
        container = ft.Container(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("profile"),
                    size=theme_manager.font_size_page_title,
                    weight=ft.FontWeight.BOLD
                ),
                
                # Profile card - built fresh each time
                self._build_profile_card(),
                
                theme_manager.spacing_container("lg"),
                
                # License status card
                self._build_license_status_card(),
                
            ], scroll=ft.ScrollMode.AUTO, spacing=theme_manager.spacing_sm, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=theme_manager.padding_lg,
            expand=True
        )
        
        return container
    
    def _handle_logout(self, e):
        """Handle logout button click."""
        logger.info("=== LOGOUT BUTTON CLICKED ===")
        logger.info(f"Page reference: {self.page}")
        
        # Confirm logout
        def confirm_logout(confirm_event):
            logger.info("=== CONFIRM LOGOUT CLICKED ===")
            try:
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
        
        # Show confirmation dialog using centralized manager
        logger.info("Creating confirmation dialog")
        dialog_manager.show_confirmation_dialog(
            page=self.page,
            title=theme_manager.t("logout"),
            message=theme_manager.t("logout_confirm"),
            on_confirm=confirm_logout,
            confirm_text=theme_manager.t("yes"),
            cancel_text=theme_manager.t("cancel"),
            confirm_color=theme_manager.primary_color,
            event=e
        )
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
        
        # Tier color - dynamic mapping based on tier key
        tier_colors = {
            'bronze': ft.Colors.BROWN,
            'silver': ft.Colors.GREY,
            'gold': ft.Colors.AMBER,
            'premium': ft.Colors.PURPLE,
            'custom': ft.Colors.BLUE_GREY
        }
        tier_color = tier_colors.get(tier.lower(), ft.Colors.GREY)
        
        # Status badge
        if expired:
            status_badge = ft.Container(
                content=ft.Text(
                    theme_manager.t("license_expired"),
                    color=ft.Colors.WHITE,
                    size=theme_manager.font_size_small,
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
                    size=theme_manager.font_size_small,
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
                    size=theme_manager.font_size_small,
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
                        size=theme_manager.font_size_section_title,
                        weight=ft.FontWeight.BOLD
                    ),
                    status_badge
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
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
                ], spacing=theme_manager.spacing_sm),
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
                    width=500
                ) if days_remaining is not None or expiration_date is None else ft.Container(height=0),
                theme_manager.spacing_container("sm"),
                ft.ElevatedButton(
                    theme_manager.t("view_pricing"),
                    icon=ft.Icons.ARROW_FORWARD,
                    on_click=lambda e: self._navigate_to_pricing(),
                    bgcolor=theme_manager.primary_color,
                    color=ft.Colors.WHITE
                )
            ], spacing=theme_manager.spacing_md),
            width=500
        )
    
    def _navigate_to_pricing(self):
        """Navigate to About page, Pricing tab."""
        # This will be handled by the parent app's navigation
        # We'll use a callback or event
        if hasattr(self.page, 'route'):
            # Try to trigger navigation through page
            pass

