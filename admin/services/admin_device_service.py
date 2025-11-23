"""
Admin device management service.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from admin.services.admin_license_service import admin_license_service
from admin.services.admin_user_service import admin_user_service
from admin.config.admin_config import admin_config

logger = logging.getLogger(__name__)


class AdminDeviceService:
    """Handles device management."""
    
    def get_all_devices(self) -> List[dict]:
        """List all devices across all users with full device info."""
        try:
            users = admin_user_service.get_all_users()
            all_devices = []
            
            for user in users:
                uid = user["uid"]
                devices = self.get_user_devices_with_info(uid)
                
                for device in devices:
                    device["user_uid"] = uid
                    device["user_email"] = user.get("email", "unknown")
                    all_devices.append(device)
            
            return all_devices
            
        except Exception as e:
            logger.error(f"Error getting all devices: {e}", exc_info=True)
            return []
    
    def get_user_devices(self, uid: str) -> List[str]:
        """Get device IDs for specific user (from license)."""
        return admin_license_service.get_user_devices(uid)
    
    def get_user_devices_with_info(self, uid: str) -> List[dict]:
        """
        Get devices with full info from subcollection.
        
        Args:
            uid: User ID
        
        Returns:
            List of device documents with full info
        """
        if not admin_config.is_initialized():
            return []
        
        try:
            db = admin_config.get_firestore()
            devices_ref = db.collection("user_licenses").document(uid).collection("user_devices")
            docs = devices_ref.stream()
            
            devices = []
            for doc in docs:
                device_data = doc.to_dict()
                device_data["device_id"] = doc.id
                devices.append(device_data)
            
            return devices
            
        except Exception as e:
            logger.error(f"Error getting user devices with info for {uid}: {e}", exc_info=True)
            return []
    
    def remove_device(self, uid: str, device_id: str) -> bool:
        """
        Remove device from user.
        Removes from active_devices array and marks as revoked in subcollection.
        """
        try:
            # Remove from active_devices array in license
            license_data = admin_license_service.get_license(uid)
            if not license_data:
                logger.warning(f"No license found for user {uid}")
                return False
            
            active_devices = license_data.get("active_devices", []) or license_data.get("active_device_ids", [])
            if device_id in active_devices:
                active_devices.remove(device_id)
                # Update license with correct field name
                update_data = {
                    "active_device_ids": active_devices
                }
                if not admin_license_service.update_license(uid, update_data):
                    logger.warning(f"Failed to update license for user {uid}")
            
            # Mark device as revoked in subcollection
            if admin_config.is_initialized():
                try:
                    db = admin_config.get_firestore()
                    device_ref = db.collection("user_licenses").document(uid).collection("user_devices").document(device_id)
                    
                    now = datetime.utcnow()
                    device_ref.update({
                        "is_active": False,
                        "revoked_at": now
                    })
                    logger.info(f"Device {device_id} marked as revoked for user {uid}")
                except Exception as e:
                    logger.error(f"Error marking device as revoked: {e}", exc_info=True)
                    # Continue even if this fails
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing device: {e}", exc_info=True)
            return False
    
    def get_device_stats(self) -> dict:
        """Get device statistics."""
        try:
            all_devices = self.get_all_devices()
            users = admin_user_service.get_all_users()
            
            total_devices = len(all_devices)
            total_users = len(users)
            
            avg_devices_per_user = (
                total_devices / total_users if total_users > 0 else 0
            )
            
            # Count devices per user
            devices_per_user = {}
            for device in all_devices:
                uid = device["user_uid"]
                devices_per_user[uid] = devices_per_user.get(uid, 0) + 1
            
            users_with_devices = len(devices_per_user)
            users_without_devices = total_users - users_with_devices
            
            return {
                "total": total_devices,
                "average_per_user": round(avg_devices_per_user, 2),
                "users_with_devices": users_with_devices,
                "users_without_devices": users_without_devices,
            }
            
        except Exception as e:
            logger.error(f"Error getting device stats: {e}", exc_info=True)
            return {
                "total": 0,
                "average_per_user": 0,
                "users_with_devices": 0,
                "users_without_devices": 0,
            }


# Global admin device service instance
admin_device_service = AdminDeviceService()

