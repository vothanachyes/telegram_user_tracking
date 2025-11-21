"""
Firebase configuration and initialization.
"""

import os
import sys
from typing import Optional
import logging
from pathlib import Path

try:
    import firebase_admin
    from firebase_admin import credentials, auth
    try:
        from firebase_admin import firestore
        FIRESTORE_AVAILABLE = True
    except ImportError:
        FIRESTORE_AVAILABLE = False
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    FIRESTORE_AVAILABLE = False
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
        self.db: Optional[firestore.Client] = None
    
    def _find_firebase_credentials(self, credentials_path: Optional[str] = None) -> Optional[str]:
        """
        Find Firebase credentials file path.
        Handles both development (source) and production (bundled executable) scenarios.
        
        Args:
            credentials_path: Explicit path provided (takes priority)
        
        Returns:
            Path to credentials file or None if not found
        """
        # Priority 1: Explicit path provided
        if credentials_path and os.path.exists(credentials_path):
            return credentials_path
        
        # Priority 2: Environment variable
        if FIREBASE_CREDENTIALS_PATH and os.path.exists(FIREBASE_CREDENTIALS_PATH):
            return FIREBASE_CREDENTIALS_PATH
        
        # Priority 3: Check if running from PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Running from executable - files are in sys._MEIPASS
            base_path = Path(sys._MEIPASS)
            config_dir = base_path / 'config'
            
            # Look for any .json file in config/ (Firebase credentials)
            json_files = list(config_dir.glob('*.json'))
            if json_files:
                # Prefer files with 'firebase' in name, otherwise use first .json
                firebase_files = [f for f in json_files if 'firebase' in f.name.lower() or 'fbsvc' in f.name.lower()]
                if firebase_files:
                    cred_path = firebase_files[0]
                    logger.debug(f"Found Firebase credentials in bundle: {cred_path}")
                    return str(cred_path)
                else:
                    # Use first JSON file found
                    cred_path = json_files[0]
                    logger.debug(f"Using JSON file from bundle: {cred_path}")
                    return str(cred_path)
        
        # Priority 4: Check in source code directory (development)
        # Get the directory where this file is located
        current_file = Path(__file__).resolve()
        config_dir = current_file.parent
        
        # Look for Firebase credentials JSON files
        json_files = list(config_dir.glob('*.json'))
        if json_files:
            # Prefer files with 'firebase' in name, otherwise use first .json
            firebase_files = [f for f in json_files if 'firebase' in f.name.lower() or 'fbsvc' in f.name.lower()]
            if firebase_files:
                cred_path = firebase_files[0]
                logger.debug(f"Found Firebase credentials in source: {cred_path}")
                return str(cred_path)
            else:
                # Use first JSON file found
                cred_path = json_files[0]
                logger.debug(f"Using JSON file from source: {cred_path}")
                return str(cred_path)
        
        return None
    
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
            # Find credentials file (handles both dev and bundled executable)
            cred_path = self._find_firebase_credentials(credentials_path)

            if not cred_path or not os.path.exists(cred_path):
                logger.warning(f"Firebase credentials file not found")
                logger.debug(f"  Searched paths:")
                logger.debug(f"    - Explicit: {credentials_path}")
                logger.debug(f"    - Env var: {FIREBASE_CREDENTIALS_PATH}")
                if getattr(sys, 'frozen', False):
                    logger.debug(f"    - Bundle: {sys._MEIPASS}/config/*.json")
                logger.debug(f"    - Source: {Path(__file__).parent}/*.json")
                logger.info("Firebase features will be disabled")
                return False
            
            logger.info(f"Using Firebase credentials: {cred_path}")
            
            # Initialize Firebase
            cred = credentials.Certificate(cred_path)
            self.app = firebase_admin.initialize_app(cred)
            
            # Initialize Firestore if available
            if FIRESTORE_AVAILABLE:
                self.db = firestore.client()
                logger.info("Firestore client initialized successfully")
            else:
                logger.warning("Firestore is not available - license features will not work")
                self.db = None
            
            self._initialized = True
            logger.info("Firebase initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Firebase: {e}", exc_info=True)
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
    
    # ==================== Firestore License Methods ====================
    
    def get_user_license(self, uid: str) -> Optional[dict]:
        """
        Get user license from Firestore.
        Returns license document if found, None otherwise.
        """
        if not self._initialized:
            logger.error("Firebase not initialized")
            return None
        
        if not self.db:
            logger.error("Firestore database not available")
            return None
        
        try:
            doc_ref = self.db.collection('user_licenses').document(uid)
            logger.debug(f"Checking for license document for user {uid}")
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                data['uid'] = uid
                logger.debug(f"License found for user {uid}: {data}")
                return data
            logger.debug(f"No license document found for user {uid}")
            return None
        except Exception as e:
            logger.error(f"Error getting user license: {e}", exc_info=True)
            return None
    
    def set_user_license(self, uid: str, license_data: dict) -> bool:
        """
        Set or update user license in Firestore.
        Returns True if successful.
        """
        if not self._initialized:
            logger.error("Firebase not initialized")
            return False
        
        if not self.db:
            logger.error("Firestore database not available")
            return False
        
        try:
            doc_ref = self.db.collection('user_licenses').document(uid)
            # Remove uid from data if present (it's the document ID)
            data = {k: v for k, v in license_data.items() if k != 'uid'}
            logger.info(f"Attempting to create/update license document for user {uid} with data: {data}")
            doc_ref.set(data, merge=True)
            logger.info(f"License successfully created/updated for user: {uid}")
            return True
        except Exception as e:
            logger.error(f"Error setting user license: {e}", exc_info=True)
            return False
    
    def add_device_to_license(self, uid: str, device_id: str) -> bool:
        """
        Add a device ID to user's active devices list.
        Returns True if successful.
        """
        if not self._initialized or not self.db:
            logger.error("Firebase not initialized")
            return False
        
        try:
            doc_ref = self.db.collection('user_licenses').document(uid)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                active_devices = data.get('active_device_ids', [])
                if device_id not in active_devices:
                    active_devices.append(device_id)
                    doc_ref.update({'active_device_ids': active_devices})
                    logger.info(f"Device {device_id} added to user {uid}")
                return True
            else:
                # Create new license document with this device
                doc_ref.set({
                    'active_device_ids': [device_id],
                    'license_tier': 'silver',  # Default tier
                    'max_devices': 1,
                    'max_groups': 3
                })
                logger.info(f"Created new license for user {uid} with device {device_id}")
                return True
        except Exception as e:
            logger.error(f"Error adding device to license: {e}")
            return False
    
    def remove_device_from_license(self, uid: str, device_id: str) -> bool:
        """
        Remove a device ID from user's active devices list.
        Returns True if successful.
        """
        if not self._initialized or not self.db:
            logger.error("Firebase not initialized")
            return False
        
        try:
            doc_ref = self.db.collection('user_licenses').document(uid)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                active_devices = data.get('active_device_ids', [])
                if device_id in active_devices:
                    active_devices.remove(device_id)
                    doc_ref.update({'active_device_ids': active_devices})
                    logger.info(f"Device {device_id} removed from user {uid}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing device from license: {e}")
            return False
    
    def get_active_devices(self, uid: str) -> list:
        """
        Get list of active device IDs for a user.
        Returns list of device IDs.
        """
        if not self._initialized or not self.db:
            logger.error("Firebase not initialized")
            return []
        
        try:
            doc_ref = self.db.collection('user_licenses').document(uid)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return data.get('active_device_ids', [])
            return []
        except Exception as e:
            logger.error(f"Error getting active devices: {e}")
            return []
    
    def get_app_update_info(self) -> Optional[dict]:
        """
        Get latest app update information from Firestore.
        Returns update document if found, None otherwise.
        """
        if not self._initialized:
            logger.error("Firebase not initialized")
            return None
        
        if not self.db:
            logger.error("Firestore database not available")
            return None
        
        try:
            from utils.constants import FIREBASE_APP_UPDATES_COLLECTION, FIREBASE_APP_UPDATES_DOCUMENT
            
            doc_ref = self.db.collection(FIREBASE_APP_UPDATES_COLLECTION).document(FIREBASE_APP_UPDATES_DOCUMENT)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                logger.debug(f"App update info retrieved: version={data.get('version')}")
                return data
            logger.debug("No app update document found")
            return None
        except Exception as e:
            logger.error(f"Error getting app update info: {e}", exc_info=True)
            return None
    
    def set_app_update_info(self, update_data: dict) -> bool:
        """
        Set or update app update information in Firestore.
        
        Args:
            update_data: Dictionary containing update information:
                - version: Version string (required)
                - download_url_windows: Windows download URL (optional)
                - download_url_macos: macOS download URL (optional)
                - download_url_linux: Linux download URL (optional)
                - checksum_windows: Windows SHA256 checksum (optional)
                - checksum_macos: macOS SHA256 checksum (optional)
                - checksum_linux: Linux SHA256 checksum (optional)
                - file_size_windows: Windows file size in bytes (optional)
                - file_size_macos: macOS file size in bytes (optional)
                - file_size_linux: Linux file size in bytes (optional)
                - release_date: ISO format date string (optional)
                - is_available: Boolean (optional, default True)
                - release_notes: Release notes string (optional)
                - min_version_required: Minimum version required (optional)
        
        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            logger.error("Firebase not initialized")
            return False
        
        if not self.db:
            logger.error("Firestore database not available")
            return False
        
        try:
            from utils.constants import FIREBASE_APP_UPDATES_COLLECTION, FIREBASE_APP_UPDATES_DOCUMENT
            
            # Validate required fields
            if 'version' not in update_data:
                logger.error("Version is required in update_data")
                return False
            
            # Set defaults
            if 'is_available' not in update_data:
                update_data['is_available'] = True
            
            if 'release_date' not in update_data:
                from datetime import datetime
                update_data['release_date'] = datetime.utcnow().isoformat() + "Z"
            
            # Update Firestore document
            doc_ref = self.db.collection(FIREBASE_APP_UPDATES_COLLECTION).document(FIREBASE_APP_UPDATES_DOCUMENT)
            doc_ref.set(update_data, merge=True)
            
            logger.info(f"App update info set: version={update_data.get('version')}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting app update info: {e}", exc_info=True)
            return False


# Global Firebase config instance
firebase_config = FirebaseConfig()

