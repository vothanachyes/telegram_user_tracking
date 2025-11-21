"""
Firebase configuration and initialization using REST API (no Admin SDK).
This eliminates the need for Admin credentials in the desktop app.
"""

import os
import sys
from typing import Optional
import logging
from pathlib import Path
import base64
import json

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


class FirebaseConfig:
    """
    Firebase configuration manager using REST API.
    No Admin SDK required - uses Firebase REST API with ID token authentication.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseConfig, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.is_available = JWT_AVAILABLE and REQUESTS_AVAILABLE
        self.project_id = FIREBASE_PROJECT_ID
        self.web_api_key = FIREBASE_WEB_API_KEY
        self._current_id_token: Optional[str] = None
    
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
    
    def get_user_license(self, uid: str, id_token: Optional[str] = None) -> Optional[dict]:
        """
        Get user license from Firestore using REST API.
        
        Args:
            uid: User ID
            id_token: Firebase ID token for authentication (optional, uses current token)
        
        Returns:
            License document if found, None otherwise
        """
        if not self._initialized:
            logger.error("Firebase not initialized")
            return None
        
        if not self.project_id:
            logger.error("FIREBASE_PROJECT_ID not configured")
            return None
        
        token = id_token or self._current_id_token
        if not token:
            logger.error("No ID token available for Firestore access")
            return None
        
        try:
            # Firestore REST API endpoint
            url = f"{FIRESTORE_REST_URL}/projects/{self.project_id}/databases/(default)/documents/user_licenses/{uid}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Convert Firestore document format to dict
                license_data = self._convert_firestore_document(data)
                if license_data:
                    license_data['uid'] = uid
                    logger.debug(f"License found for user {uid}: {license_data}")
                    return license_data
            elif response.status_code == 404:
                logger.debug(f"No license document found for user {uid}")
                return None
            else:
                logger.error(f"Error getting license: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error getting license: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting user license: {e}", exc_info=True)
            return None
    
    def _convert_firestore_document(self, firestore_doc: dict) -> Optional[dict]:
        """
        Convert Firestore REST API document format to Python dict.
        
        Firestore REST API returns documents in a nested format:
        {
            "fields": {
                "field_name": {
                    "stringValue": "value"  # or integerValue, booleanValue, etc.
                }
            }
        }
        """
        if 'fields' not in firestore_doc:
            return None
        
        result = {}
        for field_name, field_value in firestore_doc['fields'].items():
            # Handle different Firestore value types
            if 'stringValue' in field_value:
                result[field_name] = field_value['stringValue']
            elif 'integerValue' in field_value:
                result[field_name] = int(field_value['integerValue'])
            elif 'doubleValue' in field_value:
                result[field_name] = float(field_value['doubleValue'])
            elif 'booleanValue' in field_value:
                result[field_name] = field_value['booleanValue']
            elif 'timestampValue' in field_value:
                # Parse ISO timestamp
                result[field_name] = field_value['timestampValue']
            elif 'arrayValue' in field_value:
                # Handle arrays
                values = field_value['arrayValue'].get('values', [])
                result[field_name] = [
                    self._convert_firestore_value(v) for v in values
                ]
            elif 'mapValue' in field_value:
                # Handle nested maps
                result[field_name] = self._convert_firestore_document(field_value['mapValue'])
            else:
                # Unknown type, try to extract value
                logger.warning(f"Unknown Firestore field type for {field_name}: {field_value}")
                result[field_name] = str(field_value)
        
        return result
    
    def _convert_firestore_value(self, value: dict) -> any:
        """Convert a single Firestore value to Python type."""
        if 'stringValue' in value:
            return value['stringValue']
        elif 'integerValue' in value:
            return int(value['integerValue'])
        elif 'doubleValue' in value:
            return float(value['doubleValue'])
        elif 'booleanValue' in value:
            return value['booleanValue']
        else:
            return str(value)
    
    def get_app_update_info(self, id_token: Optional[str] = None) -> Optional[dict]:
        """
        Get latest app update information from Firestore using REST API.
        
        Args:
            id_token: Firebase ID token (optional, uses current token)
        
        Returns:
            Update document if found, None otherwise
        """
        if not self._initialized or not self.project_id:
            logger.error("Firebase not initialized")
            return None
        
        token = id_token or self._current_id_token
        if not token:
            logger.error("No ID token available")
            return None
        
        try:
            from utils.constants import FIREBASE_APP_UPDATES_COLLECTION, FIREBASE_APP_UPDATES_DOCUMENT
            
            url = f"{FIRESTORE_REST_URL}/projects/{self.project_id}/databases/(default)/documents/{FIREBASE_APP_UPDATES_COLLECTION}/{FIREBASE_APP_UPDATES_DOCUMENT}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                update_data = self._convert_firestore_document(data)
                if update_data:
                    logger.debug(f"App update info retrieved: version={update_data.get('version')}")
                    return update_data
            elif response.status_code == 404:
                logger.debug("No app update document found")
                return None
            else:
                logger.error(f"Error getting app update info: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting app update info: {e}", exc_info=True)
            return None
    
    # ==================== Admin-Only Methods (Not Available in Desktop App) ====================
    # These methods require Admin SDK and should only be used in deployment scripts
    
    def set_user_license(self, uid: str, license_data: dict) -> bool:
        """
        Set or update user license in Firestore.
        
        NOTE: This method requires Admin SDK and should NOT be used in the desktop app.
        License writes should only be done by admin via deployment scripts or admin panel.
        
        Returns:
            False (always fails in desktop app - use admin tools instead)
        """
        logger.warning("set_user_license() is not available in desktop app - use admin tools")
        return False
    
    def add_device_to_license(self, uid: str, device_id: str) -> bool:
        """
        Add device to license.
        
        NOTE: This method requires Admin SDK and should NOT be used in the desktop app.
        
        Returns:
            False (always fails in desktop app)
        """
        logger.warning("add_device_to_license() is not available in desktop app")
        return False
    
    def remove_device_from_license(self, uid: str, device_id: str) -> bool:
        """
        Remove device from license.
        
        NOTE: This method requires Admin SDK and should NOT be used in the desktop app.
        
        Returns:
            False (always fails in desktop app)
        """
        logger.warning("remove_device_from_license() is not available in desktop app")
        return False
    
    def get_active_devices(self, uid: str) -> list:
        """
        Get active devices from license.
        
        Returns:
            List of device IDs (from license document)
        """
        license_data = self.get_user_license(uid)
        if license_data:
            return license_data.get('active_device_ids', [])
        return []
    
    def create_user(self, email: str, password: str, display_name: Optional[str] = None) -> Optional[str]:
        """
        Create a new user.
        
        NOTE: This method requires Admin SDK and should NOT be used in the desktop app.
        
        Returns:
            None (always fails in desktop app)
        """
        logger.warning("create_user() is not available in desktop app - use admin tools")
        return None
    
    def delete_user(self, uid: str) -> bool:
        """
        Delete a user.
        
        NOTE: This method requires Admin SDK and should NOT be used in the desktop app.
        
        Returns:
            False (always fails in desktop app)
        """
        logger.warning("delete_user() is not available in desktop app - use admin tools")
        return False
    
    def set_custom_claims(self, uid: str, claims: dict) -> bool:
        """
        Set custom user claims.
        
        NOTE: This method requires Admin SDK and should NOT be used in the desktop app.
        
        Returns:
            False (always fails in desktop app)
        """
        logger.warning("set_custom_claims() is not available in desktop app - use admin tools")
        return False
    
    def set_app_update_info(self, update_data: dict) -> bool:
        """
        Set app update information.
        
        NOTE: This method requires Admin SDK and should NOT be used in the desktop app.
        Use deployment scripts instead.
        
        Returns:
            False (always fails in desktop app)
        """
        logger.warning("set_app_update_info() is not available in desktop app - use deployment scripts")
        return False


# Global Firebase config instance
firebase_config = FirebaseConfig()
