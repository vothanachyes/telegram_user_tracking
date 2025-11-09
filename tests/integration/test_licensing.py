"""
Integration tests for licensing enforcement.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from services.auth_service import AuthService
from services.license_service import LicenseService
from database.models.auth import UserLicenseCache
from database.models.telegram import TelegramGroup
from utils.constants import (
    LICENSE_TIER_BRONZE, LICENSE_TIER_SILVER, LICENSE_TIER_GOLD, LICENSE_TIER_PREMIUM,
    DEFAULT_LICENSE_TIER, LICENSE_PRICING
)


class TestLicensing:
    """Integration tests for licensing enforcement."""
    
    def test_license_tier_enforcement_on_group_creation(self, test_db_manager, mock_firebase_config):
        """Test license tier enforcement when creating groups."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_license(uid, tier=LICENSE_TIER_SILVER, max_groups=3)
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            # Save license cache
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
            
            # Create 2 groups (under limit)
            for i in range(2):
                group = TelegramGroup(
                    group_id=i + 1,
                    group_name=f'Group {i + 1}',
                    group_username=None,
                    total_messages=0
                )
                test_db_manager.save_group(group)
            
            # Should be able to add one more
            can_add, error = license_service.can_add_group(email, uid)
            assert can_add is True
            assert error is None
            
            # Add third group (at limit)
            group = TelegramGroup(
                group_id=3,
                group_name='Group 3',
                group_username=None,
                total_messages=0
            )
            test_db_manager.save_group(group)
            
            # Should not be able to add more
            can_add, error = license_service.can_add_group(email, uid)
            assert can_add is False
            assert 'group limit' in error.lower()
    
    def test_device_limit_enforcement_on_login(self, test_db_manager, mock_firebase_config, mock_requests_post):
        """Test device limit enforcement during login."""
        uid = 'test_user_123'
        email = 'test@example.com'
        password = 'password123'
        device_id = 'new_device_456'
        
        # Setup with device limit reached
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_user(uid, email)
        mock_firebase_config.create_mock_license(
            uid,
            tier=LICENSE_TIER_SILVER,
            max_devices=1,
            active_device_ids=['device_1']
        )
        mock_firebase_config.get_active_devices = Mock(return_value=['device_1'])
        
        # Mock Firebase REST API
        from tests.fixtures.firebase_mocks import create_mock_requests_response
        mock_response = create_mock_requests_response(200, {
            'idToken': 'mock_id_token',
            'email': email
        })
        mock_requests_post.return_value = mock_response
        
        decoded_token = {
            'uid': uid,
            'email': email,
            'device_id': None
        }
        mock_firebase_config.verify_token = Mock(return_value=decoded_token)
        mock_firebase_config.get_user = Mock(return_value={
            'uid': uid,
            'email': email,
            'disabled': False
        })
        
        with patch('services.auth_service.firebase_config', mock_firebase_config):
            with patch('services.license_service.firebase_config', mock_firebase_config):
                with patch('services.auth_service.FIREBASE_WEB_API_KEY', 'test_api_key'):
                    with patch.object(AuthService, 'device_id', device_id):
                        auth_service = AuthService(test_db_manager)
                        auth_service.initialize()
                        
                        # Login should fail due to device limit
                        success, error = auth_service.login(email, password)
                        
                        assert success is False
                        assert 'device limit' in error.lower()
    
    def test_license_expiration_warnings(self, test_db_manager, mock_firebase_config):
        """Test license expiration warnings."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            # License expiring in 5 days (should trigger warning)
            expiration = datetime.now() + timedelta(days=5)
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
            assert status['expired'] is False
            assert status['days_until_expiration'] == 5
            assert status['days_until_expiration'] < 7  # Should trigger warning
    
    def test_license_sync_from_firebase(self, test_db_manager, mock_firebase_config):
        """Test license sync from Firebase."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_license(
            uid,
            tier=LICENSE_TIER_GOLD,
            max_devices=2,
            max_groups=10,
            expiration_days=30
        )
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            # Sync from Firebase
            result = license_service.sync_from_firebase(email, uid)
            
            assert result is True
            
            # Check cache was updated
            cache = test_db_manager.get_license_cache(email)
            assert cache is not None
            assert cache.license_tier == LICENSE_TIER_GOLD
            assert cache.max_devices == 2
            assert cache.max_groups == 10
            assert cache.is_active is True
    
    def test_default_license_creation_for_new_users(self, test_db_manager, mock_firebase_config):
        """Test default license creation for new users."""
        uid = 'new_user_456'
        email = 'newuser@example.com'
        
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
            
            # Sync should create default license
            result = license_service.sync_from_firebase(email, uid)
            
            assert result is True
            assert mock_firebase_config.set_user_license.called
            
            # Check default license was created
            cache = test_db_manager.get_license_cache(email)
            assert cache is not None
            assert cache.license_tier == DEFAULT_LICENSE_TIER
    
    def test_license_info_retrieval(self, test_db_manager, mock_firebase_config):
        """Test comprehensive license info retrieval."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_license(
            uid,
            tier=LICENSE_TIER_PREMIUM,
            max_devices=5,
            max_groups=-1,
            active_device_ids=['device_1', 'device_2'],
            expiration_days=30
        )
        mock_firebase_config.get_active_devices = Mock(return_value=['device_1', 'device_2'])
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            # Save license cache
            expiration = datetime.now() + timedelta(days=30)
            cache = UserLicenseCache(
                user_email=email,
                license_tier=LICENSE_TIER_PREMIUM,
                expiration_date=expiration,
                max_devices=5,
                max_groups=-1,
                is_active=True
            )
            test_db_manager.save_license_cache(cache)
            
            # Create some groups
            for i in range(5):
                group = TelegramGroup(
                    group_id=i + 1,
                    group_name=f'Group {i + 1}',
                    group_username=None,
                    total_messages=0
                )
                test_db_manager.save_group(group)
            
            # Get license info
            info = license_service.get_license_info(email, uid)
            
            assert info['tier'] == LICENSE_TIER_PREMIUM
            assert info['tier_name'] == 'Premium'
            assert info['is_active'] is True
            assert info['expired'] is False
            assert info['max_devices'] == 5
            assert info['max_groups'] == -1  # Unlimited
            assert info['current_devices'] == 2
            assert info['current_groups'] == 5
            assert info['price_usd'] == LICENSE_PRICING[LICENSE_TIER_PREMIUM]['price_usd']
            assert info['price_khr'] == LICENSE_PRICING[LICENSE_TIER_PREMIUM]['price_khr']
            assert 'unlimited_groups' in info['features']
    
    def test_bronze_tier_auto_renewal(self, test_db_manager, mock_firebase_config):
        """Test Bronze tier auto-renewal on expiration."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        
        # Create expired Bronze license
        expired_date = datetime.now() - timedelta(days=1)
        expired_license = {
            'license_tier': LICENSE_TIER_BRONZE,
            'max_devices': 1,
            'max_groups': 1,
            'active_device_ids': [],
            'expiration_date': expired_date.isoformat()
        }
        mock_firebase_config.set_user_license = Mock(return_value=True)
        
        # Mock get_user_license to return expired license, then renewed
        renewed_license = expired_license.copy()
        renewed_license['expiration_date'] = (datetime.now() + timedelta(days=7)).isoformat()
        mock_firebase_config.get_user_license = Mock(side_effect=[expired_license, renewed_license])
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            # Sync should auto-renew Bronze license
            result = license_service.sync_from_firebase(email, uid)
            
            assert result is True
            assert mock_firebase_config.set_user_license.called
            
            # Check license was renewed
            cache = test_db_manager.get_license_cache(email)
            assert cache is not None
            assert cache.license_tier == LICENSE_TIER_BRONZE
            assert cache.expiration_date > datetime.now()
    
    def test_all_tier_limits(self, test_db_manager, mock_firebase_config):
        """Test limits for all license tiers."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        
        tiers = [
            (LICENSE_TIER_BRONZE, 1, 1),
            (LICENSE_TIER_SILVER, 1, 3),
            (LICENSE_TIER_GOLD, 2, 10),
            (LICENSE_TIER_PREMIUM, 5, -1)  # -1 means unlimited
        ]
        
        for tier, max_devices, max_groups in tiers:
            mock_firebase_config.create_mock_license(
                uid,
                tier=tier,
                max_devices=max_devices,
                max_groups=max_groups,
                expiration_days=30
            )
            
            with patch('services.license_service.firebase_config', mock_firebase_config):
                license_service = LicenseService(test_db_manager)
                
                # Save license cache
                expiration = datetime.now() + timedelta(days=30)
                cache = UserLicenseCache(
                    user_email=email,
                    license_tier=tier,
                    expiration_date=expiration,
                    max_devices=max_devices,
                    max_groups=max_groups,
                    is_active=True
                )
                test_db_manager.save_license_cache(cache)
                
                # Check limits
                status = license_service.check_license_status(email, uid)
                assert status['max_devices'] == max_devices
                assert status['max_groups'] == max_groups
                
                # Check group limit
                if max_groups == -1:
                    # Premium has unlimited groups
                    can_add, error = license_service.can_add_group(email, uid)
                    assert can_add is True
                else:
                    # Other tiers have limits
                    can_add, error = license_service.can_add_group(email, uid)
                    assert can_add is True  # No groups created yet
                
                # Clean up for next iteration
                test_db_manager.delete_license_cache(email)
    
    def test_license_cache_encryption_integration(self, test_db_manager, mock_firebase_config):
        """Integration test for license cache encryption with license service."""
        uid = 'test_user_123'
        email = 'test@example.com'
        
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_license(uid, tier=LICENSE_TIER_GOLD, expiration_days=30)
        
        with patch('services.license_service.firebase_config', mock_firebase_config):
            license_service = LicenseService(test_db_manager)
            
            # Sync from Firebase (this will save encrypted cache)
            result = license_service.sync_from_firebase(email, uid)
            assert result is True
            
            # Verify cache was saved and can be retrieved (decrypted)
            cache = test_db_manager.get_license_cache(email)
            assert cache is not None
            assert cache.license_tier == LICENSE_TIER_GOLD
            assert cache.is_active is True
            
            # Verify license service can use the encrypted cache
            tier = license_service.get_user_tier(email)
            assert tier == LICENSE_TIER_GOLD
            
            status = license_service.check_license_status(email, uid)
            assert status['is_active'] is True
            assert status['tier'] == LICENSE_TIER_GOLD

