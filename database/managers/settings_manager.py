"""
App settings manager.
"""

from datetime import datetime
from typing import Optional
from database.managers.base import BaseDatabaseManager, _safe_get_row_value, _parse_datetime
from database.models.app_settings import AppSettings
from utils.credential_storage import credential_storage
import logging

logger = logging.getLogger(__name__)


class SettingsManager(BaseDatabaseManager):
    """Manages app settings operations."""
    
    def _encrypt_field(self, value: Optional[str]) -> Optional[str]:
        """Encrypt a field value for storage."""
        if value is None:
            return None
        try:
            return credential_storage.encrypt(value)
        except Exception as e:
            logger.error(f"Error encrypting field: {e}")
            return None
    
    def _decrypt_field(self, encrypted_value: Optional[str]) -> Optional[str]:
        """Decrypt a field value."""
        if encrypted_value is None:
            return None
        try:
            return credential_storage.decrypt(encrypted_value)
        except Exception as e:
            logger.error(f"Error decrypting field: {e}")
            return None
    
    def get_rate_limit_warning_last_seen(self) -> Optional[datetime]:
        """Get the last seen timestamp for rate limit warning."""
        settings = self.get_settings()
        return settings.rate_limit_warning_last_seen
    
    def update_rate_limit_warning_last_seen(self, timestamp: datetime) -> bool:
        """Update the last seen timestamp for rate limit warning."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE app_settings 
                    SET rate_limit_warning_last_seen = ?
                    WHERE id = 1
                """, (timestamp,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating rate_limit_warning_last_seen: {e}")
            return False
    
    def get_settings(self) -> AppSettings:
        """Get application settings and decrypt sensitive fields."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM app_settings WHERE id = 1")
            row = cursor.fetchone()
            if row:
                # Decrypt Telegram API credentials
                telegram_api_id = self._decrypt_field(_safe_get_row_value(row, 'telegram_api_id'))
                telegram_api_hash = self._decrypt_field(_safe_get_row_value(row, 'telegram_api_hash'))
                
                return AppSettings(
                    id=row['id'],
                    theme=row['theme'],
                    language=row['language'],
                    corner_radius=row['corner_radius'],
                    telegram_api_id=telegram_api_id,
                    telegram_api_hash=telegram_api_hash,
                    download_root_dir=row['download_root_dir'],
                    download_media=bool(row['download_media']),
                    max_file_size_mb=row['max_file_size_mb'],
                    fetch_delay_seconds=row['fetch_delay_seconds'],
                    download_photos=bool(row['download_photos']),
                    download_videos=bool(row['download_videos']),
                    download_documents=bool(row['download_documents']),
                    download_audio=bool(row['download_audio']),
                    track_reactions=bool(_safe_get_row_value(row, 'track_reactions', True)),
                    reaction_fetch_delay=_safe_get_row_value(row, 'reaction_fetch_delay', 0.5),
                    pin_enabled=bool(_safe_get_row_value(row, 'pin_enabled', False)),
                    encrypted_pin=_safe_get_row_value(row, 'encrypted_pin', None),
                    user_encrypted_pin=_safe_get_row_value(row, 'user_encrypted_pin', None),
                    pin_attempt_count=int(_safe_get_row_value(row, 'pin_attempt_count', 0)),
                    pin_lockout_until=_parse_datetime(_safe_get_row_value(row, 'pin_lockout_until')),
                    rate_limit_warning_last_seen=_parse_datetime(_safe_get_row_value(row, 'rate_limit_warning_last_seen')),
                    db_path=_safe_get_row_value(row, 'db_path', None),
                    encryption_enabled=bool(_safe_get_row_value(row, 'encryption_enabled', False)),
                    encryption_key_hash=_safe_get_row_value(row, 'encryption_key_hash', None),
                    session_encryption_enabled=bool(_safe_get_row_value(row, 'session_encryption_enabled', False)),
                    created_at=_parse_datetime(row['created_at']),
                    updated_at=_parse_datetime(row['updated_at'])
                )
            return AppSettings()
    
    def update_settings(self, settings: AppSettings) -> bool:
        """Update application settings with encrypted sensitive fields."""
        try:
            # Encrypt Telegram API credentials
            encrypted_api_id = self._encrypt_field(settings.telegram_api_id)
            encrypted_api_hash = self._encrypt_field(settings.telegram_api_hash)
            
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE app_settings SET
                        theme = ?,
                        language = ?,
                        corner_radius = ?,
                        telegram_api_id = ?,
                        telegram_api_hash = ?,
                        download_root_dir = ?,
                        download_media = ?,
                        max_file_size_mb = ?,
                        fetch_delay_seconds = ?,
                        download_photos = ?,
                        download_videos = ?,
                        download_documents = ?,
                        download_audio = ?,
                        track_reactions = ?,
                        reaction_fetch_delay = ?,
                        pin_enabled = ?,
                        encrypted_pin = ?,
                        user_encrypted_pin = ?,
                        pin_attempt_count = ?,
                        pin_lockout_until = ?,
                        rate_limit_warning_last_seen = ?,
                        db_path = ?,
                        encryption_enabled = ?,
                        encryption_key_hash = ?,
                        session_encryption_enabled = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, (
                    settings.theme,
                    settings.language,
                    settings.corner_radius,
                    encrypted_api_id,
                    encrypted_api_hash,
                    settings.download_root_dir,
                    settings.download_media,
                    settings.max_file_size_mb,
                    settings.fetch_delay_seconds,
                    settings.download_photos,
                    settings.download_videos,
                    settings.download_documents,
                    settings.download_audio,
                    settings.track_reactions,
                    settings.reaction_fetch_delay,
                    settings.pin_enabled,
                    settings.encrypted_pin,
                    settings.user_encrypted_pin,
                    settings.pin_attempt_count,
                    settings.pin_lockout_until,
                    settings.rate_limit_warning_last_seen,
                    settings.db_path,
                    settings.encryption_enabled,
                    settings.encryption_key_hash,
                    settings.session_encryption_enabled
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return False

