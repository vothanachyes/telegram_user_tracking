"""
License checker for status checking and tier retrieval.
"""

import logging
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

from database.db_manager import DatabaseManager
from utils.constants import (
    LICENSE_PRICING, DEFAULT_LICENSE_TIER
)

if TYPE_CHECKING:
    from services.auth_service import AuthService

logger = logging.getLogger(__name__)


class LicenseChecker:
    """Handles license status checking and tier retrieval."""
    
    def __init__(self, db_manager: DatabaseManager, auth_service_instance: Optional['AuthService'] = None):
        self.db_manager = db_manager
        self._auth_service = auth_service_instance
    
    def _get_auth_service(self):
        """Lazy import of auth_service to avoid circular dependency."""
        if self._auth_service is None:
            from services.auth_service import auth_service
            return auth_service
        return self._auth_service
    
    def get_user_tier(self, user_email: Optional[str] = None) -> str:
        """
        Get current user's license tier.
        Returns tier name (silver, gold, premium) or default if not found.
        """
        if not user_email:
            auth_service = self._get_auth_service()
            current_user = auth_service.get_current_user()
            if not current_user:
                return DEFAULT_LICENSE_TIER
            user_email = current_user.get('email')
        
        if not user_email:
            return DEFAULT_LICENSE_TIER
        
        # Check local cache first
        cache = self.db_manager.get_license_cache(user_email)
        if cache and cache.is_active:
            return cache.license_tier
        
        # Try to sync from Firebase (will be handled by LicenseSync)
        # For now, return default if cache not found
        return DEFAULT_LICENSE_TIER
    
    def check_license_status(self, user_email: Optional[str] = None, uid: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if user has an active license.
        Returns dict with status, tier, expiration, etc.
        """
        if not user_email or not uid:
            auth_service = self._get_auth_service()
            current_user = auth_service.get_current_user()
            if not current_user:
                # Return default values with max_devices and max_groups
                default_tier_info = LICENSE_PRICING.get(DEFAULT_LICENSE_TIER, {})
                return {
                    'is_active': False,
                    'tier': DEFAULT_LICENSE_TIER,
                    'expired': True,
                    'expiration_date': None,
                    'days_until_expiration': None,
                    'max_devices': default_tier_info.get('max_devices', 1),
                    'max_groups': default_tier_info.get('max_groups', 3),
                    'max_accounts': default_tier_info.get('max_accounts', 1),
                    'max_account_actions': 2
                }
            if not user_email:
                user_email = current_user.get('email')
            if not uid:
                uid = current_user.get('uid')
        
        # Check local cache
        cache = self.db_manager.get_license_cache(user_email)

        logger.debug(f"License cache for {user_email}: {cache}")
        
        # Note: Sync from Firebase should be called before this method
        # This is handled by LicenseService or LimitEnforcer
        
        if not cache:
            # Return default values with max_devices and max_groups
            default_tier_info = LICENSE_PRICING.get(DEFAULT_LICENSE_TIER, {})
            return {
                'is_active': False,
                'tier': DEFAULT_LICENSE_TIER,
                'expired': True,
                'expiration_date': None,
                'days_until_expiration': None,
                'max_devices': default_tier_info.get('max_devices', 1),
                'max_groups': default_tier_info.get('max_groups', 3),
                'max_accounts': default_tier_info.get('max_accounts', 1)
            }
        
        # Check expiration
        expired = False
        days_until_expiration = None
        
        if cache.expiration_date:
            now = datetime.now()
            if cache.expiration_date.tzinfo:
                now = now.replace(tzinfo=cache.expiration_date.tzinfo)
            
            if cache.expiration_date < now:
                expired = True
            else:
                delta = cache.expiration_date - now
                days_until_expiration = delta.days
    
        return {
            'is_active': cache.is_active and not expired,
            'tier': cache.license_tier,
            'expired': expired,
            'expiration_date': cache.expiration_date,
            'days_until_expiration': days_until_expiration,
            'max_devices': cache.max_devices,
            'max_groups': cache.max_groups,
            'max_accounts': cache.max_accounts,
            'max_account_actions': cache.max_account_actions
        }
    
    def get_license_info(self, user_email: Optional[str] = None, uid: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive license information for current user.
        Returns dict with all license details.
        """
        status = self.check_license_status(user_email, uid)
        tier = status['tier']
        pricing_info = LICENSE_PRICING.get(tier, {})
        
        # Count current usage
        groups = self.db_manager.get_all_groups()
        group_count = len(groups)
        
        auth_service = self._get_auth_service()
        current_user = auth_service.get_current_user()
        device_count = 0
        if current_user:
            uid = current_user.get('uid')
            # Get active devices directly from Firebase
            from config.firebase_config import firebase_config
            active_devices = firebase_config.get_active_devices(uid)
            device_count = len(active_devices)
        
        return {
            'tier': tier,
            'tier_name': pricing_info.get('name', tier.capitalize()),
            'is_active': status['is_active'],
            'expired': status['expired'],
            'expiration_date': status['expiration_date'],
            'days_until_expiration': status['days_until_expiration'],
            'max_devices': status['max_devices'],
            'max_groups': status['max_groups'],
            'current_devices': device_count,
            'current_groups': group_count,
            'price_usd': pricing_info.get('price_usd', 0),
            'price_khr': pricing_info.get('price_khr', 0),
            'features': pricing_info.get('features', [])
        }

