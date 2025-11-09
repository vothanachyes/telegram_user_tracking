"""
Dialog for Telegram QR code authentication.
"""

import flet as ft
import io
import logging
from typing import Optional, Callable
from ui.theme import theme_manager
import qrcode

logger = logging.getLogger(__name__)


class QRCodeDialog(ft.AlertDialog):
    """Dialog for displaying QR code and handling QR code login flow."""
    
    def __init__(
        self,
        qr_token: str,
        on_cancel: Optional[Callable[[], None]] = None,
        on_refresh: Optional[Callable[[], str]] = None
    ):
        self.qr_token = qr_token
        self.on_cancel_callback = on_cancel
        self.on_refresh_callback = on_refresh
        self.is_cancelled = False
        
        # Create QR code image (empty initially if no token)
        self.qr_image = self._generate_qr_image(qr_token) if qr_token else ""
        
        # Status text
        self.status_text = ft.Text(
            theme_manager.t("qr_code_scanning") if qr_token else "Generating QR code...",
            size=14,
            color=theme_manager.text_secondary_color,
            text_align=ft.TextAlign.CENTER
        )
        
        # Instructions text
        instructions = ft.Text(
            theme_manager.t("qr_code_instructions"),
            size=12,
            color=theme_manager.text_secondary_color,
            text_align=ft.TextAlign.CENTER
        )
        
        # QR code image display (show placeholder if no image)
        if self.qr_image:
            self.qr_image_widget = ft.Image(
                src_base64=self.qr_image,
                width=300,
                height=300,
                fit=ft.ImageFit.CONTAIN
            )
        else:
            # Show loading indicator
            self.qr_image_widget = ft.Column([
                ft.ProgressRing(),
                ft.Text("Generating QR code...", size=12)
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
            )
        
        # Container for QR image (so we can update it easily)
        self.qr_image_container = ft.Container(
            content=self.qr_image_widget,
            alignment=ft.alignment.center,
            padding=20,
            width=300,
            height=300
        )
        
        # Refresh button (hidden initially, shown if QR expires)
        self.refresh_btn = ft.ElevatedButton(
            theme_manager.t("refresh"),
            icon=ft.Icons.REFRESH,
            on_click=self._handle_refresh,
            visible=False
        )
        
        # Create dialog
        super().__init__(
            modal=True,
            title=ft.Text(theme_manager.t("login_with_qr_code")),
            content=ft.Container(
                content=ft.Column([
                    instructions,
                    self.qr_image_container,
                    self.status_text,
                    ft.Container(
                        content=self.refresh_btn,
                        alignment=ft.alignment.center
                    )
                ], 
                spacing=15, 
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                width=400,
                padding=20
            ),
            actions=[
                ft.TextButton(
                    theme_manager.t("cancel"),
                    on_click=self._handle_cancel
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _generate_qr_image(self, token: str) -> str:
        """
        Generate QR code image from Telethon QR login URL.
        
        According to Telethon docs, qr_login.url already contains the full
        tg://login URI with the token, so we can use it directly.
        See: https://docs.telethon.dev/en/stable/modules/custom.html#module-telethon.tl.custom.qrlogin
        """
        if not token:
            return ""
        
        try:
            # Telethon's qr_login.url already contains the full tg://login URI
            # The URL "simply consists of token base64-encoded" according to docs
            # So we can use it directly without any transformation
            qr_data = token
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Convert to base64 for Flet
            import base64
            img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
            
            return img_base64
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return ""
    
    def update_status(self, status: str, is_error: bool = False, is_success: bool = False):
        """Update status text."""
        logger.debug(f"QRCodeDialog.update_status called: {status}, is_success={is_success}, is_error={is_error}")
        self.status_text.value = status
        if is_success:
            self.status_text.color = ft.Colors.GREEN
        elif is_error:
            self.status_text.color = ft.Colors.RED
        else:
            self.status_text.color = theme_manager.text_secondary_color
        
        # Try to update the page
        if self.page:
            try:
                self.page.update()
                logger.debug(f"Page updated successfully for status: {status}")
            except Exception as e:
                logger.error(f"Error updating page in QRCodeDialog: {e}", exc_info=True)
        else:
            logger.warning(f"QRCodeDialog has no page reference, cannot update UI for status: {status}")
    
    def show_refresh_button(self, show: bool = True):
        """Show or hide refresh button."""
        self.refresh_btn.visible = show
        if self.page:
            self.page.update()
    
    def refresh_qr_code(self, new_token: str):
        """Refresh QR code with new token."""
        logger.info(f"refresh_qr_code called with token (len={len(new_token) if new_token else 0})")
        if not new_token:
            logger.warning("refresh_qr_code: empty token, skipping")
            return
        
        self.qr_token = new_token
        logger.debug("Generating new QR image...")
        new_image = self._generate_qr_image(new_token)
        if new_image:
            # Update QR image widget
            self.qr_image_widget = ft.Image(
                src_base64=new_image,
                width=300,
                height=300,
                fit=ft.ImageFit.CONTAIN
            )
            # Update container content
            self.qr_image_container.content = self.qr_image_widget
            
            self.status_text.value = theme_manager.t("qr_code_scanning")
            self.status_text.color = theme_manager.text_secondary_color
            self.refresh_btn.visible = False
            if self.page:
                self.page.update()
    
    def _handle_refresh(self, e):
        """Handle refresh button click."""
        if self.on_refresh_callback:
            new_token = self.on_refresh_callback()
            if new_token:
                self.refresh_qr_code(new_token)
    
    def _handle_cancel(self, e):
        """Handle cancel button click."""
        self.is_cancelled = True
        if self.on_cancel_callback:
            self.on_cancel_callback()
        
        self.open = False
        if self.page:
            self.page.update()
    
    def get_cancelled(self) -> bool:
        """Check if dialog was cancelled."""
        return self.is_cancelled

