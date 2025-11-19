"""
Utility functions for managing user-encrypted PIN storage and retrieval.
"""

import logging
from typing import Optional
from database.db_manager import DatabaseManager
from utils.pin_validator import encrypt_pin_with_user_id
from services.auth_service import auth_service

logger = logging.getLogger(__name__)


def get_or_create_user_encrypted_pin(db_manager: DatabaseManager) -> Optional[str]:
    """
    Get user-encrypted PIN from database, or create it if it doesn't exist.
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        User-encrypted PIN string, or None if PIN is not enabled or user not logged in
    """
    try:
        settings = db_manager.get_settings()
        
        # Check if PIN is enabled
        if not settings.pin_enabled or not settings.encrypted_pin:
            return None
        
        # Get current user
        current_user = auth_service.get_current_user()
        if not current_user:
            logger.warning("No user logged in, cannot encrypt PIN with user ID")
            return None
        
        user_id = current_user.get('uid')
        if not user_id:
            logger.warning("User ID not available")
            return None
        
        # If user-encrypted PIN already exists, return it
        if settings.user_encrypted_pin:
            return settings.user_encrypted_pin
        
        # Create user-encrypted PIN
        user_encrypted = encrypt_pin_with_user_id(settings.encrypted_pin, user_id)
        
        # Save to database
        settings.user_encrypted_pin = user_encrypted
        db_manager.update_settings(settings)
        
        logger.info("Created and saved user-encrypted PIN")
        return user_encrypted
        
    except Exception as e:
        logger.error(f"Error getting/creating user-encrypted PIN: {e}")
        return None


def update_user_encrypted_pin(db_manager: DatabaseManager) -> bool:
    """
    Update user-encrypted PIN in database (call when PIN changes).
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        settings = db_manager.get_settings()
        
        # Check if PIN is enabled
        if not settings.pin_enabled or not settings.encrypted_pin:
            # Clear user-encrypted PIN if PIN is disabled
            if settings.user_encrypted_pin:
                settings.user_encrypted_pin = None
                db_manager.update_settings(settings)
            return True
        
        # Get current user
        current_user = auth_service.get_current_user()
        if not current_user:
            logger.warning("No user logged in, cannot update user-encrypted PIN")
            return False
        
        user_id = current_user.get('uid')
        if not user_id:
            logger.warning("User ID not available")
            return False
        
        # Create new user-encrypted PIN
        user_encrypted = encrypt_pin_with_user_id(settings.encrypted_pin, user_id)
        
        # Save to database
        settings.user_encrypted_pin = user_encrypted
        db_manager.update_settings(settings)
        
        logger.info("Updated user-encrypted PIN")
        return True
        
    except Exception as e:
        logger.error(f"Error updating user-encrypted PIN: {e}")
        return False

