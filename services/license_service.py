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
    LICENSE_PRICING, LICENSE_TIER_BRONZE, LICENSE_TIER_SILVER, LICENSE_TIER_GOLD, LICENSE_TIER_PREMIUM,
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
                    'max_accounts': default_tier_info.get('max_accounts', 1)
                }
            if not user_email:
                user_email = current_user.get('email')
            if not uid:
                uid = current_user.get('uid')
        
        # Check local cache
        cache = self.db_manager.get_license_cache(user_email)

        logger.debug(f"License cache for {user_email}: {cache}")
        
        # Sync from Firebase if cache is stale or missing - ALWAYS sync if we have uid
        if not cache or not cache.is_active:
            if uid:
                logger.info(f"Syncing license from Firebase for user {user_email} (uid: {uid})")
                sync_success = self.sync_from_firebase(user_email, uid)
                if sync_success:
                    cache = self.db_manager.get_license_cache(user_email)
                else:
                    logger.warning(f"Failed to sync license from Firebase for user {user_email}")
            else:
                logger.warning(f"No UID provided, cannot sync from Firebase for user {user_email}")
        
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
            'max_accounts': cache.max_accounts
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
                logger.info(f"No license found in Firebase for user {uid}, creating default license")
                # Create default license document for new user
                default_tier = DEFAULT_LICENSE_TIER
                tier_info = LICENSE_PRICING.get(default_tier, {})
                # Get period from tier info (default to 7 days if not specified)
                period_days = tier_info.get('period', 7)
                default_license = {
                    'license_tier': default_tier,
                    'max_devices': tier_info.get('max_devices', 1),
                    'max_groups': tier_info.get('max_groups', 1),
                    'max_accounts': tier_info.get('max_accounts', 1),
                    'active_device_ids': [],
                    # Set expiration based on tier's period
                    # Admin can extend this later
                    'expiration_date': (datetime.now() + timedelta(days=period_days)).isoformat()
                }
                
                # Create the license document in Firestore
                if not firebase_config.set_user_license(uid, default_license):
                    logger.error(f"Failed to create default license for user {uid}")
                    return False
                
                # Retry getting the license
                license_data = firebase_config.get_user_license(uid)
                if not license_data:
                    logger.error(f"Failed to retrieve newly created license for user {uid}")
                    return False
                
                logger.info(f"Created default {default_tier} license for user {uid}")
            
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
            
            # Check if license is expired and auto-renew Bronze (free trial) licenses
            if expiration_date:
                now = datetime.now()
                # Handle timezone-aware dates
                if expiration_date.tzinfo:
                    now = now.replace(tzinfo=expiration_date.tzinfo)
                elif expiration_date.tzinfo is None and now.tzinfo:
                    # If expiration is naive but now is timezone-aware, make expiration aware
                    expiration_date = expiration_date.replace(tzinfo=now.tzinfo)
                
                if expiration_date < now:
                    if tier == LICENSE_TIER_BRONZE:
                        # Auto-renew expired Bronze (free trial) licenses
                        logger.info(f"Bronze license expired for user {uid}, auto-renewing")
                        tier_info = LICENSE_PRICING.get(LICENSE_TIER_BRONZE, {})
                        period_days = tier_info.get('period', 7)
                        new_expiration = datetime.now() + timedelta(days=period_days)
                        
                        # Preserve timezone if original had one
                        if expiration_date.tzinfo:
                            new_expiration = new_expiration.replace(tzinfo=expiration_date.tzinfo)
                        
                        # Update expiration date in Firestore
                        updated_license = {
                            'expiration_date': new_expiration.isoformat(),
                            'license_tier': LICENSE_TIER_BRONZE,
                            'max_devices': tier_info.get('max_devices', 1),
                            'max_groups': tier_info.get('max_groups', 1),
                            'max_accounts': tier_info.get('max_accounts', 1)
                        }
                        firebase_config.set_user_license(uid, updated_license)
                        
                        # Update expiration_date for local processing
                        expiration_date = new_expiration
                        logger.info(f"Auto-renewed Bronze license for user {uid}, new expiration: {new_expiration.isoformat()}")
                    else:
                        # For expired paid tiers, convert to Bronze and renew (grace period)
                        # This handles cases where users had expired licenses before Bronze tier existed
                        original_tier = tier
                        logger.info(f"Expired {original_tier} license for user {uid}, converting to Bronze and renewing")
                        tier_info = LICENSE_PRICING.get(LICENSE_TIER_BRONZE, {})
                        period_days = tier_info.get('period', 7)
                        new_expiration = datetime.now() + timedelta(days=period_days)
                        
                        # Preserve timezone if original had one
                        if expiration_date.tzinfo:
                            new_expiration = new_expiration.replace(tzinfo=expiration_date.tzinfo)
                        
                        # Convert to Bronze and renew
                        updated_license = {
                            'expiration_date': new_expiration.isoformat(),
                            'license_tier': LICENSE_TIER_BRONZE,
                            'max_devices': tier_info.get('max_devices', 1),
                            'max_groups': tier_info.get('max_groups', 1),
                            'max_accounts': tier_info.get('max_accounts', 1)
                        }
                        firebase_config.set_user_license(uid, updated_license)
                        
                        # Update tier and expiration_date for local processing
                        tier = LICENSE_TIER_BRONZE
                        expiration_date = new_expiration
                        logger.info(f"Converted expired {original_tier} license to Bronze and renewed for user {uid}, new expiration: {new_expiration.isoformat()}")
            max_devices = license_data.get('max_devices', LICENSE_PRICING.get(tier, {}).get('max_devices', 1))
            max_groups = license_data.get('max_groups', LICENSE_PRICING.get(tier, {}).get('max_groups', 3))
            max_accounts = license_data.get('max_accounts', LICENSE_PRICING.get(tier, {}).get('max_accounts', 1))
            
            # Create cache entry
            cache = UserLicenseCache(
                user_email=user_email,
                license_tier=tier,
                expiration_date=expiration_date,
                max_devices=max_devices,
                max_groups=max_groups,
                max_accounts=max_accounts,
                is_active=True
            )
            
            # Save to local cache
            self.db_manager.save_license_cache(cache)
            logger.info(f"Synced license for user {user_email}: tier={tier}")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing license from Firebase: {e}")
            return False
    
    def can_add_group(self, user_email: Optional[str] = None, uid: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if user can add another group.
        Returns (can_add, error_message)
        """
        status = self.check_license_status(user_email, uid)
        
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
        
        # Ensure we sync from Firebase before checking status
        # This ensures license is created if it doesn't exist
        if uid and user_email:
            logger.info(f"Syncing license before device check for user {user_email} (uid: {uid})")
            self.sync_from_firebase(user_email, uid)
        
        status = self.check_license_status(user_email, uid)
        
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
    
    def can_add_account(self, user_email: Optional[str] = None, uid: Optional[str] = None) -> Tuple[bool, Optional[str], int, int]:
        """
        Check if user can add another Telegram account.
        
        Args:
            user_email: User email (optional, will get from auth service if not provided)
            uid: User UID (optional, will get from auth service if not provided)
            
        Returns:
            Tuple of (can_add, error_message, current_count, max_count)
        """
        if not user_email or not uid:
            auth_service = self._get_auth_service()
            current_user = auth_service.get_current_user()
            if not current_user:
                return False, "User not authenticated", 0, 0
            if not user_email:
                user_email = current_user.get('email')
            if not uid:
                uid = current_user.get('uid')
        
        # Check license status
        status = self.check_license_status(user_email, uid)
        
        if not status['is_active']:
            return False, "Your license has expired. Please contact admin to renew.", 0, 0
        
        if status['expired']:
            return False, "Your license has expired. Please contact admin to renew.", 0, 0
        
        max_accounts = status['max_accounts']
        
        # Get current account count from database
        credentials = self.db_manager.get_telegram_credentials()
        current_count = len(credentials)
        
        if current_count >= max_accounts:
            tier = status['tier']
            tier_name = LICENSE_PRICING.get(tier, {}).get('name', tier.capitalize())
            return False, f"You have reached the account limit ({max_accounts}) for {tier_name} tier. Please contact admin to upgrade.", current_count, max_accounts
        
        return True, None, current_count, max_accounts
    
    def enforce_group_limit(self, user_email: Optional[str] = None) -> bool:
        """
        Enforce group limit - check if user can add groups.
        Returns True if allowed, False if blocked.
        """
        can_add, _ = self.can_add_group(user_email)
        return can_add
    
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

