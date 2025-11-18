"""
Sidebar navigation component.
"""

import flet as ft
from typing import Callable, Optional
from ui.theme import theme_manager
from utils.helpers import safe_page_update


class Sidebar(ft.Container):
    """Sidebar navigation with icon-only buttons."""
    
    def __init__(
        self,
        on_navigate: Callable[[str], None],
        on_fetch_data: Optional[Callable[[], None]] = None,
        current_page: str = "dashboard"
    ):
        self.on_navigate = on_navigate
        self.on_fetch_data = on_fetch_data
        self.current_page = current_page
        self._is_fetching = False
        self._nav_buttons = []
        
        # Create navigation buttons and store references
        self._nav_buttons = [
            self._create_nav_button("dashboard", ft.Icons.DASHBOARD, theme_manager.t("dashboard")),
            self._create_nav_button("telegram", ft.Icons.TELEGRAM, theme_manager.t("telegram")),
            self._create_nav_button("groups", ft.Icons.GROUP, theme_manager.t("groups")),
            self._create_nav_button("user_dashboard", ft.Icons.PERSON_SEARCH, theme_manager.t("user_dashboard")),
            self._create_nav_button("reports", ft.Icons.ASSESSMENT, theme_manager.t("reports")),
            self._create_nav_button("settings", ft.Icons.SETTINGS, theme_manager.t("settings")),
            ft.Container(expand=True),  # Spacer
            self._create_fetch_button(),
            self._create_nav_button("profile", ft.Icons.PERSON, theme_manager.t("profile")),
        ]
        
        super().__init__(
            width=65,
            bgcolor=theme_manager.surface_color,
            border=ft.border.only(right=ft.BorderSide(1, theme_manager.border_color)),
            padding=ft.padding.only(top=20, bottom=20),
            content=ft.Column(
                controls=self._nav_buttons,
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            # Ensure Container doesn't block pointer events to children
            clip_behavior=ft.ClipBehavior.NONE
        )
    
    def _create_nav_button(
        self,
        page_id: str,
        icon: str,
        tooltip: str
    ) -> ft.Container:
        """Create a navigation button."""
        is_active = self.current_page == page_id
        
        # Create a proper closure to capture page_id
        def make_click_handler(pid: str):
            def handler(e):
                # Navigation is always allowed - fetch continues in background
                self._handle_click(pid)
            return handler
        
        click_handler = make_click_handler(page_id)
        
        # Create IconButton with styling and click handler
        icon_button = ft.IconButton(
            icon=icon,
            icon_color=ft.Colors.WHITE if is_active else theme_manager.text_secondary_color,
            icon_size=24,
            tooltip=tooltip,
            on_click=click_handler,
            disabled=False,  # Navigation always allowed
            style=ft.ButtonStyle(
                bgcolor=theme_manager.primary_color if is_active else ft.Colors.TRANSPARENT,
                shape=ft.RoundedRectangleBorder(radius=theme_manager.corner_radius),
                padding=12  # Padding to center the icon
            )
        )
        
        # Wrap in Container for sizing only - IconButton handles clicks and tooltips
        # Don't set bgcolor or on_click on Container to avoid blocking events
        return ft.Container(
            content=icon_button,
            width=50,
            height=50,
            alignment=ft.alignment.center,
            ink=False
        )
    
    def _handle_click(self, page_id: str):
        """Handle navigation button click."""
        import logging
        logger = logging.getLogger(__name__)
        try:
            logger.debug(f"Sidebar navigation clicked: {page_id} (current: {self.current_page})")
            # Always navigate, even if same page (allows refresh)
            self.current_page = page_id
            if self.on_navigate:
                logger.debug(f"Calling on_navigate with page_id: {page_id}")
                self.on_navigate(page_id)
            else:
                logger.warning("on_navigate callback is None!")
            self._update_buttons()
        except Exception as e:
            logger.error(f"Error handling navigation click to '{page_id}': {e}", exc_info=True)
    
    def _create_fetch_button(self) -> ft.Container:
        """Create the fetch data button."""
        icon_button = ft.IconButton(
            icon=ft.Icons.DOWNLOAD,
            icon_color=ft.Colors.WHITE,
            icon_size=24,
            tooltip=theme_manager.t("fetch_data"),
            on_click=lambda e: self._handle_fetch_click(),
            disabled=False,  # Allow clicking fetch button even during fetch
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN,
                shape=ft.RoundedRectangleBorder(radius=theme_manager.corner_radius),
                padding=12  # Padding to center the icon
            )
        )
        
        # Wrap in Container for sizing only - IconButton handles clicks and tooltips
        return ft.Container(
            content=icon_button,
            width=50,
            height=50,
            alignment=ft.alignment.center,
            ink=False
        )
    
    def _handle_fetch_click(self):
        """Handle fetch data button click."""
        if self.on_fetch_data:
            self.on_fetch_data()
    
    def set_fetching_state(self, is_fetching: bool):
        """Enable/disable sidebar buttons based on fetching state."""
        self._is_fetching = is_fetching
        self._update_buttons()
    
    def _update_buttons(self):
        """Update button styles based on current page."""
        import logging
        logger = logging.getLogger(__name__)
        try:
            # Recreate navigation buttons with updated active state
            self._nav_buttons = [
                self._create_nav_button("dashboard", ft.Icons.DASHBOARD, theme_manager.t("dashboard")),
                self._create_nav_button("telegram", ft.Icons.TELEGRAM, theme_manager.t("telegram")),
                self._create_nav_button("groups", ft.Icons.GROUP, theme_manager.t("groups")),
                self._create_nav_button("user_dashboard", ft.Icons.PERSON_SEARCH, theme_manager.t("user_dashboard")),
                self._create_nav_button("reports", ft.Icons.ASSESSMENT, theme_manager.t("reports")),
                self._create_nav_button("settings", ft.Icons.SETTINGS, theme_manager.t("settings")),
                ft.Container(expand=True),
                self._create_fetch_button(),
                self._create_nav_button("profile", ft.Icons.PERSON, theme_manager.t("profile")),
            ]
            self.content.controls = self._nav_buttons
            # Update through page if available, otherwise try self.update()
            if hasattr(self, 'page') and self.page:
                if not safe_page_update(self.page):
                    # If page update failed (e.g., event loop closed), try self.update()
                    try:
                        self.update()
                    except (AssertionError, AttributeError, RuntimeError):
                        # Control not yet added to page or event loop closed, will update when added
                        logger.debug("Could not update sidebar buttons: page or event loop unavailable")
            else:
                try:
                    self.update()
                except (AssertionError, AttributeError, RuntimeError):
                    # Control not yet added to page, will update when added
                    logger.debug("Could not update sidebar buttons: control not yet added to page")
        except (AssertionError, AttributeError) as e:
            # Control not yet added to page, will update when added
            logger.debug(f"Could not update sidebar buttons: {e}")
        except RuntimeError as e:
            # Event loop closed or other runtime error
            if "Event loop is closed" in str(e):
                logger.debug("Could not update sidebar buttons: event loop is closed")
            else:
                logger.error(f"Error updating sidebar buttons: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error updating sidebar buttons: {e}", exc_info=True)
    
    def set_current_page(self, page_id: str):
        """Update current page from external source (e.g., when navigating from app)."""
        if self.current_page != page_id:
            self.current_page = page_id
            self._update_buttons()

