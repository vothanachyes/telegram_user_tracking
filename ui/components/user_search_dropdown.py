"""
Reusable user search component with dropdown.
"""

import flet as ft
from typing import Optional, Callable, List
from database.models import TelegramUser
from ui.theme import theme_manager


class UserSearchDropdown:
    """Reusable user search component with dropdown."""
    
    def __init__(
        self,
        on_user_selected: Callable[[TelegramUser], None],
        on_search_change: Optional[Callable[[str], None]] = None,
        width: int = 300,
        min_query_length: int = 2
    ):
        """
        Initialize user search dropdown.
        
        Args:
            on_user_selected: Callback when a user is selected
            on_search_change: Optional callback when search query changes
            width: Width of the search field
            min_query_length: Minimum query length to trigger search
        """
        self.on_user_selected = on_user_selected
        self.on_search_change = on_search_change
        self.page: Optional[ft.Page] = None
        self.min_query_length = min_query_length
        
        # Search field with dropdown
        self.search_field = ft.TextField(
            hint_text=theme_manager.t("search_user"),
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._on_search_change,
            on_focus=self._on_search_focus,
            on_blur=self._on_search_blur,
            width=width,
            border_radius=theme_manager.corner_radius
        )
        
        # Helper text below search field
        self.search_helper_text = ft.Text(
            "",
            size=11,
            color=theme_manager.text_secondary_color,
            visible=False
        )
        
        self.search_dropdown = ft.Container(
            visible=False,
            bgcolor=theme_manager.surface_color,
            border=ft.border.all(1, theme_manager.border_color),
            border_radius=theme_manager.corner_radius,
            padding=5,
            width=width,
            content=ft.Column([], spacing=2, scroll=ft.ScrollMode.AUTO, tight=True)
        )
    
    def build(self) -> ft.Column:
        """Build the search component."""
        return ft.Column([
            self.search_field,
            self.search_helper_text,
            self.search_dropdown,
        ], spacing=2, tight=True)
    
    def set_page(self, page: ft.Page):
        """Set the Flet page instance for updates."""
        self.page = page
    
    def update_dropdown(self, users: List[TelegramUser]):
        """
        Update dropdown with search results.
        
        Args:
            users: List of TelegramUser objects to display
        """
        dropdown_items = []
        for user in users:
            display_name = user.full_name
            username_display = f"@{user.username}" if user.username else ""
            phone_display = user.phone or ""
            
            item = ft.Container(
                content=ft.Column([
                    ft.Text(display_name, size=14, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Text(username_display, size=12, color=theme_manager.text_secondary_color) if username_display else ft.Container(),
                        ft.Text(phone_display, size=12, color=theme_manager.text_secondary_color) if phone_display else ft.Container(),
                    ], spacing=10, wrap=False)
                ], spacing=2, tight=True),
                padding=10,
                on_click=lambda e, u=user: self._select_user(u),
                data=user,
                bgcolor=theme_manager.surface_color,
                border_radius=theme_manager.corner_radius
            )
            dropdown_items.append(item)
        
        self.search_dropdown.content.controls = dropdown_items
        self.search_dropdown.visible = len(users) > 0
        if self.page:
            self.search_dropdown.update()
    
    def set_value(self, value: str):
        """Set search field value."""
        self.search_field.value = value
        if self.page:
            self.search_field.update()
    
    def clear(self):
        """Clear search field and hide dropdown."""
        self.search_field.value = ""
        self._update_helper_text("")
        self.search_dropdown.visible = False
        self.search_dropdown.content.controls = []
        if self.page:
            self.search_dropdown.update()
    
    def _on_search_change(self, e):
        """Handle search field change."""
        query = e.control.value or ""
        
        # Update helper text based on prefix
        self._update_helper_text(query)
        
        if not query or len(query) < self.min_query_length:
            self.search_dropdown.visible = False
            self.search_dropdown.content.controls = []
            if self.page:
                self.search_dropdown.update()
            return
        
        if self.on_search_change:
            self.on_search_change(query)
    
    def _update_helper_text(self, value: str):
        """Update helper text based on search prefix."""
        if value.startswith('@'):
            self.search_helper_text.value = theme_manager.t("searching_by_username")
            self.search_helper_text.visible = True
        else:
            self.search_helper_text.visible = False
        
        try:
            self.search_helper_text.update()
        except (AssertionError, AttributeError):
            pass
    
    def _on_search_focus(self, e):
        """Handle search field focus."""
        if self.search_dropdown.content.controls:
            self.search_dropdown.visible = True
            if self.page:
                self.search_dropdown.update()
    
    def _on_search_blur(self, e):
        """Handle search field blur - hide dropdown after delay."""
        if self.page:
            import threading
            def hide_dropdown():
                import time
                time.sleep(0.2)
                self.search_dropdown.visible = False
                if self.page:
                    try:
                        self.search_dropdown.update()
                    except Exception:
                        pass
            threading.Thread(target=hide_dropdown, daemon=True).start()
    
    def _select_user(self, user: TelegramUser):
        """Select a user from dropdown."""
        self.search_field.value = user.full_name
        self.search_dropdown.visible = False
        self.on_user_selected(user)
        if self.page:
            self.page.update()

