"""
Firebase authentication service with single-device enforcement.
"""

import logging
import hashlib
import platform
from typing import Optional, Tuple
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("requests library not installed")

from config.firebase_config import firebase_config
from utils.constants import FIREBASE_WEB_API_KEY
from database.db_manager import DatabaseManager
from services.license_service import LicenseService
from utils.database_path import get_user_database_path

logger = logging.getLogger(__name__)


class AuthService:
    """Handles Firebase authentication with single-device enforcement."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.current_user: Optional[dict] = None
        self._device_id: Optional[str] = None
        self.db_manager = db_manager
        # Pass self to LicenseService to avoid circular import
        self.license_service = LicenseService(db_manager, auth_service_instance=self) if db_manager else None
    
    @property
    def device_id(self) -> str:
        """Generate unique device ID based on machine info."""
        if self._device_id is None:
            # Generate device ID from machine info
            machine_info = f"{platform.node()}-{platform.machine()}-{platform.system()}"
            self._device_id = hashlib.sha256(machine_info.encode()).hexdigest()[:16]
        return self._device_id
    
    def initialize(self) -> bool:
        """Initialize Firebase authentication."""
        return firebase_config.initialize()
    
    def authenticate_with_email_password(self, email: str, password: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Authenticate user with email and password using Firebase REST API.
        Returns (success, error_message, id_token)
        """
        if not REQUESTS_AVAILABLE:
            return False, "requests library is required for authentication", None
        
        if not FIREBASE_WEB_API_KEY:
            return False, "Firebase Web API key not configured. Please set FIREBASE_WEB_API_KEY in .env file", None
        
        try:
            # Firebase REST API endpoint for email/password authentication
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
            
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                id_token = data.get("idToken")
                if id_token:
                    return True, None, id_token
                else:
                    return False, "Failed to get authentication token", None
            else:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "Authentication failed")
                
                # Map Firebase error messages to user-friendly messages
                error_mapping = {
                    "EMAIL_NOT_FOUND": "No account found with this email address",
                    "INVALID_PASSWORD": "Invalid password",
                    "USER_DISABLED": "This account has been disabled",
                    "INVALID_EMAIL": "Invalid email address",
                    "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many failed login attempts. Please try again later"
                }
                
                error_code = error_data.get("error", {}).get("message", "")
                user_message = error_mapping.get(error_code, error_message)
                
                return False, user_message, None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during authentication: {e}")
            return False, "Network error. Please check your internet connection", None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False, f"Authentication failed: {str(e)}", None
    
    def login(self, email: str, password: str, id_token: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Login user with email and password.
        If id_token is not provided, it will authenticate using Firebase REST API first.
        
        Returns (success, error_message)
        """
        try:
            # If no ID token provided, authenticate first using REST API
            if not id_token:
                success, error, token = self.authenticate_with_email_password(email, password)
                if not success:
                    return False, error
                id_token = token
            
            # Initialize Firebase with ID token (no Admin SDK needed)
            if not firebase_config.initialize(id_token):
                return False, "Failed to initialize Firebase"
            
            # Verify and decode the ID token
            decoded_token = firebase_config.verify_token(id_token)
            if not decoded_token:
                return False, "Invalid authentication token"
            
            # Extract UID from token (Firebase uses 'user_id' in REST API tokens)
            uid = decoded_token.get('user_id') or decoded_token.get('uid')
            if not uid:
                return False, "Could not extract user ID from token"
            
            # Get user info from token (no Admin SDK needed)
            user_info = firebase_config.get_user(uid, id_token)
            if not user_info:
                return False, "User not found"
            
            # Note: Can't check if user is disabled without Admin SDK
            # This would need to be handled server-side or via custom claims
            
            # Check device limit if license service is available
            # Device limits are enforced by license service based on license tier and active devices in Firestore
            if self.license_service:
                can_add, error_msg, active_devices = self.license_service.can_add_device(
                    self.device_id, user_email=email, uid=uid
                )
                if not can_add:
                    # Device limit reached
                    logger.warning(f"Device limit reached: {error_msg}")
                    return False, error_msg
                
                # Note: Adding device to license requires Admin SDK (admin-only operation)
                # This should be done server-side or via admin panel
                # For now, we'll just check the limit and allow login
                logger.info(f"Device {self.device_id} allowed for user {email} (device management is admin-only)")
            
            # Note: Setting custom claims requires Admin SDK (admin-only operation)
            # Device enforcement should be handled server-side or via admin panel
            
            # Store current user (after successful authentication)
            self.current_user = user_info
            
            # Check if device is revoked - if so, unrevoke it on successful login
            from services.device_manager_service import device_manager_service
            is_revoked, error_msg = device_manager_service.check_device_status(uid)
            if is_revoked:
                logger.info(f"Device {self.device_id} was revoked for user {email}, but login successful - unrevoking device")
                # Device will be unrevoked when we register/update it below
            
            # Track device login and register device (this will unrevoke if it was revoked)
            try:
                from services.user_activities_service import user_activities_service
                # Register/update device with Firebase (this will clear revoked_at and set is_active=True)
                device_manager_service.register_device(uid)
                # Increment devices count
                user_activities_service.increment_devices_count(uid)
                # Update app version
                user_activities_service.update_app_version(uid)
                if is_revoked:
                    logger.info(f"Device {self.device_id} has been unrevoked for user {email}")
            except Exception as e:
                logger.error(f"Error tracking device login: {e}", exc_info=True)
                # Don't fail login if tracking fails
            
            logger.info(f"User logged in: {email}")
            return True, None
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False, str(e)
    
    def logout(self) -> bool:
        """Logout current user."""
        try:
            logger.info("Logout method called")
            
            if self.current_user:
                uid = self.current_user.get('uid')
                email = self.current_user.get('email')
                
                logger.info(f"Logging out user: {email}")
                
                # Note: Clearing custom claims requires Admin SDK (admin-only operation)
                # Device management should be handled server-side or via admin panel
                
                logger.info(f"User logged out successfully: {email}")
                self.current_user = None
                return True
            else:
                logger.warning("No user logged in to logout")
                # Still return True because there's no user session to clear
                return True
                
        except Exception as e:
            logger.error(f"Logout error: {e}", exc_info=True)
            # Even if there's an error, clear the current user
            self.current_user = None
            return True
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in."""
        return self.current_user is not None
    
    def get_current_user(self) -> Optional[dict]:
        """Get current logged in user."""
        return self.current_user
    
    def get_user_email(self) -> Optional[str]:
        """Get current user email."""
        if self.current_user:
            return self.current_user.get('email')
        return None
    
    def get_user_display_name(self) -> Optional[str]:
        """Get current user display name."""
        if self.current_user:
            return self.current_user.get('display_name')
        return None
    
    def get_user_database_path(self) -> Optional[str]:
        """
        Get user-specific database path for current logged-in user.
        
        Returns:
            Path to user-specific database file, or None if not logged in.
        """
        if not self.current_user:
            return None
        
        uid = self.current_user.get('uid')
        if not uid:
            return None
        
        return get_user_database_path(uid)


# Global auth service instance (will be initialized with db_manager in app)
auth_service = AuthService()

