"""
Device management service.
Handles device registration, status checking, and revocation.
"""

import logging
import platform
from typing import Optional, List, Dict, Tuple
from datetime import datetime

from config.firebase_config import firebase_config
from services.auth_service import auth_service

logger = logging.getLogger(__name__)


class DeviceManagerService:
    """Handles device management operations."""
    
    def __init__(self):
        self._device_info_cache: Optional[dict] = None
    
    def get_device_info(self) -> dict:
        """
        Get current device information.
        
        Returns:
            Dict with device_name, platform, etc.
        """
        if self._device_info_cache:
            return self._device_info_cache
        
        system = platform.system()
        node = platform.node()
        machine = platform.machine()
        
        # Generate friendly device name
        if system == "Windows":
            device_name = f"Windows PC ({node})" if node else "Windows PC"
        elif system == "Darwin":
            device_name = f"Mac ({node})" if node else "Mac"
        elif system == "Linux":
            device_name = f"Linux ({node})" if node else "Linux PC"
        else:
            device_name = f"{system} ({node})" if node else "Unknown Device"
        
        platform_name = "Windows" if system == "Windows" else ("macOS" if system == "Darwin" else ("Linux" if system == "Linux" else system))
        
        self._device_info_cache = {
            "device_name": device_name,
            "platform": platform_name,
            "system": system,
            "node": node,
            "machine": machine
        }
        
        return self._device_info_cache
    
    def register_device(self, uid: Optional[str] = None) -> bool:
        """
        Register current device with Firebase.
        
        Args:
            uid: User ID (optional, uses current user if not provided)
        
        Returns:
            True if successful, False otherwise
        """
        if not uid:
            current_user = auth_service.get_current_user()
            if not current_user:
                logger.warning("No user logged in")
                return False
            uid = current_user.get("uid")
            if not uid:
                return False
        
        try:
            device_id = auth_service.device_id
            device_info = self.get_device_info()
            
            # Add device to Firebase subcollection
            success = firebase_config.add_user_device(uid, device_id, device_info)
            
            if success:
                logger.info(f"Device {device_id} registered for user {uid}")
            else:
                logger.warning(f"Failed to register device {device_id} for user {uid}")
            
            return success
        except Exception as e:
            logger.error(f"Error registering device: {e}", exc_info=True)
            return False
    
    def get_all_devices(self, uid: Optional[str] = None) -> List[dict]:
        """
        Get all user's devices from Firebase.
        
        Args:
            uid: User ID (optional, uses current user if not provided)
        
        Returns:
            List of device documents
        """
        if not uid:
            current_user = auth_service.get_current_user()
            if not current_user:
                logger.warning("No user logged in")
                return []
            uid = current_user.get("uid")
            if not uid:
                return []
        
        try:
            devices = firebase_config.get_user_devices(uid)
            
            # Sort by last_login (most recent first)
            devices.sort(key=lambda x: x.get("last_login", ""), reverse=True)
            
            logger.debug(f"Retrieved {len(devices)} devices for user {uid}")
            return devices
        except Exception as e:
            logger.error(f"Error getting devices: {e}", exc_info=True)
            return []
    
    def check_device_status(self, uid: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if current device is revoked.
        
        Args:
            uid: User ID (optional, uses current user if not provided)
        
        Returns:
            (is_revoked, error_message)
        """
        if not uid:
            current_user = auth_service.get_current_user()
            if not current_user:
                return False, "No user logged in"
            uid = current_user.get("uid")
            if not uid:
                return False, "No user ID"
        
        try:
            device_id = auth_service.device_id
            is_revoked = firebase_config.check_device_revoked(uid, device_id)
            
            if is_revoked:
                logger.warning(f"Device {device_id} is revoked for user {uid}")
                return True, "Device has been revoked"
            
            return False, None
        except Exception as e:
            logger.error(f"Error checking device status: {e}", exc_info=True)
            return False, str(e)
    
    def revoke_device(self, device_id: str, uid: Optional[str] = None) -> bool:
        """
        Revoke own device (remove from active_devices).
        Note: This removes the device from license but doesn't mark it as revoked.
        Only admin can mark devices as revoked.
        
        Args:
            device_id: Device ID to revoke
            uid: User ID (optional, uses current user if not provided)
        
        Returns:
            True if successful, False otherwise
        """
        if not uid:
            current_user = auth_service.get_current_user()
            if not current_user:
                logger.warning("No user logged in")
                return False
            uid = current_user.get("uid")
            if not uid:
                return False
        
        try:
            # Get current license
            license_data = firebase_config.get_user_license(uid)
            if not license_data:
                logger.warning(f"No license found for user {uid}")
                return False
            
            # Remove device from active_devices array
            active_devices = license_data.get("active_device_ids", [])
            if device_id in active_devices:
                active_devices.remove(device_id)
                
                # Note: Updating license requires Admin SDK
                # For now, we'll just log it - actual removal should be done via admin
                logger.info(f"Device {device_id} marked for removal from active_devices (admin action required)")
                return True
            else:
                logger.warning(f"Device {device_id} not found in active_devices")
                return False
        except Exception as e:
            logger.error(f"Error revoking device: {e}", exc_info=True)
            return False


# Global device manager service instance
device_manager_service = DeviceManagerService()

