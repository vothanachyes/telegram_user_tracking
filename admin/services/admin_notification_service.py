"""
Admin notification management service.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from admin.config.admin_config import admin_config
from admin.services.admin_auth_service import admin_auth_service
from admin.utils.constants import (
    FIRESTORE_NOTIFICATIONS_COLLECTION,
    FIRESTORE_USER_NOTIFICATIONS_COLLECTION
)

logger = logging.getLogger(__name__)


class AdminNotificationService:
    """Handles notification CRUD operations."""
    
    def __init__(self):
        self._db = None
    
    def _ensure_initialized(self) -> bool:
        """Ensure Firebase is initialized."""
        if not admin_config.is_initialized():
            if not admin_config.initialize():
                return False
        self._db = admin_config.get_firestore()
        return self._db is not None
    
    def create_notification(self, notification_data: dict) -> bool:
        """Create new notification."""
        if not self._ensure_initialized():
            return False
        
        try:
            # Validate required fields
            if "title" not in notification_data or not notification_data["title"]:
                logger.error("Notification title is required")
                return False
            
            if "content" not in notification_data or not notification_data["content"]:
                logger.error("Notification content is required")
                return False
            
            if "type" not in notification_data:
                logger.error("Notification type is required")
                return False
            
            # Set defaults
            notification_data.setdefault("created_at", datetime.utcnow())
            current_admin = admin_auth_service.get_current_admin()
            notification_data.setdefault("created_by", current_admin.get("uid") if current_admin else None)
            
            # Auto-generate notification_id using Firestore document ID
            # Create document reference (Firestore will auto-generate ID)
            doc_ref = self._db.collection(FIRESTORE_NOTIFICATIONS_COLLECTION).document()
            notification_id = doc_ref.id
            
            # Add notification_id to data
            notification_data["notification_id"] = notification_id
            
            # Set document
            doc_ref.set(notification_data)
            
            logger.info(f"Notification created: {notification_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}", exc_info=True)
            return False
    
    def get_all_notifications(self) -> List[dict]:
        """List all notifications from Firestore."""
        if not self._ensure_initialized():
            return []
        
        try:
            notifications = []
            docs = self._db.collection(FIRESTORE_NOTIFICATIONS_COLLECTION).order_by("created_at", direction="DESCENDING").stream()
            
            for doc in docs:
                data = doc.to_dict()
                data["notification_id"] = doc.id
                # Convert Firestore timestamp to ISO string if needed
                if "created_at" in data and hasattr(data["created_at"], "isoformat"):
                    data["created_at"] = data["created_at"].isoformat() + "Z"
                notifications.append(data)
            
            logger.info(f"Retrieved {len(notifications)} notifications")
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting all notifications: {e}", exc_info=True)
            return []
    
    def get_notification(self, notification_id: str) -> Optional[dict]:
        """Get notification by ID."""
        if not self._ensure_initialized():
            return None
        
        try:
            doc_ref = self._db.collection(FIRESTORE_NOTIFICATIONS_COLLECTION).document(notification_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data["notification_id"] = notification_id
                # Convert Firestore timestamp to ISO string if needed
                if "created_at" in data and hasattr(data["created_at"], "isoformat"):
                    data["created_at"] = data["created_at"].isoformat() + "Z"
                return data
            return None
            
        except Exception as e:
            logger.error(f"Error getting notification {notification_id}: {e}", exc_info=True)
            return None
    
    def update_notification(self, notification_id: str, data: dict) -> bool:
        """Update notification."""
        if not self._ensure_initialized():
            return False
        
        try:
            # Don't allow updating notification_id or created_at
            data.pop("notification_id", None)
            data.pop("created_at", None)
            
            doc_ref = self._db.collection(FIRESTORE_NOTIFICATIONS_COLLECTION).document(notification_id)
            doc_ref.update(data)
            
            logger.info(f"Notification updated: {notification_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating notification {notification_id}: {e}", exc_info=True)
            return False
    
    def delete_notification(self, notification_id: str) -> bool:
        """Delete notification."""
        if not self._ensure_initialized():
            return False
        
        try:
            doc_ref = self._db.collection(FIRESTORE_NOTIFICATIONS_COLLECTION).document(notification_id)
            doc_ref.delete()
            
            logger.info(f"Notification deleted: {notification_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting notification {notification_id}: {e}", exc_info=True)
            return False
    
    def get_all_users(self) -> List[dict]:
        """Get all users for selection (reuse from admin_user_service)."""
        try:
            from admin.services.admin_user_service import admin_user_service
            return admin_user_service.get_all_users()
        except Exception as e:
            logger.error(f"Error getting users: {e}", exc_info=True)
            return []
    
    def create_welcome_notification(
        self,
        uid: str,
        email: str,
        display_name: Optional[str] = None,
        license_tier: Optional[str] = None
    ) -> bool:
        """
        Create welcome notification for a new user.
        
        Args:
            uid: User UID
            email: User email
            display_name: User display name (optional)
            license_tier: License tier key (optional)
        
        Returns:
            True if notification created successfully, False otherwise
        """
        try:
            from admin.utils.template_loader import template_loader
            from admin.services.admin_license_service import admin_license_service
            from admin.services.admin_license_tier_service import admin_license_tier_service
            from datetime import datetime
            from utils.constants import APP_NAME
            
            # Build variables dictionary
            variables = {
                "user_name": display_name or email,
                "user_email": email,
                "user_uid": uid,
                "app_name": APP_NAME,
                "current_date": datetime.utcnow().strftime("%B %d, %Y"),
            }
            
            # Build license section HTML if license exists
            license_section = ""
            if license_tier and license_tier != "none":
                try:
                    license_data = admin_license_service.get_license(uid)
                    tier_definition = admin_license_service.get_tier_definition(license_tier)
                    
                    if license_data and tier_definition:
                        tier_name = tier_definition.get("name", license_tier.capitalize())
                        max_groups = license_data.get("max_groups", tier_definition.get("max_groups", 1))
                        max_devices = license_data.get("max_devices", tier_definition.get("max_devices", 1))
                        max_accounts = license_data.get("max_accounts", tier_definition.get("max_accounts", 1))
                        
                        # Format expiration date
                        expiration_date = ""
                        if license_data.get("expiration_date"):
                            try:
                                exp_str = license_data["expiration_date"]
                                if isinstance(exp_str, str):
                                    # Remove Z suffix if present
                                    exp_str = exp_str.replace("Z", "+00:00")
                                    dt = datetime.fromisoformat(exp_str)
                                    expiration_date = dt.strftime("%B %d, %Y")
                            except Exception:
                                expiration_date = str(license_data.get("expiration_date", ""))
                        
                        # Format limits
                        def format_limit(value):
                            if value == -1:
                                return "∞"
                            return str(value)
                        
                        # Build license section HTML
                        license_section = f'''
            <div class="license-section">
                <h3>
                    <span>🎁</span>
                    Your License Information
                </h3>
                <div class="license-badge">{tier_name}</div>
                
                <div class="license-details">
                    <div class="license-item">
                        <div class="license-item-label">Groups</div>
                        <div class="license-item-value {"unlimited" if max_groups == -1 else ""}">
                            {format_limit(max_groups)}
                        </div>
                    </div>
                    <div class="license-item">
                        <div class="license-item-label">Devices</div>
                        <div class="license-item-value {"unlimited" if max_devices == -1 else ""}">
                            {format_limit(max_devices)}
                        </div>
                    </div>
                    <div class="license-item">
                        <div class="license-item-label">Accounts</div>
                        <div class="license-item-value {"unlimited" if max_accounts == -1 else ""}">
                            {format_limit(max_accounts)}
                        </div>
                    </div>
                </div>
'''
                        if expiration_date:
                            license_section += f'''
                <div class="expiration-date">
                    <strong>Expires:</strong> {expiration_date}
                </div>
'''
                        license_section += "            </div>"
                        
                        # Add license variables
                        variables["license_tier_name"] = tier_name
                        variables["license_tier_key"] = license_tier
                        variables["license_expiration_date"] = expiration_date
                        variables["license_max_groups"] = format_limit(max_groups)
                        variables["license_max_devices"] = format_limit(max_devices)
                        variables["license_max_accounts"] = format_limit(max_accounts)
                except Exception as e:
                    # If license data can't be loaded, continue without license section
                    logger.warning(f"Could not load license data for welcome notification: {e}")
            
            variables["license_section"] = license_section
            
            # Load and process template
            try:
                template_content = template_loader.load_template("new_user_greeting.html")
                content = template_loader.replace_variables(template_content, variables)
            except FileNotFoundError:
                # Fallback to simple text notification
                logger.warning("Welcome template not found, using fallback text")
                content = f"""<h1>Welcome to {APP_NAME}!</h1>
<p>Hello, {variables['user_name']}!</p>
<p>Thank you for joining {APP_NAME}. We're excited to have you on board!</p>
"""
                if license_section:
                    # Try to extract license info from variables
                    if "license_tier_name" in variables:
                        content += f"<p><strong>Your License:</strong> {variables['license_tier_name']}</p>"
                        if variables.get("license_expiration_date"):
                            content += f"<p><strong>Expires:</strong> {variables['license_expiration_date']}</p>"
            except Exception as e:
                logger.error(f"Error processing welcome template: {e}", exc_info=True)
                # Fallback to simple text
                content = f"""<h1>Welcome to {APP_NAME}!</h1>
<p>Hello, {variables['user_name']}!</p>
<p>Thank you for joining {APP_NAME}. We're excited to have you on board!</p>
"""
            
            # Create notification
            notification_data = {
                "title": f"Welcome to {APP_NAME}!",
                "subtitle": "We're excited to have you on board",
                "content": content,
                "type": "welcome",
                "target_users": [uid],  # Target specific user
            }
            
            success = self.create_notification(notification_data)
            
            if success:
                logger.info(f"Welcome notification created for user {uid}")
            else:
                logger.error(f"Failed to create welcome notification for user {uid}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error creating welcome notification: {e}", exc_info=True)
            return False
    
    def create_deletion_warning_notification(
        self,
        uid: str,
        email: str,
        display_name: Optional[str] = None,
        deletion_date: Optional[datetime] = None
    ) -> bool:
        """
        Create deletion warning notification for a user.
        
        Args:
            uid: User UID
            email: User email
            display_name: User display name (optional)
            deletion_date: Scheduled deletion date (optional, defaults to 24 hours from now)
        
        Returns:
            True if notification created successfully, False otherwise
        """
        try:
            from admin.utils.template_loader import template_loader
            from utils.constants import APP_NAME
            
            if deletion_date is None:
                deletion_date = datetime.utcnow() + timedelta(hours=24)
            
            # Format deletion date and time
            deletion_date_str = deletion_date.strftime("%B %d, %Y")
            deletion_time_str = deletion_date.strftime("%I:%M %p UTC")
            
            # Build variables dictionary
            variables = {
                "user_name": display_name or email,
                "user_email": email,
                "user_uid": uid,
                "app_name": APP_NAME,
                "deletion_date": deletion_date_str,
                "deletion_time": deletion_time_str,
            }
            
            # Load and process template
            try:
                template_content = template_loader.load_template("user_deletion_warning.html")
                content = template_loader.replace_variables(template_content, variables)
            except FileNotFoundError:
                # Fallback to simple text notification
                logger.warning("Deletion warning template not found, using fallback text")
                content = f"""<h1>Account Deletion Notice</h1>
<p>Hello, {variables['user_name']}!</p>
<p><strong>Your account has been scheduled for deletion.</strong></p>
<p>Your account will be deleted on <strong>{deletion_date_str}</strong> at <strong>{deletion_time_str}</strong>.</p>
<p>This action cannot be undone. If you believe this is a mistake, please contact support immediately.</p>
"""
            except Exception as e:
                logger.error(f"Error processing deletion warning template: {e}", exc_info=True)
                # Fallback to simple text
                content = f"""<h1>Account Deletion Notice</h1>
<p>Hello, {variables['user_name']}!</p>
<p><strong>Your account has been scheduled for deletion.</strong></p>
<p>Your account will be deleted on <strong>{deletion_date_str}</strong> at <strong>{deletion_time_str}</strong>.</p>
<p>This action cannot be undone. If you believe this is a mistake, please contact support immediately.</p>
"""
            
            # Create notification
            notification_data = {
                "title": "Account Deletion Notice",
                "subtitle": "Your account will be deleted in 24 hours",
                "content": content,
                "type": "warning",
                "target_users": [uid],  # Target specific user
            }
            
            success = self.create_notification(notification_data)
            
            if success:
                logger.info(f"Deletion warning notification created for user {uid}")
            else:
                logger.error(f"Failed to create deletion warning notification for user {uid}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error creating deletion warning notification: {e}", exc_info=True)
            return False
    
    def create_app_update_notification(self, update_data: dict) -> bool:
        """
        Create app update notification for all users.
        
        Args:
            update_data: Dictionary containing update information:
                - version: Version string (required)
                - release_notes: Release notes (markdown/HTML)
                - download_url_windows: Windows download URL (optional)
                - download_url_macos: macOS download URL (optional)
                - download_url_linux: Linux download URL (optional)
                - release_date: ISO format date string (optional)
        
        Returns:
            True if notification created successfully, False otherwise
        """
        try:
            from admin.utils.template_loader import template_loader
            from datetime import datetime
            from utils.constants import APP_NAME
            
            # Build variables dictionary
            version = update_data.get("version", "Unknown")
            release_notes = update_data.get("release_notes", "")
            release_date_str = update_data.get("release_date", "")
            
            # Format release date
            formatted_release_date = ""
            if release_date_str:
                try:
                    # Handle ISO format with Z suffix
                    date_str = release_date_str.replace("Z", "+00:00") if isinstance(release_date_str, str) and release_date_str.endswith("Z") else release_date_str
                    dt = datetime.fromisoformat(date_str)
                    formatted_release_date = dt.strftime("%B %d, %Y")
                except Exception as e:
                    logger.warning(f"Error parsing release date '{release_date_str}': {e}")
                    formatted_release_date = release_date_str
            
            # Build download section HTML
            download_section = self._build_download_section(update_data)
            
            variables = {
                "app_name": APP_NAME,
                "version": version,
                "release_notes": release_notes or "No release notes available.",
                "release_date": formatted_release_date or datetime.utcnow().strftime("%B %d, %Y"),
                "download_section": download_section,
            }
            
            # Load and process template
            try:
                template_content = template_loader.load_template("app_update_notification.html")
                content = template_loader.replace_variables(template_content, variables)
            except FileNotFoundError:
                # Fallback to simple text notification
                logger.warning("App update template not found, using fallback text")
                content = f"""<h1>New Update Available!</h1>
<p>A new version of <strong>{APP_NAME}</strong> is now available!</p>
<p><strong>Version:</strong> {version}</p>
<p><strong>Release Date:</strong> {variables['release_date']}</p>
"""
                if release_notes:
                    content += f"<h2>What's New</h2><div>{release_notes}</div>"
                if download_section:
                    content += download_section
            except Exception as e:
                logger.error(f"Error processing app update template: {e}", exc_info=True)
                # Fallback to simple text
                content = f"""<h1>New Update Available!</h1>
<p>A new version of <strong>{APP_NAME}</strong> is now available!</p>
<p><strong>Version:</strong> {version}</p>
<p><strong>Release Date:</strong> {variables['release_date']}</p>
"""
                if release_notes:
                    content += f"<h2>What's New</h2><div>{release_notes}</div>"
                if download_section:
                    content += download_section
            
            # Create notification
            notification_data = {
                "title": "New Update Available!",
                "subtitle": f"Version {version} is now available",
                "content": content,
                "type": "update",
                "target_users": None,  # Send to all users
            }
            
            success = self.create_notification(notification_data)
            
            if success:
                logger.info(f"App update notification created successfully for version {version}")
            else:
                logger.error(f"Failed to create app update notification for version {version}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error creating app update notification: {e}", exc_info=True)
            return False
    
    def _build_download_section(self, update_data: dict) -> str:
        """
        Build download section HTML with platform-specific download buttons.
        
        Args:
            update_data: Dictionary containing download URLs
        
        Returns:
            HTML string for download section, or empty string if no URLs
        """
        download_urls = {
            "Windows": update_data.get("download_url_windows", ""),
            "macOS": update_data.get("download_url_macos", ""),
            "Linux": update_data.get("download_url_linux", ""),
        }
        
        # Filter out empty URLs
        available_platforms = {platform: url for platform, url in download_urls.items() if url and url.strip()}
        
        if not available_platforms:
            return ""
        
        # Platform icons/emojis
        platform_icons = {
            "Windows": "🪟",
            "macOS": "🍎",
            "Linux": "🐧",
        }
        
        # Build download buttons HTML
        download_buttons = []
        for platform, url in available_platforms.items():
            icon = platform_icons.get(platform, "📦")
            download_buttons.append(f'''
                <a href="{url}" class="download-button" target="_blank">
                    <div class="download-button-icon">{icon}</div>
                    <div class="download-button-label">Download</div>
                    <div class="download-button-platform">{platform}</div>
                </a>
            ''')
        
        # Build complete download section
        download_section = f'''
            <div class="download-section">
                <h3>
                    <span>⬇️</span>
                    Download Update
                </h3>
                <div class="download-buttons">
                    {''.join(download_buttons)}
                </div>
            </div>
        '''
        
        return download_section


# Global admin notification service instance
admin_notification_service = AdminNotificationService()

