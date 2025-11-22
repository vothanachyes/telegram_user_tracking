"""
Admin authentication service.
"""

import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta
from admin.config.admin_config import admin_config
from admin.utils.constants import ADMIN_SESSION_TIMEOUT_MINUTES

logger = logging.getLogger(__name__)


class AdminAuthService:
    """Handles admin authentication and session management."""
    
    def __init__(self):
        self.current_admin: Optional[dict] = None
        self.session_start: Optional[datetime] = None
        self._auth = None
    
    def initialize(self) -> bool:
        """Initialize admin authentication."""
        if not admin_config.initialize():
            return False
        self._auth = admin_config.get_auth()
        return self._auth is not None
    
    def login(self, email: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Authenticate admin user.
        
        Args:
            email: Admin email
            password: Admin password
            
        Returns:
            Tuple of (success, error_message)
        """
        if not self._auth:
            if not self.initialize():
                return False, "Failed to initialize Firebase Admin SDK"
        
        try:
            # Verify admin credentials by attempting to sign in
            # Note: In production, you should have a separate admin collection
            # or use Firebase Custom Claims to identify admins
            # For now, we'll verify the user exists and check if they're an admin
            
            # Get user by email
            user = self._auth.get_user_by_email(email)
            
            # Check if user is disabled
            if user.disabled:
                return False, "This account has been disabled"
            
            # TODO: In production, check custom claims or admin collection
            # For now, we'll allow any authenticated user as admin
            # You should implement proper admin verification here
            
            # Verify password by attempting to sign in with REST API
            # Admin SDK doesn't have password verification, so we need REST API
            try:
                import requests
                from utils.constants import FIREBASE_WEB_API_KEY
                
                if not FIREBASE_WEB_API_KEY:
                    return False, "Firebase Web API key not configured"
                
                url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
                payload = {
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                }
                
                response = requests.post(url, json=payload, timeout=10)
                
                if response.status_code != 200:
                    error_data = response.json()
                    error_message = error_data.get("error", {}).get("message", "Authentication failed")
                    
                    error_mapping = {
                        "EMAIL_NOT_FOUND": "No account found with this email address",
                        "INVALID_PASSWORD": "Invalid password",
                        "USER_DISABLED": "This account has been disabled",
                        "INVALID_EMAIL": "Invalid email address",
                    }
                    
                    error_code = error_data.get("error", {}).get("message", "")
                    user_message = error_mapping.get(error_code, error_message)
                    return False, user_message
                
                # Password verified, set admin session
                self.current_admin = {
                    "uid": user.uid,
                    "email": user.email,
                    "display_name": user.display_name or email,
                    "email_verified": user.email_verified,
                }
                self.session_start = datetime.now()
                
                logger.info(f"Admin logged in: {email}")
                return True, None
                
            except ImportError:
                return False, "requests library is required for authentication"
            except Exception as e:
                logger.error(f"Error verifying password: {e}")
                return False, f"Authentication error: {str(e)}"
                
        except Exception as e:
            logger.error(f"Admin login error: {e}", exc_info=True)
            return False, f"Login failed: {str(e)}"
    
    def logout(self) -> bool:
        """Log out current admin."""
        if self.current_admin:
            logger.info(f"Admin logged out: {self.current_admin.get('email')}")
        self.current_admin = None
        self.session_start = None
        return True
    
    def is_authenticated(self) -> bool:
        """Check if admin is authenticated and session is valid."""
        if not self.current_admin:
            return False
        
        # Check session timeout
        if self.session_start:
            elapsed = datetime.now() - self.session_start
            if elapsed > timedelta(minutes=ADMIN_SESSION_TIMEOUT_MINUTES):
                logger.info("Admin session expired")
                self.logout()
                return False
        
        return True
    
    def get_current_admin(self) -> Optional[dict]:
        """Get current admin information."""
        if not self.is_authenticated():
            return None
        return self.current_admin.copy() if self.current_admin else None
    
    def refresh_session(self):
        """Refresh session timeout."""
        if self.is_authenticated():
            self.session_start = datetime.now()


# Global admin auth service instance
admin_auth_service = AdminAuthService()

