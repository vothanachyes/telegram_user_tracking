"""
Unit tests for AuthService.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from services.auth_service import AuthService
from tests.fixtures.firebase_mocks import create_mock_requests_response


class TestAuthService:
    """Test cases for AuthService."""
    
    def test_initialize_success(self, test_db_manager, mock_firebase_config):
        """Test successful Firebase initialization."""
        mock_firebase_config.initialize()
        
        with patch('services.auth_service.firebase_config', mock_firebase_config):
            auth_service = AuthService(test_db_manager)
            result = auth_service.initialize()
            
            assert result is True
            assert mock_firebase_config.is_initialized() is True
    
    def test_initialize_failure(self, test_db_manager):
        """Test failed Firebase initialization."""
        # Mock firebase_config.initialize to return False
        with patch('services.auth_service.firebase_config') as mock_config:
            mock_config.initialize = Mock(return_value=False)
            mock_config.is_initialized = Mock(return_value=False)
            
            auth_service = AuthService(test_db_manager)
            result = auth_service.initialize()
            
            assert result is False
    
    def test_device_id_property(self, test_db_manager):
        """Test device ID generation."""
        auth_service = AuthService(test_db_manager)
        device_id = auth_service.device_id
        
        assert device_id is not None
        assert isinstance(device_id, str)
        assert len(device_id) > 0
        
        # Should be consistent
        assert auth_service.device_id == device_id
    
    def test_authenticate_with_email_password_success(self, test_db_manager, mock_requests_post):
        """Test successful authentication with email and password."""
        mock_response = create_mock_requests_response(200, {
            'idToken': 'mock_token_123',
            'email': 'test@example.com'
        })
        mock_requests_post.return_value = mock_response
        
        with patch('services.auth_service.FIREBASE_WEB_API_KEY', 'test_api_key'):
            auth_service = AuthService(test_db_manager)
            success, error, token = auth_service.authenticate_with_email_password(
                'test@example.com', 'password123'
            )
            
            assert success is True
            assert error is None
            assert token == 'mock_token_123'
    
    def test_authenticate_with_email_password_invalid_credentials(self, test_db_manager, mock_requests_post):
        """Test authentication with invalid credentials."""
        mock_response = create_mock_requests_response(400, {
            'error': {
                'message': 'INVALID_PASSWORD'
            }
        })
        mock_requests_post.return_value = mock_response
        
        with patch('services.auth_service.FIREBASE_WEB_API_KEY', 'test_api_key'):
            auth_service = AuthService(test_db_manager)
            success, error, token = auth_service.authenticate_with_email_password(
                'test@example.com', 'wrong_password'
            )
            
            assert success is False
            assert error == 'Invalid password'
            assert token is None
    
    def test_authenticate_with_email_password_email_not_found(self, test_db_manager, mock_requests_post):
        """Test authentication with non-existent email."""
        mock_response = create_mock_requests_response(400, {
            'error': {
                'message': 'EMAIL_NOT_FOUND'
            }
        })
        mock_requests_post.return_value = mock_response
        
        with patch('services.auth_service.FIREBASE_WEB_API_KEY', 'test_api_key'):
            auth_service = AuthService(test_db_manager)
            success, error, token = auth_service.authenticate_with_email_password(
                'nonexistent@example.com', 'password123'
            )
            
            assert success is False
            assert error == 'No account found with this email address'
            assert token is None
    
    def test_authenticate_with_email_password_network_error(self, test_db_manager, mock_requests_post):
        """Test authentication with network error."""
        import requests
        mock_requests_post.side_effect = requests.exceptions.RequestException("Network error")
        
        with patch('services.auth_service.FIREBASE_WEB_API_KEY', 'test_api_key'):
            auth_service = AuthService(test_db_manager)
            success, error, token = auth_service.authenticate_with_email_password(
                'test@example.com', 'password123'
            )
            
            assert success is False
            assert 'Network error' in error
            assert token is None
    
    def test_authenticate_with_email_password_no_api_key(self, test_db_manager):
        """Test authentication without Firebase API key."""
        with patch('services.auth_service.FIREBASE_WEB_API_KEY', None):
            auth_service = AuthService(test_db_manager)
            success, error, token = auth_service.authenticate_with_email_password(
                'test@example.com', 'password123'
            )
            
            assert success is False
            assert 'Firebase Web API key not configured' in error
            assert token is None
    
    def test_login_success(self, test_db_manager, mock_firebase_config, sample_user_data, sample_decoded_token):
        """Test successful login."""
        uid = sample_user_data['uid']
        email = sample_user_data['email']
        
        # Setup mocks
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_user(uid, email)
        mock_firebase_config.create_mock_token('test_token', uid, email, device_id=None)
        mock_firebase_config.verify_token = Mock(return_value=sample_decoded_token)
        mock_firebase_config.get_user = Mock(return_value=sample_user_data)
        mock_firebase_config.set_custom_claims = Mock(return_value=True)
        mock_firebase_config.get_active_devices = Mock(return_value=[])
        mock_firebase_config.add_device_to_license = Mock(return_value=True)
        
        with patch('services.auth_service.firebase_config', mock_firebase_config):
            auth_service = AuthService(test_db_manager)
            auth_service.initialize()
            
            success, error = auth_service.login(email, 'password123', id_token='test_token')
            
            assert success is True
            assert error is None
            assert auth_service.is_logged_in() is True
            assert auth_service.get_current_user() == sample_user_data
    
    def test_login_invalid_token(self, test_db_manager, mock_firebase_config):
        """Test login with invalid token."""
        mock_firebase_config.initialize()
        mock_firebase_config.verify_token = Mock(return_value=None)
        
        with patch('services.auth_service.firebase_config', mock_firebase_config):
            auth_service = AuthService(test_db_manager)
            auth_service.initialize()
            
            success, error = auth_service.login('test@example.com', 'password123', id_token='invalid_token')
            
            assert success is False
            assert 'Invalid authentication token' in error
    
    def test_login_disabled_user(self, test_db_manager, mock_firebase_config, sample_decoded_token):
        """Test login with disabled user."""
        uid = sample_decoded_token['uid']
        disabled_user = {
            'uid': uid,
            'email': 'test@example.com',
            'disabled': True
        }
        
        mock_firebase_config.initialize()
        mock_firebase_config.verify_token = Mock(return_value=sample_decoded_token)
        mock_firebase_config.get_user = Mock(return_value=disabled_user)
        
        with patch('services.auth_service.firebase_config', mock_firebase_config):
            auth_service = AuthService(test_db_manager)
            auth_service.initialize()
            
            success, error = auth_service.login('test@example.com', 'password123', id_token='test_token')
            
            assert success is False
            assert 'User account is disabled' in error
    
    def test_login_single_device_enforcement(self, test_db_manager, mock_firebase_config, sample_decoded_token):
        """Test single-device enforcement on login."""
        uid = sample_decoded_token['uid']
        email = sample_decoded_token['email']
        
        # Set device_id in token to different device
        sample_decoded_token['device_id'] = 'other_device_456'
        
        mock_firebase_config.initialize()
        mock_firebase_config.verify_token = Mock(return_value=sample_decoded_token)
        
        with patch('services.auth_service.firebase_config', mock_firebase_config):
            with patch.object(AuthService, 'device_id', 'test_device_123'):
                auth_service = AuthService(test_db_manager)
                auth_service.initialize()
                
                success, error = auth_service.login(email, 'password123', id_token='test_token')
                
                assert success is False
                assert 'already logged in on another device' in error
    
    def test_login_device_limit_reached(self, test_db_manager, mock_firebase_config, sample_user_data, sample_decoded_token):
        """Test login when device limit is reached."""
        uid = sample_user_data['uid']
        email = sample_user_data['email']
        
        mock_firebase_config.initialize()
        mock_firebase_config.create_mock_user(uid, email)
        mock_firebase_config.create_mock_license(uid, tier='silver', max_devices=1, active_device_ids=['device_1'])
        mock_firebase_config.verify_token = Mock(return_value=sample_decoded_token)
        mock_firebase_config.get_user = Mock(return_value=sample_user_data)
        mock_firebase_config.get_active_devices = Mock(return_value=['device_1'])
        
        with patch('services.auth_service.firebase_config', mock_firebase_config):
            with patch.object(AuthService, 'device_id', 'test_device_123'):
                auth_service = AuthService(test_db_manager)
                auth_service.initialize()
                
                success, error = auth_service.login(email, 'password123', id_token='test_token')
                
                assert success is False
                assert 'device limit' in error.lower()
    
    def test_logout_success(self, test_db_manager, mock_firebase_config, sample_user_data):
        """Test successful logout."""
        uid = sample_user_data['uid']
        email = sample_user_data['email']
        
        mock_firebase_config.initialize()
        mock_firebase_config.set_custom_claims = Mock(return_value=True)
        
        with patch('services.auth_service.firebase_config', mock_firebase_config):
            auth_service = AuthService(test_db_manager)
            auth_service.initialize()
            auth_service.current_user = sample_user_data
            
            result = auth_service.logout()
            
            assert result is True
            assert auth_service.is_logged_in() is False
            assert auth_service.get_current_user() is None
    
    def test_logout_no_user(self, test_db_manager):
        """Test logout when no user is logged in."""
        auth_service = AuthService(test_db_manager)
        result = auth_service.logout()
        
        assert result is True
        assert auth_service.is_logged_in() is False
    
    def test_is_logged_in(self, test_db_manager, sample_user_data):
        """Test is_logged_in check."""
        auth_service = AuthService(test_db_manager)
        
        assert auth_service.is_logged_in() is False
        
        auth_service.current_user = sample_user_data
        assert auth_service.is_logged_in() is True
    
    def test_get_current_user(self, test_db_manager, sample_user_data):
        """Test get_current_user."""
        auth_service = AuthService(test_db_manager)
        
        assert auth_service.get_current_user() is None
        
        auth_service.current_user = sample_user_data
        assert auth_service.get_current_user() == sample_user_data
    
    def test_get_user_email(self, test_db_manager, sample_user_data):
        """Test get_user_email."""
        auth_service = AuthService(test_db_manager)
        
        assert auth_service.get_user_email() is None
        
        auth_service.current_user = sample_user_data
        assert auth_service.get_user_email() == sample_user_data['email']
    
    def test_get_user_display_name(self, test_db_manager, sample_user_data):
        """Test get_user_display_name."""
        auth_service = AuthService(test_db_manager)
        
        assert auth_service.get_user_display_name() is None
        
        auth_service.current_user = sample_user_data
        assert auth_service.get_user_display_name() == sample_user_data.get('display_name')

