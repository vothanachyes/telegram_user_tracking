"""
Admin user management service.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from admin.config.admin_config import admin_config
from admin.utils.constants import FIRESTORE_SCHEDULED_DELETIONS_COLLECTION

logger = logging.getLogger(__name__)


class AdminUserService:
    """Handles user CRUD operations."""
    
    def __init__(self):
        self._auth = None
        self._db = None
    
    def _ensure_initialized(self) -> bool:
        """Ensure Firebase is initialized."""
        if not admin_config.is_initialized():
            if not admin_config.initialize():
                return False
        self._auth = admin_config.get_auth()
        self._db = admin_config.get_firestore()
        return self._auth is not None and self._db is not None
    
    def get_all_users(self) -> List[dict]:
        """List all Firebase users."""
        if not self._ensure_initialized():
            logger.error("Firebase not initialized")
            return []
        
        try:
            users = []
            # List users (Firebase Auth has pagination, but we'll get first batch)
            # Note: list_users() returns an iterator, we'll convert to list
            page = self._auth.list_users()
            for user in page.iterate_all():
                user_dict = {
                    "uid": user.uid,
                    "email": user.email,
                    "display_name": user.display_name,
                    "email_verified": user.email_verified,
                    "disabled": user.disabled,
                    "created_at": user.user_metadata.creation_timestamp,
                    "last_sign_in": user.user_metadata.last_sign_in_timestamp,
                }
                # Get license info (lazy import to avoid circular dependency)
                try:
                    from admin.services.admin_license_service import admin_license_service
                    license_data = admin_license_service.get_license(user.uid)
                    if license_data:
                        user_dict["license_tier"] = license_data.get("tier", "none")
                        user_dict["license_expires"] = license_data.get("expiration_date")
                    else:
                        user_dict["license_tier"] = "none"
                        user_dict["license_expires"] = None
                except Exception:
                    user_dict["license_tier"] = "none"
                    user_dict["license_expires"] = None
                
                # Get scheduled deletion info
                try:
                    scheduled_deletion = self.get_scheduled_deletion(user.uid)
                    if scheduled_deletion:
                        user_dict["scheduled_deletion_date"] = scheduled_deletion.get("deletion_date")
                        user_dict["scheduled_deletion"] = scheduled_deletion
                    else:
                        user_dict["scheduled_deletion_date"] = None
                        user_dict["scheduled_deletion"] = None
                except Exception:
                    user_dict["scheduled_deletion_date"] = None
                    user_dict["scheduled_deletion"] = None
                
                users.append(user_dict)
            
            logger.info(f"Retrieved {len(users)} users")
            return users
            
        except Exception as e:
            logger.error(f"Error getting all users: {e}", exc_info=True)
            return []
    
    def get_user(self, uid: str) -> Optional[dict]:
        """Get user by UID."""
        if not self._ensure_initialized():
            return None
        
        try:
            user = self._auth.get_user(uid)
            user_dict = {
                "uid": user.uid,
                "email": user.email,
                "display_name": user.display_name,
                "email_verified": user.email_verified,
                "disabled": user.disabled,
                "created_at": user.user_metadata.creation_timestamp,
                "last_sign_in": user.user_metadata.last_sign_in_timestamp,
                "phone_number": user.phone_number,
            }
            
            # Get license info (lazy import to avoid circular dependency)
            try:
                from admin.services.admin_license_service import admin_license_service
                license_data = admin_license_service.get_license(uid)
                if license_data:
                    user_dict["license"] = license_data
                
                # Get devices
                user_dict["devices"] = admin_license_service.get_user_devices(uid)
            except Exception:
                user_dict["devices"] = []
            
            return user_dict
            
        except Exception as e:
            logger.error(f"Error getting user {uid}: {e}", exc_info=True)
            return None
    
    def create_user(self, email: str, password: str, display_name: Optional[str] = None) -> Optional[str]:
        """
        Create a new user.
        Returns UID if successful, None otherwise.
        """
        if not self._ensure_initialized():
            return None
        
        try:
            user = self._auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=False
            )
            logger.info(f"User created: {user.uid} ({email})")
            return user.uid
            
        except Exception as e:
            logger.error(f"Error creating user: {e}", exc_info=True)
            return None
    
    def update_user(self, uid: str, **kwargs) -> bool:
        """
        Update user properties.
        Supported kwargs: email, display_name, disabled, email_verified, password
        """
        if not self._ensure_initialized():
            return False
        
        try:
            update_data = {}
            
            if "email" in kwargs:
                update_data["email"] = kwargs["email"]
            if "display_name" in kwargs:
                update_data["display_name"] = kwargs["display_name"]
            if "disabled" in kwargs:
                update_data["disabled"] = kwargs["disabled"]
            if "email_verified" in kwargs:
                update_data["email_verified"] = kwargs["email_verified"]
            if "password" in kwargs:
                update_data["password"] = kwargs["password"]
            
            if not update_data:
                return False
            
            self._auth.update_user(uid, **update_data)
            logger.info(f"User updated: {uid}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user {uid}: {e}", exc_info=True)
            return False
    
    def delete_user(self, uid: str) -> bool:
        """Delete a user."""
        if not self._ensure_initialized():
            return False
        
        try:
            self._auth.delete_user(uid)
            logger.info(f"User deleted: {uid}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user {uid}: {e}", exc_info=True)
            return False
    
    def get_user_license(self, uid: str) -> Optional[dict]:
        """Get user's license."""
        try:
            from admin.services.admin_license_service import admin_license_service
            return admin_license_service.get_license(uid)
        except Exception:
            return None
    
    def get_user_devices(self, uid: str) -> List[str]:
        """Get user's active devices."""
        try:
            from admin.services.admin_license_service import admin_license_service
            return admin_license_service.get_user_devices(uid)
        except Exception:
            return []
    
    def schedule_user_deletion(self, uid: str, scheduled_by: Optional[str] = None) -> Optional[datetime]:
        """
        Schedule user deletion in 24 hours.
        
        Args:
            uid: User UID
            scheduled_by: Admin UID who scheduled the deletion
        
        Returns:
            Scheduled deletion datetime if successful, None otherwise
        """
        if not self._ensure_initialized():
            return None
        
        try:
            from admin.services.admin_auth_service import admin_auth_service
            
            # Calculate deletion date (24 hours from now)
            deletion_date = datetime.utcnow() + timedelta(hours=24)
            
            # Get current admin if not provided
            if not scheduled_by:
                current_admin = admin_auth_service.get_current_admin()
                scheduled_by = current_admin.get("uid") if current_admin else None
            
            # Store scheduled deletion in Firestore
            deletion_data = {
                "uid": uid,
                "deletion_date": deletion_date,
                "scheduled_at": datetime.utcnow(),
                "scheduled_by": scheduled_by,
                "status": "scheduled",
            }
            
            doc_ref = self._db.collection(FIRESTORE_SCHEDULED_DELETIONS_COLLECTION).document(uid)
            doc_ref.set(deletion_data)
            
            logger.info(f"User deletion scheduled: {uid} for {deletion_date}")
            return deletion_date
        
        except Exception as e:
            logger.error(f"Error scheduling user deletion: {e}", exc_info=True)
            return None
    
    def get_scheduled_deletion(self, uid: str) -> Optional[dict]:
        """
        Get scheduled deletion information for a user.
        
        Args:
            uid: User UID
        
        Returns:
            Scheduled deletion data dict or None
        """
        if not self._ensure_initialized():
            return None
        
        try:
            doc_ref = self._db.collection(FIRESTORE_SCHEDULED_DELETIONS_COLLECTION).document(uid)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return data
            return None
        
        except Exception as e:
            logger.error(f"Error getting scheduled deletion: {e}", exc_info=True)
            return None
    
    def cancel_scheduled_deletion(self, uid: str) -> bool:
        """
        Cancel a scheduled user deletion.
        
        Args:
            uid: User UID
        
        Returns:
            True if successful, False otherwise
        """
        if not self._ensure_initialized():
            return False
        
        try:
            doc_ref = self._db.collection(FIRESTORE_SCHEDULED_DELETIONS_COLLECTION).document(uid)
            doc_ref.delete()
            
            logger.info(f"Scheduled deletion cancelled for user: {uid}")
            return True
        
        except Exception as e:
            logger.error(f"Error cancelling scheduled deletion: {e}", exc_info=True)
            return False
    
    def execute_scheduled_deletions(self) -> int:
        """
        Check and execute scheduled deletions that are due.
        This should be called periodically by a background service.
        
        Returns:
            Number of users deleted
        """
        if not self._ensure_initialized():
            return 0
        
        try:
            now = datetime.utcnow()
            deleted_count = 0
            
            # Get all scheduled deletions
            docs = self._db.collection(FIRESTORE_SCHEDULED_DELETIONS_COLLECTION).where("status", "==", "scheduled").stream()
            
            for doc in docs:
                data = doc.to_dict()
                deletion_date = data.get("deletion_date")
                uid = data.get("uid")
                
                if not deletion_date or not uid:
                    continue
                
                # Convert Firestore timestamp to datetime if needed
                if hasattr(deletion_date, "timestamp"):
                    deletion_date = deletion_date.replace(tzinfo=None)
                elif isinstance(deletion_date, str):
                    try:
                        deletion_date = datetime.fromisoformat(deletion_date.replace("Z", "+00:00")).replace(tzinfo=None)
                    except Exception:
                        logger.warning(f"Invalid deletion_date format for {uid}: {deletion_date}")
                        continue
                
                # Check if deletion is due
                if deletion_date <= now:
                    try:
                        # Disable user first
                        self.update_user(uid, disabled=True)
                        
                        # Delete user
                        if self.delete_user(uid):
                            # Update deletion status
                            doc.reference.update({"status": "completed", "executed_at": datetime.utcnow()})
                            deleted_count += 1
                            logger.info(f"Executed scheduled deletion for user: {uid}")
                        else:
                            logger.error(f"Failed to delete user {uid} during scheduled deletion")
                            doc.reference.update({"status": "failed", "error": "Delete operation failed"})
                    
                    except Exception as e:
                        logger.error(f"Error executing scheduled deletion for {uid}: {e}", exc_info=True)
                        try:
                            doc.reference.update({"status": "failed", "error": str(e)})
                        except Exception:
                            pass
            
            if deleted_count > 0:
                logger.info(f"Executed {deleted_count} scheduled user deletions")
            
            return deleted_count
        
        except Exception as e:
            logger.error(f"Error executing scheduled deletions: {e}", exc_info=True)
            return 0


# Global admin user service instance
admin_user_service = AdminUserService()

