"""
Admin app update management service.
"""

import logging
from typing import Optional, Dict
from datetime import datetime
from admin.config.admin_config import admin_config
from admin.utils.constants import (
    FIRESTORE_APP_UPDATES_COLLECTION,
    FIRESTORE_APP_UPDATES_DOCUMENT
)

logger = logging.getLogger(__name__)


class AdminAppUpdateService:
    """Handles app update management."""
    
    def __init__(self):
        self._db = None
    
    def _ensure_initialized(self) -> bool:
        """Ensure Firebase is initialized."""
        if not admin_config.is_initialized():
            if not admin_config.initialize():
                return False
        self._db = admin_config.get_firestore()
        return self._db is not None
    
    def get_app_update_info(self) -> Optional[dict]:
        """Get current app update info."""
        if not self._ensure_initialized():
            return None
        
        try:
            doc_ref = self._db.collection(FIRESTORE_APP_UPDATES_COLLECTION).document(
                FIRESTORE_APP_UPDATES_DOCUMENT
            )
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Error getting app update info: {e}", exc_info=True)
            return None
    
    def update_app_update_info(self, update_data: dict) -> bool:
        """Update app update info."""
        if not self._ensure_initialized():
            return False
        
        try:
            # Validate required fields
            if "version" not in update_data:
                logger.error("Version is required")
                return False
            
            # Set release_date if not provided
            if "release_date" not in update_data:
                update_data["release_date"] = datetime.utcnow().isoformat() + "Z"
            
            # Ensure is_available is boolean
            if "is_available" in update_data:
                update_data["is_available"] = bool(update_data["is_available"])
            else:
                update_data["is_available"] = True
            
            doc_ref = self._db.collection(FIRESTORE_APP_UPDATES_COLLECTION).document(
                FIRESTORE_APP_UPDATES_DOCUMENT
            )
            doc_ref.set(update_data, merge=True)
            
            logger.info(f"App update info updated: version={update_data.get('version')}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating app update info: {e}", exc_info=True)
            return False
    
    def set_update_status(self, is_available: bool) -> bool:
        """Enable/disable updates."""
        if not self._ensure_initialized():
            return False
        
        try:
            doc_ref = self._db.collection(FIRESTORE_APP_UPDATES_COLLECTION).document(
                FIRESTORE_APP_UPDATES_DOCUMENT
            )
            doc_ref.update({"is_available": is_available})
            
            logger.info(f"Update status set to: {is_available}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting update status: {e}", exc_info=True)
            return False


# Global admin app update service instance
admin_app_update_service = AdminAppUpdateService()

