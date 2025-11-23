"""
About tab content for about page.
"""

import flet as ft
from ui.theme import theme_manager
from config.settings import settings
from services.license_service import LicenseService


class AboutTab:
    """About tab component."""
    
    def __init__(self, license_service: LicenseService):
        self.license_service = license_service
        self.license_info = None  # Will be loaded when needed
    
    def build(self) -> ft.Container:
        """Build About tab content."""
        return ft.Container(
            content=ft.Column([
                # App info card
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Text(
                            theme_manager.t("app_info"),
                            size=theme_manager.font_size_section_title,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        ft.Text(
                            theme_manager.t("app_description"),
                            size=theme_manager.font_size_body,
                            color=theme_manager.text_secondary_color
                        ),
                        theme_manager.spacing_container("lg"),
                        ft.Text(
                            theme_manager.t("features_overview"),
                            size=theme_manager.font_size_subsection_title,
                            weight=ft.FontWeight.BOLD
                        ),
                        theme_manager.spacing_container("sm"),
                        self._create_feature_item(theme_manager.t("feature_track_messages")),
                        self._create_feature_item(theme_manager.t("feature_user_analytics")),
                        self._create_feature_item(theme_manager.t("feature_export_reports")),
                        self._create_feature_item(theme_manager.t("feature_media_download")),
                        self._create_feature_item(theme_manager.t("feature_reaction_tracking")),
                    ], spacing=theme_manager.spacing_md),
                    width=700
                ),
                
                theme_manager.spacing_container("lg"),
                
                # Developer info card
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Text(
                            theme_manager.t("developer_info"),
                            size=theme_manager.font_size_section_title,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        ft.Row([
                            ft.Icon(ft.Icons.INFO, color=theme_manager.primary_color),
                            ft.Column([
                                ft.Text(theme_manager.t("version"), size=theme_manager.font_size_small, color=theme_manager.text_secondary_color),
                                ft.Text(settings.app_version, size=theme_manager.font_size_body),
                            ], spacing=theme_manager.spacing_xs)
                        ], spacing=theme_manager.spacing_sm),
                        ft.Row([
                            ft.Icon(ft.Icons.PERSON, color=theme_manager.primary_color),
                            ft.Column([
                                ft.Text("Developer", size=theme_manager.font_size_small, color=theme_manager.text_secondary_color),
                                ft.Text(settings.developer_name, size=theme_manager.font_size_body),
                            ], spacing=theme_manager.spacing_xs)
                        ], spacing=theme_manager.spacing_sm),
                        ft.Row([
                            ft.Icon(ft.Icons.EMAIL, color=theme_manager.primary_color),
                            ft.Column([
                                ft.Text(theme_manager.t("email"), size=theme_manager.font_size_small, color=theme_manager.text_secondary_color),
                                ft.Text(settings.developer_email, size=theme_manager.font_size_body),
                            ], spacing=theme_manager.spacing_xs)
                        ], spacing=theme_manager.spacing_sm),
                        ft.Row([
                            ft.Icon(ft.Icons.PHONE, color=theme_manager.primary_color),
                            ft.Column([
                                ft.Text(theme_manager.t("contact"), size=theme_manager.font_size_small, color=theme_manager.text_secondary_color),
                                ft.Text(settings.developer_contact, size=theme_manager.font_size_body),
                            ], spacing=theme_manager.spacing_xs)
                        ], spacing=theme_manager.spacing_sm),
                    ], spacing=theme_manager.spacing_md),
                    width=700
                ),
                
                theme_manager.spacing_container("lg"),
                
                # License info card
                self._build_license_info_card()
                
            ], scroll=ft.ScrollMode.AUTO, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            expand=True
        )
    
    def _create_feature_item(self, text: str) -> ft.Row:
        """Create a feature list item with checkmark."""
        return ft.Row([
            ft.Icon(ft.Icons.CHECK_CIRCLE, color=theme_manager.success_color, size=20),
            ft.Text(text, size=theme_manager.font_size_body, color=theme_manager.text_color)
        ], spacing=theme_manager.spacing_sm)
    
    def _build_license_info_card(self) -> ft.Container:
        """Build license information card."""
        from ui.pages.about.license_card import LicenseInfoCard
        # Load license info if not loaded
        if self.license_info is None:
            self.license_info = self.license_service.get_license_info()
        card = LicenseInfoCard(self.license_info)
        return card.build()

