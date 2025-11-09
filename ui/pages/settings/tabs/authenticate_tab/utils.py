"""
Utility methods for authenticate tab.
"""

from ui.theme import theme_manager


class AuthenticateTabUtils:
    """Utility methods for authenticate tab."""
    
    @staticmethod
    def get_api_status_text(current_settings) -> str:
        """Get API App status text."""
        if current_settings.telegram_api_id and current_settings.telegram_api_hash:
            return theme_manager.t("api_app_configured")
        return theme_manager.t("api_app_not_configured")
    
    @staticmethod
    def get_account_status_text(telegram_service, db_manager) -> str:
        """Get account connection status text."""
        if not telegram_service:
            return theme_manager.t("account_not_connected")
        
        if telegram_service.is_connected():
            credential = db_manager.get_default_credential()
            if credential:
                return f"{theme_manager.t('account_connected')} ({credential.phone_number})"
            return theme_manager.t("account_connected")
        return theme_manager.t("account_not_connected")
    
    @staticmethod
    def get_status_text(status: str) -> str:
        """Get localized status text."""
        status_map = {
            'active': theme_manager.t("account_status_active"),
            'expired': theme_manager.t("account_status_expired"),
            'not_connected': theme_manager.t("account_status_not_available"),
            'error': theme_manager.t("account_status_not_available")
        }
        return status_map.get(status, status)
    
    @staticmethod
    def handle_phone_change(phone_input, page):
        """Handle phone number input change - remove leading zero."""
        if phone_input.value and phone_input.value.startswith("0"):
            # Remove leading zero
            phone_input.value = phone_input.value.lstrip("0")
            if page:
                page.update()

