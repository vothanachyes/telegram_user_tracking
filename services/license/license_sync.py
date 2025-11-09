"""
License sync for Firebase synchronization and cache management.
"""

import logging
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timedelta

from config.firebase_config import firebase_config
from database.db_manager import DatabaseManager
from database.models import UserLicenseCache
from utils.constants import (
    LICENSE_PRICING, LICENSE_TIER_BRONZE, DEFAULT_LICENSE_TIER
)

if TYPE_CHECKING:
    from services.auth_service import AuthService

logger = logging.getLogger(__name__)


class LicenseSync:
    """Handles Firebase sync and cache management."""
    
    def __init__(self, db_manager: DatabaseManager, auth_service_instance: Optional['AuthService'] = None):
        self.db_manager = db_manager
        self._auth_service = auth_service_instance
    
    def _get_auth_service(self):
        """Lazy import of auth_service to avoid circular dependency."""
        if self._auth_service is None:
            from services.auth_service import auth_service
            return auth_service
        return self._auth_service
    
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

