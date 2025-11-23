"""
Admin notifications management page.
"""

import flet as ft
import logging
from typing import Optional, List, Dict, Set
from datetime import datetime
from admin.services.admin_notification_service import admin_notification_service
from admin.ui.components.data_table import DataTable
from admin.ui.components.user_multi_select import UserMultiSelect
from admin.ui.dialogs.notification_form_dialog import NotificationFormDialog
from admin.ui.dialogs.notification_view_dialog import NotificationViewDialog
from admin.ui.dialogs import DeleteConfirmDialog

logger = logging.getLogger(__name__)


class AdminNotificationsPage(ft.Container):
    """Admin notifications management page."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    CARD_BG = "#252525"
    BORDER_COLOR = "#333333"
    SUCCESS_COLOR = "#4caf50"
    WARNING_COLOR = "#ff9800"
    ERROR_COLOR = "#f44336"
    INFO_COLOR = "#2196f3"
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.data_table: Optional[DataTable] = None
        self.table_container: Optional[ft.Container] = None
        self.all_notifications: List[Dict] = []
        
        # Filter state
        self.selected_type: Optional[str] = "all"
        self.selected_user_ids: Set[str] = set()
        self.show_all_users: bool = False
        
        self.create_button = ft.ElevatedButton(
            text="+ Create Notification",
            icon=ft.Icons.ADD_CIRCLE_OUTLINE,
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
            on_click=self._on_create_notification,
            height=40,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )
        
        # Statistics cards
        self.stats_container = ft.Container(
            content=None,
            visible=False,
        )
        
        # Filter controls
        self.type_filter = ft.Dropdown(
            label="Type",
            hint_text="All types",
            options=[
                ft.dropdown.Option(key="all", text="All Types"),
                ft.dropdown.Option(key="info", text="Info"),
                ft.dropdown.Option(key="warning", text="Warning"),
                ft.dropdown.Option(key="announcement", text="Announcement"),
                ft.dropdown.Option(key="update", text="Update"),
                ft.dropdown.Option(key="welcome", text="Welcome"),
            ],
            value="all",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            on_change=self._on_type_filter_changed,
            width=180,
        )
        
        self.user_filter = UserMultiSelect(
            label="Users",
            width=280,
            on_selection_changed=self._on_user_filter_changed,
        )
        
        self.all_users_filter = ft.Checkbox(
            label="Include 'All Users' notifications",
            value=False,
            on_change=self._on_all_users_filter_changed,
        )
        
        self.clear_filters_button = ft.OutlinedButton(
            text="Clear All",
            icon=ft.Icons.CLEAR_ALL,
            on_click=self._on_clear_filters,
            tooltip="Clear all filters",
        )
        
        # Filter card container
        self.filter_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.FILTER_LIST, color=self.PRIMARY_COLOR, size=20),
                            ft.Text(
                                "Filters",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=self.TEXT_COLOR,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Divider(height=15, color="transparent"),
                    ft.Row(
                        controls=[
                            self.type_filter,
                            self.user_filter,
                        ],
                        spacing=15,
                        wrap=False,
                    ),
                    ft.Divider(height=10, color="transparent"),
                    ft.Row(
                        controls=[
                            self.all_users_filter,
                            ft.Container(expand=True),
                            self.clear_filters_button,
                        ],
                        spacing=10,
                    ),
                ],
                spacing=0,
            ),
            bgcolor=self.CARD_BG,
            padding=ft.padding.all(20),
            border_radius=12,
            border=ft.border.all(1, self.BORDER_COLOR),
        )
        
        super().__init__(
            content=ft.Column(
                controls=[
                    # Header section
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "Notifications",
                                        size=32,
                                        weight=ft.FontWeight.BOLD,
                                        color=self.TEXT_COLOR,
                                    ),
                                    ft.Text(
                                        "Manage and send notifications to users",
                                        size=14,
                                        color=self.TEXT_SECONDARY,
                                    ),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                            self.create_button,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=30, color="transparent"),
                    # Statistics section
                    self.stats_container,
                    ft.Divider(height=20, color="transparent"),
                    # Filter section
                    self.filter_card,
                    ft.Divider(height=20, color="transparent"),
                ],
                spacing=0,
                expand=True,
            ),
            padding=ft.padding.all(24),
            bgcolor=self.BG_COLOR,
            expand=True,
        )
        
        # Set page reference for user filter component (will be updated in set_page if needed)
        if self.page:
            self.user_filter.page = self.page
        
        # Don't load notifications here - will be loaded asynchronously in set_page
        self.all_notifications = []
    
    def set_page(self, page: ft.Page):
        """Set page reference and load data asynchronously."""
        # Only set page if it's different (to avoid duplicate loading)
        if self.page != page:
            self.page = page
            self.user_filter.page = page
        
        # Load notifications asynchronously
        if page and hasattr(page, 'run_task'):
            page.run_task(self._load_notifications_async)
        else:
            import asyncio
            asyncio.create_task(self._load_notifications_async())
    
    async def _load_notifications_async(self):
        """Load notifications asynchronously."""
        try:
            # Show loading indicator
            if hasattr(self, 'data_table') and self.data_table:
                # Show loading in table
                pass
            
            # Check cache
            from services.page_cache_service import page_cache_service
            cache_key = page_cache_service.generate_key("admin_notifications")
            notifications = page_cache_service.get(cache_key)
            
            if not notifications:
                # Load from service (may be slow - Firebase API call)
                notifications = admin_notification_service.get_all_notifications()
                # Cache for 60 seconds
                if page_cache_service.is_enabled():
                    page_cache_service.set(cache_key, notifications, ttl=60)
            
            self.all_notifications = notifications
            self._apply_filters()
            
            if self.page:
                self.page.update()
            
        except Exception as e:
            logger.error(f"Error loading notifications: {e}", exc_info=True)
            if self.page:
                self.page.update()
    
    def _apply_filters(self):
        """Apply filters to notifications and update table."""
        try:
            # Start with all notifications
            filtered = self.all_notifications.copy()
            
            # Filter by type (AND logic)
            if self.selected_type and self.selected_type != "all":
                filtered = [
                    n for n in filtered
                    if n.get("type", "").lower() == self.selected_type.lower()
                ]
            
            # Filter by user (OR logic - show notifications that match either condition)
            user_filtered = []
            has_user_filters = self.selected_user_ids or self.show_all_users
            
            if has_user_filters:
                for n in filtered:
                    target_users = n.get("target_users")
                    # Check if matches "All Users" filter
                    if self.show_all_users and target_users is None:
                        user_filtered.append(n)
                    # Check if matches specific user filter
                    elif self.selected_user_ids and target_users and any(
                        uid in target_users for uid in self.selected_user_ids
                    ):
                        user_filtered.append(n)
                
                filtered = user_filtered
            
            # Format data for table
            columns = [
                {"key": "title", "label": "Title", "width": 200},
                {"key": "subtitle", "label": "Subtitle", "width": 150},
                {"key": "type", "label": "Type", "width": 100},
                {"key": "target", "label": "Target", "width": 150},
                {"key": "created_at", "label": "Created At", "width": 150},
            ]
            
            table_data = []
            for notification_data in filtered:
                target_users = notification_data.get("target_users")
                if target_users is None:
                    target = "All Users"
                else:
                    count = len(target_users) if isinstance(target_users, list) else 0
                    target = f"{count} User(s)"
                
                created_at = notification_data.get("created_at", "")
                if created_at:
                    try:
                        if isinstance(created_at, str):
                            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                            created_at = dt.strftime("%Y-%m-%d %H:%M")
                        elif hasattr(created_at, "strftime"):
                            created_at = created_at.strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        created_at = str(created_at)
                
                # Get notification type for styling
                notif_type = notification_data.get("type", "info").lower()
                type_display = notif_type.capitalize()
                
                table_data.append({
                    "title": notification_data.get("title", ""),
                    "subtitle": notification_data.get("subtitle", "N/A") if notification_data.get("subtitle") else "",
                    "type": type_display,  # Store type for badge rendering
                    "type_raw": notif_type,  # Store raw type for badge creation
                    "target": target,
                    "created_at": created_at or "N/A",
                    "_notification_data": notification_data,  # Store full notification data
                })
            
            actions = [
                {
                    "label": "View",
                    "icon": ft.Icons.VISIBILITY,
                    "on_click": self._on_view_notification,
                    "tooltip": "View notification details",
                },
                {
                    "label": "Delete",
                    "icon": ft.Icons.DELETE,
                    "on_click": self._on_delete_notification,
                    "tooltip": "Delete notification",
                },
            ]
            
            # Remove old table container if exists
            if self.table_container and self.table_container in self.content.controls:
                self.content.controls.remove(self.table_container)
            
            # Create new table with filtered data
            if table_data:
                # Custom cell renderer for type column
                def render_type_cell(row_data: dict) -> ft.Control:
                    notif_type = row_data.get("type_raw", "info")
                    type_label = row_data.get("type", "Info")
                    return self._create_type_badge(notif_type, type_label)
                
                self.data_table = DataTable(
                    columns=columns,
                    data=table_data,
                    actions=actions,
                    cell_renderers={"type": render_type_cell},
                )
                
                # Wrap table in container for full width
                self.table_container = ft.Container(
                    content=self.data_table,
                    expand=True,
                )
                
                self.content.controls.append(self.table_container)
            else:
                # Show empty state
                if self.table_container and self.table_container in self.content.controls:
                    self.content.controls.remove(self.table_container)
                
                empty_state = self._create_empty_state()
                if empty_state not in self.content.controls:
                    self.content.controls.append(empty_state)
            
            # Update statistics
            self._update_statistics()
            
            # Only update if control is on the page
            if hasattr(self, 'page') and self.page:
                self.update()
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}", exc_info=True)
    
    def _on_create_notification(self, e: ft.ControlEvent):
        """Handle create notification button click."""
        dialog = NotificationFormDialog(
            notification_data=None,
            on_submit=self._handle_create_notification,
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening create notification dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_view_notification(self, notification_data: dict):
        """Handle view notification action."""
        full_notification_data = notification_data.get("_notification_data", notification_data)
        dialog = NotificationViewDialog(
            notification_data=full_notification_data,
            on_edit=lambda data: self._on_edit_notification_from_view(data),
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening view notification dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_edit_notification_from_view(self, notification_data: dict):
        """Handle edit notification from view dialog."""
        dialog = NotificationFormDialog(
            notification_data=notification_data,
            on_submit=lambda notification_data_param: self._handle_update_notification(
                notification_data.get("notification_id"), notification_data_param
            ),
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening edit notification dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_delete_notification(self, notification_data: dict):
        """Handle delete notification action."""
        full_notification_data = notification_data.get("_notification_data", notification_data)
        notification_id = full_notification_data.get("notification_id", "unknown")
        title = full_notification_data.get("title", "Unknown")
        
        dialog = DeleteConfirmDialog(
            title="Delete Notification",
            message=f"Are you sure you want to delete the notification '{title}'? This action cannot be undone.",
            item_name=title,
            on_confirm=lambda: self._handle_delete_notification(notification_id),
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening delete confirmation dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _handle_create_notification(self, notification_data: dict):
        """Handle notification creation."""
        try:
            success = admin_notification_service.create_notification(notification_data)
            
            if success:
                # Reload notifications
                self._reload_notifications()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Notification created successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to create notification. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error creating notification: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _handle_update_notification(self, notification_id: str, notification_data: dict):
        """Handle notification update."""
        try:
            success = admin_notification_service.update_notification(notification_id, notification_data)
            
            if success:
                # Reload notifications
                self._reload_notifications()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Notification updated successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to update notification. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error updating notification: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error updating notification: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _handle_delete_notification(self, notification_id: str):
        """Handle notification deletion."""
        try:
            success = admin_notification_service.delete_notification(notification_id)
            
            if success:
                # Reload notifications
                self._reload_notifications()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Notification deleted successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to delete notification. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error deleting notification: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error deleting notification: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _reload_notifications(self):
        """Reload notifications table."""
        # Load new data (preserves filter state)
        self._load_notifications()
    
    def _on_type_filter_changed(self, e: ft.ControlEvent):
        """Handle type filter change."""
        self.selected_type = e.control.value
        self._apply_filters()
    
    def _on_user_filter_changed(self, selected_ids: Set[str]):
        """Handle user filter change."""
        self.selected_user_ids = selected_ids
        self._apply_filters()
    
    def _on_all_users_filter_changed(self, e: ft.ControlEvent):
        """Handle 'All Users' filter change."""
        self.show_all_users = e.control.value
        self._apply_filters()
    
    def _on_clear_filters(self, e: ft.ControlEvent):
        """Clear all filters."""
        self.selected_type = "all"
        self.type_filter.value = "all"
        self.selected_user_ids = set()
        self.user_filter.clear_selection()
        self.show_all_users = False
        self.all_users_filter.value = False
        self._apply_filters()
    
    def _create_type_badge(self, notif_type: str, label: str) -> ft.Container:
        """Create a colored badge for notification type."""
        color_map = {
            "info": self.INFO_COLOR,
            "warning": self.WARNING_COLOR,
            "error": self.ERROR_COLOR,
            "announcement": self.PRIMARY_COLOR,
            "update": self.SUCCESS_COLOR,
            "welcome": self.SUCCESS_COLOR,
        }
        
        bg_color = color_map.get(notif_type.lower(), self.TEXT_SECONDARY)
        
        return ft.Container(
            content=ft.Text(
                label,
                size=10,
                weight=ft.FontWeight.BOLD,
                color="#ffffff",
            ),
            bgcolor=bg_color,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=8,
            alignment=ft.alignment.center,
        )
    
    def _create_empty_state(self) -> ft.Container:
        """Create empty state when no notifications match filters."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.NOTIFICATIONS_NONE,
                        size=64,
                        color=self.TEXT_SECONDARY,
                    ),
                    ft.Divider(height=20, color="transparent"),
                    ft.Text(
                        "No notifications found",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=self.TEXT_COLOR,
                    ),
                    ft.Text(
                        "Try adjusting your filters or create a new notification",
                        size=14,
                        color=self.TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Divider(height=30, color="transparent"),
                    ft.ElevatedButton(
                        text="Create Notification",
                        icon=ft.Icons.ADD,
                        bgcolor=self.PRIMARY_COLOR,
                        color=self.TEXT_COLOR,
                        on_click=self._on_create_notification,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=ft.padding.all(60),
            alignment=ft.alignment.center,
        )
    
    def _update_statistics(self):
        """Update statistics cards."""
        try:
            total = len(self.all_notifications)
            filtered = len([n for n in self.all_notifications if self._matches_filters(n)])
            
            # Count by type
            type_counts = {}
            for notif in self.all_notifications:
                notif_type = notif.get("type", "info")
                type_counts[notif_type] = type_counts.get(notif_type, 0) + 1
            
            stats_cards = ft.Row(
                controls=[
                    self._create_stat_card(
                        "Total",
                        str(total),
                        ft.Icons.NOTIFICATIONS,
                        self.TEXT_COLOR,
                    ),
                    self._create_stat_card(
                        "Filtered",
                        str(filtered),
                        ft.Icons.FILTER_LIST,
                        self.PRIMARY_COLOR,
                    ),
                    self._create_stat_card(
                        "Info",
                        str(type_counts.get("info", 0)),
                        ft.Icons.INFO,
                        self.INFO_COLOR,
                    ),
                    self._create_stat_card(
                        "Warning",
                        str(type_counts.get("warning", 0)),
                        ft.Icons.WARNING,
                        self.WARNING_COLOR,
                    ),
                ],
                spacing=15,
            )
            
            self.stats_container.content = stats_cards
            self.stats_container.visible = True
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}", exc_info=True)
    
    def _create_stat_card(self, label: str, value: str, icon: str, icon_color: str) -> ft.Container:
        """Create a statistics card."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon, color=icon_color, size=20),
                            ft.Text(
                                label,
                                size=12,
                                color=self.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Text(
                        value,
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=self.TEXT_COLOR,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=self.CARD_BG,
            padding=ft.padding.all(16),
            border_radius=12,
            border=ft.border.all(1, self.BORDER_COLOR),
            expand=True,
        )
    
    def _matches_filters(self, notification: dict) -> bool:
        """Check if notification matches current filters."""
        # Type filter
        if self.selected_type and self.selected_type != "all":
            if notification.get("type", "").lower() != self.selected_type.lower():
                return False
        
        # User filter
        has_user_filters = self.selected_user_ids or self.show_all_users
        if has_user_filters:
            target_users = notification.get("target_users")
            matches_all_users = self.show_all_users and target_users is None
            matches_specific = self.selected_user_ids and target_users and any(
                uid in target_users for uid in self.selected_user_ids
            )
            if not (matches_all_users or matches_specific):
                return False
        
        return True

