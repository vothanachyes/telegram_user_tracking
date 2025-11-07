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

logger = logging.getLogger(__name__)


class AuthService:
    """Handles Firebase authentication with single-device enforcement."""
    
    def __init__(self):
        self.current_user: Optional[dict] = None
        self._device_id: Optional[str] = None
    
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
            
            if not firebase_config.is_initialized():
                return False, "Firebase not initialized"
            
            # Verify the ID token
            decoded_token = firebase_config.verify_token(id_token)
            if not decoded_token:
                return False, "Invalid authentication token"
            
            uid = decoded_token['uid']
            
            # Get user info
            user_info = firebase_config.get_user(uid)
            if not user_info:
                return False, "User not found"
            
            # Check if user is disabled
            if user_info.get('disabled', False):
                return False, "User account is disabled"
            
            # Implement single-device enforcement
            # Get current device ID from custom claims
            current_device = decoded_token.get('device_id')
            
            if current_device and current_device != self.device_id:
                # User is logged in on another device
                return False, "This account is already logged in on another device. Please logout from the other device first."
            
            # Set device ID in custom claims
            firebase_config.set_custom_claims(uid, {
                'device_id': self.device_id,
                'last_login': datetime.now().isoformat()
            })
            
            # Store current user
            self.current_user = user_info
            
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
                
                # Try to clear device ID from custom claims
                try:
                    if firebase_config.is_initialized() and uid:
                        firebase_config.set_custom_claims(uid, {
                            'device_id': None,
                            'last_logout': datetime.now().isoformat()
                        })
                        logger.info(f"Cleared custom claims for user: {email}")
                except Exception as e:
                    logger.warning(f"Failed to clear custom claims: {e}")
                    # Continue with logout even if clearing claims fails
                
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


# Global auth service instance
auth_service = AuthService()

