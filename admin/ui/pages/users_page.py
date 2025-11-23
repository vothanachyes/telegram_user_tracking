"""
Admin users management page.
"""

import flet as ft
import logging
from typing import Optional
from admin.services.admin_user_service import admin_user_service
from admin.ui.components.data_table import DataTable
from admin.ui.dialogs import UserFormDialog, DeleteConfirmDialog

logger = logging.getLogger(__name__)


class AdminUsersPage(ft.Container):
    """Admin users management page."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.data_table: Optional[DataTable] = None
        
        self.create_button = ft.ElevatedButton(
            text="Create User",
            icon=ft.Icons.ADD,
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
            on_click=self._on_create_user,
        )
        
        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Users",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color=self.TEXT_COLOR,
                            ),
                            self.create_button,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=20, color="transparent"),
                ],
                spacing=10,
                expand=True,
            ),
            padding=ft.padding.all(20),
            bgcolor=self.BG_COLOR,
            expand=True,
        )
        
        self._load_users()
    
    def _load_users(self):
        """Load users and populate table."""
        try:
            users = admin_user_service.get_all_users()
            
            columns = [
                {"key": "email", "label": "Email", "width": 200},
                {"key": "display_name", "label": "Display Name", "width": 150},
                {"key": "uid", "label": "UID", "width": 200},
                {"key": "disabled", "label": "Status", "width": 100},
                {"key": "license_tier", "label": "License Tier", "width": 120},
                {"key": "scheduled_deletion", "label": "Scheduled Deletion", "width": 180},
            ]
            
            # Format data for table
            table_data = []
            for user in users:
                # Format scheduled deletion date
                scheduled_deletion_date = user.get("scheduled_deletion_date")
                deletion_display = "N/A"
                if scheduled_deletion_date:
                    try:
                        from datetime import datetime
                        if isinstance(scheduled_deletion_date, str):
                            dt = datetime.fromisoformat(scheduled_deletion_date.replace("Z", "+00:00"))
                        elif hasattr(scheduled_deletion_date, "timestamp"):
                            dt = scheduled_deletion_date.replace(tzinfo=None)
                        else:
                            dt = scheduled_deletion_date
                        deletion_display = dt.strftime("%Y-%m-%d %H:%M UTC")
                    except Exception:
                        deletion_display = str(scheduled_deletion_date)
                
                table_data.append({
                    "email": user.get("email", ""),
                    "display_name": user.get("display_name", "N/A"),
                    "uid": user.get("uid", ""),
                    "disabled": "Disabled" if user.get("disabled") else "Active",
                    "license_tier": user.get("license_tier", "none").capitalize(),
                    "scheduled_deletion": deletion_display,
                    "_user_data": user,  # Store full user data
                })
            
            actions = [
                {
                    "label": "Edit",
                    "icon": ft.Icons.EDIT,
                    "on_click": self._on_edit_user,
                },
                {
                    "label": "Delete",
                    "icon": ft.Icons.DELETE,
                    "on_click": self._on_delete_user,
                },
            ]
            
            self.data_table = DataTable(
                columns=columns,
                data=table_data,
                actions=actions,
            )
            
            self.content.controls.append(self.data_table)
            # Only update if control is on the page
            if hasattr(self, 'page') and self.page:
                self.update()
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading users: {e}", exc_info=True)
    
    def _on_create_user(self, e: ft.ControlEvent):
        """Handle create user button click."""
        dialog = UserFormDialog(
            user_data=None,
            on_submit=self._handle_create_user,
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening create user dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_edit_user(self, user_data: dict):
        """Handle edit user action."""
        # Get full user data
        full_user_data = user_data.get("_user_data", user_data)
        dialog = UserFormDialog(
            user_data=full_user_data,
            on_submit=lambda **kwargs: self._handle_update_user(full_user_data.get("uid"), **kwargs),
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening edit user dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_delete_user(self, user_data: dict):
        """Handle delete user action."""
        full_user_data = user_data.get("_user_data", user_data)
        user_email = full_user_data.get("email", "this user")
        user_uid = full_user_data.get("uid")
        
        # Check if deletion is already scheduled
        scheduled_deletion = admin_user_service.get_scheduled_deletion(user_uid)
        if scheduled_deletion:
            deletion_date = scheduled_deletion.get("deletion_date")
            if isinstance(deletion_date, str):
                from datetime import datetime
                try:
                    deletion_date = datetime.fromisoformat(deletion_date.replace("Z", "+00:00"))
                except Exception:
                    pass
            
            if deletion_date:
                formatted_date = deletion_date.strftime("%B %d, %Y at %I:%M %p UTC") if hasattr(deletion_date, 'strftime') else str(deletion_date)
                message = f"User '{user_email}' is already scheduled for deletion on {formatted_date}."
            else:
                message = f"User '{user_email}' is already scheduled for deletion."
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor="#ff9800",
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        dialog = DeleteConfirmDialog(
            title="Schedule User Deletion",
            message=f"Are you sure you want to schedule deletion for user '{user_email}'? The user will be notified and their account will be deleted in 24 hours. This action cannot be undone.",
            item_name=user_email,
            on_confirm=lambda: self._handle_delete_user(user_uid, user_email, full_user_data.get("display_name")),
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening delete confirmation dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _handle_create_user(self, email: str, password: str, display_name: Optional[str], disabled: bool, license_tier: Optional[str] = None):
        """Handle user creation."""
        try:
            uid = admin_user_service.create_user(
                email=email,
                password=password,
                display_name=display_name,
            )
            
            if uid:
                # Update disabled status if needed
                if disabled:
                    admin_user_service.update_user(uid, disabled=True)
                
                # Create license if tier is selected
                if license_tier and license_tier != "none":
                    from admin.services.admin_license_service import admin_license_service
                    from datetime import datetime, timedelta
                    
                    # Get tier definition to set expiration date
                    tier_definition = admin_license_service.get_tier_definition(license_tier)
                    period_days = tier_definition.get("period", 30) if tier_definition else 30
                    
                    license_data = {
                        "tier": license_tier,
                        "expiration_date": (datetime.utcnow() + timedelta(days=period_days)).isoformat() + "Z",
                    }
                    
                    if not admin_license_service.create_license(uid, license_data):
                        logger.warning(f"User created but failed to create license for {uid}")
                
                # Create welcome notification
                try:
                    from admin.services.admin_notification_service import admin_notification_service
                    admin_notification_service.create_welcome_notification(
                        uid=uid,
                        email=email,
                        display_name=display_name,
                        license_tier=license_tier if license_tier and license_tier != "none" else None
                    )
                except Exception as e:
                    # Don't block user creation if notification fails
                    logger.error(f"Failed to create welcome notification for user {uid}: {e}", exc_info=True)
                
                # Reload users
                self._reload_users()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"User created successfully: {email}"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to create user. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error creating user: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error creating user: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _handle_update_user(self, uid: str, email: str, password: Optional[str], display_name: Optional[str], disabled: bool, license_tier: Optional[str] = None):
        """Handle user update."""
        try:
            update_data = {
                "email": email,
                "display_name": display_name,
                "disabled": disabled,
            }
            
            # Only update password if provided
            if password:
                update_data["password"] = password
            
            success = admin_user_service.update_user(uid, **update_data)
            
            if success:
                # Update license if tier is provided
                if license_tier is not None:
                    from admin.services.admin_license_service import admin_license_service
                    from datetime import datetime, timedelta
                    
                    existing_license = admin_license_service.get_license(uid)
                    
                    if license_tier == "none":
                        # Delete license if "none" is selected
                        if existing_license:
                            admin_license_service.delete_license(uid)
                    else:
                        # Create or update license
                        if existing_license:
                            # Update existing license
                            license_update = {"tier": license_tier}
                            admin_license_service.update_license(uid, license_update)
                        else:
                            # Create new license
                            tier_definition = admin_license_service.get_tier_definition(license_tier)
                            period_days = tier_definition.get("period", 30) if tier_definition else 30
                            
                            license_data = {
                                "tier": license_tier,
                                "expiration_date": (datetime.utcnow() + timedelta(days=period_days)).isoformat() + "Z",
                            }
                            admin_license_service.create_license(uid, license_data)
                
                # Reload users
                self._reload_users()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("User updated successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to update user. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error updating user: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error updating user: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _handle_delete_user(self, uid: str, email: str, display_name: Optional[str] = None):
        """Handle user deletion scheduling."""
        try:
            from datetime import datetime, timedelta
            
            # Schedule deletion (24 hours from now)
            deletion_date = admin_user_service.schedule_user_deletion(uid)
            
            if deletion_date:
                # Send deletion warning notification
                try:
                    from admin.services.admin_notification_service import admin_notification_service
                    admin_notification_service.create_deletion_warning_notification(
                        uid=uid,
                        email=email,
                        display_name=display_name,
                        deletion_date=deletion_date
                    )
                except Exception as e:
                    logger.error(f"Failed to send deletion notification: {e}", exc_info=True)
                    # Continue even if notification fails
                
                # Reload users
                self._reload_users()
                
                formatted_date = deletion_date.strftime("%B %d, %Y at %I:%M %p UTC")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"User deletion scheduled for {formatted_date}. User has been notified."),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to schedule user deletion. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error scheduling user deletion: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error scheduling user deletion: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _reload_users(self):
        """Reload users table."""
        # Remove old table
        if self.data_table and self.data_table in self.content.controls:
            self.content.controls.remove(self.data_table)
        
        # Load new data
        self._load_users()

