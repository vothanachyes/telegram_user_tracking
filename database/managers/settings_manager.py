"""
App settings manager.
"""

from database.managers.base import BaseDatabaseManager, _safe_get_row_value, _parse_datetime
from database.models.app_settings import AppSettings
import logging

logger = logging.getLogger(__name__)


class SettingsManager(BaseDatabaseManager):
    """Manages app settings operations."""
    
    def get_settings(self) -> AppSettings:
        """Get application settings."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM app_settings WHERE id = 1")
            row = cursor.fetchone()
            if row:
                return AppSettings(
                    id=row['id'],
                    theme=row['theme'],
                    language=row['language'],
                    corner_radius=row['corner_radius'],
                    telegram_api_id=row['telegram_api_id'],
                    telegram_api_hash=row['telegram_api_hash'],
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
                    created_at=_parse_datetime(row['created_at']),
                    updated_at=_parse_datetime(row['updated_at'])
                )
            return AppSettings()
    
    def update_settings(self, settings: AppSettings) -> bool:
        """Update application settings."""
        try:
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
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, (
                    settings.theme,
                    settings.language,
                    settings.corner_radius,
                    settings.telegram_api_id,
                    settings.telegram_api_hash,
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
                    settings.encrypted_pin
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return False

