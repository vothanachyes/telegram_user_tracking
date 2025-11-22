"""
Admin license management service.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime
from admin.config.admin_config import admin_config
from admin.utils.constants import (
    FIRESTORE_USER_LICENSES_COLLECTION,
    LICENSE_TIERS  # Fallback if Firestore tiers not available
)

logger = logging.getLogger(__name__)


class AdminLicenseService:
    """Handles license CRUD operations."""
    
    def __init__(self):
        self._db = None
    
    def _ensure_initialized(self) -> bool:
        """Ensure Firebase is initialized."""
        if not admin_config.is_initialized():
            if not admin_config.initialize():
                return False
        self._db = admin_config.get_firestore()
        return self._db is not None
    
    def get_all_licenses(self) -> List[dict]:
        """List all licenses from Firestore."""
        if not self._ensure_initialized():
            return []
        
        try:
            licenses = []
            docs = self._db.collection(FIRESTORE_USER_LICENSES_COLLECTION).stream()
            
            for doc in docs:
                data = doc.to_dict()
                data["uid"] = doc.id
                licenses.append(data)
            
            logger.info(f"Retrieved {len(licenses)} licenses")
            return licenses
            
        except Exception as e:
            logger.error(f"Error getting all licenses: {e}", exc_info=True)
            return []
    
    def get_license(self, uid: str) -> Optional[dict]:
        """Get license by UID."""
        if not self._ensure_initialized():
            return None
        
        try:
            doc_ref = self._db.collection(FIRESTORE_USER_LICENSES_COLLECTION).document(uid)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data["uid"] = uid
                return data
            return None
            
        except Exception as e:
            logger.error(f"Error getting license for {uid}: {e}", exc_info=True)
            return None
    
    def get_tier_definition(self, tier_key: str) -> Optional[dict]:
        """Get tier definition from Firestore (or fallback to constants)."""
        try:
            from admin.services.admin_license_tier_service import admin_license_tier_service
            tier = admin_license_tier_service.get_tier(tier_key)
            if tier:
                return tier
        except Exception as e:
            logger.debug(f"Could not get tier from Firestore: {e}")
        
        # Fallback to constants
        try:
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(project_root))
            from utils.constants import LICENSE_PRICING
            if tier_key in LICENSE_PRICING:
                tier_data = LICENSE_PRICING[tier_key].copy()
                tier_data["tier_key"] = tier_key
                return tier_data
        except Exception as e:
            logger.debug(f"Could not get tier from constants: {e}")
        
        return None
    
    def create_license(self, uid: str, license_data: dict) -> bool:
        """Create new license."""
        if not self._ensure_initialized():
            return False
        
        try:
            # Validate required fields
            if "tier" not in license_data:
                logger.error("License tier is required")
                return False
            
            tier_key = license_data["tier"]
            
            # Validate tier exists (check Firestore first, then constants)
            tier_definition = self.get_tier_definition(tier_key)
            if not tier_definition:
                logger.error(f"Invalid license tier: {tier_key}")
                return False
            
            # Use tier definition defaults if not provided
            if "max_devices" not in license_data:
                license_data["max_devices"] = tier_definition.get("max_devices", 1)
            if "max_groups" not in license_data:
                license_data["max_groups"] = tier_definition.get("max_groups", 1)
            if "max_accounts" not in license_data:
                license_data["max_accounts"] = tier_definition.get("max_accounts", 1)
            
            # Set defaults
            license_data.setdefault("created_at", datetime.utcnow().isoformat() + "Z")
            license_data.setdefault("active_devices", [])
            license_data.setdefault("max_devices", 1)
            license_data.setdefault("max_groups", 1)
            license_data.setdefault("max_accounts", 1)
            
            doc_ref = self._db.collection(FIRESTORE_USER_LICENSES_COLLECTION).document(uid)
            doc_ref.set(license_data)
            
            logger.info(f"License created for user: {uid}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating license for {uid}: {e}", exc_info=True)
            return False
    
    def update_license(self, uid: str, license_data: dict) -> bool:
        """Update license."""
        if not self._ensure_initialized():
            return False
        
        try:
            # Validate tier if provided
            if "tier" in license_data:
                tier_key = license_data["tier"]
                tier_definition = self.get_tier_definition(tier_key)
                if not tier_definition:
                    logger.error(f"Invalid license tier: {tier_key}")
                    return False
            
            doc_ref = self._db.collection(FIRESTORE_USER_LICENSES_COLLECTION).document(uid)
            doc_ref.update(license_data)
            
            logger.info(f"License updated for user: {uid}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating license for {uid}: {e}", exc_info=True)
            return False
    
    def delete_license(self, uid: str) -> bool:
        """Delete license."""
        if not self._ensure_initialized():
            return False
        
        try:
            doc_ref = self._db.collection(FIRESTORE_USER_LICENSES_COLLECTION).document(uid)
            doc_ref.delete()
            
            logger.info(f"License deleted for user: {uid}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting license for {uid}: {e}", exc_info=True)
            return False
    
    def get_license_stats(self) -> dict:
        """Get license statistics."""
        licenses = self.get_all_licenses()
        
        stats = {
            "total": len(licenses),
            "by_tier": {},
            "active": 0,
            "expired": 0,
        }
        
        # Get tiers from Firestore or fallback to constants
        try:
            from admin.services.admin_license_tier_service import admin_license_tier_service
            tiers = admin_license_tier_service.get_all_tiers()
            tier_keys = [t.get("tier_key") for t in tiers if t.get("tier_key")]
        except Exception:
            tier_keys = LICENSE_TIERS  # Fallback
        
        # Initialize tier counts
        for tier in tier_keys:
            stats["by_tier"][tier] = 0
        
        now = datetime.utcnow()
        
        for license_data in licenses:
            tier = license_data.get("tier", "none")
            if tier in stats["by_tier"]:
                stats["by_tier"][tier] += 1
            
            # Check if expired
            expiration = license_data.get("expiration_date")
            if expiration:
                try:
                    if isinstance(expiration, str):
                        exp_date = datetime.fromisoformat(expiration.replace("Z", "+00:00"))
                    else:
                        exp_date = expiration
                    
                    if exp_date > now:
                        stats["active"] += 1
                    else:
                        stats["expired"] += 1
                except Exception:
                    # If we can't parse, assume active
                    stats["active"] += 1
            else:
                stats["active"] += 1
        
        return stats
    
    def get_user_devices(self, uid: str) -> List[str]:
        """Get user's active devices."""
        license_data = self.get_license(uid)
        if license_data:
            return license_data.get("active_devices", [])
        return []


# Global admin license service instance
admin_license_service = AdminLicenseService()

