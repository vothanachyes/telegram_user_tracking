"""
Update tab content for about page.
"""

import flet as ft
import asyncio
import logging
from pathlib import Path
from typing import Optional
from ui.theme import theme_manager
from utils.constants import APP_VERSION
from services.update_service import UpdateService

logger = logging.getLogger(__name__)


class UpdateTab:
    """Update tab component."""
    
    def __init__(
        self,
        update_service: Optional[UpdateService] = None,
        page: Optional[ft.Page] = None
    ):
        self.update_service = update_service
        self.page = page
        self._update_info: Optional[dict] = None
        self._is_checking = False
        self._is_downloading = False
        
        # UI components
        self.current_version_text = ft.Text(
            f"Current Version: {APP_VERSION}",
            size=theme_manager.font_size_body,
            weight=ft.FontWeight.BOLD
        )
        
        self.update_status_text = ft.Text(
            "",
            size=theme_manager.font_size_body,
            color=theme_manager.text_secondary_color
        )
        
        self.update_info_text = ft.Text(
            "",
            size=theme_manager.font_size_body,
            color=theme_manager.text_secondary_color
        )
        
        self.check_button = theme_manager.create_button(
            text="Check for Updates",
            icon=ft.Icons.UPDATE,
            on_click=self._on_check_updates,
            style="primary"
        )
        
        self.download_button = theme_manager.create_button(
            text="Download Update",
            icon=ft.Icons.DOWNLOAD,
            on_click=self._on_download_update,
            style="success",
            visible=False
        )
        
        self.install_button = theme_manager.create_button(
            text="Install Update",
            icon=ft.Icons.INSTALL_DESKTOP,
            on_click=self._on_install_update,
            style="success",
            visible=False
        )
        
        self.loading_indicator = ft.ProgressRing(
            width=20,
            height=20,
            visible=False
        )
    
    def set_page(self, page: ft.Page):
        """Set page reference."""
        self.page = page
    
    def set_update_service(self, update_service: UpdateService):
        """Set update service reference."""
        self.update_service = update_service
    
    def build(self) -> ft.Container:
        """Build Update tab content."""
        return ft.Container(
            content=ft.Column([
                # Current version card
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Text(
                            "App Version",
                            size=theme_manager.font_size_section_title,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        self.current_version_text,
                    ], spacing=theme_manager.spacing_sm)
                ),
                
                # Update status card
                theme_manager.create_card(
                    content=ft.Column([
                        ft.Text(
                            "Update Status",
                            size=theme_manager.font_size_section_title,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        ft.Row([
                            self.update_status_text,
                            self.loading_indicator,
                        ], spacing=10),
                        self.update_info_text,
                        ft.Row([
                            self.check_button,
                            self.download_button,
                            self.install_button,
                        ], spacing=10, wrap=False),
                    ], spacing=theme_manager.spacing_sm)
                ),
            ], scroll=ft.ScrollMode.AUTO, spacing=theme_manager.spacing_lg),
            padding=theme_manager.padding_lg,
            expand=True
        )
    
    async def _on_check_updates(self, e):
        """Handle check for updates button click."""
        if not self.update_service:
            self._show_error("Update service not available")
            return
        
        if self._is_checking:
            return
        
        self._is_checking = True
        self.check_button.disabled = True
        self.loading_indicator.visible = True
        self.update_status_text.value = "Checking for updates..."
        self.update_status_text.color = theme_manager.text_secondary_color
        
        if self.page:
            self.page.update()
        
        try:
            # Check for updates
            update_info = await self.update_service.check_for_updates()
            
            if update_info:
                version = update_info.get('version')
                download_path = update_info.get('download_path')
                update_info_data = update_info.get('update_info', {})
                
                self._update_info = update_info
                
                if download_path:
                    # Update already downloaded
                    self.update_status_text.value = f"Update {version} ready to install!"
                    self.update_status_text.color = ft.Colors.GREEN
                    self.update_info_text.value = self._format_update_info(update_info_data)
                    self.install_button.visible = True
                    self.download_button.visible = False
                else:
                    # Update available but not downloaded
                    self.update_status_text.value = f"Update {version} available!"
                    self.update_status_text.color = ft.Colors.ORANGE
                    self.update_info_text.value = self._format_update_info(update_info_data)
                    self.download_button.visible = True
                    self.install_button.visible = False
            else:
                # No update available
                self.update_status_text.value = "You are using the latest version"
                self.update_status_text.color = ft.Colors.GREEN
                self.update_info_text.value = ""
                self.download_button.visible = False
                self.install_button.visible = False
                
        except Exception as ex:
            logger.error(f"Error checking for updates: {ex}", exc_info=True)
            self._show_error(f"Error checking for updates: {str(ex)}")
        finally:
            self._is_checking = False
            self.check_button.disabled = False
            self.loading_indicator.visible = False
            if self.page:
                self.page.update()
    
    async def _on_download_update(self, e):
        """Handle download update button click."""
        if not self.update_service or not self._update_info:
            self._show_error("Update info not available")
            return
        
        if self._is_downloading:
            return
        
        self._is_downloading = True
        self.download_button.disabled = True
        self.loading_indicator.visible = True
        self.update_status_text.value = "Downloading update..."
        self.update_status_text.color = theme_manager.text_secondary_color
        
        if self.page:
            self.page.update()
        
        try:
            download_url = self._update_info.get('download_url')
            version = self._update_info.get('version')
            checksum = self._update_info.get('checksum')
            file_size = self._update_info.get('file_size')
            
            if not download_url or not version:
                self._show_error("Invalid update info")
                return
            
            # Download update
            download_path = await self.update_service.download_update(
                download_url,
                version,
                checksum,
                file_size
            )
            
            if download_path:
                self._update_info['download_path'] = download_path
                self.update_status_text.value = f"Update {version} downloaded and ready to install!"
                self.update_status_text.color = ft.Colors.GREEN
                self.download_button.visible = False
                self.install_button.visible = True
            else:
                self._show_error("Failed to download update")
                
        except Exception as ex:
            logger.error(f"Error downloading update: {ex}", exc_info=True)
            self._show_error(f"Error downloading update: {str(ex)}")
        finally:
            self._is_downloading = False
            self.download_button.disabled = False
            self.loading_indicator.visible = False
            if self.page:
                self.page.update()
    
    def _on_install_update(self, e):
        """Handle install update button click."""
        if not self.update_service or not self._update_info:
            self._show_error("Update info not available")
            return
        
        download_path = self._update_info.get('download_path')
        version = self._update_info.get('version')
        
        if not download_path or not version:
            self._show_error("Update file not available")
            return
        
        try:
            # Install update
            success = self.update_service.install_update(Path(download_path))
            
            if success:
                self.update_status_text.value = "Installer launched. Please complete the installation."
                self.update_status_text.color = ft.Colors.GREEN
                self.install_button.visible = False
            else:
                self._show_error("Failed to launch installer")
                
        except Exception as ex:
            logger.error(f"Error installing update: {ex}", exc_info=True)
            self._show_error(f"Error installing update: {str(ex)}")
        
        if self.page:
            self.page.update()
    
    def _format_update_info(self, update_info: dict) -> str:
        """Format update info for display."""
        parts = []
        
        description = update_info.get('description')
        if description:
            parts.append(f"Description: {description}")
        
        release_date = update_info.get('release_date')
        if release_date:
            parts.append(f"Release Date: {release_date}")
        
        file_size = self._update_info.get('file_size') if self._update_info else None
        if file_size:
            size_mb = file_size / (1024 * 1024)
            parts.append(f"Size: {size_mb:.2f} MB")
        
        return "\n".join(parts) if parts else ""
    
    def _show_error(self, message: str):
        """Show error message."""
        self.update_status_text.value = message
        self.update_status_text.color = ft.Colors.RED
        self.update_info_text.value = ""

