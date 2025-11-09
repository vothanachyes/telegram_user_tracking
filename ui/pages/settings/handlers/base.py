"""
Base utilities for settings handlers.
"""

import logging
from typing import Optional, Tuple
import flet as ft
from ui.theme import theme_manager

logger = logging.getLogger(__name__)


class BaseHandlerMixin:
    """Base mixin with common utility methods."""
    
    def _show_error(self, message: str, error_text_control: ft.Text):
        """Show error message."""
        error_text_control.value = message
        error_text_control.visible = True
        if self.page:
            self.page.update()
    
    def _get_auth_service(self):
        """Get auth service instance."""
        try:
            from services.auth_service import auth_service
            return auth_service
        except ImportError:
            logger.error("Failed to import auth_service")
            return None
    
    def _check_account_activity_limit(self, user_email: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user can perform account action (add/delete).
        
        Args:
            user_email: Email of the user
            
        Returns:
            (can_perform, error_message)
        """
        if not user_email:
            return False, "User email not available"
        
        try:
            can_perform = self.db_manager.can_perform_account_action(user_email)
            if not can_perform:
                return False, theme_manager.t("account_deletion_limit_reached")
            return True, None
        except Exception as e:
            logger.error(f"Error checking account activity limit: {e}")
            return False, f"Error checking limit: {str(e)}"

