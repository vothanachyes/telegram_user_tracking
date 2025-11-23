"""
Admin license tier management service.
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from admin.config.admin_config import admin_config
from admin.utils.constants import FIRESTORE_LICENSE_TIERS_COLLECTION

logger = logging.getLogger(__name__)


class AdminLicenseTierService:
    """Handles license tier CRUD operations."""
    
    def __init__(self):
        self._db = None
    
    def _ensure_initialized(self) -> bool:
        """Ensure Firebase is initialized."""
        if not admin_config.is_initialized():
            if not admin_config.initialize():
                return False
        self._db = admin_config.get_firestore()
        return self._db is not None
    
    def get_all_tiers(self) -> List[dict]:
        """Get all license tier definitions from Firestore."""
        if not self._ensure_initialized():
            return []
        
        try:
            tiers = []
            docs = self._db.collection(FIRESTORE_LICENSE_TIERS_COLLECTION).stream()
            
            for doc in docs:
                data = doc.to_dict()
                data["tier_key"] = doc.id
                tiers.append(data)
            
            # Sort by tier_key for consistent ordering
            tiers.sort(key=lambda x: x.get("tier_key", ""))
            
            logger.info(f"Retrieved {len(tiers)} license tiers")
            return tiers
            
        except Exception as e:
            logger.error(f"Error getting all license tiers: {e}", exc_info=True)
            return []
    
    def get_tier(self, tier_key: str) -> Optional[dict]:
        """Get specific tier definition by key."""
        if not self._ensure_initialized():
            return None
        
        try:
            doc_ref = self._db.collection(FIRESTORE_LICENSE_TIERS_COLLECTION).document(tier_key)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data["tier_key"] = tier_key
                return data
            return None
            
        except Exception as e:
            logger.error(f"Error getting license tier {tier_key}: {e}", exc_info=True)
            return None
    
    def create_tier(self, tier_key: str, tier_data: dict) -> bool:
        """Create new license tier."""
        if not self._ensure_initialized():
            return False
        
        try:
            # Validate tier key format
            if not self._validate_tier_key(tier_key):
                logger.error(f"Invalid tier key format: {tier_key}")
                return False
            
            # Check if tier already exists
            existing = self.get_tier(tier_key)
            if existing:
                logger.error(f"Tier {tier_key} already exists")
                return False
            
            # Validate tier data
            if not self._validate_tier_data(tier_data):
                return False
            
            # Set metadata
            tier_data["tier_key"] = tier_key
            tier_data["created_at"] = datetime.utcnow().isoformat() + "Z"
            tier_data["updated_at"] = datetime.utcnow().isoformat() + "Z"
            
            # Ensure features is a list
            if "features" in tier_data and isinstance(tier_data["features"], str):
                tier_data["features"] = [f.strip() for f in tier_data["features"].split(",") if f.strip()]
            elif "features" not in tier_data:
                tier_data["features"] = []
            
            doc_ref = self._db.collection(FIRESTORE_LICENSE_TIERS_COLLECTION).document(tier_key)
            doc_ref.set(tier_data)
            
            logger.info(f"License tier created: {tier_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating license tier {tier_key}: {e}", exc_info=True)
            return False
    
    def update_tier(self, tier_key: str, tier_data: dict) -> bool:
        """Update license tier."""
        if not self._ensure_initialized():
            return False
        
        try:
            # Check if tier exists
            existing = self.get_tier(tier_key)
            if not existing:
                logger.error(f"Tier {tier_key} does not exist")
                return False
            
            # Validate tier data
            if not self._validate_tier_data(tier_data):
                return False
            
            # Don't update tier_key in data (it's the document ID)
            if "tier_key" in tier_data:
                del tier_data["tier_key"]
            
            # Update metadata
            tier_data["updated_at"] = datetime.utcnow().isoformat() + "Z"
            
            # Ensure features is a list
            if "features" in tier_data and isinstance(tier_data["features"], str):
                tier_data["features"] = [f.strip() for f in tier_data["features"].split(",") if f.strip()]
            
            doc_ref = self._db.collection(FIRESTORE_LICENSE_TIERS_COLLECTION).document(tier_key)
            doc_ref.update(tier_data)
            
            logger.info(f"License tier updated: {tier_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating license tier {tier_key}: {e}", exc_info=True)
            return False
    
    def delete_tier(self, tier_key: str) -> bool:
        """Delete license tier."""
        if not self._ensure_initialized():
            return False
        
        try:
            # Check if tier exists
            existing = self.get_tier(tier_key)
            if not existing:
                logger.error(f"Tier {tier_key} does not exist")
                return False
            
            # Check if tier has active licenses (optional validation)
            # This could be done in the UI layer instead
            
            doc_ref = self._db.collection(FIRESTORE_LICENSE_TIERS_COLLECTION).document(tier_key)
            doc_ref.delete()
            
            logger.info(f"License tier deleted: {tier_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting license tier {tier_key}: {e}", exc_info=True)
            return False
    
    def get_tiers_in_use_count(self, tier_key: str) -> int:
        """Get count of user licenses using this tier."""
        try:
            from admin.services.admin_license_service import admin_license_service
            licenses = admin_license_service.get_all_licenses()
            count = sum(1 for lic in licenses if lic.get("tier") == tier_key)
            return count
        except Exception as e:
            logger.error(f"Error counting licenses for tier {tier_key}: {e}")
            return 0
    
    def sync_tiers_from_constants(self) -> bool:
        """
        Sync license tiers from constants.py to Firestore.
        Note: This method is deprecated as license tiers are now managed in the admin app.
        Returns False as constants no longer exist.
        """
        logger.warning("sync_tiers_from_constants() is deprecated - license tiers are now managed in the admin app")
        return False
    
    def update_existing_licenses(self, tier_key: str, tier_data: dict) -> int:
        """Update all user licenses using this tier with new tier values."""
        if not self._ensure_initialized():
            return 0
        
        try:
            from admin.services.admin_license_service import admin_license_service
            licenses = admin_license_service.get_all_licenses()
            
            updated_count = 0
            for license_data in licenses:
                if license_data.get("tier") == tier_key:
                    # Update license with new tier values
                    update_data = {
                        "max_groups": tier_data.get("max_groups", license_data.get("max_groups")),
                        "max_devices": tier_data.get("max_devices", license_data.get("max_devices")),
                        "max_accounts": tier_data.get("max_accounts", license_data.get("max_accounts")),
                    }
                    
                    uid = license_data.get("uid")
                    if uid and admin_license_service.update_license(uid, update_data):
                        updated_count += 1
            
            logger.info(f"Updated {updated_count} licenses for tier {tier_key}")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating existing licenses for tier {tier_key}: {e}", exc_info=True)
            return 0
    
    def _validate_tier_key(self, tier_key: str) -> bool:
        """Validate tier key format (lowercase, alphanumeric, underscores only)."""
        if not tier_key:
            return False
        pattern = r'^[a-z0-9_]+$'
        return bool(re.match(pattern, tier_key))
    
    def sync_tiers_to_json(self, json_path: Optional[str] = None) -> bool:
        """
        Sync all license tiers from Firebase to JSON file.
        
        Args:
            json_path: Path to JSON file (defaults to admin/config/licence_teir_init.json)
        
        Returns:
            True if successful, False otherwise
        """
        if not self._ensure_initialized():
            logger.error("Firebase not initialized")
            return False
        
        try:
            # Get all tiers from Firebase
            tiers = self.get_all_tiers()
            
            # Determine JSON file path
            if json_path is None:
                # Get admin config directory
                admin_config_dir = Path(__file__).parent.parent / "config"
                json_path = admin_config_dir / "licence_teir_init.json"
            else:
                json_path = Path(json_path)
            
            # Prepare data for JSON export
            sync_date = datetime.utcnow().isoformat() + "Z"
            tiers_data = []
            
            for tier in tiers:
                tier_export = {
                    "tier_key": tier.get("tier_key", ""),
                    "name": tier.get("name", ""),
                    "price_usd": tier.get("price_usd", 0),
                    "price_khr": tier.get("price_khr", 0),
                    "max_groups": tier.get("max_groups", 1),
                    "max_devices": tier.get("max_devices", 1),
                    "max_accounts": tier.get("max_accounts", 1),
                    "period": tier.get("period", 30),
                    "features": tier.get("features", []),
                    "created_at": tier.get("created_at", ""),
                    "modified_date": tier.get("updated_at", tier.get("modified_date", "")),
                }
                tiers_data.append(tier_export)
            
            # Create JSON structure
            json_data = {
                "sync_date": sync_date,
                "tiers": tiers_data
            }
            
            # Ensure directory exists
            json_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to JSON file
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Synced {len(tiers_data)} license tiers to {json_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing tiers to JSON: {e}", exc_info=True)
            return False
    
    def _validate_tier_data(self, tier_data: dict) -> bool:
        """Validate tier data fields."""
        # Required fields
        if "name" not in tier_data or not tier_data["name"]:
            logger.error("Tier name is required")
            return False
        
        # Validate numeric fields
        numeric_fields = ["price_usd", "price_khr", "max_groups", "max_devices", "max_accounts", "period"]
        for field in numeric_fields:
            if field in tier_data:
                try:
                    value = float(tier_data[field])
                    if field in ["price_usd", "price_khr"]:
                        if value < 0:
                            logger.error(f"{field} must be >= 0")
                            return False
                    elif field in ["max_groups", "max_devices", "max_accounts"]:
                        if value < -1:
                            logger.error(f"{field} must be >= -1 (where -1 means unlimited)")
                            return False
                    elif field == "period":
                        if value <= 0:
                            logger.error(f"{field} must be > 0")
                            return False
                except (ValueError, TypeError):
                    logger.error(f"{field} must be a valid number")
                    return False
        
        return True


# Global admin license tier service instance
admin_license_tier_service = AdminLicenseTierService()

