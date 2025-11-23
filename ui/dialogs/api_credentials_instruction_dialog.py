"""
Dialog showing instructions for obtaining Telegram API credentials.
"""

import flet as ft
import logging
from typing import Optional, Callable
from ui.theme import theme_manager

logger = logging.getLogger(__name__)


class APICredentialsInstructionDialog(ft.AlertDialog):
    """Dialog displaying instructions for getting API ID and API Hash from Telegram."""
    
    def __init__(self, on_close: Optional[Callable[[], None]] = None):
        """Initialize the API credentials instruction dialog."""
        super().__init__()
        
        # Markdown content with instructions
        instruction_content = f"""# {theme_manager.t("how_to_get_api_credentials")}

## {theme_manager.t("step_1")}: {theme_manager.t("visit_telegram_apps")}

Visit [https://my.telegram.org/apps](https://my.telegram.org/apps) in your web browser.

## {theme_manager.t("step_2")}: {theme_manager.t("log_in_to_telegram")}

Log in using your phone number and the verification code sent to your Telegram app.

## {theme_manager.t("step_3")}: {theme_manager.t("create_new_application")}

1. Click on **"API development tools"** or **"Create new application"**
2. Fill in the required information:
   - **App title**: Enter any name (e.g., "My App")
   - **Short name**: Enter a short identifier (e.g., "myapp")
   - **Platform**: Select "Desktop"
   - **Description**: Optional description

## {theme_manager.t("step_4")}: {theme_manager.t("copy_credentials")}

After creating the application, you will see:
- **api_id**: A numeric ID (e.g., 12345678)
- **api_hash**: A long alphanumeric string

Copy both values and paste them into the fields above.

---

**Note**: Keep your API credentials secure and never share them publicly.
"""
        
        # Create markdown widget
        markdown_content = ft.Markdown(
            instruction_content,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            code_theme="atom-one-dark",
            selectable=True,
        )
        
        # Create scrollable container for content
        content_container = ft.Container(
            content=ft.Column(
                [
                    markdown_content,
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            width=600,
            height=500,
            padding=20,
            alignment=ft.alignment.top_left,
        )
        
        # Create dialog
        super().__init__(
            modal=True,
            title=ft.Text(
                theme_manager.t("api_credentials_instructions") or "How to Get API Credentials",
                weight=ft.FontWeight.BOLD,
            ),
            content=content_container,
            actions=[
                ft.TextButton(
                    theme_manager.t("close") or "Close",
                    on_click=self._handle_close,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.on_close = on_close
    
    def _handle_close(self, e):
        """Handle close button click."""
        if self.on_close:
            self.on_close()
        
        # Close dialog
        if hasattr(self, 'page') and self.page:
            try:
                # Use page.close() if available, otherwise set open=False
                if hasattr(self.page, 'close'):
                    self.page.close(self)
                else:
                    self.open = False
                    self.page.update()
            except Exception as ex:
                logger.error(f"Error closing dialog: {ex}")
                # Fallback
                self.open = False
                if hasattr(self, 'page') and self.page:
                    self.page.update()

