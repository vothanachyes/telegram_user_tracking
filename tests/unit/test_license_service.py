"""
Unit tests for LicenseService.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from services.license_service import LicenseService
from database.models.auth import UserLicenseCache
from utils.constants import (
    LICENSE_TIER_BRONZE, LICENSE_TIER_SILVER, LICENSE_TIER_GOLD, LICENSE_TIER_PREMIUM,
    DEFAULT_LICENSE_TIER, LICENSE_PRICING
)


class TestLicenseService:
    """Test cases for LicenseService."""
    
    def test_get_user_tier_bronze(self, test_db_manager, mock_firebase_config):
        """Test get_user_tier returns Bronze tier."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_license(uid, tier=LICENSE_TIER_BRONZE)
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            # Save license cache
            cache = UserLicenseCache(
                user_email=email,
                license_tier=LICENSE_TIER_BRONZE,
                is_active=True
            )
            test_db_manager.save_license_cache(cache)
            
            tier = license_service.get_user_tier(email)
            assert tier == LICENSE_TIER_BRONZE
    
    def test_get_user_tier_silver(self, test_db_manager, mock_firebase_config):
        """Test get_user_tier returns Silver tier."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_license(uid, tier=LICENSE_TIER_SILVER)
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            from database.models import UserLicenseCache
            cache = UserLicenseCache(
                user_email=email,
                license_tier=LICENSE_TIER_SILVER,
                is_active=True
            )
            test_db_manager.save_license_cache(cache)
            
            tier = license_service.get_user_tier(email)
            assert tier == LICENSE_TIER_SILVER
    
    def test_get_user_tier_default_when_no_user(self, test_db_manager):
        """Test get_user_tier returns default when no user."""
        license_service = LicenseService(test_db_manager)
        tier = license_service.get_user_tier()
        assert tier == DEFAULT_LICENSE_TIER
    
    def test_check_license_status_active(self, test_db_manager, mock_firebase_config):
        """Test check_license_status with active license."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_license(uid, tier=LICENSE_TIER_SILVER, expiration_days=30)
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            from database.models import UserLicenseCache
            expiration = datetime.now() + timedelta(days=30)
            cache = UserLicenseCache(
                user_email=email,
                license_tier=LICENSE_TIER_SILVER,
                expiration_date=expiration,
                max_devices=1,
                max_groups=3,
                is_active=True
            )
            test_db_manager.save_license_cache(cache)
            
            status = license_service.check_license_status(email, uid)
            
            assert status['is_active'] is True
            assert status['tier'] == LICENSE_TIER_SILVER
            assert status['expired'] is False
            assert status['expiration_date'] is not None
            assert status['days_until_expiration'] is not None
            assert status['max_devices'] == 1
            assert status['max_groups'] == 3
    
    def test_check_license_status_expired(self, test_db_manager, mock_firebase_config):
        """Test check_license_status with expired license."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            from database.models import UserLicenseCache
            expiration = datetime.now() - timedelta(days=1)
            cache = UserLicenseCache(
                user_email=email,
                license_tier=LICENSE_TIER_SILVER,
                expiration_date=expiration,
                max_devices=1,
                max_groups=3,
                is_active=True
            )
            test_db_manager.save_license_cache(cache)
            
            status = license_service.check_license_status(email, uid)
            
            assert status['is_active'] is False
            assert status['expired'] is True
            assert status['days_until_expiration'] is None
    
    def test_check_license_status_no_user(self, test_db_manager):
        """Test check_license_status when no user is logged in."""
        license_service = LicenseService(test_db_manager)
        status = license_service.check_license_status()
        
        assert status['is_active'] is False
        assert status['tier'] == DEFAULT_LICENSE_TIER
        assert status['expired'] is True
        assert 'max_devices' in status
        assert 'max_groups' in status
    
    def test_sync_from_firebase_success(self, test_db_manager, mock_firebase_config):
        """Test successful sync from Firebase."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_license(uid, tier=LICENSE_TIER_GOLD, expiration_days=30)
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            result = license_service.sync_from_firebase(email, uid)
            
            assert result is True
            
            # Check cache was created
            cache = test_db_manager.get_license_cache(email)
            assert cache is not None
            assert cache.license_tier == LICENSE_TIER_GOLD
            assert cache.is_active is True
    
    def test_sync_from_firebase_creates_default_license(self, test_db_manager, mock_firebase_config):
        """Test sync creates default license when none exists."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        mock_firebase_config.get_user_license = Mock(return_value=None)
        mock_firebase_config.set_user_license = Mock(return_value=True)
        
        # Mock the second call to return the created license
        default_license = {
            'license_tier': DEFAULT_LICENSE_TIER,
            'max_devices': LICENSE_PRICING[DEFAULT_LICENSE_TIER]['max_devices'],
            'max_groups': LICENSE_PRICING[DEFAULT_LICENSE_TIER]['max_groups'],
            'active_device_ids': [],
            'expiration_date': (datetime.now() + timedelta(days=7)).isoformat()
        }
        mock_firebase_config.get_user_license = Mock(side_effect=[None, default_license])
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            result = license_service.sync_from_firebase(email, uid)
            
            assert result is True
            assert mock_firebase_config.set_user_license.called
    
    def test_sync_from_firebase_failure(self, test_db_manager, mock_firebase_config):
        """Test sync failure from Firebase."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        mock_firebase_config.get_user_license = Mock(side_effect=Exception("Firebase error"))
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            result = license_service.sync_from_firebase(email, uid)
            
            assert result is False
    
    def test_can_add_group_bronze(self, test_db_manager, mock_firebase_config):
        """Test can_add_group for Bronze tier."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_license(uid, tier=LICENSE_TIER_BRONZE, max_groups=1)
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            from database.models import UserLicenseCache
            expiration = datetime.now() + timedelta(days=7)
            cache = UserLicenseCache(
                user_email=email,
                license_tier=LICENSE_TIER_BRONZE,
                expiration_date=expiration,
                max_groups=1,
                is_active=True
            )
            test_db_manager.save_license_cache(cache)
            
            # No groups yet, should be able to add
            can_add, error = license_service.can_add_group(email, uid)
            assert can_add is True
            assert error is None
    
    def test_can_add_group_limit_reached(self, test_db_manager, mock_firebase_config):
        """Test can_add_group when limit is reached."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_license(uid, tier=LICENSE_TIER_SILVER, max_groups=3)
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            from database.models import UserLicenseCache, Group
            expiration = datetime.now() + timedelta(days=30)
            cache = UserLicenseCache(
                user_email=email,
                license_tier=LICENSE_TIER_SILVER,
                expiration_date=expiration,
                max_groups=3,
                is_active=True
            )
            test_db_manager.save_license_cache(cache)
            
            # Create 3 groups to reach limit
            for i in range(3):
                group = Group(
                    group_id=f'group_{i}',
                    title=f'Group {i}',
                    username=None,
                    member_count=0
                )
                test_db_manager.save_group(group)
            
            can_add, error = license_service.can_add_group(email, uid)
            assert can_add is False
            assert 'group limit' in error.lower()
    
    def test_can_add_group_premium_unlimited(self, test_db_manager, mock_firebase_config):
        """Test can_add_group for Premium tier (unlimited)."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_license(uid, tier=LICENSE_TIER_PREMIUM, max_groups=-1)
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            from database.models import UserLicenseCache
            expiration = datetime.now() + timedelta(days=30)
            cache = UserLicenseCache(
                user_email=email,
                license_tier=LICENSE_TIER_PREMIUM,
                expiration_date=expiration,
                max_groups=-1,
                is_active=True
            )
            test_db_manager.save_license_cache(cache)
            
            can_add, error = license_service.can_add_group(email, uid)
            assert can_add is True
            assert error is None
    
    def test_can_add_group_expired_license(self, test_db_manager, mock_firebase_config):
        """Test can_add_group with expired license."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            from database.models import UserLicenseCache
            expiration = datetime.now() - timedelta(days=1)
            cache = UserLicenseCache(
                user_email=email,
                license_tier=LICENSE_TIER_SILVER,
                expiration_date=expiration,
                max_groups=3,
                is_active=True
            )
            test_db_manager.save_license_cache(cache)
            
            can_add, error = license_service.can_add_group(email, uid)
            assert can_add is False
            assert 'expired' in error.lower()
    
    def test_can_add_device_success(self, test_db_manager, mock_firebase_config):
        """Test can_add_device when device can be added."""
        uid = 'test_user_123'
        email = 'test@example.com'
        device_id = 'test_device_123'
        
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_license(uid, tier=LICENSE_TIER_GOLD, max_devices=2, active_device_ids=[])
        mock_firebase_config.get_active_devices = Mock(return_value=[])
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            from database.models import UserLicenseCache
            expiration = datetime.now() + timedelta(days=30)
            cache = UserLicenseCache(
                user_email=email,
                license_tier=LICENSE_TIER_GOLD,
                expiration_date=expiration,
                max_devices=2,
                is_active=True
            )
            test_db_manager.save_license_cache(cache)
            
            can_add, error, active_devices = license_service.can_add_device(device_id, email, uid)
            assert can_add is True
            assert error is None
            assert isinstance(active_devices, list)
    
    def test_can_add_device_already_registered(self, test_db_manager, mock_firebase_config):
        """Test can_add_device when device is already registered."""
        uid = 'test_user_123'
        email = 'test@example.com'
        device_id = 'test_device_123'
        
        mock_firebase_config.initialize()
        mock_firebase_config.get_active_devices = Mock(return_value=[device_id])
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            from database.models import UserLicenseCache
            expiration = datetime.now() + timedelta(days=30)
            cache = UserLicenseCache(
                user_email=email,
                license_tier=LICENSE_TIER_SILVER,
                expiration_date=expiration,
                max_devices=1,
                is_active=True
            )
            test_db_manager.save_license_cache(cache)
            
            can_add, error, active_devices = license_service.can_add_device(device_id, email, uid)
            assert can_add is True  # Already registered, so can add
            assert error is None
    
    def test_can_add_device_limit_reached(self, test_db_manager, mock_firebase_config):
        """Test can_add_device when device limit is reached."""
        uid = 'test_user_123'
        email = 'test@example.com'
        device_id = 'new_device_456'
        
        mock_firebase_config.initialize()
        mock_firebase_config.get_active_devices = Mock(return_value=['device_1'])
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            from database.models import UserLicenseCache
            expiration = datetime.now() + timedelta(days=30)
            cache = UserLicenseCache(
                user_email=email,
                license_tier=LICENSE_TIER_SILVER,
                expiration_date=expiration,
                max_devices=1,
                is_active=True
            )
            test_db_manager.save_license_cache(cache)
            
            can_add, error, active_devices = license_service.can_add_device(device_id, email, uid)
            assert can_add is False
            assert 'device limit' in error.lower()
            assert len(active_devices) == 1
    
    def test_can_add_device_expired_license(self, test_db_manager, mock_firebase_config):
        """Test can_add_device with expired license."""
        uid = 'test_user_123'
        email = 'test@example.com'
        device_id = 'test_device_123'
        
        mock_firebase_config.initialize()
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            from database.models import UserLicenseCache
            expiration = datetime.now() - timedelta(days=1)
            cache = UserLicenseCache(
                user_email=email,
                license_tier=LICENSE_TIER_SILVER,
                expiration_date=expiration,
                max_devices=1,
                is_active=True
            )
            test_db_manager.save_license_cache(cache)
            
            can_add, error, active_devices = license_service.can_add_device(device_id, email, uid)
            assert can_add is False
            assert 'expired' in error.lower()
    
    def test_get_active_devices(self, test_db_manager, mock_firebase_config):
        """Test get_active_devices."""
        uid = 'test_user_123'
        device_ids = ['device_1', 'device_2']
        
        mock_firebase_config.initialize()
        mock_firebase_config.get_active_devices = Mock(return_value=device_ids)
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            devices = license_service.get_active_devices(uid)
            
            assert devices == device_ids
    
    def test_enforce_group_limit(self, test_db_manager, mock_firebase_config):
        """Test enforce_group_limit."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            from database.models import UserLicenseCache
            expiration = datetime.now() + timedelta(days=30)
            cache = UserLicenseCache(
                user_email=email,
                license_tier=LICENSE_TIER_SILVER,
                expiration_date=expiration,
                max_groups=3,
                is_active=True
            )
            test_db_manager.save_license_cache(cache)
            
            can_add = license_service.enforce_group_limit(email)
            assert can_add is True
    
    def test_get_license_info(self, test_db_manager, mock_firebase_config):
        """Test get_license_info."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        mock_firebase_config.get_active_devices = Mock(return_value=['device_1'])
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            from database.models import UserLicenseCache
            expiration = datetime.now() + timedelta(days=30)
            cache = UserLicenseCache(
                user_email=email,
                license_tier=LICENSE_TIER_GOLD,
                expiration_date=expiration,
                max_devices=2,
                max_groups=10,
                is_active=True
            )
            test_db_manager.save_license_cache(cache)
            
            info = license_service.get_license_info(email, uid)
            
            assert info['tier'] == LICENSE_TIER_GOLD
            assert info['is_active'] is True
            assert info['max_devices'] == 2
            assert info['max_groups'] == 10
            assert info['current_devices'] == 1
            assert 'tier_name' in info
            assert 'price_usd' in info
            assert 'price_khr' in info
    
    def test_license_cache_encryption(self, test_db_manager):
        """Test that license cache fields are encrypted when saved."""
        email = 'test@example.com'
        expiration = datetime.now() + timedelta(days=30)
        
        cache = UserLicenseCache(
            user_email=email,
            license_tier=LICENSE_TIER_SILVER,
            expiration_date=expiration,
            max_devices=2,
            max_groups=5,
            max_accounts=1,
            max_account_actions=2,
            is_active=True,
            last_synced=datetime.now()
        )
        
        # Save license cache
        result = test_db_manager.save_license_cache(cache)
        assert result is not None
        
        # Check that data in database is encrypted (not plain text)
        with test_db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT license_tier, expiration_date, max_devices, max_groups, is_active FROM user_license_cache WHERE user_email = ?",
                (email,)
            )
            row = cursor.fetchone()
            assert row is not None
            
            # Encrypted values should be base64-encoded strings, not plain text
            assert row['license_tier'] != LICENSE_TIER_SILVER
            assert row['max_devices'] != 2
            assert row['max_groups'] != 5
            assert row['is_active'] != 1  # Should be encrypted string, not boolean
    
    def test_license_cache_decryption(self, test_db_manager):
        """Test that license cache fields are decrypted when retrieved."""
        email = 'test@example.com'
        expiration = datetime.now() + timedelta(days=30)
        original_tier = LICENSE_TIER_GOLD
        original_max_devices = 3
        original_max_groups = 7
        
        cache = UserLicenseCache(
            user_email=email,
            license_tier=original_tier,
            expiration_date=expiration,
            max_devices=original_max_devices,
            max_groups=original_max_groups,
            max_accounts=2,
            max_account_actions=3,
            is_active=True,
            last_synced=datetime.now()
        )
        
        # Save license cache
        test_db_manager.save_license_cache(cache)
        
        # Retrieve and verify decryption
        retrieved_cache = test_db_manager.get_license_cache(email)
        assert retrieved_cache is not None
        assert retrieved_cache.license_tier == original_tier
        assert retrieved_cache.max_devices == original_max_devices
        assert retrieved_cache.max_groups == original_max_groups
        assert retrieved_cache.is_active is True
        assert retrieved_cache.expiration_date is not None
    
    def test_license_cache_encryption_with_none_values(self, test_db_manager):
        """Test that None values are handled correctly in encryption."""
        email = 'test@example.com'
        
        cache = UserLicenseCache(
            user_email=email,
            license_tier=LICENSE_TIER_SILVER,
            expiration_date=None,
            max_devices=1,
            max_groups=3,
            max_accounts=1,
            max_account_actions=2,
            is_active=True,
            last_synced=None
        )
        
        # Save license cache
        result = test_db_manager.save_license_cache(cache)
        assert result is not None
        
        # Retrieve and verify None values are preserved
        retrieved_cache = test_db_manager.get_license_cache(email)
        assert retrieved_cache is not None
        assert retrieved_cache.expiration_date is None
        assert retrieved_cache.last_synced is None

