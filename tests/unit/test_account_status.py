"""
Unit tests for account status checking.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from database.managers.telegram_credential_manager import TelegramCredentialManager
from database.models.telegram import TelegramCredential
from services.telegram.telegram_service import TelegramService
from services.telegram.account_status_service import AccountStatusService
from tests.fixtures.db_fixtures import create_test_db_manager


class TestAccountStatus:
    """Test account status checking functionality."""
    
    @pytest.fixture
    def db_manager(self):
        """Create test database manager."""
        return create_test_db_manager()
    
    @pytest.fixture
    def telegram_service(self, db_manager):
        """Create TelegramService with mocked client manager."""
        service = TelegramService(db_manager)
        # Mock client manager to avoid actual Telegram API calls
        service.client_manager = Mock()
        return service
    
    @pytest.fixture
    def sample_credential(self):
        """Create sample Telegram credential."""
        return TelegramCredential(
            id=1,
            phone_number="+1234567890",
            session_string="/path/to/session",
            is_default=True,
            last_used=None,
            created_at=None
        )
    
    @pytest.mark.asyncio
    async def test_check_account_status_active(self, telegram_service, sample_credential):
        """Test checking status for active account."""
        # Mock successful connection
        mock_client = Mock()
        mock_client.get_me = AsyncMock(return_value=Mock())
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        
        telegram_service.client_manager.create_client = Mock(return_value=mock_client)
        
        status = await telegram_service.check_account_status(sample_credential)
        assert status == 'active'
    
    @pytest.mark.asyncio
    async def test_check_account_status_expired(self, telegram_service, sample_credential):
        """Test checking status for expired account."""
        # Mock failed connection (expired session)
        mock_client = Mock()
        mock_client.get_me = AsyncMock(side_effect=Exception("Session expired"))
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        
        telegram_service.client_manager.create_client = Mock(return_value=mock_client)
        
        status = await telegram_service.check_account_status(sample_credential)
        assert status == 'expired'
    
    @pytest.mark.asyncio
    async def test_check_account_status_error(self, telegram_service, sample_credential):
        """Test checking status when client creation fails."""
        # Mock client creation failure
        telegram_service.client_manager.create_client = Mock(return_value=None)
        
        status = await telegram_service.check_account_status(sample_credential)
        assert status == 'error'
    
    def test_get_credential_by_id(self, db_manager, sample_credential):
        """Test getting credential by ID."""
        # Save credential first
        db_manager.save_telegram_credential(sample_credential)
        
        # Get it back
        credential = db_manager.get_credential_by_id(1)
        assert credential is not None
        assert credential.phone_number == sample_credential.phone_number
    
    def test_get_credential_by_id_not_found(self, db_manager):
        """Test getting non-existent credential."""
        credential = db_manager.get_credential_by_id(999)
        assert credential is None
    
    def test_delete_telegram_credential(self, db_manager, sample_credential):
        """Test deleting credential."""
        # Save credential first
        db_manager.save_telegram_credential(sample_credential)
        
        # Delete it
        success = db_manager.delete_telegram_credential(1)
        assert success is True
        
        # Verify it's deleted
        credential = db_manager.get_credential_by_id(1)
        assert credential is None
    
    def test_delete_telegram_credential_not_found(self, db_manager):
        """Test deleting non-existent credential."""
        success = db_manager.delete_telegram_credential(999)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_get_all_accounts_with_status(self, telegram_service, db_manager):
        """Test getting all accounts with status."""
        # Save some credentials
        cred1 = TelegramCredential(phone_number="+1111111111", session_string="/path1")
        cred2 = TelegramCredential(phone_number="+2222222222", session_string="/path2")
        
        db_manager.save_telegram_credential(cred1)
        db_manager.save_telegram_credential(cred2)
        
        # Mock status checking
        async def mock_check_status(cred):
            return 'active'
        
        telegram_service.check_account_status = mock_check_status
        
        accounts_with_status = await telegram_service.get_all_accounts_with_status()
        
        assert len(accounts_with_status) == 2
        assert accounts_with_status[0]['status'] == 'active'
        assert accounts_with_status[1]['status'] == 'active'
    
    @pytest.mark.asyncio
    async def test_account_status_service_refresh(self, telegram_service, db_manager):
        """Test account status service refresh."""
        status_service = AccountStatusService(telegram_service, db_manager)
        
        # Save a credential
        cred = TelegramCredential(phone_number="+1111111111", session_string="/path1")
        db_manager.save_telegram_credential(cred)
        
        # Mock status checking
        async def mock_check_status(cred):
            return 'active'
        
        telegram_service.check_account_status = mock_check_status
        
        # Refresh status
        status = await status_service.refresh_status(1)
        assert status == 'active'
        
        # Check cached status
        cached = status_service.get_cached_status(1)
        assert cached is not None
        assert cached['status'] == 'active'
    
    @pytest.mark.asyncio
    async def test_account_status_service_refresh_not_found(self, telegram_service, db_manager):
        """Test refreshing status for non-existent credential."""
        status_service = AccountStatusService(telegram_service, db_manager)
        
        status = await status_service.refresh_status(999)
        assert status is None

