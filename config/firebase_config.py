"""
Firebase configuration and initialization.
"""

import os
from typing import Optional
import logging

try:
    import firebase_admin
    from firebase_admin import credentials, auth
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("Firebase Admin SDK not installed")

from utils.constants import FIREBASE_CREDENTIALS_PATH, FIREBASE_PROJECT_ID

logger = logging.getLogger(__name__)


class FirebaseConfig:
    """Firebase configuration manager."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseConfig, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.app: Optional[firebase_admin.App] = None
        self.is_available = FIREBASE_AVAILABLE
    
    def initialize(self, credentials_path: Optional[str] = None) -> bool:
        """
        Initialize Firebase Admin SDK.
        Returns True if successful.
        """
        if self._initialized:
            return True
        
        if not self.is_available:
            logger.error("Firebase Admin SDK is not available")
            return False
        
        try:
            # Get credentials path
            cred_path = credentials_path or FIREBASE_CREDENTIALS_PATH

            print(f"cred_path: {cred_path}")
            if not cred_path or not os.path.exists(cred_path):
                logger.error(f"Firebase credentials file not found: {cred_path}")
                return False
            
            # Initialize Firebase
            cred = credentials.Certificate(cred_path)
            self.app = firebase_admin.initialize_app(cred)
            
            self._initialized = True
            logger.info("Firebase initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Firebase: {e}")
            return False
    
    def is_initialized(self) -> bool:
        """Check if Firebase is initialized."""
        return self._initialized
    
    def verify_token(self, id_token: str) -> Optional[dict]:
        """
        Verify Firebase ID token.
        Returns decoded token if valid, None otherwise.
        """
        if not self._initialized:
            logger.error("Firebase not initialized")
            return None
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    def get_user(self, uid: str) -> Optional[dict]:
        """
        Get user by UID.
        Returns user record if found, None otherwise.
        """
        if not self._initialized:
            logger.error("Firebase not initialized")
            return None
        
        try:
            user = auth.get_user(uid)
            return {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'photo_url': user.photo_url,
                'email_verified': user.email_verified,
                'disabled': user.disabled
            }
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def create_user(self, email: str, password: str, display_name: Optional[str] = None) -> Optional[str]:
        """
        Create a new user.
        Returns UID if successful, None otherwise.
        """
        if not self._initialized:
            logger.error("Firebase not initialized")
            return None
        
        try:
            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_name
            )
            logger.info(f"User created: {user.uid}")
            return user.uid
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def delete_user(self, uid: str) -> bool:
        """
        Delete a user.
        Returns True if successful.
        """
        if not self._initialized:
            logger.error("Firebase not initialized")
            return False
        
        try:
            auth.delete_user(uid)
            logger.info(f"User deleted: {uid}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False
    
    def set_custom_claims(self, uid: str, claims: dict) -> bool:
        """
        Set custom user claims (for device enforcement).
        Returns True if successful.
        """
        if not self._initialized:
            logger.error("Firebase not initialized")
            return False
        
        try:
            auth.set_custom_user_claims(uid, claims)
            return True
        except Exception as e:
            logger.error(f"Error setting custom claims: {e}")
            return False


# Global Firebase config instance
firebase_config = FirebaseConfig()

