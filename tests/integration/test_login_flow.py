"""
Integration tests for login flow.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from services.auth_service import AuthService
from services.license_service import LicenseService
from tests.fixtures.firebase_mocks import create_mock_requests_response
from utils.credential_storage import credential_storage
from database.models.auth import LoginCredential, UserLicenseCache


class TestLoginFlow:
    """Integration tests for complete login flow."""
    
    def test_complete_login_flow_success(self, test_db_manager, mock_firebase_config, mock_requests_post):
        """Test complete login flow with valid credentials."""
        uid = 'test_user_123'
        email = 'test@example.com'
        password = 'password123'
        device_id = 'test_device_123'
        
        # Setup Firebase mocks
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_user(uid, email)
        mock_firebase_config.create_mock_license(uid, tier='silver', max_devices=1, active_device_ids=[])
        mock_firebase_config.get_active_devices = Mock(return_value=[])
        mock_firebase_config.add_device_to_license = Mock(return_value=True)
        
        # Mock Firebase REST API authentication
        mock_response = create_mock_requests_response(200, {
            'idToken': 'mock_id_token',
            'email': email
        })
        mock_requests_post.return_value = mock_response
        
        # Mock token verification
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
        mock_firebase_config.set_custom_claims = Mock(return_value=True)
        
        with patch('services.auth_service.firebase_config', mock_firebase_config):
            with patch('services.license_service.firebase_config', mock_firebase_config):
                with patch('services.auth_service.FIREBASE_WEB_API_KEY', 'test_api_key'):
                    with patch.object(AuthService, 'device_id', device_id):
                        auth_service = AuthService(test_db_manager)
                        auth_service.initialize()
                        
                        # Perform login
                        success, error = auth_service.login(email, password)
                        
                        assert success is True
                        assert error is None
                        assert auth_service.is_logged_in() is True
                        assert auth_service.get_current_user() is not None
                        assert auth_service.get_user_email() == email
    
    def test_login_with_saved_credentials(self, test_db_manager, mock_firebase_config, mock_requests_post):
        """Test login with saved credentials (remember me)."""
        uid = 'test_user_123'
        email = 'test@example.com'
        password = 'password123'
        
        # Save encrypted credentials
        encrypted_password = credential_storage.encrypt(password)
        credential = LoginCredential(
            email=email,
            encrypted_password=encrypted_password
        )
        test_db_manager.save_login_credential(email, encrypted_password)
        
        # Setup Firebase mocks
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_user(uid, email)
        mock_firebase_config.create_mock_license(uid, tier='silver', max_devices=1, active_device_ids=[])
        mock_firebase_config.get_active_devices = Mock(return_value=[])
        mock_firebase_config.add_device_to_license = Mock(return_value=True)
        
        # Mock Firebase REST API
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
        mock_firebase_config.set_custom_claims = Mock(return_value=True)
        
        with patch('services.auth_service.firebase_config', mock_firebase_config):
            with patch('services.license_service.firebase_config', mock_firebase_config):
                with patch('services.auth_service.FIREBASE_WEB_API_KEY', 'test_api_key'):
                    auth_service = AuthService(test_db_manager)
                    auth_service.initialize()
                    
                    # Retrieve saved credentials
                    saved_credential = test_db_manager.get_login_credential()
                    assert saved_credential is not None
                    assert saved_credential.email == email
                    
                    # Decrypt password
                    decrypted_password = credential_storage.decrypt(saved_credential.encrypted_password)
                    assert decrypted_password == password
                    
                    # Login with saved credentials
                    success, error = auth_service.login(email, decrypted_password)
                    
                    assert success is True
                    assert error is None
    
    def test_login_failure_invalid_credentials(self, test_db_manager, mock_requests_post):
        """Test login failure with invalid credentials."""
        email = 'test@example.com'
        password = 'wrong_password'
        
        # Mock Firebase REST API to return error
        mock_response = create_mock_requests_response(400, {
            'error': {
                'message': 'INVALID_PASSWORD'
            }
        })
        mock_requests_post.return_value = mock_response
        
        with patch('services.auth_service.FIREBASE_WEB_API_KEY', 'test_api_key'):
            auth_service = AuthService(test_db_manager)
            success, error = auth_service.login(email, password)
            
            assert success is False
            assert 'Invalid password' in error
            assert auth_service.is_logged_in() is False
    
    def test_login_with_expired_license(self, test_db_manager, mock_firebase_config, mock_requests_post):
        """Test login with expired license."""
        uid = 'test_user_123'
        email = 'test@example.com'
        password = 'password123'
        
        # Setup Firebase mocks
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_user(uid, email)
        
        # Create expired license
        expired_date = datetime.now() - timedelta(days=1)
        mock_firebase_config.create_mock_license(
            uid,
            tier='silver',
            max_devices=1,
            active_device_ids=[],
            expiration_days=-1
        )
        mock_firebase_config.get_active_devices = Mock(return_value=[])
        
        # Mock Firebase REST API
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
        
        # Save expired license cache
        cache = UserLicenseCache(
            user_email=email,
            license_tier='silver',
            expiration_date=expired_date,
            max_devices=1,
            max_groups=3,
            is_active=True
        )
        test_db_manager.save_license_cache(cache)
        
        with patch('services.auth_service.firebase_config', mock_firebase_config):
            with patch('services.license_service.firebase_config', mock_firebase_config):
                with patch('services.auth_service.FIREBASE_WEB_API_KEY', 'test_api_key'):
                    auth_service = AuthService(test_db_manager)
                    auth_service.initialize()
                    
                    # Login should still succeed, but license check will show expired
                    success, error = auth_service.login(email, password)
                    
                    # Login succeeds, but license is expired
                    assert success is True
                    
                    # Check license status
                    license_service = LicenseService(test_db_manager)
                    status = license_service.check_license_status(email, uid)
                    assert status['expired'] is True
    
    def test_login_with_device_limit_reached(self, test_db_manager, mock_firebase_config, mock_requests_post):
        """Test login when device limit is reached."""
        uid = 'test_user_123'
        email = 'test@example.com'
        password = 'password123'
        device_id = 'new_device_456'
        
        # Setup Firebase mocks with device limit reached
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_user(uid, email)
        mock_firebase_config.create_mock_license(
            uid,
            tier='silver',
            max_devices=1,
            active_device_ids=['device_1']
        )
        mock_firebase_config.get_active_devices = Mock(return_value=['device_1'])
        
        # Mock Firebase REST API
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
                        
                        success, error = auth_service.login(email, password)
                        
                        assert success is False
                        assert 'device limit' in error.lower()
    
    def test_login_with_custom_claim_device_id(self, test_db_manager, mock_firebase_config, mock_requests_post):
        """Test login when token has custom claim device_id (should not block login).
        
        Custom claim device_id is ignored - device limits are enforced by license service.
        """
        uid = 'test_user_123'
        email = 'test@example.com'
        password = 'password123'
        device_id = 'test_device_123'
        other_device_id = 'other_device_456'
        
        # Setup Firebase mocks
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_user(uid, email)
        mock_firebase_config.create_mock_license(uid, tier='silver', max_devices=1, active_device_ids=[])
        mock_firebase_config.get_active_devices = Mock(return_value=[])
        
        # Mock Firebase REST API
        mock_response = create_mock_requests_response(200, {
            'idToken': 'mock_id_token',
            'email': email
        })
        mock_requests_post.return_value = mock_response
        
        # Token has different device_id in custom claim (this is now ignored)
        decoded_token = {
            'uid': uid,
            'email': email,
            'device_id': other_device_id
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
                        
                        success, error = auth_service.login(email, password)
                        
                        # Login should succeed - custom claim device_id is ignored
                        # Device limits are enforced by license service instead
                        assert success is True
                        assert error is None
    
    def test_credential_encryption_decryption(self):
        """Test credential encryption and decryption."""
        password = 'test_password_123'
        
        # Encrypt
        encrypted = credential_storage.encrypt(password)
        assert encrypted != password
        assert isinstance(encrypted, str)
        
        # Decrypt
        decrypted = credential_storage.decrypt(encrypted)
        assert decrypted == password
    
    def test_credential_storage_and_retrieval(self, test_db_manager):
        """Test credential storage and retrieval from database."""
        email = 'test@example.com'
        password = 'test_password_123'
        
        # Encrypt and save
        encrypted_password = credential_storage.encrypt(password)
        test_db_manager.save_login_credential(email, encrypted_password)
        
        # Retrieve
        credential = test_db_manager.get_login_credential()
        assert credential is not None
        assert credential.email == email
        assert credential.encrypted_password == encrypted_password
        
        # Decrypt
        decrypted_password = credential_storage.decrypt(credential.encrypted_password)
        assert decrypted_password == password
    
    def test_credential_deletion(self, test_db_manager):
        """Test credential deletion."""
        email = 'test@example.com'
        password = 'test_password_123'
        
        # Save credential
        encrypted_password = credential_storage.encrypt(password)
        test_db_manager.save_login_credential(email, encrypted_password)
        
        # Verify it exists
        credential = test_db_manager.get_login_credential()
        assert credential is not None
        
        # Delete
        test_db_manager.delete_login_credential()
        
        # Verify it's deleted
        credential = test_db_manager.get_login_credential()
        assert credential is None

