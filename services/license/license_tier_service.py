"""
License tier service for fetching tier definitions from Firestore.
"""

import logging
from typing import List, Optional, Dict
from config.firebase_config import firebase_config

logger = logging.getLogger(__name__)


class LicenseTierService:
    """Handles license tier retrieval from Firestore."""
    
    def __init__(self):
        self._tiers_cache: Optional[List[dict]] = None
    
    def get_all_tiers(self, use_cache: bool = True) -> List[dict]:
        """
        Get all license tier definitions from Firestore.
        
        Args:
            use_cache: Whether to use cached tiers (default: True)
        
        Returns:
            List of tier definition dictionaries
        """
        # Return cached tiers if available and cache is enabled
        if use_cache and self._tiers_cache is not None:
            return self._tiers_cache
        
        try:
            tiers = firebase_config.get_license_tiers()
            
            # Filter out "custom" tier (not shown in pricing)
            tiers = [tier for tier in tiers if tier.get("tier_key") != "custom"]
            
            # Cache the result
            self._tiers_cache = tiers
            
            logger.info(f"Retrieved {len(tiers)} license tiers from Firestore")
            return tiers
            
        except Exception as e:
            logger.error(f"Error getting license tiers: {e}", exc_info=True)
            return []
    
    def get_tier(self, tier_key: str) -> Optional[dict]:
        """
        Get specific tier definition by key.
        
        Args:
            tier_key: Tier key (e.g., "bronze", "silver", "gold", "premium", "custom")
        
        Returns:
            Tier definition dictionary if found, None otherwise
        """
        # Handle "custom" tier - no definition needed
        if tier_key == "custom":
            return None
        
        try:
            tier = firebase_config.get_license_tier(tier_key)
            if tier:
                logger.debug(f"Retrieved license tier {tier_key} from Firestore")
                return tier
            return None
            
        except Exception as e:
            logger.error(f"Error getting license tier {tier_key}: {e}", exc_info=True)
            return None
    
    def clear_cache(self):
        """Clear the tiers cache."""
        self._tiers_cache = None


# Global license tier service instance
license_tier_service = LicenseTierService()

