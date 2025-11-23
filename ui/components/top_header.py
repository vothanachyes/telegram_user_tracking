"""
Top header component with greeting and About navigation.
"""

import flet as ft
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from ui.theme import theme_manager
from services.auth_service import auth_service
from services.fetch_state_manager import fetch_state_manager
from services.notification_service import notification_service
from services.polling.notification_polling_service import NotificationPollingService

# Import configuration flag
try:
    from config.settings import ENABLE_REALTIME_WATCH_SERVICES
except ImportError:
    # Fallback if settings not available
    ENABLE_REALTIME_WATCH_SERVICES = False

logger = logging.getLogger(__name__)


class TopHeader(ft.Container):
    """Top header with time-based greeting and About button."""
    
    def __init__(self, on_navigate: Callable[[str], None]):
        self.on_navigate = on_navigate
        # Header text should be white/light for visibility on dark gradient background
        # Use white text in both modes since header has dark gradient
        self.greeting_text = ft.Text(
            self._get_greeting(),
            size=theme_manager.font_size_body,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE
        )
        
        # Avatar icon (can be replaced with image later)
        # Improved visibility with background and border
        avatar_bg_color = ft.Colors.with_opacity(0.2, ft.Colors.WHITE) if theme_manager.is_dark else ft.Colors.with_opacity(0.1, ft.Colors.BLACK)
        avatar_border_color = ft.Colors.WHITE if theme_manager.is_dark else ft.Colors.with_opacity(0.3, ft.Colors.BLACK)
        self.avatar = ft.Container(
            content=ft.CircleAvatar(
                content=ft.Icon(
                    ft.Icons.PERSON, 
                    size=20, 
                    color=ft.Colors.WHITE
                ),
                radius=18,
                bgcolor=avatar_bg_color
            ),
            border=ft.border.all(2, avatar_border_color),
            border_radius=20,
            on_click=lambda e: self.on_navigate("profile"),
            tooltip=theme_manager.t("profile") or "Profile",
            padding=2
        )
        
        # Fetch indicator (shows when fetching)
        # Use secondary color (which is a Color constant) with opacity for dark mode,
        # or use a semi-transparent blue for light mode
        if theme_manager.is_dark:
            # Dark mode: use secondary color (sky blue) with opacity
            primary_color_with_opacity = ft.Colors.with_opacity(0.2, ft.Colors.CYAN_700)
        else:
            # Light mode: use primary-like color with opacity
            primary_color_with_opacity = ft.Colors.with_opacity(0.2, ft.Colors.BLUE_700)
        
        self.fetch_indicator = ft.Container(
            content=ft.Row([
                ft.ProgressRing(width=12, height=12, stroke_width=2),
                ft.Text(
                    "",
                    size=12,
                    color=ft.Colors.WHITE,
                    weight=ft.FontWeight.BOLD
                )
            ], spacing=5, tight=True),
            visible=False,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=theme_manager.corner_radius,
            bgcolor=primary_color_with_opacity,
            on_click=lambda e: self.on_navigate("fetch_data"),
            tooltip="Click to view fetch progress"
        )
        
        # Notification icon with badge
        self.notification_badge_text = ft.Text(
            "0",
            size=10,
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.BOLD,
        )
        self.notification_badge = ft.Container(
            content=self.notification_badge_text,
            bgcolor=ft.Colors.RED,
            border_radius=10,
            width=20,
            height=20,
            alignment=ft.alignment.center,
            visible=False,
        )
        # Telegram Bot icon (future feature)
        self.telegram_bot_button = ft.IconButton(
            icon=ft.Icons.SMART_TOY,
            tooltip="Telegram Bot (Future)",
            icon_color=ft.Colors.WHITE
        )
        
        # Initialize notification polling service
        self._notification_polling_service: Optional[NotificationPollingService] = None
        
        self.notification_button = ft.Stack(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.NOTIFICATIONS,
                    tooltip=theme_manager.t("notifications") or "Notifications",
                    on_click=lambda e: self.on_navigate("notifications"),
                    icon_color=ft.Colors.WHITE
                ),
                ft.Container(
                    content=self.notification_badge,
                    right=5,
                    top=5,
                ),
            ],
        )
        
        # About button
        self.about_button = ft.IconButton(
            icon=ft.Icons.INFO_OUTLINE,
            tooltip=theme_manager.t("about"),
            on_click=lambda e: self.on_navigate("about"),
            icon_color=ft.Colors.WHITE
        )
        
        # Check for background image
        project_root = Path(__file__).parent.parent.parent
        header_bg_path = None
        for ext in ['.png', '.jpg', '.jpeg']:
            bg_path = project_root / "assets" / f"header_background{ext}"
            if bg_path.exists():
                header_bg_path = str(bg_path)
                break
        
        # Create content row
        content_row = ft.Row([
            self.avatar,
            theme_manager.spacing_container("sm"),  # Spacing between avatar and text
            ft.GestureDetector(
                content=self.greeting_text,
                on_tap=lambda e: self.on_navigate("dashboard")
            ),
            ft.Container(expand=True),  # Spacer
            self.fetch_indicator,
            self.telegram_bot_button,
            self.notification_button,
            self.about_button
        ], 
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Create stack for gradient + image + content
        stack_children = []
        
        # Gradient background - use primary colors for both themes
        # Text is now white, so dark gradient works in both modes
        gradient_container = ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[theme_manager.primary_color, theme_manager.primary_dark]
            )
        )
        stack_children.append(gradient_container)
        
        # Background image (if exists)
        if header_bg_path:
            bg_image = ft.Image(
                src=header_bg_path,
                fit=ft.ImageFit.COVER,
                opacity=0.3,
                expand=True
            )
            stack_children.append(bg_image)
        
        # Content layer
        content_layer = ft.Container(
            content=content_row,
            padding=ft.padding.symmetric(horizontal=theme_manager.padding_sm, vertical=theme_manager.spacing_sm),
        )
        stack_children.append(content_layer)
        
        # Set background color as fallback to ensure visibility
        # Use primary color as fallback in case gradient doesn't render
        super().__init__(
            content=ft.Stack(stack_children),
            bgcolor=theme_manager.primary_color,  # Fallback background color
            border=ft.border.only(bottom=ft.BorderSide(1, theme_manager.border_color)),
            height=45
        )
    
    def _get_greeting(self) -> str:
        """Get time-based greeting with user name."""
        current_user = auth_service.get_current_user()
        user_name = current_user.get("display_name", "") if current_user else ""
        if not user_name:
            user_name = current_user.get("email", "").split("@")[0] if current_user else "User"
        
        hour = datetime.now().hour
        
        if hour < 12:
            greeting = theme_manager.t("good_morning")
        elif hour < 18:
            greeting = theme_manager.t("good_afternoon")
        else:
            greeting = theme_manager.t("good_evening")
        
        return f"{greeting}, {user_name}"
    
    def update_greeting(self):
        """Update greeting text (call when time changes or user changes)."""
        self.greeting_text.value = self._get_greeting()
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def update_fetch_indicator(self):
        """Update fetch indicator visibility and text."""
        if fetch_state_manager.is_fetching:
            count = fetch_state_manager.processed_count
            indicator_text = self.fetch_indicator.content.controls[1]
            indicator_text.value = theme_manager.t("fetching_indicator").format(count=count) or f"Fetching: {count} messages"
            self.fetch_indicator.visible = True
        else:
            self.fetch_indicator.visible = False
        
        if hasattr(self, 'page') and self.page:
            try:
                self.page.update()
            except:
                pass
    
    def update_notification_badge(self):
        """Update notification badge count."""
        try:
            current_user = auth_service.get_current_user()
            if not current_user:
                self.notification_badge.visible = False
                return
            
            user_id = current_user.get("uid")
            if not user_id:
                self.notification_badge.visible = False
                return
            
            # Get unread count
            unread_count = notification_service.get_unread_count(user_id)
            
            if unread_count > 0:
                self.notification_badge_text.value = str(unread_count) if unread_count <= 99 else "99+"
                self.notification_badge.visible = True
            else:
                self.notification_badge.visible = False
            
            if hasattr(self, 'page') and self.page:
                try:
                    self.page.update()
                except:
                    pass
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.debug(f"Error updating notification badge: {e}")
    
    async def start_fetch_indicator_updates(self):
        """Start periodic updates for fetch indicator (async coroutine for page.run_task)."""
        # Check if already running using a flag
        if hasattr(self, '_fetch_updates_running') and self._fetch_updates_running:
            return  # Already running
        
        self._fetch_updates_running = True
        
        try:
            # Periodically update fetch indicator and notification badge
            while True:
                try:
                    await asyncio.sleep(0.5)  # Update every 0.5 seconds
                    if hasattr(self, 'page') and self.page:
                        self.update_fetch_indicator()
                except asyncio.CancelledError:
                    break
                except Exception:
                    pass
        finally:
            self._fetch_updates_running = False
    
    async def setup_realtime_notifications(self):
        """Setup real-time notification listener with fallback to polling."""
        try:
            current_user = auth_service.get_current_user()
            if not current_user:
                logger.debug("No current user for real-time notifications")
                return
            
            user_id = current_user.get("uid")
            if not user_id:
                logger.debug("No user ID for real-time notifications")
                return
            
            # Try to start real-time listener
            from services.notification_service import notification_service
            
            def on_unread_count_changed(count: int):
                """Callback when unread count changes."""
                try:
                    if count > 0:
                        self.notification_badge_text.value = str(count) if count <= 99 else "99+"
                        self.notification_badge.visible = True
                    else:
                        self.notification_badge.visible = False
                    
                    if hasattr(self, 'page') and self.page:
                        try:
                            self.page.update()
                        except Exception:
                            pass
                except Exception as e:
                    logger.error(f"Error updating badge from real-time: {e}")
            
            # Start real-time listener
            success = await notification_service.start_realtime_listener(
                user_id=user_id,
                on_unread_count_changed=on_unread_count_changed
            )
            
            if success:
                logger.info("Real-time notification listener started")
                # Initial update
                self.update_notification_badge()
            else:
                # Only log as warning if watch services are enabled (unexpected failure)
                # If disabled, this is expected behavior
                if ENABLE_REALTIME_WATCH_SERVICES:
                    logger.warning("Failed to start real-time listener, falling back to polling")
                else:
                    logger.debug("Real-time listener not started (watch services disabled - using polling)")
                # Fallback to polling
                await self.start_notification_badge_updates()
        
        except Exception as e:
            logger.error(f"Error setting up real-time notifications: {e}", exc_info=True)
            # Fallback to polling
            await self.start_notification_badge_updates()
    
    async def start_notification_badge_updates(self):
        """Start periodic updates for notification badge using generic polling service."""
        # Stop existing polling service if running
        if self._notification_polling_service and self._notification_polling_service.is_running:
            await self._notification_polling_service.stop()
        
        # Create callback for unread count changes
        def on_unread_count_changed(count: int):
            """Callback when unread count changes."""
            try:
                if count > 0:
                    self.notification_badge_text.value = str(count) if count <= 99 else "99+"
                    self.notification_badge.visible = True
                else:
                    self.notification_badge.visible = False
                
                if hasattr(self, 'page') and self.page:
                    try:
                        self.page.update()
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Error updating badge from polling: {e}")
        
        # Create and start polling service
        self._notification_polling_service = NotificationPollingService(
            on_unread_count_changed=on_unread_count_changed
        )
        
        # Set condition check: only poll if user is logged in
        def should_poll() -> bool:
            return auth_service.is_logged_in()
        
        self._notification_polling_service.set_condition_check(should_poll)
        
        # Start the service
        await self._notification_polling_service.start()
        logger.debug("Notification polling service started")
    
    async def stop_notification_polling(self):
        """Stop notification polling service."""
        if self._notification_polling_service and self._notification_polling_service.is_running:
            await self._notification_polling_service.stop()
            logger.debug("Notification polling service stopped")

