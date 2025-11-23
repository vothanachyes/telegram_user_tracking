"""
Device operations for Firestore REST API.
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime
import requests

from config.firebase.core import FirebaseCore, FIRESTORE_REST_URL
from config.firebase.helpers import FirestoreHelpers

logger = logging.getLogger(__name__)


class DeviceOperations:
    """Device-related Firestore operations."""
    
    def __init__(self, core: FirebaseCore):
        """
        Initialize device operations.
        
        Args:
            core: FirebaseCore instance
        """
        self.core = core
        self.helpers = FirestoreHelpers()
    
    def get_user_devices(self, uid: str, id_token: Optional[str] = None) -> List[dict]:
        """
        Get all devices for a user from Firestore subcollection using REST API.
        
        Args:
            uid: User ID
            id_token: Firebase ID token (optional, uses current token)
        
        Returns:
            List of device documents
        """
        if not self.core.is_initialized() or not self.core.project_id:
            logger.error("Firebase not initialized")
            return []
        
        token = self.core.get_id_token(id_token)
        if not token:
            logger.error("No ID token available")
            return []
        
        try:
            url = f"{FIRESTORE_REST_URL}/projects/{self.core.project_id}/databases/(default)/documents/user_licenses/{uid}/user_devices"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                devices = []
                
                documents = data.get("documents", [])
                for doc in documents:
                    doc_name = doc.get("name", "")
                    device_id = doc_name.split("/")[-1] if "/" in doc_name else ""
                    
                    device_data = self.helpers.convert_firestore_document(doc)
                    if device_data:
                        device_data["device_id"] = device_id
                        devices.append(device_data)
                
                logger.debug(f"Retrieved {len(devices)} devices for user {uid}")
                return devices
            elif response.status_code == 404:
                logger.debug(f"No devices found for user {uid}")
                return []
            else:
                logger.error(f"Error getting user devices: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting user devices: {e}", exc_info=True)
            return []
    
    def add_user_device(self, uid: str, device_id: str, device_info: dict, id_token: Optional[str] = None) -> bool:
        """
        Add or update device info in Firestore subcollection using REST API.
        
        Args:
            uid: User ID
            device_id: Device ID
            device_info: Dict with device_name, platform, etc.
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
            url = f"{FIRESTORE_REST_URL}/projects/{self.core.project_id}/databases/(default)/documents/user_licenses/{uid}/user_devices/{device_id}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            now = datetime.utcnow().isoformat() + "Z"
            fields = {
                "device_id": {"stringValue": device_id},
                "device_name": {"stringValue": device_info.get("device_name", "Unknown Device")},
                "platform": {"stringValue": device_info.get("platform", "Unknown")},
                "last_login": {"timestampValue": now},
                "is_active": {"booleanValue": True}
            }
            
            # Check if device exists to preserve first_login
            existing_devices = self.get_user_devices(uid, token)
            existing_device = next((d for d in existing_devices if d.get("device_id") == device_id), None)
            
            if existing_device:
                # Update existing device, preserve first_login
                if "first_login" in existing_device:
                    fields["first_login"] = {"timestampValue": existing_device["first_login"]}
                # Clear revoked_at if device was previously revoked (unrevoke on successful login)
                if existing_device.get("revoked_at"):
                    fields["revoked_at"] = {"nullValue": None}
            else:
                # New device, set first_login
                fields["first_login"] = {"timestampValue": now}
            
            document_data = {"fields": fields}
            
            response = requests.patch(url, headers=headers, json=document_data, timeout=10)
            
            if response.status_code == 200:
                logger.debug(f"Device {device_id} added/updated for user {uid}")
                return True
            else:
                logger.error(f"Error adding device: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding user device: {e}", exc_info=True)
            return False
    
    def check_device_revoked(self, uid: str, device_id: str, id_token: Optional[str] = None) -> bool:
        """
        Check if a device is revoked by checking the user_devices subcollection.
        
        Args:
            uid: User ID
            device_id: Device ID
            id_token: Firebase ID token (optional, uses current token)
        
        Returns:
            True if device is revoked, False otherwise
        """
        if not self.core.is_initialized() or not self.core.project_id:
            logger.error("Firebase not initialized")
            return False
        
        token = self.core.get_id_token(id_token)
        if not token:
            logger.error("No ID token available")
            return False
        
        try:
            url = f"{FIRESTORE_REST_URL}/projects/{self.core.project_id}/databases/(default)/documents/user_licenses/{uid}/user_devices/{device_id}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                device_data = self.helpers.convert_firestore_document(data)
                if device_data:
                    # Check if revoked_at exists and is not None
                    revoked_at = device_data.get("revoked_at")
                    is_active = device_data.get("is_active", True)
                    return revoked_at is not None or not is_active
            elif response.status_code == 404:
                # Device not found, not revoked (doesn't exist yet)
                return False
            else:
                logger.error(f"Error checking device status: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking device revoked status: {e}", exc_info=True)
            return False

