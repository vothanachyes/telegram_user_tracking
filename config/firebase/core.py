"""
Core Firebase configuration and initialization.
"""

import logging
from typing import Optional

try:
    import jwt
    import requests
    JWT_AVAILABLE = True
    REQUESTS_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    REQUESTS_AVAILABLE = False
    logging.warning("PyJWT or requests not installed - Firebase features will be limited")

from utils.constants import FIREBASE_PROJECT_ID, FIREBASE_WEB_API_KEY

logger = logging.getLogger(__name__)

# Firebase REST API endpoints
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1"
FIRESTORE_REST_URL = "https://firestore.googleapis.com/v1"


class FirebaseCore:
    """Core Firebase initialization and token management."""
    
    def __init__(self):
        """Initialize core Firebase configuration."""
        self.is_available = JWT_AVAILABLE and REQUESTS_AVAILABLE
        self.project_id = FIREBASE_PROJECT_ID
        self.web_api_key = FIREBASE_WEB_API_KEY
        self._current_id_token: Optional[str] = None
        self._initialized = False
    
    def initialize(self, id_token: Optional[str] = None) -> bool:
        """
        Initialize Firebase (no credentials needed).
        Just stores the ID token for Firestore REST API calls.
        
        Args:
            id_token: Firebase ID token from authentication (optional, can be set later)
        
        Returns:
            True if successful
        """
        if self._initialized:
            return True
        
        if not self.is_available:
            logger.warning("Firebase REST API not available (missing PyJWT or requests)")
            return False
        
        if not self.project_id:
            logger.warning("FIREBASE_PROJECT_ID not configured")
            return False
        
        if id_token:
            self._current_id_token = id_token
        
        self._initialized = True
        logger.info("Firebase REST API initialized successfully")
        return True
    
    def set_id_token(self, id_token: str) -> None:
        """Set the current ID token for Firestore API calls."""
        self._current_id_token = id_token
        if not self._initialized:
            self.initialize(id_token)
    
    def is_initialized(self) -> bool:
        """Check if Firebase is initialized."""
        return self._initialized
    
    def verify_token(self, id_token: str) -> Optional[dict]:
        """
        Decode Firebase ID token (client-side decoding, no verification).
        For production, you should verify the token signature, but for desktop apps,
        we trust the token from Firebase REST API.
        
        Returns:
            Decoded token dict if valid, None otherwise
        """
        if not self.is_available:
            logger.error("JWT library not available")
            return None
        
        try:
            # Decode without verification (we trust Firebase REST API)
            # In production, you should verify the signature using Firebase public keys
            decoded_token = jwt.decode(
                id_token,
                options={"verify_signature": False}  # Skip signature verification for now
            )
            
            # Store token for Firestore calls
            self._current_id_token = id_token
            
            return decoded_token
        except jwt.DecodeError as e:
            logger.error(f"Error decoding token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    def get_id_token(self, id_token: Optional[str] = None) -> Optional[str]:
        """
        Get current ID token.
        
        Args:
            id_token: Optional token to use (otherwise uses current token)
        
        Returns:
            ID token string or None
        """
        return id_token or self._current_id_token
    
    def get_user(self, uid: Optional[str] = None, id_token: Optional[str] = None) -> Optional[dict]:
        """
        Get user info from ID token (no Admin SDK needed).
        User info is embedded in the ID token itself.
        
        Args:
            uid: User ID (optional, will extract from token if not provided)
            id_token: ID token to decode (optional, uses current token if not provided)
        
        Returns:
            User info dict if found, None otherwise
        """
        token = id_token or self._current_id_token
        if not token:
            logger.error("No ID token available")
            return None
        
        try:
            decoded_token = self.verify_token(token)
            if not decoded_token:
                return None
            
            # Extract user info from token
            user_info = {
                'uid': decoded_token.get('user_id') or decoded_token.get('uid') or uid,
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False),
                'disabled': False,  # Can't check this without Admin SDK, assume enabled
                'display_name': decoded_token.get('name'),
                'photo_url': decoded_token.get('picture')
            }
            
            return user_info
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None

