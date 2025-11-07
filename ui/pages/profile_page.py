"""
Profile page showing current user and app info.
"""

import flet as ft
import logging
from typing import Callable, Optional
from ui.theme import theme_manager
from services.auth_service import auth_service
from config.settings import settings

logger = logging.getLogger(__name__)


class ProfilePage:
    """Profile page with user info and logout."""
    
    def __init__(self, page: ft.Page, on_logout: Callable[[], None]):
        self.page = page
        self.on_logout = on_logout
        self.logout_dialog: Optional[ft.AlertDialog] = None
        
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

