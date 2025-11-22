"""
UI components for authenticate tab.
"""

import flet as ft
from ui.theme import theme_manager


class AuthenticateTabComponents:
    """UI component builders for authenticate tab."""
    
    def __init__(self, authenticate_tab):
        """Initialize components with reference to tab."""
        self.tab = authenticate_tab
    
    def build(self) -> ft.Container:
        """Build the authenticate tab with left navigation."""
        # Left navigation sidebar
        left_nav = self._build_left_navigation()
        
        # Right content area
        content_area = self._build_content_area()
        
        return ft.Container(
            content=ft.Row([
                left_nav,
                ft.VerticalDivider(width=1),
                content_area,
            ], spacing=0, expand=True),
            padding=10,
            expand=True
        )
    
    def _build_left_navigation(self) -> ft.Container:
        """Build left navigation sidebar."""
        # Store button references for style updates
        self.tab.accounts_nav_btn = ft.ElevatedButton(
            text=theme_manager.t("accounts_section"),
            icon=ft.Icons.ACCOUNT_CIRCLE,
            on_click=lambda e: self.tab._switch_section("accounts"),
            style=ft.ButtonStyle(
                bgcolor=theme_manager.primary_color if self.tab.selected_section == "accounts" else None,
                color=ft.Colors.WHITE if self.tab.selected_section == "accounts" else None
            ),
            width=150,
            height=40
        )
        
        self.tab.config_nav_btn = ft.ElevatedButton(
            text=theme_manager.t("configuration_section"),
            icon=ft.Icons.SETTINGS,
            on_click=lambda e: self.tab._switch_section("configuration"),
            style=ft.ButtonStyle(
                bgcolor=theme_manager.primary_color if self.tab.selected_section == "configuration" else None,
                color=ft.Colors.WHITE if self.tab.selected_section == "configuration" else None
            ),
            width=150,
            height=40
        )
        
        return ft.Container(
            content=ft.Column([
                self.tab.accounts_nav_btn,
                self.tab.config_nav_btn,
            ], spacing=10),
            width=170,
            padding=10,
            bgcolor=theme_manager.surface_color,
            border_radius=theme_manager.corner_radius
        )
    
    def _build_content_area(self) -> ft.Container:
        """Build right content area based on selected section."""
        if self.tab.selected_section == "accounts":
            content = self._build_accounts_section_content()
        else:
            content = self._build_configuration_section_content()
        
        container = ft.Container(
            content=content,
            expand=True,
            padding=10
        )
        self.tab.content_area_container = container
        return container
    
    def _build_accounts_section_content(self) -> ft.Column:
        """Build accounts section content."""
        return ft.Column([
            ft.Row([
                ft.Text(
                    theme_manager.t("accounts_section"),
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    expand=True
                ),
                self.tab.account_count_text,
            ], spacing=10),
            ft.Divider(),
            ft.Row([
                ft.Row([
                    self.tab.add_account_btn,
                    self.tab.add_account_loading,
                ], spacing=5, tight=True),
                ft.Row([
                    self.tab.refresh_status_btn,
                    self.tab.refresh_loading,
                ], spacing=5, tight=True),
            ], spacing=10),
            self.tab.sample_db_info if hasattr(self.tab, 'sample_db_info') else ft.Container(),
            self.tab.accounts_list,
            self.tab.error_text,
        ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)
    
    def _build_configuration_section_content(self) -> ft.Column:
        """Build configuration section content."""
        save_api_btn = theme_manager.create_button(
            text=theme_manager.t("save_api_credentials"),
            icon=ft.Icons.SAVE,
            on_click=self.tab._save,
            style="success"
        )
        cancel_api_btn = theme_manager.create_button(
            text=theme_manager.t("cancel"),
            icon=ft.Icons.CANCEL,
            on_click=self.tab._reset,
            style="error"
        )
        
        return ft.Column([
            ft.Text(
                theme_manager.t("configuration_section"),
                size=24,
                weight=ft.FontWeight.BOLD
            ),
            ft.Divider(),
            theme_manager.create_card(
                content=ft.Column([
                    ft.Text(
                        theme_manager.t("api_app_configuration"),
                        size=20,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Divider(),
                    self.tab.api_id_field,
                    self.tab.api_hash_field,
                    ft.Text(
                        theme_manager.t("get_api_credentials"),
                        size=12,
                        color=theme_manager.text_secondary_color,
                        italic=True
                    ),
                    self.tab.api_status_text,
                ], spacing=15)
            ),
            self.tab.error_text,
            ft.Row([
                cancel_api_btn,
                save_api_btn,
            ], alignment=ft.MainAxisAlignment.END, spacing=10),
        ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)
    
    def _build_accounts_section(self) -> ft.Container:
        """Build the saved accounts management section."""
        return theme_manager.create_card(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        theme_manager.t("saved_telegram_accounts"),
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        expand=True
                    ),
                    self.tab.refresh_status_btn,
                ], spacing=10),
                ft.Divider(),
                self.tab.accounts_list,
            ], spacing=15)
        )

