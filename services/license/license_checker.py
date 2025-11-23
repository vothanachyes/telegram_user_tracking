"""
License checker for status checking and tier retrieval.
"""

import logging
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

from database.db_manager import DatabaseManager
from utils.constants import DEFAULT_LICENSE_TIER

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
                # Try to get tier info from Firestore, fallback to defaults
                try:
                    from services.license.license_tier_service import license_tier_service
                    default_tier_info = license_tier_service.get_tier(DEFAULT_LICENSE_TIER) or {}
                except Exception:
                    default_tier_info = {}
                
                return {
                    'is_active': False,
                    'tier': DEFAULT_LICENSE_TIER,
                    'expired': True,
                    'expiration_date': None,
                    'days_until_expiration': None,
                    'max_devices': default_tier_info.get('max_devices', 1),
                    'max_groups': default_tier_info.get('max_groups', 1),
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
            # No cache found - this could mean:
            # 1. License hasn't been synced yet (should be handled by LicenseService.sync_from_firebase)
            # 2. User doesn't have a license in Firebase
            # Log warning but don't mark as expired if we just synced (might be a timing issue)
            logger.warning(
                f"No license cache found for {user_email}. "
                f"This might indicate the license hasn't been synced yet or user has no license."
            )
            # Return default values with max_devices and max_groups
            # Note: expired=True here means "unknown status" - should trigger sync
            # Try to get tier info from Firestore, fallback to defaults
            try:
                from services.license.license_tier_service import license_tier_service
                default_tier_info = license_tier_service.get_tier(DEFAULT_LICENSE_TIER) or {}
            except Exception:
                default_tier_info = {}
            
            return {
                'is_active': False,
                'tier': DEFAULT_LICENSE_TIER,
                'expired': True,  # Mark as expired if no cache (will trigger sync/check)
                'expiration_date': None,
                'days_until_expiration': None,
                'max_devices': default_tier_info.get('max_devices', 1),
                'max_groups': default_tier_info.get('max_groups', 1),
                'max_accounts': default_tier_info.get('max_accounts', 1)
            }
        
        # Check expiration
        expired = False
        days_until_expiration = None
        
        if cache.expiration_date:
            now = datetime.now()
            
            # Handle timezone comparison properly
            expiration_date = cache.expiration_date
            
            # If expiration_date is timezone-aware, make now timezone-aware too
            if expiration_date.tzinfo:
                # Expiration is timezone-aware (likely UTC from Firebase)
                # Make now timezone-aware with same timezone for proper comparison
                if now.tzinfo is None:
                    # Now is naive, make it timezone-aware using expiration's timezone
                    now = now.replace(tzinfo=expiration_date.tzinfo)
                elif now.tzinfo != expiration_date.tzinfo:
                    # Different timezones, convert now to expiration's timezone
                    now = now.astimezone(expiration_date.tzinfo)
            elif now.tzinfo:
                # Now is timezone-aware but expiration is naive
                # Make expiration timezone-aware using now's timezone
                expiration_date = expiration_date.replace(tzinfo=now.tzinfo)
            
            # Compare dates
            if expiration_date < now:
                expired = True
                logger.warning(
                    f"License expired: expiration_date={expiration_date}, now={now}, "
                    f"expiration_tzinfo={expiration_date.tzinfo}, now_tzinfo={now.tzinfo}"
                )
            else:
                delta = expiration_date - now
                days_until_expiration = delta.days
                logger.debug(
                    f"License valid: expiration_date={expiration_date}, now={now}, "
                    f"days_until_expiration={days_until_expiration}"
                )
    
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
        
        # Get tier info from Firestore
        try:
            from services.license.license_tier_service import license_tier_service
            pricing_info = license_tier_service.get_tier(tier) or {}
        except Exception:
            pricing_info = {}
        
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

