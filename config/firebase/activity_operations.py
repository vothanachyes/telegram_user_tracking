"""
User activities operations for Firestore REST API.
"""

import logging
from typing import Optional, Dict
from datetime import datetime
import requests

from config.firebase.core import FirebaseCore, FIRESTORE_REST_URL
from config.firebase.helpers import FirestoreHelpers

logger = logging.getLogger(__name__)


class ActivityOperations:
    """User activities-related Firestore operations."""
    
    def __init__(self, core: FirebaseCore):
        """
        Initialize activity operations.
        
        Args:
            core: FirebaseCore instance
        """
        self.core = core
        self.helpers = FirestoreHelpers()
    
    def get_user_activities(self, uid: str, id_token: Optional[str] = None) -> Optional[dict]:
        """
        Get user activities from Firestore using REST API.
        
        Args:
            uid: User ID
            id_token: Firebase ID token (optional, uses current token)
        
        Returns:
            User activities document if found, None otherwise
        """
        if not self.core.is_initialized() or not self.core.project_id:
            logger.error("Firebase not initialized")
            return None
        
        token = self.core.get_id_token(id_token)
        if not token:
            logger.error("No ID token available")
            return None
        
        try:
            url = f"{FIRESTORE_REST_URL}/projects/{self.core.project_id}/databases/(default)/documents/user_activities/{uid}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                activities = self.helpers.convert_firestore_document(data)
                if activities:
                    logger.debug(f"User activities retrieved for {uid}")
                    return activities
            elif response.status_code == 404:
                logger.debug(f"No activities document found for user {uid}")
                return None
            else:
                logger.error(f"Error getting user activities: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user activities: {e}", exc_info=True)
            return None
    
    def update_user_activities(self, uid: str, updates: dict, id_token: Optional[str] = None) -> bool:
        """
        Update user activities in Firestore using REST API.
        Client can only update certain fields (counts, app_version).
        
        Args:
            uid: User ID
            updates: Dict of fields to update
            id_token: Firebase ID token (optional, uses current token)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.core.is_initialized() or not self.core.project_id:
            logger.error("Firebase not initialized")
            return False
        
        token = self.core.get_id_token(id_token)
        if not token:
            logger.error("No ID token available")
            return False
        
        try:
            url = f"{FIRESTORE_REST_URL}/projects/{self.core.project_id}/databases/(default)/documents/user_activities/{uid}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Prepare update data in Firestore format
            fields = {}
            for key, value in updates.items():
                fields[key] = self.helpers.convert_to_firestore_value(value)
            
            # Always update last_updated timestamp
            now = datetime.utcnow().isoformat() + "Z"
            fields["last_updated"] = {"timestampValue": now}
            
            # Check if document exists
            existing = self.get_user_activities(uid, token)
            if not existing:
                # Create new document with created_at
                fields["created_at"] = {"timestampValue": now}
            
            document_data = {"fields": fields}
            
            # Use PATCH to update (creates if doesn't exist)
            response = requests.patch(url, headers=headers, json=document_data, timeout=10)
            
            if response.status_code == 200:
                logger.debug(f"User activities updated for {uid}")
                return True
            else:
                logger.error(f"Error updating user activities: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating user activities: {e}", exc_info=True)
            return False

