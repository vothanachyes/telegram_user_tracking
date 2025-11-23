"""
App update operations for Firestore REST API.
"""

import logging
from typing import Optional, Dict
import requests

from config.firebase.core import FirebaseCore, FIRESTORE_REST_URL
from config.firebase.helpers import FirestoreHelpers

logger = logging.getLogger(__name__)


class UpdateOperations:
    """App update-related Firestore operations."""
    
    def __init__(self, core: FirebaseCore):
        """
        Initialize update operations.
        
        Args:
            core: FirebaseCore instance
        """
        self.core = core
        self.helpers = FirestoreHelpers()
    
    def get_app_update_info(self, id_token: Optional[str] = None) -> Optional[dict]:
        """
        Get latest app update information from Firestore using REST API.
        
        Args:
            id_token: Firebase ID token (optional, uses current token)
        
        Returns:
            Update document if found, None otherwise
        """
        if not self.core.is_initialized() or not self.core.project_id:
            logger.error("Firebase not initialized")
            return None
        
        token = self.core.get_id_token(id_token)
        if not token:
            logger.error("No ID token available")
            return None
        
        try:
            from utils.constants import FIREBASE_APP_UPDATES_COLLECTION, FIREBASE_APP_UPDATES_DOCUMENT
            
            url = f"{FIRESTORE_REST_URL}/projects/{self.core.project_id}/databases/(default)/documents/{FIREBASE_APP_UPDATES_COLLECTION}/{FIREBASE_APP_UPDATES_DOCUMENT}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                update_data = self.helpers.convert_firestore_document(data)
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

