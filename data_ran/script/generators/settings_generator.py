"""
Settings generator for app_settings data.
"""

from typing import Dict, Any, List
from datetime import datetime
from data_ran.pattern.base import BaseGenerator


class SettingsGenerator(BaseGenerator):
    """Generates app_settings data."""
    
    def generate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate app_settings data.
        
        Args:
            config: Configuration (optional)
            
        Returns:
            List with single app_settings dictionary
        """
        now = datetime.now()
        
        settings = {
            'id': 1,
            'theme': 'dark',
            'language': 'en',
            'corner_radius': 10,
            'telegram_api_id': None,
            'telegram_api_hash': None,
            'download_root_dir': './downloads',
            'download_media': True,
            'max_file_size_mb': 50,
            'fetch_delay_seconds': 5.0,
            'download_photos': True,
            'download_videos': True,
            'download_documents': True,
            'download_audio': True,
            'track_reactions': True,
            'reaction_fetch_delay': 0.5,
            'pin_enabled': False,
            'encrypted_pin': None,
            'created_at': now.isoformat(),
            'updated_at': now.isoformat()
        }
        
        return [settings]
    
    def get_dependencies(self) -> List[str]:
        """Settings have no dependencies."""
        return []

