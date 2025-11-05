"""
Firebase authentication service with single-device enforcement.
"""

import logging
import hashlib
import platform
from typing import Optional, Tuple
from datetime import datetime

from config.firebase_config import firebase_config

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
    
    def login(self, email: str, password: str, id_token: str) -> Tuple[bool, Optional[str]]:
        """
        Login user with email and password.
        This method expects an ID token from the client-side Firebase auth.
        
        Returns (success, error_message)
        """
        try:
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
            if self.current_user:
                uid = self.current_user['uid']
                
                # Clear device ID from custom claims
                firebase_config.set_custom_claims(uid, {
                    'device_id': None,
                    'last_logout': datetime.now().isoformat()
                })
                
                logger.info(f"User logged out: {self.current_user.get('email')}")
                self.current_user = None
                return True
            return False
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
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

