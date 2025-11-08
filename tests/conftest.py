"""
Shared pytest fixtures for testing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any

from database.managers.db_manager import DatabaseManager
from services.auth_service import AuthService
from services.license_service import LicenseService
from tests.fixtures.firebase_mocks import MockFirebaseConfig
from tests.fixtures.db_fixtures import create_test_db_manager, cleanup_temp_db
from utils.constants import (
    LICENSE_TIER_BRONZE, LICENSE_TIER_SILVER, LICENSE_TIER_GOLD, LICENSE_TIER_PREMIUM,
    LICENSE_PRICING
)


@pytest.fixture
def test_db_manager():
    """Create a test database manager with temporary file database."""
    db_manager = create_test_db_manager()
    db_path = db_manager.db_path
    yield db_manager
    # Cleanup temporary database file
    cleanup_temp_db(db_path)


@pytest.fixture
def temp_db_manager():
    """Create a temporary file-based test database manager."""
    import tempfile
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    db_path = temp_file.name
    
    db_manager = create_test_db_manager(db_path)
    yield db_manager
    
    # Cleanup
    cleanup_temp_db(db_path)


@pytest.fixture
def mock_firebase_config():
    """Create a mock Firebase configuration."""
    mock_config = MockFirebaseConfig()
    yield mock_config
    mock_config.reset()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'uid': 'test_user_123',
        'email': 'test@example.com',
        'display_name': 'Test User',
        'photo_url': None,
        'email_verified': True,
        'disabled': False
    }


@pytest.fixture
def sample_license_data():
    """Sample license data for all tiers."""
    now = datetime.now()
    return {
        LICENSE_TIER_BRONZE: {
            'license_tier': LICENSE_TIER_BRONZE,
            'max_devices': LICENSE_PRICING[LICENSE_TIER_BRONZE]['max_devices'],
            'max_groups': LICENSE_PRICING[LICENSE_TIER_BRONZE]['max_groups'],
            'active_device_ids': [],
            'expiration_date': (now + timedelta(days=7)).isoformat()
        },
        LICENSE_TIER_SILVER: {
            'license_tier': LICENSE_TIER_SILVER,
            'max_devices': LICENSE_PRICING[LICENSE_TIER_SILVER]['max_devices'],
            'max_groups': LICENSE_PRICING[LICENSE_TIER_SILVER]['max_groups'],
            'active_device_ids': [],
            'expiration_date': (now + timedelta(days=30)).isoformat()
        },
        LICENSE_TIER_GOLD: {
            'license_tier': LICENSE_TIER_GOLD,
            'max_devices': LICENSE_PRICING[LICENSE_TIER_GOLD]['max_devices'],
            'max_groups': LICENSE_PRICING[LICENSE_TIER_GOLD]['max_groups'],
            'active_device_ids': [],
            'expiration_date': (now + timedelta(days=30)).isoformat()
        },
        LICENSE_TIER_PREMIUM: {
            'license_tier': LICENSE_TIER_PREMIUM,
            'max_devices': LICENSE_PRICING[LICENSE_TIER_PREMIUM]['max_devices'],
            'max_groups': LICENSE_PRICING[LICENSE_TIER_PREMIUM]['max_groups'],
            'active_device_ids': [],
            'expiration_date': (now + timedelta(days=30)).isoformat()
        }
    }


@pytest.fixture
def expired_license_data():
    """Expired license data for testing."""
    past_date = datetime.now() - timedelta(days=1)
    return {
        'license_tier': LICENSE_TIER_SILVER,
        'max_devices': 1,
        'max_groups': 3,
        'active_device_ids': [],
        'expiration_date': past_date.isoformat()
    }


@pytest.fixture
def mock_auth_service(test_db_manager, mock_firebase_config):
    """Create a mock AuthService with mocked Firebase."""
    with patch('services.auth_service.firebase_config', mock_firebase_config):
        auth_service = AuthService(test_db_manager)
        yield auth_service


@pytest.fixture
def mock_license_service(test_db_manager, mock_firebase_config):
    """Create a mock LicenseService with mocked Firebase."""
    with patch('services.license_service.firebase_config', mock_firebase_config):
        license_service = LicenseService(test_db_manager)
        yield license_service


@pytest.fixture
def mock_requests_post():
    """Mock requests.post for Firebase REST API calls."""
    with patch('services.auth_service.requests.post') as mock_post:
        yield mock_post


@pytest.fixture
def mock_device_id():
    """Mock device ID for consistent testing."""
    with patch('services.auth_service.AuthService.device_id', new_callable=lambda: 'test_device_123'):
        yield 'test_device_123'


@pytest.fixture
def sample_token():
    """Sample Firebase ID token."""
    return 'mock_id_token_12345'


@pytest.fixture
def sample_decoded_token(sample_user_data):
    """Sample decoded Firebase token."""
    return {
        'uid': sample_user_data['uid'],
        'email': sample_user_data['email'],
        'device_id': None
    }

