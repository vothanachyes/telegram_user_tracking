"""
License operations for Firestore REST API.
"""

import logging
from typing import Optional, List, Dict
import requests

from config.firebase.core import FirebaseCore, FIRESTORE_REST_URL
from config.firebase.helpers import FirestoreHelpers

logger = logging.getLogger(__name__)


class LicenseOperations:
    """License-related Firestore operations."""
    
    def __init__(self, core: FirebaseCore):
        """
        Initialize license operations.
        
        Args:
            core: FirebaseCore instance
        """
        self.core = core
        self.helpers = FirestoreHelpers()
    
    def get_user_license(self, uid: str, id_token: Optional[str] = None) -> Optional[dict]:
        """
        Get user license from Firestore using REST API.
        
        Args:
            uid: User ID
            id_token: Firebase ID token for authentication (optional, uses current token)
        
        Returns:
            License document if found, None otherwise
        """
        if not self.core.is_initialized():
            logger.error("Firebase not initialized")
            return None
        
        if not self.core.project_id:
            logger.error("FIREBASE_PROJECT_ID not configured")
            return None
        
        token = self.core.get_id_token(id_token)
        if not token:
            logger.error("No ID token available for Firestore access")
            return None
        
        try:
            url = f"{FIRESTORE_REST_URL}/projects/{self.core.project_id}/databases/(default)/documents/user_licenses/{uid}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                license_data = self.helpers.convert_firestore_document(data)
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
    
    def get_license_tiers(self, id_token: Optional[str] = None) -> List[dict]:
        """
        Get all license tier definitions from Firestore using REST API.
        
        Args:
            id_token: Firebase ID token (optional, uses current token)
        
        Returns:
            List of tier definition documents
        """
        if not self.core.is_initialized() or not self.core.project_id:
            logger.error("Firebase not initialized")
            return []
        
        token = self.core.get_id_token(id_token)
        if not token:
            logger.error("No ID token available")
            return []
        
        try:
            collection_name = "license_tiers"
            url = f"{FIRESTORE_REST_URL}/projects/{self.core.project_id}/databases/(default)/documents/{collection_name}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                tiers = []
                
                documents = data.get("documents", [])
                for doc in documents:
                    doc_name = doc.get("name", "")
                    doc_id = doc_name.split("/")[-1] if "/" in doc_name else ""
                    
                    tier_data = self.helpers.convert_firestore_document(doc)
                    if tier_data:
                        tier_data["tier_key"] = doc_id
                        tiers.append(tier_data)
                
                tiers.sort(key=lambda x: x.get("tier_key", ""))
                
                logger.debug(f"Retrieved {len(tiers)} license tiers")
                return tiers
            elif response.status_code == 404:
                logger.debug("No license tiers found")
                return []
            else:
                logger.error(f"Error getting license tiers: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting license tiers: {e}", exc_info=True)
            return []
    
    def get_license_tier(self, tier_key: str, id_token: Optional[str] = None) -> Optional[dict]:
        """
        Get specific license tier definition from Firestore using REST API.
        
        Args:
            tier_key: Tier key (document ID)
            id_token: Firebase ID token (optional, uses current token)
        
        Returns:
            Tier definition document if found, None otherwise
        """
        if not self.core.is_initialized() or not self.core.project_id:
            logger.error("Firebase not initialized")
            return None
        
        token = self.core.get_id_token(id_token)
        if not token:
            logger.error("No ID token available")
            return None
        
        try:
            collection_name = "license_tiers"
            url = f"{FIRESTORE_REST_URL}/projects/{self.core.project_id}/databases/(default)/documents/{collection_name}/{tier_key}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                tier_data = self.helpers.convert_firestore_document(data)
                if tier_data:
                    tier_data["tier_key"] = tier_key
                    logger.debug(f"License tier {tier_key} retrieved")
                    return tier_data
            elif response.status_code == 404:
                logger.debug(f"No license tier found for {tier_key}")
                return None
            else:
                logger.error(f"Error getting license tier: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting license tier {tier_key}: {e}", exc_info=True)
            return None
    
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

