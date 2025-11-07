"""
License service for managing user subscriptions and limits.
"""

import logging
from typing import Optional, Dict, Any, Tuple, TYPE_CHECKING
from datetime import datetime, timedelta
from config.firebase_config import firebase_config
from database.db_manager import DatabaseManager
from database.models import UserLicenseCache
from utils.constants import (
    LICENSE_PRICING, LICENSE_TIER_SILVER, LICENSE_TIER_GOLD, LICENSE_TIER_PREMIUM,
    DEFAULT_LICENSE_TIER
)

if TYPE_CHECKING:
    from services.auth_service import AuthService

logger = logging.getLogger(__name__)


class LicenseService:
    """Service for managing user licenses and enforcing limits."""
    
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
        
        # Try to sync from Firebase
        self.sync_from_firebase(user_email)
        cache = self.db_manager.get_license_cache(user_email)
        if cache and cache.is_active:
            return cache.license_tier
        
        return DEFAULT_LICENSE_TIER
    
    def check_license_status(self, user_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if user has an active license.
        Returns dict with status, tier, expiration, etc.
        """
        if not user_email:
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
                    'max_groups': default_tier_info.get('max_groups', 3)
                }
            user_email = current_user.get('email')
            uid = current_user.get('uid')
        else:
            uid = None
        
        # Check local cache
        cache = self.db_manager.get_license_cache(user_email)
        
        # Sync from Firebase if cache is stale or missing
        if not cache or not cache.is_active:
            if uid:
                self.sync_from_firebase(user_email, uid)
                cache = self.db_manager.get_license_cache(user_email)
        
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
                'max_groups': default_tier_info.get('max_groups', 3)
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
            'max_groups': cache.max_groups
        }
    
    def sync_from_firebase(self, user_email: Optional[str] = None, uid: Optional[str] = None) -> bool:
        """
        Sync license data from Firebase Firestore to local cache.
        Returns True if successful.
        """
        if not uid:
            auth_service = self._get_auth_service()
            current_user = auth_service.get_current_user()
            if not current_user:
                return False
            uid = current_user.get('uid')
            if not user_email:
                user_email = current_user.get('email')
        
        if not uid or not user_email:
            return False
        
        try:
            # Get license from Firestore
            license_data = firebase_config.get_user_license(uid)
            
            if not license_data:
                logger.warning(f"No license found in Firebase for user {uid}")
                return False
            
            # Parse expiration date
            expiration_date = None
            if 'expiration_date' in license_data:
                exp_val = license_data['expiration_date']
                if isinstance(exp_val, str):
                    # Try to parse timestamp string
                    try:
                        expiration_date = datetime.fromisoformat(exp_val.replace('Z', '+00:00'))
                    except:
                        try:
                            expiration_date = datetime.strptime(exp_val, '%Y-%m-%d')
                        except:
                            pass
                elif hasattr(exp_val, 'timestamp'):
                    expiration_date = datetime.fromtimestamp(exp_val.timestamp())
            
            # Get tier and limits
            tier = license_data.get('license_tier', DEFAULT_LICENSE_TIER)
            max_devices = license_data.get('max_devices', LICENSE_PRICING.get(tier, {}).get('max_devices', 1))
            max_groups = license_data.get('max_groups', LICENSE_PRICING.get(tier, {}).get('max_groups', 3))
            
            # Create cache entry
            cache = UserLicenseCache(
                user_email=user_email,
                license_tier=tier,
                expiration_date=expiration_date,
                max_devices=max_devices,
                max_groups=max_groups,
                is_active=True
            )
            
            # Save to local cache
            self.db_manager.save_license_cache(cache)
            logger.info(f"Synced license for user {user_email}: tier={tier}")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing license from Firebase: {e}")
            return False
    
    def can_add_group(self, user_email: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if user can add another group.
        Returns (can_add, error_message)
        """
        status = self.check_license_status(user_email)
        
        if not status['is_active']:
            return False, "Your license has expired. Please contact admin to renew."
        
        if status['expired']:
            return False, "Your license has expired. Please contact admin to renew."
        
        tier = status['tier']
        max_groups = status['max_groups']
        
        # Premium tier has unlimited groups
        if max_groups == -1:
            return True, None
        
        # Count current groups
        groups = self.db_manager.get_all_groups()
        current_count = len(groups)
        
        if current_count >= max_groups:
            tier_name = LICENSE_PRICING.get(tier, {}).get('name', tier.capitalize())
            return False, f"You have reached the group limit ({max_groups}) for {tier_name} tier. Please contact admin to upgrade."
        
        return True, None
    
    def can_add_device(self, device_id: str, user_email: Optional[str] = None, uid: Optional[str] = None) -> Tuple[bool, Optional[str], list]:
        """
        Check if user can add another device.
        Returns (can_add, error_message, active_devices)
        """
        if not uid:
            auth_service = self._get_auth_service()
            current_user = auth_service.get_current_user()
            if not current_user:
                return False, "User not authenticated", []
            uid = current_user.get('uid')
            if not user_email:
                user_email = current_user.get('email')
        
        status = self.check_license_status(user_email)
        
        if not status['is_active']:
            return False, "Your license has expired. Please contact admin to renew.", []
        
        if status['expired']:
            return False, "Your license has expired. Please contact admin to renew.", []
        
        max_devices = status['max_devices']
        
        # Get active devices from Firebase
        active_devices = firebase_config.get_active_devices(uid)
        
        # Check if current device is already registered
        if device_id in active_devices:
            return True, None, active_devices
        
        # Check if limit reached
        if len(active_devices) >= max_devices:
            tier = status['tier']
            tier_name = LICENSE_PRICING.get(tier, {}).get('name', tier.capitalize())
            return False, f"You have reached the device limit ({max_devices}) for {tier_name} tier. Please contact admin to upgrade or deactivate a device.", active_devices
        
        return True, None, active_devices
    
    def get_active_devices(self, uid: Optional[str] = None) -> list:
        """Get list of active device IDs for current user."""
        if not uid:
            auth_service = self._get_auth_service()
            current_user = auth_service.get_current_user()
            if not current_user:
                return []
            uid = current_user.get('uid')
        
        return firebase_config.get_active_devices(uid)
    
    def enforce_group_limit(self, user_email: Optional[str] = None) -> bool:
        """
        Enforce group limit - check if user can add groups.
        Returns True if allowed, False if blocked.
        """
        can_add, _ = self.can_add_group(user_email)
        return can_add
    
    def get_license_info(self, user_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive license information for current user.
        Returns dict with all license details.
        """
        status = self.check_license_status(user_email)
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
            active_devices = self.get_active_devices(uid)
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

