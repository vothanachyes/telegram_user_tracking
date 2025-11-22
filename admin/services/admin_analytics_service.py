"""
Admin analytics and statistics service.
"""

import logging
from typing import Dict
from datetime import datetime, timedelta
from admin.services.admin_user_service import admin_user_service
from admin.services.admin_license_service import admin_license_service
from admin.services.admin_device_service import admin_device_service

logger = logging.getLogger(__name__)


class AdminAnalyticsService:
    """Handles analytics and statistics."""
    
    def get_user_stats(self) -> dict:
        """Get user statistics."""
        try:
            users = admin_user_service.get_all_users()
            
            now = datetime.utcnow()
            thirty_days_ago = now - timedelta(days=30)
            
            total_users = len(users)
            active_users = sum(1 for u in users if not u.get("disabled", False))
            new_users = sum(
                1 for u in users
                if u.get("created_at") and u["created_at"] >= thirty_days_ago
            )
            
            return {
                "total": total_users,
                "active": active_users,
                "disabled": total_users - active_users,
                "new_last_30_days": new_users,
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}", exc_info=True)
            return {
                "total": 0,
                "active": 0,
                "disabled": 0,
                "new_last_30_days": 0,
            }
    
    def get_license_stats(self) -> dict:
        """Get license statistics."""
        return admin_license_service.get_license_stats()
    
    def get_device_stats(self) -> dict:
        """Get device statistics."""
        return admin_device_service.get_device_stats()
    
    def get_activity_stats(self) -> dict:
        """
        Get activity statistics.
        Note: This is a placeholder - implement activity logging if needed.
        """
        return {
            "logins_today": 0,
            "logins_last_7_days": 0,
            "license_renewals_last_30_days": 0,
        }


# Global admin analytics service instance
admin_analytics_service = AdminAnalyticsService()

