"""
Client manager for Telegram Telethon client operations.
"""

import asyncio
import logging
from typing import Optional, Callable, Tuple
from pathlib import Path

try:
    from telethon import TelegramClient
    from telethon.errors import FloodWaitError, UnauthorizedError, SessionPasswordNeededError
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    TelegramClient = None
    logging.warning("Telethon not installed")

from database.models import TelegramCredential
from config.settings import settings
from utils.constants import BASE_DIR, TELEGRAM_DEVICE_MODEL

logger = logging.getLogger(__name__)


def _setup_telethon_logging():
    """Configure Telethon's internal logging for useful output (not encrypted payloads)."""
    if TELETHON_AVAILABLE:
        # Set main Telethon logger to INFO to see high-level operations
        telethon_logger = logging.getLogger('telethon')
        telethon_logger.setLevel(logging.INFO)
        
        # Keep client-level logging at DEBUG for useful info
        logging.getLogger('telethon.client').setLevel(logging.DEBUG)
        
        # Set network layer to INFO to avoid encrypted payload spam
        # These loggers produce too much noise with encryption details
        logging.getLogger('telethon.network').setLevel(logging.INFO)
        logging.getLogger('telethon.network.mtprotosender').setLevel(logging.INFO)
        logging.getLogger('telethon.extensions.messagepacker').setLevel(logging.INFO)
        
        # Sessions can be DEBUG for useful session info
        logging.getLogger('telethon.sessions').setLevel(logging.DEBUG)
        
        # Keep connection info at INFO level
        logging.getLogger('telethon.network.connection').setLevel(logging.INFO)
        
        logger.debug("Telethon logging configured (network encryption logs filtered)")


class ClientManager:
    """Manages Telegram Telethon client creation, connection, and session management."""
    
    def __init__(self):
        self.client: Optional[TelegramClient] = None
        self.is_available = TELETHON_AVAILABLE
        self._session_path = BASE_DIR / "data" / "sessions"
        self._session_path.mkdir(parents=True, exist_ok=True)
        
        # Enable Telethon verbose logging
        _setup_telethon_logging()
        
        # Clean up any leftover temporary QR login session files
        self._cleanup_temp_sessions()
    
    def _cleanup_temp_sessions(self):
        """Clean up any leftover temporary QR login session files."""
        try:
            temp_session_names = ["qr_login_temp", "qr_code_temp"]
            for temp_name in temp_session_names:
                # Clean up with .session extension (Telethon standard)
                temp_file = self._session_path / f"{temp_name}.session"
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                        logger.debug(f"Cleaned up temporary session file: {temp_name}.session")
                    except Exception as e:
                        logger.warning(f"Could not delete temporary session file {temp_name}.session: {e}")
                
                
                # Also check without extension (legacy)
                temp_file_no_ext = self._session_path / temp_name
                if temp_file_no_ext.exists():
                    try:
                        temp_file_no_ext.unlink()
                        logger.debug(f"Cleaned up temporary session file (no extension): {temp_name}")
                    except Exception as e:
                        logger.warning(f"Could not delete temporary session file {temp_name}: {e}")
                
                # Also clean up .session-journal files
                temp_journal = self._session_path / f"{temp_name}.session-journal"
                if temp_journal.exists():
                    try:
                        temp_journal.unlink()
                    except Exception:
                        pass  # Journal files are optional
        except Exception as e:
            logger.warning(f"Error cleaning up temporary sessions: {e}")
    
    def create_client(
        self,
        phone: str,
        api_id: str,
        api_hash: str,
        session_path: Optional[str] = None
    ) -> Optional[TelegramClient]:
        """
        Create Telethon client with encrypted session support.
        
        Args:
            phone: Phone number
            api_id: Telegram API ID
            api_hash: Telegram API hash
            session_path: Optional session file path (from credential.session_string).
                         If provided, uses this path; otherwise constructs from phone number.
            
        Returns:
            TelegramClient instance or None if failed
        """
        if not self.is_available:
            logger.error("Telethon is not available")
            return None
        
        try:
            # Use provided session path or construct from phone number
            if session_path:
                # Use the stored session path
                session_file = Path(session_path)
                # If path has .session.enc extension, convert to .session (legacy support)
                if session_file.name.endswith('.session.enc'):
                    session_file = session_file.with_suffix('').with_suffix('.session')
                    logger.debug(f"Converted .session.enc path to .session: {session_file}")
                logger.debug(f"Using stored session path: {session_file}")
            else:
                # Construct path from phone number
                session_name = f"session_{phone.replace('+', '')}"
                session_file = self._session_path / session_name
                logger.debug(f"Constructed session path from phone: {session_file}")
            
            # Use regular Telethon session (Telethon handles its own encryption internally)
            client = TelegramClient(
                str(session_file),
                int(api_id),
                api_hash
            )
            logger.debug(f"Created client with session: {session_file}")
            
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
    ) -> Tuple[bool, Optional[str], Optional[TelegramClient]]:
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
            
            # Check if already authorized
            if await client.is_user_authorized():
                try:
                    me = await client.get_me()
                    if me:
                        self.client = client
                        logger.info(f"Already authorized for {phone} as {me.first_name or phone}")
                        return True, None, client
                except Exception:
                    pass
            
            # Send code request
            try:
                logger.info(f"Sending code request to {phone}")
                sent_code = await client.send_code_request(phone)
                
                # Log useful response data (not encrypted payload)
                code_type = type(sent_code.type).__name__ if hasattr(sent_code, 'type') else 'unknown'
                next_type = type(sent_code.next_type).__name__ if hasattr(sent_code, 'next_type') and sent_code.next_type else 'None'
                
                logger.info(
                    f"Code request sent successfully. "
                    f"Phone code hash: {sent_code.phone_code_hash[:10]}..., "
                    f"Type: {code_type}, "
                    f"Next type: {next_type}"
                )
                
                # Check if code is sent via app instead of SMS
                if 'App' in code_type:
                    logger.warning(
                        f"⚠️ Code is being sent via Telegram App (NOT SMS). "
                        f"User should check their Telegram app for the code. "
                        f"Next type available: {next_type}"
                    )
                    # Try to request SMS if available
                    if sent_code.next_type and 'Sms' in next_type:
                        try:
                            logger.info("Requesting SMS code instead of app code...")
                            sent_code = await client.send_code_request(phone, force_sms=True)
                            code_type = type(sent_code.type).__name__ if hasattr(sent_code, 'type') else 'unknown'
                            logger.info(f"✓ SMS code requested successfully. New type: {code_type}")
                        except Exception as sms_error:
                            logger.warning(f"Could not request SMS code: {sms_error}. User must check Telegram app.")
                    else:
                        logger.info("SMS not available as alternative. User must check Telegram app for code.")
                    
            except Exception as e:
                logger.error(f"Failed to send code request: {e}", exc_info=True)
                await client.disconnect()
                return False, f"Failed to send code: {str(e)}", None
            
            # Get code from callback
            if code_callback:
                logger.info("Waiting for OTP code from user...")
                if asyncio.iscoroutinefunction(code_callback):
                    code = await code_callback()
                else:
                    code = code_callback()
                if not code:
                    logger.warning("OTP code not provided by user")
                    await client.disconnect()
                    return False, "Code not provided", None
                logger.info(f"OTP code received (length: {len(code)})")
            else:
                logger.error("Code callback not provided")
                await client.disconnect()
                return False, "Code callback not provided", None
            
            # Sign in with code
            # Telethon sign_in signature: sign_in(phone=None, code=None, password=None, bot_token=None, phone_code_hash=None)
            try:
                logger.info(f"Attempting to sign in with OTP code (code length: {len(code)})...")
                result = await client.sign_in(phone=phone, code=code, phone_code_hash=sent_code.phone_code_hash)
                # Log successful sign-in result
                if result:
                    logger.info(f"Successfully signed in. User: {getattr(result, 'first_name', 'Unknown')} {getattr(result, 'last_name', '')}")
                else:
                    logger.info("Successfully signed in with OTP code")
            except SessionPasswordNeededError:
                logger.info("2FA password required")
                # 2FA required
                if password_callback:
                    if asyncio.iscoroutinefunction(password_callback):
                        password = await password_callback()
                    else:
                        password = password_callback()
                    if not password:
                        await client.disconnect()
                        return False, "Password not provided", None
                    
                    try:
                        await client.sign_in(password=password)
                    except Exception as e:
                        await client.disconnect()
                        return False, f"2FA authentication failed: {str(e)}", None
                else:
                    await client.disconnect()
                    return False, "Two-factor password required but callback not provided", None
            except Exception as e:
                logger.error(f"Authentication failed with OTP code: {e}", exc_info=True)
                await client.disconnect()
                # Provide more specific error messages
                error_msg = str(e)
                if "PHONE_CODE_INVALID" in error_msg or "invalid" in error_msg.lower():
                    return False, "Invalid OTP code. Please check and try again.", None
                elif "PHONE_CODE_EXPIRED" in error_msg or "expired" in error_msg.lower():
                    return False, "OTP code expired. Please request a new code.", None
                else:
                    return False, f"Authentication failed: {error_msg}", None
            
            self.client = client
            logger.info(f"Successfully authorized {phone}")
            return True, None, client
            
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            if self.client:
                await self.client.disconnect()
            return False, str(e), None
    
    async def start_session_qr(
        self,
        api_id: str,
        api_hash: str,
        qr_callback: Optional[Callable[[str], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        password_callback: Optional[Callable[[], str]] = None,
        cancelled_callback: Optional[Callable[[], bool]] = None
    ) -> Tuple[bool, Optional[str], Optional[TelegramClient], Optional[str], Optional[str]]:
        """
        Start Telegram session with QR code flow.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
            qr_callback: Callback to display QR code (receives QR code data as string)
            status_callback: Callback to update status messages
            password_callback: Callback to get 2FA password
            cancelled_callback: Callback to check if user cancelled
            
        Returns:
            (success, error_message, client, phone_number, session_file_path)
        """
        try:
            # Create temporary session for QR login
            session_name = "qr_login_temp"
            session_file = self._session_path / session_name
            
            # Use regular Telethon session (Telethon handles its own encryption internally)
            client = TelegramClient(
                str(session_file),
                int(api_id),
                api_hash
            )
            
            await client.connect()
            
            if status_callback:
                status_callback("Generating QR code...")
            
            # Use Telethon's qr_login method
            qr_login = await client.qr_login()
            
            if qr_callback:
                qr_callback(qr_login.url)
            
            if status_callback:
                status_callback("Waiting for QR code scan...")
            
            # Wait for QR code to be scanned
            try:
                me = await qr_login.wait(timeout=60)
                phone_number = me.phone if me else None
                
                if status_callback:
                    status_callback("QR code scanned successfully!")
                
                # Handle 2FA if needed
                if password_callback:
                    try:
                        # Check if 2FA is required
                        if not await client.is_user_authorized():
                            if asyncio.iscoroutinefunction(password_callback):
                                password = await password_callback()
                            else:
                                password = password_callback()
                            if password:
                                await client.start(password=password)
                    except Exception:
                        pass  # 2FA might not be required
                
                # Update session file name to match phone number
                if phone_number:
                    new_session_name = f"session_{phone_number.replace('+', '')}"
                    new_session_file = self._session_path / f"{new_session_name}.session"
                    old_session_file = self._session_path / f"{session_name}.session"
                    
                    # Ensure session is saved
                    try:
                        if hasattr(client.session, 'save'):
                            client.session.save()
                        # Small delay to ensure session is flushed to disk
                        await asyncio.sleep(0.2)
                    except Exception as e:
                        logger.warning(f"Error saving session: {e}")
                    
                    # Try to rename while client is still connected (Telethon may allow this)
                    # If that fails, we'll disconnect and rename
                    rename_success = False
                    actual_session_path = old_session_file  # Default to old path if rename fails
                    
                    # Use regular .session file
                    old_file_to_rename = old_session_file if old_session_file.exists() else None
                    new_file_path = new_session_file
                    
                    if old_file_to_rename and old_file_to_rename.exists():
                        try:
                            old_file_to_rename.rename(new_file_path)
                            rename_success = True
                            actual_session_path = new_file_path
                            logger.info(f"Successfully renamed session file from {old_file_to_rename.name} to {new_file_path.name}")
                        except Exception as e:
                            logger.debug(f"Could not rename while connected (expected): {e}")
                            # Disconnect to release file lock, then rename
                            try:
                                await client.disconnect()
                                await asyncio.sleep(0.2)  # Brief delay after disconnect
                                if old_file_to_rename.exists():
                                    old_file_to_rename.rename(new_file_path)
                                    rename_success = True
                                    actual_session_path = new_file_path
                                    logger.info(f"Successfully renamed session file after disconnect: {old_file_to_rename.name} to {new_file_path.name}")
                                else:
                                    logger.warning(f"Old session file disappeared after disconnect: {old_file_to_rename}")
                            except Exception as e2:
                                logger.error(f"Error renaming session file: {e2}", exc_info=True)
                                # Try copy as last resort
                                try:
                                    import shutil
                                    if old_file_to_rename.exists():
                                        shutil.copy2(old_file_to_rename, new_file_path)
                                        old_file_to_rename.unlink()
                                        rename_success = True
                                        actual_session_path = new_file_path
                                        logger.info(f"Copied session file from {old_file_to_rename.name} to {new_file_path.name}")
                                    else:
                                        logger.error(f"Old session file does not exist for copying: {old_file_to_rename}")
                                except Exception as e3:
                                    logger.error(f"Error copying session file: {e3}", exc_info=True)
                    
                    # Handle .session-journal file if it exists (Telethon WAL mode)
                    old_journal = self._session_path / f"{session_name}.session-journal"
                    if old_journal.exists():
                        try:
                            new_journal = self._session_path / f"{new_session_name}.session-journal"
                            old_journal.rename(new_journal)
                        except Exception:
                            pass  # Journal file is optional
                    
                    # Also check for session file without extension (legacy or if Telethon didn't add it)
                    # But prioritize the .session file
                    if not actual_session_path.exists() and old_session_file.with_suffix('').exists():
                        # Try without extension as fallback
                        old_session_no_ext = self._session_path / session_name
                        new_session_no_ext = self._session_path / new_session_name
                        if old_session_no_ext.exists():
                            try:
                                old_session_no_ext.rename(new_session_no_ext)
                                actual_session_path = new_session_no_ext
                                rename_success = True
                                logger.info(f"Renamed session file (no extension) from {session_name} to {new_session_name}")
                            except Exception as e:
                                logger.debug(f"Could not rename session file without extension: {e}")
                                actual_session_path = old_session_no_ext
                    
                    # Verify the final session file exists
                    if not actual_session_path.exists():
                        logger.error(f"Session file does not exist at expected path: {actual_session_path}")
                        if client.is_connected():
                            await client.disconnect()
                        return False, f"Session file not found at {actual_session_path}", None, None, None
                    
                    # If we disconnected, reconnect with the session file (renamed or original)
                    if not client.is_connected():
                        try:
                            client = TelegramClient(
                                str(actual_session_path),
                                int(api_id),
                                api_hash
                            )
                            await client.connect()
                            # Don't call start() - just check if authorized
                            # The session should load automatically when connecting
                            if await client.is_user_authorized():
                                self.client = client
                                logger.info(f"Successfully reconnected with session: {phone_number} (path: {actual_session_path})")
                                # Return the actual session path for database storage
                                return True, None, client, phone_number, str(actual_session_path)
                            else:
                                await client.disconnect()
                                logger.error(f"Client not authorized after reconnecting with session for {phone_number}")
                                return False, "Session not authorized after reconnect", None, None, None
                        except Exception as e:
                            logger.error(f"Error reconnecting with session: {e}", exc_info=True)
                            return False, f"Failed to reconnect with session: {str(e)}", None, None, None
                    else:
                        # Client is still connected - verify it's still authorized
                        if await client.is_user_authorized():
                            self.client = client
                            logger.info(f"Successfully authorized via QR code: {phone_number} (session path: {actual_session_path})")
                            # Return the actual session path for database storage
                            return True, None, client, phone_number, str(actual_session_path)
                        else:
                            logger.error(f"Client lost authorization for {phone_number}")
                            await client.disconnect()
                            return False, "Client lost authorization", None, None, None
                else:
                    await client.disconnect()
                    return False, "Phone number not available after QR login", None, None, None
                
            except asyncio.TimeoutError:
                await client.disconnect()
                return False, "QR code expired or not scanned in time", None, None, None
            except Exception as e:
                await client.disconnect()
                return False, f"QR login failed: {str(e)}", None, None, None
                
        except Exception as e:
            logger.error(f"Error starting QR session: {e}")
            if self.client:
                await self.client.disconnect()
            return False, str(e), None, None, None
    
    async def load_session(
        self,
        credential: TelegramCredential,
        api_id: str,
        api_hash: str
    ) -> Tuple[bool, Optional[str], Optional[TelegramClient]]:
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
            
            # Use stored session_path from credential if available
            session_path = credential.session_string if credential.session_string else None
            client = self.create_client(
                credential.phone_number,
                api_id,
                api_hash,
                session_path=session_path
            )
            
            if not client:
                return False, "Failed to create Telegram client", None
            
            await client.connect()
            
            # Check if authorized
            if not await client.is_user_authorized():
                await client.disconnect()
                return False, "Session expired or invalid", None
            
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
        return self.client is not None and self.client.is_connected()
    
    async def is_authorized(self) -> bool:
        """Check if Telegram client is authorized (async check)."""
        if not self.client:
            return False
        try:
            return await self.client.is_user_authorized()
        except Exception as e:
            logger.error(f"Error checking authorization: {e}")
            return False
    
    def get_client(self) -> Optional[TelegramClient]:
        """Get current client instance."""
        return self.client
