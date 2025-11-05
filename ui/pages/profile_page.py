"""
Profile page showing current user and app info.
"""

import flet as ft
from typing import Callable
from ui.theme import theme_manager
from services.auth_service import auth_service
from config.settings import settings


class ProfilePage(ft.Container):
    """Profile page with user info and logout."""
    
    def __init__(self, on_logout: Callable[[], None]):
        self.on_logout = on_logout
        
        # Get current user
        current_user = auth_service.get_current_user()
        
        # Build layout
        super().__init__(
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
                                ft.icons.ACCOUNT_CIRCLE,
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
                        theme_manager.create_button(
                            text=theme_manager.t("logout"),
                            icon=ft.icons.LOGOUT,
                            on_click=self._handle_logout,
                            style="error"
                        ),
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
                            ft.Icon(ft.icons.INFO, color=theme_manager.primary_color),
                            ft.Column([
                                ft.Text(theme_manager.t("version"), size=12, color=theme_manager.text_secondary_color),
                                ft.Text(settings.app_version, size=16),
                            ], spacing=2)
                        ], spacing=10),
                        ft.Row([
                            ft.Icon(ft.icons.PERSON, color=theme_manager.primary_color),
                            ft.Column([
                                ft.Text("Developer", size=12, color=theme_manager.text_secondary_color),
                                ft.Text(settings.developer_name, size=16),
                            ], spacing=2)
                        ], spacing=10),
                        ft.Row([
                            ft.Icon(ft.icons.EMAIL, color=theme_manager.primary_color),
                            ft.Column([
                                ft.Text(theme_manager.t("email"), size=12, color=theme_manager.text_secondary_color),
                                ft.Text(settings.developer_email, size=16),
                            ], spacing=2)
                        ], spacing=10),
                        ft.Row([
                            ft.Icon(ft.icons.PHONE, color=theme_manager.primary_color),
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
    
    def _handle_logout(self, e):
        """Handle logout button click."""
        # Confirm logout
        def confirm_logout(e):
            if auth_service.logout():
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("logout_success"),
                    bgcolor=ft.colors.GREEN
                )
                self.on_logout()
            self.page.dialog.open = False
            self.page.update()
        
        def cancel_logout(e):
            self.page.dialog.open = False
            self.page.update()
        
        theme_manager.show_dialog(
            self.page,
            title=theme_manager.t("logout"),
            content=ft.Text("Are you sure you want to logout?"),
            actions=[
                ft.TextButton(theme_manager.t("cancel"), on_click=cancel_logout),
                ft.TextButton(theme_manager.t("yes"), on_click=confirm_logout),
            ]
        )

