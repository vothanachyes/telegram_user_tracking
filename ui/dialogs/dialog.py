"""
Centralized dialog management for AlertDialogs.
Handles nested dialogs, confirmations, and simple dialogs with consistent patterns.
"""

import flet as ft
from typing import Callable, Optional, Any
from ui.theme import theme_manager


class DialogManager:
    """Manages AlertDialog creation and display with consistent patterns."""
    
    @staticmethod
    def _get_page_from_event(e: Any, fallback_page: Optional[ft.Page] = None) -> Optional[ft.Page]:
        """
        Extract page reference from event, control, or fallback.
        
        Args:
            e: Event object (may have page or control.page)
            fallback_page: Fallback page reference (e.g., self.page)
            
        Returns:
            Page reference or None if not found
        """
        # Try to get page from event directly
        if hasattr(e, 'page') and e.page:
            return e.page
        
        # Try to get page from event's control
        if hasattr(e, 'control') and hasattr(e.control, 'page') and e.control.page:
            return e.control.page
        
        # Use fallback if provided
        if fallback_page:
            return fallback_page
        
        # Last resort: try to walk up the control tree
        if hasattr(e, 'control'):
            control = e.control
            while control:
                if hasattr(control, 'page') and control.page:
                    return control.page
                control = getattr(control, 'parent', None)
        
        return None
    
    @staticmethod
    def show_confirmation_dialog(
        page: Optional[ft.Page],
        title: str,
        message: str,
        on_confirm: Callable,
        on_cancel: Optional[Callable] = None,
        confirm_text: Optional[str] = None,
        cancel_text: Optional[str] = None,
        confirm_color: str = ft.Colors.RED,
        main_dialog: Optional[ft.AlertDialog] = None,
        event: Optional[Any] = None
    ) -> bool:
        """
        Show a confirmation dialog, optionally nested within another dialog.
        
        Args:
            page: Page reference (can be None if event is provided)
            title: Dialog title
            message: Confirmation message
            on_confirm: Callback when user confirms (receives event)
            on_cancel: Optional callback when user cancels (receives event)
            confirm_text: Text for confirm button (default: "delete" or "yes")
            cancel_text: Text for cancel button (default: "cancel")
            confirm_color: Color for confirm button (default: RED)
            main_dialog: Optional main dialog to restore on cancel (for nested dialogs)
            event: Optional event object to extract page from
            
        Returns:
            True if dialog was shown, False otherwise
        """
        # Get page from event if not provided
        if not page and event:
            page = DialogManager._get_page_from_event(event)
        
        if not page:
            return False
        
        # Use theme manager for translations
        confirm_btn_text = confirm_text or theme_manager.t("delete") or "Delete"
        cancel_btn_text = cancel_text or theme_manager.t("cancel") or "Cancel"
        
        def handle_confirm(confirm_e):
            """Handle confirmation."""
            confirm_dialog.open = False
            page.update()
            on_confirm(confirm_e)
        
        def handle_cancel(cancel_e):
            """Handle cancellation."""
            # Close confirmation dialog
            confirm_dialog.open = False
            page.update()
            
            # Restore main dialog if provided (for nested dialogs)
            if main_dialog:
                # Use page.open() to restore the main dialog
                page.open(main_dialog)
            
            # Call custom cancel handler if provided
            if on_cancel:
                on_cancel(cancel_e)
        
        # Create confirmation dialog
        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton(cancel_btn_text, on_click=handle_cancel),
                ft.TextButton(
                    confirm_btn_text,
                    on_click=handle_confirm,
                    style=ft.ButtonStyle(color=confirm_color)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            elevation=24 if main_dialog else None,  # Higher elevation for nested dialogs
        )
        
        # Show dialog
        if main_dialog:
            # For nested dialogs, use page.open() which will replace the current dialog
            # Flet handles closing the previous dialog automatically
            page.open(confirm_dialog)
        else:
            # For standalone dialogs, use page.dialog
            page.dialog = confirm_dialog
            confirm_dialog.open = True
            page.update()
        
        return True
    
    @staticmethod
    def show_simple_dialog(
        page: Optional[ft.Page],
        title: str,
        message: str,
        actions: Optional[list] = None,
        event: Optional[Any] = None
    ) -> bool:
        """
        Show a simple info/error dialog.
        
        Args:
            page: Page reference (can be None if event is provided)
            title: Dialog title
            message: Dialog message
            actions: Optional list of action buttons (default: single "Close" button)
            event: Optional event object to extract page from
            
        Returns:
            True if dialog was shown, False otherwise
        """
        # Get page from event if not provided
        if not page and event:
            page = DialogManager._get_page_from_event(event)
        
        if not page:
            return False
        
        # Default actions if not provided
        if actions is None:
            close_text = theme_manager.t("close") or "Close"
            actions = [
                ft.TextButton(
                    close_text,
                    on_click=lambda e: setattr(dialog, 'open', False) or page.update()
                )
            ]
        
        # Create dialog
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        # Show dialog
        page.dialog = dialog
        dialog.open = True
        page.update()
        
        return True
    
    @staticmethod
    def show_custom_dialog(
        page: Optional[ft.Page],
        title: str,
        content: ft.Control,
        actions: Optional[list] = None,
        modal: bool = True,
        elevation: Optional[int] = None,
        event: Optional[Any] = None,
        main_dialog: Optional[ft.AlertDialog] = None
    ) -> Optional[ft.AlertDialog]:
        """
        Show a dialog with custom content and full control.
        
        Args:
            page: Page reference (can be None if event is provided)
            title: Dialog title (can be Control or str)
            content: Dialog content control
            actions: Optional list of action buttons
            modal: Whether dialog is modal (default: True)
            elevation: Optional elevation value
            event: Optional event object to extract page from
            
        Returns:
            Created AlertDialog instance or None if page not found
        """
        # Get page from event if not provided
        if not page and event:
            page = DialogManager._get_page_from_event(event)
        
        if not page:
            return None
        
        # Convert title to Text if it's a string
        if isinstance(title, str):
            title = ft.Text(title)
        
        # Use higher elevation for nested dialogs
        if main_dialog and elevation is None:
            elevation = 24
        
        # Create dialog
        dialog = ft.AlertDialog(
            modal=modal,
            title=title,
            content=content,
            actions=actions or [],
            actions_alignment=ft.MainAxisAlignment.END,
            elevation=elevation
        )
        
        # If main_dialog is provided, wrap actions to restore main dialog on close
        if main_dialog:
            def restore_main_dialog():
                """Helper to restore main dialog."""
                dialog.open = False
                page.dialog = main_dialog
                main_dialog.open = True
                page.update()
            
            # Wrap each action's on_click to restore main dialog
            if actions:
                for action in actions:
                    original_on_click = getattr(action, 'on_click', None)
                    if original_on_click:
                        # Use a factory function to avoid closure issues
                        def make_wrapper(orig_func):
                            def wrapper(e):
                                restore_main_dialog()
                                orig_func(e)
                            return wrapper
                        action.on_click = make_wrapper(original_on_click)
                    else:
                        # No handler, just restore main dialog
                        # Use a function to avoid closure issues
                        def make_restore_handler():
                            def handler(e):
                                restore_main_dialog()
                            return handler
                        action.on_click = make_restore_handler()
        
        # Show dialog
        page.dialog = dialog
        dialog.open = True
        page.update()
        
        return dialog
    
    @staticmethod
    def show_dialog(
        page: ft.Page,
        title: str,
        content: ft.Control,
        actions: Optional[list] = None
    ) -> None:
        """
        Show a dialog (backward compatibility method).
        
        Args:
            page: Page reference
            title: Dialog title
            content: Dialog content control
            actions: Optional list of action buttons
        """
        DialogManager.show_custom_dialog(
            page=page,
            title=title,
            content=content,
            actions=actions
        )


# Global dialog manager instance
dialog_manager = DialogManager()

