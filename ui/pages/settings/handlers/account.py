"""
Account management handlers for settings.
"""

import logging
import flet as ft
from ui.theme import theme_manager
from ui.pages.settings.handlers.base import BaseHandlerMixin

logger = logging.getLogger(__name__)


class AccountHandlerMixin(BaseHandlerMixin):
    """Handlers for account management."""
    
    def handle_remove_account(self, credential_id: int):
        """
        Handle account removal with activity limits and confirmation dialog.
        
        Args:
            credential_id: ID of the credential to remove
        """
        if not self.page:
            logger.error("Page not available for account removal")
            return
        
        # Get credential to get phone number for confirmation message
        credential = self.db_manager.get_credential_by_id(credential_id)
        if not credential:
            theme_manager.show_snackbar(
                self.page,
                "Account not found",
                bgcolor=ft.Colors.RED
            )
            return
        
        phone_number = credential.phone_number
        
        # Show confirmation dialog before deletion
        def on_confirm(e):
            """Handle confirmation - proceed with deletion."""
            logger.info(f"on_confirm called for credential_id: {credential_id}, phone: {phone_number}")
            
            try:
                # Get current user email
                auth_service = self._get_auth_service()
                if not auth_service:
                    logger.error("Auth service not available in on_confirm")
                    theme_manager.show_snackbar(
                        self.page,
                        "Authentication service not available",
                        bgcolor=ft.Colors.RED
                    )
                    return
                
                user_email = auth_service.get_user_email()
                logger.info(f"User email from auth_service: {user_email}")
                
                # Check activity limits only if user is logged in
                if user_email:
                    logger.info(f"User email: {user_email}, checking activity limits")
                    can_perform, error_msg = self._check_account_activity_limit(user_email)
                    if not can_perform:
                        logger.warning(f"Activity limit reached: {error_msg}")
                        theme_manager.show_snackbar(
                            self.page,
                            error_msg or theme_manager.t("account_deletion_limit_reached"),
                            bgcolor=ft.Colors.RED
                        )
                        return
                else:
                    logger.warning("User email not available - proceeding with deletion without activity limit check")
                
                # Delete session file from disk
                try:
                    from pathlib import Path
                    if credential.session_string:
                        session_path = Path(credential.session_string)
                        if session_path.exists():
                            session_path.unlink()
                            # Also delete journal file if exists
                            journal_path = session_path.with_suffix(session_path.suffix + '-journal')
                            if journal_path.exists():
                                journal_path.unlink()
                            logger.info(f"Deleted session file: {session_path}")
                except Exception as e:
                    logger.error(f"Error deleting session file: {e}", exc_info=True)
                    # Continue with deletion even if file deletion fails
                
                # Delete credential from database
                logger.info(f"Deleting credential from database: {credential_id}")
                success = self.db_manager.delete_telegram_credential(credential_id)
                if not success:
                    logger.error(f"Failed to delete credential {credential_id} from database")
                    theme_manager.show_snackbar(
                        self.page,
                        "Failed to delete account",
                        bgcolor=ft.Colors.RED
                    )
                    return
                
                logger.info(f"Successfully deleted credential {credential_id} from database")
                
                # Log deletion in activity log (only if user is logged in)
                if user_email:
                    try:
                        self.db_manager.log_account_action(
                            user_email=user_email,
                            action='delete',
                            phone_number=phone_number
                        )
                        logger.info(f"Logged account deletion action for {phone_number}")
                    except Exception as e:
                        logger.error(f"Error logging account deletion: {e}", exc_info=True)
                        # Continue even if logging fails
                else:
                    logger.info("Skipping activity log - user not logged in")
                
                # Show success message
                theme_manager.show_snackbar(
                    self.page,
                    f"Account {phone_number} removed successfully",
                    bgcolor=ft.Colors.GREEN
                )
                
                # Update authenticate tab if available
                if hasattr(self, 'authenticate_tab') and self.authenticate_tab:
                    logger.info("Updating accounts list in authenticate tab")
                    self.authenticate_tab.update_accounts_list()
                
                # Update page
                if self.page:
                    self.page.update()
                    logger.info("Page updated after account removal")
            except Exception as ex:
                logger.error(f"Error in on_confirm callback: {ex}", exc_info=True)
                theme_manager.show_snackbar(
                    self.page,
                    f"Error removing account: {str(ex)}",
                    bgcolor=ft.Colors.RED
                )
        
        def on_cancel(e):
            """Handle cancellation - do nothing."""
            pass
        
        # Show confirmation dialog using page.open() method
        from ui.dialogs.dialog import DialogManager
        confirm_title = theme_manager.t("confirm_removal") or "Confirm Removal"
        confirm_message = theme_manager.t("confirm_remove_account_message") or f"Are you sure you want to remove account {phone_number}? This action cannot be undone."
        
        # Use DialogManager to show confirmation dialog
        DialogManager.show_confirmation_dialog(
            page=self.page,
            title=confirm_title,
            message=confirm_message,
            on_confirm=on_confirm,
            on_cancel=on_cancel,
            confirm_text=theme_manager.t("remove") or "Remove",
            cancel_text=theme_manager.t("cancel") or "Cancel",
            confirm_color=ft.Colors.RED
        )
    
    def handle_add_account(self, e=None):
        """
        Handle add account button click.
        Shows add account dialog and handles account addition flow.
        
        Args:
            e: Optional event object (can be used to get page reference)
        """
        logger.info("=== handle_add_account() called ===")
        logger.info(f"Event provided: {e is not None}")
        logger.info(f"self.page available: {self.page is not None}")
        
        # Try to get page from event if self.page is not available
        page = self.page
        if not page and e:
            logger.debug("Attempting to get page from event")
            if hasattr(e, 'page') and e.page:
                page = e.page
                logger.info("Got page from e.page")
            elif hasattr(e, 'control') and hasattr(e.control, 'page') and e.control.page:
                page = e.control.page
                logger.info("Got page from e.control.page")
        
        if not page:
            logger.error("Page not available for adding account - handler exiting early")
            return
        
        logger.info(f"Page reference obtained: {page is not None}")
        
        # Get current user email and uid for license check
        logger.info("Getting auth service...")
        auth_service = self._get_auth_service()
        if not auth_service:
            logger.error("Auth service not available - returning early")
            theme_manager.show_snackbar(
                page,
                "Authentication service not available. Please restart the application.",
                bgcolor=ft.Colors.RED
            )
            return
        
        # Check if auth service is initialized
        if not hasattr(auth_service, 'get_current_user'):
            logger.error("Auth service does not have get_current_user method")
            theme_manager.show_snackbar(
                page,
                "Authentication service is not properly initialized. Please restart the application.",
                bgcolor=ft.Colors.RED
            )
            return
        
        # Check license limit before opening dialog
        try:
            current_user = auth_service.get_current_user()
        except Exception as e:
            logger.error(f"Error getting current user: {e}", exc_info=True)
            theme_manager.show_snackbar(
                page,
                "Error checking authentication status. Please try again or restart the application.",
                bgcolor=ft.Colors.RED
            )
            return
        
        if not current_user:
            logger.warning("Current user not available - user may not be logged in")
            # Show a more visible error message using dialog
            from ui.dialogs.dialog import DialogManager
            DialogManager.show_simple_dialog(
                page=page,
                title=theme_manager.t("error") or "Error",
                message="You are not logged in. Please log in to add Telegram accounts.\n\nThis feature requires authentication to verify your license and account limits."
            )
            return
        
        user_email = current_user.get('email')
        uid = current_user.get('uid')
        
        if not user_email or not uid:
            logger.error(f"User information incomplete - email: {user_email is not None}, uid: {uid is not None}")
            theme_manager.show_snackbar(
                page,
                "User information not available. Please log in again.",
                bgcolor=ft.Colors.RED
            )
            return
        
        # Check license limit
        logger.info(f"Checking license limit for user: {user_email}")
        from services.license_service import LicenseService
        license_service = LicenseService(self.db_manager, auth_service)
        can_add, error_msg, current_count, max_count = license_service.can_add_account(user_email, uid)
        
        if not can_add:
            logger.warning(f"License limit reached - current: {current_count}, max: {max_count}")
            theme_manager.show_snackbar(
                page,
                error_msg or theme_manager.t("account_limit_reached").format(current=current_count, max=max_count),
                bgcolor=ft.Colors.RED
            )
            return
        
        # Check activity limits
        can_perform, activity_error = self._check_account_activity_limit(user_email)
        if not can_perform:
            theme_manager.show_snackbar(
                page,
                activity_error or theme_manager.t("account_addition_limit_reached"),
                bgcolor=ft.Colors.RED
            )
            return
        
        logger.info("Creating AddAccountDialog...")
        # Show add account dialog
        from ui.dialogs.add_account_dialog import AddAccountDialog
        
        def on_success(phone: str):
            """Handle successful account addition."""
            logger.info(f"Account {phone} added successfully")
            # Refresh accounts list
            if self.authenticate_tab:
                self.authenticate_tab.update_accounts_list()
                self.authenticate_tab._update_account_count()
            # Show success message
            theme_manager.show_snackbar(
                page,
                theme_manager.t("account_added_successfully") or f"Account {phone} added successfully",
                bgcolor=ft.Colors.GREEN
            )
        
        def on_cancel():
            """Handle dialog cancellation."""
            pass
        
        dialog = AddAccountDialog(
            telegram_service=self.telegram_service,
            db_manager=self.db_manager,
            on_success=on_success,
            on_cancel=on_cancel
        )
        
        # Set page reference on dialog
        dialog.page = page
        logger.debug(f"AddAccountDialog created, page reference set: {dialog.page is not None}")
        logger.debug(f"Page ID: {getattr(page, 'id', 'unknown')}, Page type: {type(page)}")
        
        # Check if a dialog is already open - if so, don't open another one
        if hasattr(page, 'dialog') and page.dialog and hasattr(page.dialog, 'open') and page.dialog.open:
            logger.warning("Dialog already open, skipping AddAccountDialog")
            return
        
        # Open dialog using page.open() method (same as telegram_page.py and user_dashboard_page.py)
        # This is the preferred Flet method for opening dialogs
        try:
            logger.info("Opening AddAccountDialog using page.open() method")
            page.open(dialog)
            logger.info("AddAccountDialog opened successfully using page.open()")
        except Exception as dialog_error:
            logger.error(f"Error opening AddAccountDialog with page.open(): {dialog_error}", exc_info=True)
            # Fallback: try page.dialog method
            try:
                logger.debug("Trying page.dialog as fallback")
                page.dialog = dialog
                dialog.open = True
                page.update()
                logger.info("AddAccountDialog opened using page.dialog fallback")
            except Exception as fallback_error:
                logger.error(f"Failed to open dialog even with fallback: {fallback_error}", exc_info=True)
                theme_manager.show_snackbar(
                    page,
                    "Failed to open add account dialog",
                    bgcolor=ft.Colors.RED
                )

