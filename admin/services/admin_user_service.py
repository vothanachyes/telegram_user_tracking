"""
Admin user management service.
"""

import logging
from typing import List, Optional, Dict
from admin.config.admin_config import admin_config

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


# Global admin user service instance
admin_user_service = AdminUserService()

