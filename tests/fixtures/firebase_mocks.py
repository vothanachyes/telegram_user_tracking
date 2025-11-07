"""
Firebase mock utilities for testing.
"""

from unittest.mock import MagicMock, Mock
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class MockFirebaseConfig:
    """Mock Firebase configuration for testing."""
    
    def __init__(self):
        self._initialized = False
        self._users: Dict[str, Dict[str, Any]] = {}
        self._tokens: Dict[str, Dict[str, Any]] = {}
        self._licenses: Dict[str, Dict[str, Any]] = {}
        self._custom_claims: Dict[str, Dict[str, Any]] = {}
    
    def initialize(self, credentials_path: Optional[str] = None) -> bool:
        """Mock initialize - always succeeds."""
        self._initialized = True
        return True
    
    def is_initialized(self) -> bool:
        """Check if mock Firebase is initialized."""
        return self._initialized
    
    def verify_token(self, id_token: str) -> Optional[dict]:
        """Mock token verification."""
        if not self._initialized:
            return None
        
        # Check if token exists in mock tokens
        if id_token in self._tokens:
            return self._tokens[id_token]
        
        # Return None for invalid tokens
        return None
    
    def get_user(self, uid: str) -> Optional[dict]:
        """Mock get user by UID."""
        if not self._initialized:
            return None
        return self._users.get(uid)
    
    def set_custom_claims(self, uid: str, claims: dict) -> bool:
        """Mock set custom claims."""
        if not self._initialized:
            return False
        self._custom_claims[uid] = claims
        return True
    
    def get_user_license(self, uid: str) -> Optional[dict]:
        """Mock get user license from Firestore."""
        if not self._initialized:
            return None
        return self._licenses.get(uid)
    
    def set_user_license(self, uid: str, license_data: dict) -> bool:
        """Mock set user license in Firestore."""
        if not self._initialized:
            return False
        self._licenses[uid] = license_data.copy()
        return True
    
    def add_device_to_license(self, uid: str, device_id: str) -> bool:
        """Mock add device to license."""
        if not self._initialized:
            return False
        
        if uid not in self._licenses:
            self._licenses[uid] = {'active_device_ids': []}
        
        active_devices = self._licenses[uid].get('active_device_ids', [])
        if device_id not in active_devices:
            active_devices.append(device_id)
            self._licenses[uid]['active_device_ids'] = active_devices
        
        return True
    
    def get_active_devices(self, uid: str) -> list:
        """Mock get active devices."""
        if not self._initialized:
            return []
        
        license_data = self._licenses.get(uid)
        if license_data:
            return license_data.get('active_device_ids', [])
        return []
    
    def create_mock_user(self, uid: str, email: str, disabled: bool = False) -> dict:
        """Create a mock user."""
        user = {
            'uid': uid,
            'email': email,
            'display_name': None,
            'photo_url': None,
            'email_verified': True,
            'disabled': disabled
        }
        self._users[uid] = user
        return user
    
    def create_mock_token(self, token_id: str, uid: str, email: str, device_id: Optional[str] = None) -> dict:
        """Create a mock token."""
        token = {
            'uid': uid,
            'email': email,
            'device_id': device_id
        }
        self._tokens[token_id] = token
        return token
    
    def create_mock_license(
        self,
        uid: str,
        tier: str = 'bronze',
        max_devices: int = 1,
        max_groups: int = 1,
        active_device_ids: Optional[list] = None,
        expiration_days: int = 7
    ) -> dict:
        """Create a mock license."""
        expiration_date = (datetime.now() + timedelta(days=expiration_days)).isoformat()
        license_data = {
            'license_tier': tier,
            'max_devices': max_devices,
            'max_groups': max_groups,
            'active_device_ids': active_device_ids or [],
            'expiration_date': expiration_date
        }
        self._licenses[uid] = license_data
        return license_data
    
    def reset(self):
        """Reset all mock data."""
        self._initialized = False
        self._users.clear()
        self._tokens.clear()
        self._licenses.clear()
        self._custom_claims.clear()


def create_mock_requests_response(status_code: int, json_data: dict) -> Mock:
    """Create a mock requests response."""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    return mock_response

