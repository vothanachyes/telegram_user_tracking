"""
Admin device management service.
"""

import logging
from typing import List, Dict
from admin.services.admin_license_service import admin_license_service
from admin.services.admin_user_service import admin_user_service

logger = logging.getLogger(__name__)


class AdminDeviceService:
    """Handles device management."""
    
    def get_all_devices(self) -> List[dict]:
        """List all devices across all users."""
        try:
            users = admin_user_service.get_all_users()
            all_devices = []
            
            for user in users:
                uid = user["uid"]
                devices = self.get_user_devices(uid)
                
                for device_id in devices:
                    all_devices.append({
                        "user_uid": uid,
                        "user_email": user.get("email", "unknown"),
                        "device_id": device_id,
                    })
            
            return all_devices
            
        except Exception as e:
            logger.error(f"Error getting all devices: {e}", exc_info=True)
            return []
    
    def get_user_devices(self, uid: str) -> List[str]:
        """Get devices for specific user."""
        return admin_license_service.get_user_devices(uid)
    
    def remove_device(self, uid: str, device_id: str) -> bool:
        """Remove device from user."""
        try:
            license_data = admin_license_service.get_license(uid)
            if not license_data:
                logger.warning(f"No license found for user {uid}")
                return False
            
            active_devices = license_data.get("active_devices", [])
            if device_id in active_devices:
                active_devices.remove(device_id)
                return admin_license_service.update_license(uid, {
                    "active_devices": active_devices
                })
            
            return False
            
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

