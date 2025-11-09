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
            (can_perform, error_message_with_waiting_time)
        """
        if not user_email:
            return False, "User email not available"
        
        try:
            # Get max_account_actions from license
            from services.license.license_checker import LicenseChecker
            auth_service = self._get_auth_service()
            license_checker = LicenseChecker(self.db_manager, auth_service)
            license_status = license_checker.check_license_status(user_email)
            max_actions = license_status.get('max_account_actions', 2)
            
            # Check if user can perform action
            can_perform = self.db_manager.can_perform_account_action(user_email, max_actions=max_actions)
            if not can_perform:
                # Get waiting time
                waiting_hours = self.db_manager.get_waiting_time_hours(user_email, max_actions=max_actions)
                
                if waiting_hours:
                    # Format waiting time
                    if waiting_hours < 1:
                        waiting_text = f"{int(waiting_hours * 60)} minutes"
                    elif waiting_hours < 24:
                        waiting_text = f"{int(waiting_hours)} hours"
                    else:
                        days = int(waiting_hours / 24)
                        hours = int(waiting_hours % 24)
                        if hours > 0:
                            waiting_text = f"{days} days {hours} hours"
                        else:
                            waiting_text = f"{days} days"
                    
                    error_msg = theme_manager.t("account_action_limit_reached_with_wait") or \
                        f"Account action limit reached. Please wait {waiting_text} before adding or deleting accounts."
                    return False, error_msg.format(waiting_time=waiting_text)
                else:
                    return False, theme_manager.t("account_deletion_limit_reached") or "Account action limit reached."
            
            return True, None
        except Exception as e:
            logger.error(f"Error checking account activity limit: {e}")
            return False, f"Error checking limit: {str(e)}"

