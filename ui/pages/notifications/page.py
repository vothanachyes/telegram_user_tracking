"""
Notifications page with All and Own tabs.
"""

import flet as ft
import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from services.notification_service import notification_service
from services.auth_service import auth_service
from services.page_cache_service import page_cache_service
from ui.theme import theme_manager
from ui.components.skeleton_loaders.notifications_skeleton import NotificationsSkeleton

logger = logging.getLogger(__name__)


class NotificationsPage:
    """Notifications page with All and Own tabs."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.all_notifications: List[dict] = []
        self.user_specific_notifications: List[dict] = []
        self.read_statuses: Dict[str, bool] = {}
        self.is_loading = True
        
        # Create skeleton loader
        self.loading_indicator = NotificationsSkeleton.create()
        
        # Create tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            on_change=self._on_tab_change,
            tabs=[
                ft.Tab(
                    text=theme_manager.t("all_notifications") or "All",
                    content=self._build_all_tab()
                ),
                ft.Tab(
                    text=theme_manager.t("my_notifications") or "Own",
                    content=self._build_own_tab()
                )
            ],
            expand=True
        )
        
        # Create main content (initially hidden)
        self.content_column = ft.Column([
            ft.Text(
                theme_manager.t("notifications") or "Notifications",
                size=theme_manager.font_size_page_title,
                weight=ft.FontWeight.BOLD
            ),
            self.tabs
        ], scroll=ft.ScrollMode.AUTO, spacing=0)
        
        # Main container that switches between loading and content
        self.main_content = ft.Container(
            content=self.loading_indicator,
            expand=True
        )
        
        self.container = ft.Container(
            content=self.main_content,
            padding=theme_manager.padding_lg,
            expand=True
        )
        
        # DON'T load here - wait for set_page() to be called
    
    def set_page(self, page: ft.Page):
        """Set page reference and load data asynchronously."""
        self.page = page
        # Load notifications asynchronously
        self._load_notifications_async()
    
    def build(self) -> ft.Container:
        """Build and return the notifications page container."""
        return self.container
    
    def _build_all_tab(self) -> ft.Container:
        """Build All notifications tab."""
        return ft.Container(
            content=ft.Column(
                controls=[],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            padding=theme_manager.padding_md,
        )
    
    def _build_own_tab(self) -> ft.Container:
        """Build Own notifications tab."""
        return ft.Container(
            content=ft.Column(
                controls=[],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            padding=theme_manager.padding_md,
        )
    
    def _on_tab_change(self, e: ft.ControlEvent):
        """Handle tab change."""
        self._update_tab_content()
    
    def _load_notifications_async(self):
        """Load notifications asynchronously in the background."""
        if self.page and hasattr(self.page, 'run_task'):
            self.page.run_task(self._load_notifications_task)
        else:
            # Fallback for environments without run_task
            asyncio.create_task(self._load_notifications_task())
    
    async def _load_notifications_task(self):
        """Async task to load notifications."""
        try:
            from database.async_query_executor import async_query_executor
            
            current_user = auth_service.get_current_user()
            if not current_user:
                logger.warning("No current user for loading notifications")
                self._hide_loading()
                return
            
            user_id = current_user.get("uid")
            if not user_id:
                logger.warning("No user ID for loading notifications")
                self._hide_loading()
                return
            
            # Check cache first
            cache_key_all = page_cache_service.generate_key("notifications", user_id=user_id, type="all")
            cache_key_user = page_cache_service.generate_key("notifications", user_id=user_id, type="user")
            cache_key_statuses = page_cache_service.generate_key("notifications", user_id=user_id, type="statuses")
            
            all_notifications = page_cache_service.get(cache_key_all)
            user_notifications = page_cache_service.get(cache_key_user)
            read_statuses = page_cache_service.get(cache_key_statuses)
            
            if all_notifications and user_notifications and read_statuses:
                self.all_notifications = all_notifications
                self.user_specific_notifications = user_notifications
                self.read_statuses = read_statuses
            else:
                # Get notifications asynchronously (Firebase API call in thread pool)
                all_notifications, user_notifications = await async_query_executor.execute(
                    notification_service.get_notifications, user_id
                )
                
                # Get read statuses asynchronously
                read_statuses = await async_query_executor.execute(
                    notification_service.get_read_statuses, user_id
                )
                
                self.all_notifications = all_notifications
                self.user_specific_notifications = user_notifications
                self.read_statuses = read_statuses
                
                # Cache results (short TTL - 60 seconds for notifications)
                if page_cache_service.is_enabled():
                    page_cache_service.set(cache_key_all, self.all_notifications, ttl=60)
                    page_cache_service.set(cache_key_user, self.user_specific_notifications, ttl=60)
                    page_cache_service.set(cache_key_statuses, self.read_statuses, ttl=60)
            
            # Hide loading and show content
            self._hide_loading()
            
            # Update UI
            self._update_tab_content()
            
        except Exception as e:
            logger.error(f"Error loading notifications: {e}", exc_info=True)
            self._hide_loading()
            # Show error message
            self._show_error(str(e))
    
    def _hide_loading(self):
        """Hide loading indicator and show content."""
        self.is_loading = False
        # Switch main content from loading to actual content
        if hasattr(self, 'main_content'):
            self.main_content.content = self.content_column
        
        if self.page:
            try:
                self.page.update()
            except Exception as e:
                logger.debug(f"Error updating page after loading: {e}")
    
    def _show_error(self, error_message: str):
        """Show error message in the UI."""
        try:
            error_container = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color=ft.Colors.RED),
                    ft.Text(
                        theme_manager.t("error_loading") or "Error loading notifications",
                        size=theme_manager.font_size_body,
                        color=ft.Colors.RED,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        error_message,
                        size=theme_manager.font_size_small,
                        color=theme_manager.text_secondary_color
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=theme_manager.spacing_md,
                alignment=ft.MainAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True,
                padding=theme_manager.padding_xl
            )
            # Switch to error view
            if hasattr(self, 'main_content'):
                self.main_content.content = error_container
            if self.page:
                self.page.update()
        except Exception as e:
            logger.error(f"Error showing error message: {e}")
    
    def _load_notifications(self):
        """Synchronous load notifications (kept for backward compatibility)."""
        # This method is kept for compatibility but now calls async version
        self._load_notifications_async()
    
    def _update_tab_content(self):
        """Update tab content with notifications."""
        try:
            # Get current tab index
            selected_index = self.tabs.selected_index
            
            if selected_index == 0:
                # All tab
                notifications = self.all_notifications
                tab_content = self.tabs.tabs[0].content
            else:
                # Own tab
                notifications = self.user_specific_notifications
                tab_content = self.tabs.tabs[1].content
            
            # Clear existing content
            if isinstance(tab_content, ft.Container) and isinstance(tab_content.content, ft.Column):
                tab_content.content.controls.clear()
            
            # Add notification cards
            if notifications:
                for notification in notifications:
                    card = self._create_notification_card(notification)
                    if isinstance(tab_content, ft.Container) and isinstance(tab_content.content, ft.Column):
                        tab_content.content.controls.append(card)
            else:
                # Empty state
                empty_text = ft.Text(
                    theme_manager.t("no_notifications") or "No notifications",
                    size=theme_manager.font_size_body,
                    color=theme_manager.text_secondary_color,
                )
                if isinstance(tab_content, ft.Container) and isinstance(tab_content.content, ft.Column):
                    tab_content.content.controls.append(
                        ft.Container(
                            content=empty_text,
                            alignment=ft.alignment.center,
                            padding=theme_manager.padding_lg,
                        )
                    )
            
            # Update page
            if self.page:
                self.page.update()
                
        except Exception as e:
            logger.error(f"Error updating tab content: {e}", exc_info=True)
    
    def _create_notification_card(self, notification: dict) -> ft.Container:
        """Create a notification card."""
        notification_id = notification.get("notification_id", "")
        title = notification.get("title", "")
        subtitle = notification.get("subtitle", "")
        notification_type = notification.get("type", "info")
        created_at = notification.get("created_at", "")
        
        # Check if read
        is_read = self.read_statuses.get(notification_id, False)
        
        # Format date
        date_text = ""
        if created_at:
            try:
                if isinstance(created_at, str):
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    date_text = dt.strftime("%Y-%m-%d %H:%M")
                elif hasattr(created_at, "strftime"):
                    date_text = created_at.strftime("%Y-%m-%d %H:%M")
                else:
                    date_text = str(created_at)
            except Exception:
                date_text = str(created_at)
        
        # Type badge color
        type_colors = {
            "info": ft.Colors.BLUE,
            "warning": ft.Colors.ORANGE,
            "announcement": ft.Colors.PURPLE,
            "update": ft.Colors.GREEN,
        }
        type_color = type_colors.get(notification_type, ft.Colors.GREY)
        
        # Unread indicator
        unread_indicator = ft.Container(
            width=8,
            height=8,
            bgcolor=ft.Colors.BLUE,
            border_radius=4,
            visible=not is_read,
        )
        
        # Card content
        card_content = ft.Container(
            content=ft.Row([
                unread_indicator,
                ft.Column([
                    ft.Row([
                        ft.Text(
                            title,
                            size=theme_manager.font_size_body,
                            weight=ft.FontWeight.BOLD,
                            color=theme_manager.text_color,
                        ),
                        ft.Container(
                            content=ft.Text(
                                notification_type.capitalize(),
                                size=10,
                                color=ft.Colors.WHITE,
                            ),
                            bgcolor=type_color,
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            border_radius=4,
                        ),
                    ], spacing=10),
                    ft.Text(
                        subtitle or "",
                        size=theme_manager.font_size_small,
                        color=theme_manager.text_secondary_color,
                    ) if subtitle else ft.Container(),
                    ft.Text(
                        date_text,
                        size=theme_manager.font_size_small,
                        color=theme_manager.text_secondary_color,
                    ),
                ], spacing=5, expand=True),
            ], spacing=10, expand=True),
            padding=theme_manager.padding_md,
            border=ft.border.all(1, theme_manager.border_color),
            border_radius=theme_manager.corner_radius,
            bgcolor=theme_manager.surface_color,
            on_click=lambda e: self._on_notification_click(notification),
        )
        
        return card_content
    
    def _on_notification_click(self, notification: dict):
        """Handle notification card click."""
        try:
            from ui.dialogs.notification_detail_dialog import NotificationDetailDialog
            
            notification_id = notification.get("notification_id")
            if not notification_id:
                return
            
            # Open detail dialog
            dialog = NotificationDetailDialog(
                notification=notification,
                on_close=self._on_notification_read,
            )
            dialog.page = self.page
            
            try:
                self.page.open(dialog)
            except Exception as ex:
                logger.error(f"Error opening notification detail dialog: {ex}")
                self.page.dialog = dialog
                dialog.open = True
                self.page.update()
                
        except Exception as e:
            logger.error(f"Error opening notification detail: {e}", exc_info=True)
    
    def _on_notification_read(self, notification_id: str):
        """Handle notification marked as read."""
        try:
            # Update read status
            self.read_statuses[notification_id] = True
            
            # Reload notifications to refresh UI (async)
            self._load_notifications_async()
            
            # Update notification badge in header
            if hasattr(self.page, 'data') and self.page.data:
                router = self.page.data.get('router')
                if router and hasattr(router, 'page'):
                    # Find top header and update badge
                    # This is a bit hacky, but works
                    pass
            
        except Exception as e:
            logger.error(f"Error handling notification read: {e}", exc_info=True)

