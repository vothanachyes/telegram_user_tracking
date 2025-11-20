"""
Session manager for Telegram session lifecycle operations.
"""

import logging
from typing import Optional, Callable, Tuple
from pathlib import Path

from database.db_manager import DatabaseManager
from database.models import TelegramCredential
from config.settings import settings
from services.telegram.client_manager import ClientManager

logger = logging.getLogger(__name__)


class SessionManager:
    """Handles Telegram session lifecycle operations."""
    
    def __init__(self, db_manager: DatabaseManager, client_manager: ClientManager):
        self.db_manager = db_manager
        self.client_manager = client_manager
    
    async def start_session(
        self,
        phone: str,
        api_id: str,
        api_hash: str,
        code_callback: Optional[Callable[[], str]] = None,
        password_callback: Optional[Callable[[], str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Start Telegram session with OTP flow.
        Returns (success, error_message)
        """
        success, error, client = await self.client_manager.start_session(
            phone, api_id, api_hash, code_callback, password_callback
        )
        
        if success and client:
            # Telethon stores session file path in client.session.filename
            session_file_path = Path(client.session.filename) if hasattr(client.session, 'filename') else None
            if not session_file_path:
                # Fallback: construct session path from phone number
                from utils.constants import APP_DATA_DIR
                session_name = f"session_{phone.replace('+', '')}"
                session_file_path = APP_DATA_DIR / "sessions" / session_name
            
            credential = TelegramCredential(
                phone_number=phone,
                session_string=str(session_file_path),
                is_default=True
            )
            self.db_manager.save_telegram_credential(credential)
        
        return success, error
    
    async def start_session_qr(
        self,
        api_id: str,
        api_hash: str,
        qr_callback: Optional[Callable[[str], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        password_callback: Optional[Callable[[], str]] = None,
        cancelled_callback: Optional[Callable[[], bool]] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Start Telegram session with QR code flow.
        Returns (success, error_message, phone_number)
        """
        success, error, client, phone_number, session_file_path = await self.client_manager.start_session_qr(
            api_id, api_hash, qr_callback, status_callback, password_callback, cancelled_callback
        )
        
        if success and client and phone_number:
            # Use the actual session file path returned from client_manager
            # This ensures we use the correct path (renamed or original if rename failed)
            if session_file_path:
                session_file_path = Path(session_file_path)
            else:
                # Fallback: construct expected path
                from utils.constants import APP_DATA_DIR
                session_name = f"session_{phone_number.replace('+', '')}"
                session_file_path = APP_DATA_DIR / "sessions" / session_name
                logger.warning(f"Session path not returned from client_manager, using fallback: {session_file_path}")
            
            # Verify the session file exists
            if not session_file_path.exists():
                logger.error(f"Session file does not exist at {session_file_path} after QR login")
                # Try to get from client as last resort
                if hasattr(client.session, 'filename'):
                    session_file_path = Path(client.session.filename)
                    logger.warning(f"Using client session filename as fallback: {session_file_path}")
                else:
                    logger.error(f"Cannot determine session file path for {phone_number}")
                    return False, "Session file path not found", phone_number
            
            credential = TelegramCredential(
                phone_number=phone_number,
                session_string=str(session_file_path),
                is_default=True
            )
            self.db_manager.save_telegram_credential(credential)
            logger.info(f"Saved QR login credential for {phone_number} with session: {session_file_path}")
        
        return success, error, phone_number
    
    async def load_session(
        self,
        credential: TelegramCredential
    ) -> Tuple[bool, Optional[str]]:
        """Load existing Telegram session."""
        if not settings.has_telegram_credentials:
            return False, "Telegram API credentials not configured"
        
        success, error, client = await self.client_manager.load_session(
            credential,
            settings.telegram_api_id,
            settings.telegram_api_hash
        )
        
        return success, error
    
    async def disconnect(self):
        """Disconnect Telegram client."""
        await self.client_manager.disconnect()
    
    def is_connected(self) -> bool:
        """Check if Telegram client is connected and authorized."""
        return self.client_manager.is_connected()
    
    async def is_authorized(self) -> bool:
        """Check if Telegram client is authorized (async check)."""
        return await self.client_manager.is_authorized()
    
    async def auto_load_session(self) -> Tuple[bool, Optional[str]]:
        """
        Automatically load the default Telegram session if available.
        Returns (success, error_message)
        """
        try:
            credential = self.db_manager.get_default_credential()
            if not credential:
                return False, "No saved Telegram session found"
            
            return await self.load_session(credential)
        except Exception as e:
            logger.error(f"Error auto-loading session: {e}")
            return False, str(e)

