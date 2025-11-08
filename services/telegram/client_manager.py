"""
Client manager for Telegram Pyrogram client operations.
"""

import asyncio
import logging
from typing import Optional, Callable, Tuple
from pathlib import Path

try:
    from pyrogram import Client
    PYROGRAM_AVAILABLE = True
except ImportError:
    PYROGRAM_AVAILABLE = False
    logging.warning("Pyrogram not installed")

from database.models import TelegramCredential
from config.settings import settings
from utils.constants import BASE_DIR

logger = logging.getLogger(__name__)


class ClientManager:
    """Manages Telegram Pyrogram client creation, connection, and session management."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.is_available = PYROGRAM_AVAILABLE
        self._session_path = BASE_DIR / "data" / "sessions"
        self._session_path.mkdir(parents=True, exist_ok=True)
    
    def create_client(
        self,
        phone: str,
        api_id: str,
        api_hash: str
    ) -> Optional[Client]:
        """
        Create Pyrogram client.
        
        Args:
            phone: Phone number
            api_id: Telegram API ID
            api_hash: Telegram API hash
            
        Returns:
            Client instance or None if failed
        """
        if not self.is_available:
            logger.error("Pyrogram is not available")
            return None
        
        try:
            session_name = f"session_{phone.replace('+', '')}"
            
            client = Client(
                name=session_name,
                api_id=int(api_id),
                api_hash=api_hash,
                phone_number=phone,
                workdir=str(self._session_path)
            )
            
            return client
        except Exception as e:
            logger.error(f"Error creating Telegram client: {e}")
            return None
    
    async def start_session(
        self,
        phone: str,
        api_id: str,
        api_hash: str,
        code_callback: Optional[Callable[[], str]] = None,
        password_callback: Optional[Callable[[], str]] = None
    ) -> Tuple[bool, Optional[str], Optional[Client]]:
        """
        Start Telegram session with OTP flow.
        
        Args:
            phone: Phone number
            api_id: Telegram API ID
            api_hash: Telegram API hash
            code_callback: Callback to get OTP code
            password_callback: Callback to get 2FA password
            
        Returns:
            (success, error_message, client)
        """
        try:
            client = self.create_client(phone, api_id, api_hash)
            if not client:
                return False, "Failed to create Telegram client", None
            
            await client.connect()
            
            try:
                me = await client.get_me()
                if me:
                    self.client = client
                    logger.info(f"Already authorized for {phone} as {me.first_name or me.phone_number}")
                    return True, None, client
            except Exception:
                pass
            
            sent_code = await client.send_code(phone)
            
            if code_callback:
                if asyncio.iscoroutinefunction(code_callback):
                    code = await code_callback()
                else:
                    code = code_callback()
                if not code:
                    await client.disconnect()
                    return False, "Code not provided", None
            else:
                await client.disconnect()
                return False, "Code callback not provided", None
            
            try:
                await client.sign_in(phone, sent_code.phone_code_hash, code)
            except Exception as e:
                if "password" in str(e).lower():
                    if password_callback:
                        if asyncio.iscoroutinefunction(password_callback):
                            password = await password_callback()
                        else:
                            password = password_callback()
                        if not password:
                            await client.disconnect()
                            return False, "Password not provided", None
                        
                        await client.check_password(password)
                    else:
                        await client.disconnect()
                        return False, "Two-factor password required but callback not provided", None
                else:
                    raise
            
            self.client = client
            logger.info(f"Successfully authorized {phone}")
            return True, None, client
            
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            if self.client:
                await self.client.disconnect()
            return False, str(e), None
    
    async def load_session(
        self,
        credential: TelegramCredential,
        api_id: str,
        api_hash: str
    ) -> Tuple[bool, Optional[str], Optional[Client]]:
        """
        Load existing Telegram session.
        
        Args:
            credential: TelegramCredential object
            api_id: Telegram API ID
            api_hash: Telegram API hash
            
        Returns:
            (success, error_message, client)
        """
        try:
            if not settings.has_telegram_credentials:
                return False, "Telegram API credentials not configured", None
            
            client = self.create_client(
                credential.phone_number,
                api_id,
                api_hash
            )
            
            if not client:
                return False, "Failed to create Telegram client", None
            
            await client.connect()
            
            try:
                me = await client.get_me()
                if not me:
                    await client.disconnect()
                    return False, "Session expired or invalid", None
            except Exception:
                await client.disconnect()
                return False, "Session expired or invalid", None
            
            self.client = client
            logger.info(f"Session loaded for {credential.phone_number}")
            return True, None, client
            
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return False, str(e), None
    
    async def disconnect(self):
        """Disconnect Telegram client."""
        if self.client:
            await self.client.disconnect()
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if Telegram client is connected."""
        return self.client is not None
    
    async def is_authorized(self) -> bool:
        """Check if Telegram client is authorized (async check)."""
        if not self.client:
            return False
        try:
            me = await self.client.get_me()
            return me is not None
        except Exception as e:
            logger.error(f"Error checking authorization: {e}")
            return False
    
    def get_client(self) -> Optional[Client]:
        """Get current client instance."""
        return self.client

