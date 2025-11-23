"""
Admin user activities management page with grouped tree view.
"""

import flet as ft
import logging
from typing import Optional, Dict, List
from datetime import datetime
from admin.services.admin_user_activities_service import admin_user_activities_service
from admin.services.admin_user_service import admin_user_service
from admin.ui.dialogs import DeleteConfirmDialog

logger = logging.getLogger(__name__)


class AdminUserActivitiesPage(ft.Container):
    """Admin user activities management page with grouped tree view."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    SUCCESS_COLOR = "#4caf50"
    ERROR_COLOR = "#f44336"
    WARNING_COLOR = "#ff9800"
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.activities_container_ref = ft.Ref[ft.Container]()
        self.expanded_users: Dict[str, bool] = {}  # Track which users are expanded
        
        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "User Activities",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color=self.TEXT_COLOR,
                            ),
                            ft.Container(expand=True),
                            ft.ElevatedButton(
                                "Refresh",
                                icon=ft.Icons.REFRESH,
                                on_click=self._on_refresh,
                            ),
                        ],
                    ),
                    ft.Divider(height=20, color="transparent"),
                    ft.Container(
                        content=ft.Column(
                            controls=[],
                            spacing=0,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        expand=True,
                        ref=self.activities_container_ref,
                    ),
                ],
                spacing=10,
                expand=True,
            ),
            padding=ft.padding.all(20),
            bgcolor=self.BG_COLOR,
            expand=True,
        )
        
        self._load_activities()
    
    def _on_refresh(self, e):
        """Handle refresh button click."""
        self._load_activities()
    
    def _load_activities(self):
        """Load activities and create grouped tree view."""
        if not self.activities_container_ref.current:
            return
        
        activities_container = self.activities_container_ref.current
        if not activities_container.content:
            return
        
        activities_column = activities_container.content
        
        try:
            # Clear existing content
            activities_column.controls.clear()
            
            # Get all activities
            activities = admin_user_activities_service.get_all_activities()
            users = {u["uid"]: u for u in admin_user_service.get_all_users()}
            
            if not activities:
                # Show empty state
                activities_column.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.ANALYTICS, size=64, color=self.TEXT_SECONDARY),
                                ft.Text(
                                    "No user activities found",
                                    size=16,
                                    color=self.TEXT_SECONDARY,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        alignment=ft.alignment.center,
                        padding=40,
                    )
                )
                if self.page:
                    self.page.update()
                return
            
            # Create tree view for each user activity
            for activity in sorted(activities, key=lambda x: users.get(x.get("uid", ""), {}).get("email", "Unknown")):
                uid = activity.get("uid", "")
                user = users.get(uid, {})
                user_email = user.get("email", "Unknown")
                user_group = self._create_user_activity_group(user_email, activity, uid)
                activities_column.controls.append(user_group)
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            logger.error(f"Error loading activities: {e}", exc_info=True)
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error loading activities: {str(e)}"),
                    bgcolor=self.ERROR_COLOR,
                )
                self.page.snack_bar.open = True
                self.page.update()
    
    def _create_user_activity_group(self, user_email: str, activity: dict, uid: str) -> ft.Container:
        """Create a collapsible user activity group."""
        is_expanded = self.expanded_users.get(uid, False)  # Default to collapsed
        
        # Determine status
        is_blocked = activity.get("is_blocked", False)
        status_text = "Blocked" if is_blocked else "Active"
        status_color = self.ERROR_COLOR if is_blocked else self.SUCCESS_COLOR
        
        # Create expand/collapse icon
        expand_icon = ft.Icons.EXPAND_MORE if is_expanded else ft.Icons.CHEVRON_RIGHT
        
        # Create header row
        header_row = ft.Row(
            controls=[
                ft.Icon(expand_icon, size=20, color=self.PRIMARY_COLOR),
                ft.Text(
                    user_email,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=self.TEXT_COLOR,
                ),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Text(
                        status_text,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=status_color,
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border=ft.border.all(1, status_color),
                    border_radius=4,
                ),
            ],
            spacing=10,
        )
        
        # Create activity details (visible if expanded)
        activity_details = self._create_activity_details(activity, uid)
        activity_details.visible = is_expanded
        
        # Create group container
        group_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=header_row,
                        on_click=lambda e, user_id=uid: self._toggle_user_group(user_id),
                        padding=ft.padding.symmetric(horizontal=10, vertical=8),
                        bgcolor="#2a2a2a",
                        border_radius=5,
                    ),
                    ft.Container(
                        content=activity_details,
                        padding=ft.padding.only(left=30, top=5, bottom=5),
                    ),
                ],
                spacing=0,
            ),
            margin=ft.margin.only(bottom=10),
        )
        
        return group_container
    
    def _create_activity_details(self, activity: dict, uid: str) -> ft.Column:
        """Create activity details view."""
        total_devices = activity.get("total_devices_logged_on", 0)
        total_accounts = activity.get("total_telegram_accounts_authenticated", 0)
        total_groups = activity.get("total_telegram_groups_added", 0)
        app_version = activity.get("current_app_version", "N/A")
        is_blocked = activity.get("is_blocked", False)
        blocked_reason = activity.get("blocked_reason", "")
        blocked_at = activity.get("blocked_at", "")
        last_updated = activity.get("last_updated", "")
        
        # Format timestamps
        blocked_at_str = self._format_timestamp(blocked_at) if blocked_at else "N/A"
        last_updated_str = self._format_timestamp(last_updated) if last_updated else "N/A"
        
        details = ft.Column(
            controls=[
                # Statistics row
                ft.Row(
                    controls=[
                        self._create_stat_card("Devices", str(total_devices), ft.Icons.DEVICES),
                        self._create_stat_card("Accounts", str(total_accounts), ft.Icons.ACCOUNT_CIRCLE),
                        self._create_stat_card("Groups", str(total_groups), ft.Icons.GROUP),
                    ],
                    spacing=10,
                ),
                ft.Divider(height=10, color="transparent"),
                # Details row
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("App Version:", size=12, color=self.TEXT_SECONDARY, width=120),
                                    ft.Text(app_version, size=12, color=self.TEXT_COLOR),
                                ],
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text("Last Updated:", size=12, color=self.TEXT_SECONDARY, width=120),
                                    ft.Text(last_updated_str, size=12, color=self.TEXT_COLOR),
                                ],
                            ),
                            ft.Divider(height=5, color="transparent") if is_blocked else ft.Container(),
                            ft.Row(
                                controls=[
                                    ft.Text("Blocked Reason:", size=12, color=self.TEXT_SECONDARY, width=120),
                                    ft.Text(blocked_reason or "N/A", size=12, color=self.ERROR_COLOR),
                                ],
                            ) if is_blocked else ft.Container(),
                            ft.Row(
                                controls=[
                                    ft.Text("Blocked At:", size=12, color=self.TEXT_SECONDARY, width=120),
                                    ft.Text(blocked_at_str, size=12, color=self.ERROR_COLOR),
                                ],
                            ) if is_blocked else ft.Container(),
                        ],
                        spacing=5,
                    ),
                    padding=ft.padding.all(10),
                    bgcolor="#252525",
                    border_radius=5,
                ),
                ft.Divider(height=10, color="transparent"),
                # Actions row
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            "View Details",
                            icon=ft.Icons.INFO,
                            on_click=lambda e, a=activity: self._on_view_details(a),
                            style=ft.ButtonStyle(color=self.PRIMARY_COLOR),
                        ),
                        ft.ElevatedButton(
                            "Unblock" if is_blocked else "Block",
                            icon=ft.Icons.LOCK_OPEN if is_blocked else ft.Icons.BLOCK,
                            on_click=lambda e, a=activity, u=uid: self._on_toggle_block(a, u),
                            style=ft.ButtonStyle(
                                color=self.SUCCESS_COLOR if is_blocked else self.ERROR_COLOR
                            ),
                        ),
                    ],
                    spacing=10,
                ),
            ],
            spacing=5,
        )
        
        return details
    
    def _create_stat_card(self, label: str, value: str, icon: str) -> ft.Container:
        """Create a statistics card."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(icon, size=24, color=self.PRIMARY_COLOR),
                    ft.Text(
                        value,
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=self.TEXT_COLOR,
                    ),
                    ft.Text(
                        label,
                        size=12,
                        color=self.TEXT_SECONDARY,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
            padding=ft.padding.all(15),
            bgcolor="#252525",
            border_radius=5,
            expand=True,
        )
    
    def _format_timestamp(self, timestamp_str: str) -> str:
        """Format timestamp string."""
        if not timestamp_str:
            return "N/A"
        try:
            if isinstance(timestamp_str, str):
                dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            return str(timestamp_str)
        except Exception:
            return str(timestamp_str)
    
    def _toggle_user_group(self, uid: str):
        """Toggle expand/collapse of user group."""
        self.expanded_users[uid] = not self.expanded_users.get(uid, False)
        self._load_activities()  # Reload to update UI
    
    def _on_view_details(self, activity: dict):
        """Handle view details action."""
        uid = activity.get("uid", "")
        user = admin_user_service.get_user(uid)
        user_email = user.get("email", "Unknown") if user else "Unknown"
        
        # Create details dialog
        details = ft.Column(
            [
                ft.Text(f"User: {user_email}", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"Total Devices: {activity.get('total_devices_logged_on', 0)}"),
                ft.Text(f"Total Accounts: {activity.get('total_telegram_accounts_authenticated', 0)}"),
                ft.Text(f"Total Groups: {activity.get('total_telegram_groups_added', 0)}"),
                ft.Text(f"App Version: {activity.get('current_app_version', 'N/A')}"),
                ft.Text(f"Status: {'Blocked' if activity.get('is_blocked') else 'Active'}"),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO
        )
        
        if activity.get("is_blocked"):
            details.controls.append(ft.Divider())
            details.controls.append(ft.Text(f"Blocked Reason: {activity.get('blocked_reason', 'N/A')}"))
            blocked_at = activity.get("blocked_at")
            if blocked_at:
                details.controls.append(ft.Text(f"Blocked At: {self._format_timestamp(blocked_at)}"))
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Activity Details"),
            content=details,
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._close_dialog(dialog))
            ]
        )
        
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening details dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_toggle_block(self, activity: dict, uid: str):
        """Handle block/unblock user action."""
        is_blocked = activity.get("is_blocked", False)
        user = admin_user_service.get_user(uid)
        user_email = user.get("email", "Unknown") if user else "Unknown"
        
        if is_blocked:
            # Unblock
            title = "Unblock User"
            message = f"Are you sure you want to unblock user '{user_email}'?"
            confirm_text = "Unblock"
            confirm_color = self.SUCCESS_COLOR
            action_func = lambda: self._handle_unblock(uid)
        else:
            # Block
            title = "Block User"
            message = f"Are you sure you want to block user '{user_email}'? This will prevent them from adding/deleting Telegram accounts."
            confirm_text = "Block"
            confirm_color = self.ERROR_COLOR
            action_func = lambda: self._handle_block(uid)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda e: self._close_dialog(dialog)
                ),
                ft.TextButton(
                    confirm_text,
                    on_click=lambda e: (self._close_dialog(dialog), action_func()),
                    style=ft.ButtonStyle(color=confirm_color)
                )
            ]
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening block/unblock dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _handle_block(self, uid: str):
        """Handle block user."""
        try:
            success = admin_user_activities_service.block_user_for_excessive_actions(uid)
            
            if success:
                self._show_message("User blocked successfully", is_error=False)
                self._load_activities()
            else:
                self._show_message("Failed to block user. Please check logs.", is_error=True)
        except Exception as e:
            logger.error(f"Error blocking user: {e}", exc_info=True)
            self._show_message(f"Error: {str(e)}", is_error=True)
    
    def _handle_unblock(self, uid: str):
        """Handle unblock user."""
        try:
            success = admin_user_activities_service.unblock_user(uid)
            
            if success:
                self._show_message("User unblocked successfully", is_error=False)
                self._load_activities()
            else:
                self._show_message("Failed to unblock user. Please check logs.", is_error=True)
        except Exception as e:
            logger.error(f"Error unblocking user: {e}", exc_info=True)
            self._show_message(f"Error: {str(e)}", is_error=True)
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """Close dialog."""
        dialog.open = False
        if self.page:
            self.page.update()
    
    def _show_message(self, message: str, is_error: bool = False):
        """Show snackbar message."""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=self.ERROR_COLOR if is_error else self.SUCCESS_COLOR,
            )
            self.page.snack_bar.open = True
            self.page.update()
