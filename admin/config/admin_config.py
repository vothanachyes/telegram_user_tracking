"""
Admin configuration and Firebase initialization.
"""

import os
import sys
from pathlib import Path
from typing import Optional
import logging

try:
    import firebase_admin
    from firebase_admin import credentials, auth, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    firestore = None  # For type hints when not available
    logging.warning("Firebase Admin SDK not installed")

logger = logging.getLogger(__name__)


class AdminConfig:
    """Admin configuration manager."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AdminConfig, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.app: Optional[firebase_admin.App] = None
        self.db: Optional[firestore.Client] = None
        self.is_available = FIREBASE_AVAILABLE
        self._initialized = True
    
    def _find_firebase_credentials(self, credentials_path: Optional[str] = None) -> Optional[str]:
        """Find Firebase credentials file."""
        # Check explicit path first
        if credentials_path and os.path.exists(credentials_path):
            return credentials_path
        
        # Check environment variable
        env_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if env_path and os.path.exists(env_path):
            return env_path
        
        # Check config directory
        config_dir = Path(__file__).parent.parent.parent / "config"
        if config_dir.exists():
            json_files = list(config_dir.glob("*.json"))
            if json_files:
                # Prefer files with 'firebase' or 'admin' in name
                for json_file in json_files:
                    if any(keyword in json_file.name.lower() for keyword in ['firebase', 'admin', 'service']):
                        return str(json_file)
                # Otherwise use first JSON file
                return str(json_files[0])
        
        return None
    
    def initialize(self, credentials_path: Optional[str] = None) -> bool:
        """
        Initialize Firebase Admin SDK.
        Returns True if successful.
        """
        if not self.is_available:
            logger.error("Firebase Admin SDK is not available")
            return False
        
        try:
            # Check if already initialized
            if firebase_admin._apps:
                self.app = firebase_admin.get_app()
                self.db = firestore.client()
                logger.info("Using existing Firebase Admin SDK instance")
                return True
            
            # Find credentials file
            cred_path = self._find_firebase_credentials(credentials_path)
            
            if not cred_path or not os.path.exists(cred_path):
                logger.error("Firebase credentials file not found")
                logger.debug(f"  Searched paths:")
                logger.debug(f"    - Explicit: {credentials_path}")
                logger.debug(f"    - Env var: {os.getenv('FIREBASE_CREDENTIALS_PATH')}")
                logger.debug(f"    - Config dir: {Path(__file__).parent.parent.parent / 'config'}")
                return False
            
            logger.info(f"Using Firebase credentials: {cred_path}")
            
            # Initialize Firebase
            cred = credentials.Certificate(cred_path)
            self.app = firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            
            logger.info("Firebase Admin SDK initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Firebase Admin SDK: {e}", exc_info=True)
            return False
    
    def is_initialized(self) -> bool:
        """Check if Firebase is initialized."""
        return self.app is not None and self.db is not None
    
    def get_auth(self):
        """Get Firebase Auth instance."""
        if not self.is_initialized():
            return None
        return auth
    
    def get_firestore(self):
        """Get Firestore client."""
        return self.db


# Global admin config instance
admin_config = AdminConfig()

