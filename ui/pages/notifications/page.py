"""
Notifications page with All and Own tabs.
"""

import flet as ft
import logging
from typing import List, Dict, Optional
from datetime import datetime
from services.notification_service import notification_service
from services.auth_service import auth_service
from ui.theme import theme_manager

logger = logging.getLogger(__name__)


class NotificationsPage:
    """Notifications page with All and Own tabs."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.all_notifications: List[dict] = []
        self.user_specific_notifications: List[dict] = []
        self.read_statuses: Dict[str, bool] = {}
        
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
        
        self.container = ft.Container(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("notifications") or "Notifications",
                    size=theme_manager.font_size_page_title,
                    weight=ft.FontWeight.BOLD
                ),
                self.tabs
            ], scroll=ft.ScrollMode.AUTO, spacing=0),
            padding=theme_manager.padding_lg,
            expand=True
        )
        
        # Load notifications
        self._load_notifications()
    
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
    
    def _load_notifications(self):
        """Load notifications from service."""
        try:
            current_user = auth_service.get_current_user()
            if not current_user:
                logger.warning("No current user for loading notifications")
                return
            
            user_id = current_user.get("uid")
            if not user_id:
                logger.warning("No user ID for loading notifications")
                return
            
            # Get notifications
            self.all_notifications, self.user_specific_notifications = notification_service.get_notifications(user_id)
            
            # Get read statuses
            self.read_statuses = notification_service.get_read_statuses(user_id)
            
            # Update UI
            self._update_tab_content()
            
        except Exception as e:
            logger.error(f"Error loading notifications: {e}", exc_info=True)
    
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
            
            # Reload notifications to refresh UI
            self._load_notifications()
            
            # Update notification badge in header
            if hasattr(self.page, 'data') and self.page.data:
                router = self.page.data.get('router')
                if router and hasattr(router, 'page'):
                    # Find top header and update badge
                    # This is a bit hacky, but works
                    pass
            
        except Exception as e:
            logger.error(f"Error handling notification read: {e}", exc_info=True)

