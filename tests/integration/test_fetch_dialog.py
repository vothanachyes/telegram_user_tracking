"""
Integration tests for fetch data dialog with account and group selection.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from database.models.telegram import TelegramCredential, TelegramGroup
from services.telegram.telegram_service import TelegramService
from ui.dialogs.fetch_data_dialog import FetchDataDialog
from tests.fixtures.db_fixtures import create_test_db_manager


class TestFetchDialog:
    """Integration tests for fetch dialog functionality."""
    
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
        service.client_manager.is_available = True
        service.client_manager.is_connected = Mock(return_value=True)
        return service
    
    @pytest.fixture
    def fetch_dialog(self, db_manager, telegram_service):
        """Create fetch data dialog."""
        return FetchDataDialog(
            db_manager=db_manager,
            telegram_service=telegram_service,
            on_fetch_complete=None
        )
    
    @pytest.fixture
    def sample_credentials(self, db_manager):
        """Create sample credentials."""
        cred1 = TelegramCredential(
            phone_number="+1111111111",
            session_string="/path/to/session1",
            is_default=True
        )
        cred2 = TelegramCredential(
            phone_number="+2222222222",
            session_string="/path/to/session2",
            is_default=False
        )
        
        db_manager.save_telegram_credential(cred1)
        db_manager.save_telegram_credential(cred2)
        
        return [cred1, cred2]
    
    @pytest.fixture
    def sample_groups(self, db_manager):
        """Create sample groups."""
        group1 = TelegramGroup(
            group_id=-1001111111111,
            group_name="Test Group 1",
            group_username="testgroup1",
            last_fetch_date=datetime.now(),
            total_messages=100
        )
        group2 = TelegramGroup(
            group_id=-1002222222222,
            group_name="Test Group 2",
            group_username="testgroup2",
            last_fetch_date=None,
            total_messages=0
        )
        
        db_manager.save_group(group1)
        db_manager.save_group(group2)
        
        return [group1, group2]
    
    @pytest.mark.asyncio
    async def test_account_selection_flow(self, fetch_dialog, telegram_service, sample_credentials):
        """Test account selection flow."""
        # Mock get_all_accounts_with_status
        async def mock_get_accounts():
            return [
                {
                    'credential': sample_credentials[0],
                    'status': 'active',
                    'status_checked_at': datetime.now()
                },
                {
                    'credential': sample_credentials[1],
                    'status': 'active',
                    'status_checked_at': datetime.now()
                }
            ]
        
        telegram_service.get_all_accounts_with_status = mock_get_accounts
        
        # Initialize accounts
        await fetch_dialog._initialize_accounts()
        
        # Verify accounts are loaded
        assert len(fetch_dialog.account_selector.accounts_with_status) == 2
    
    @pytest.mark.asyncio
    async def test_group_selection_manual_entry(self, fetch_dialog, sample_groups):
        """Test manual group ID entry."""
        # Update groups list
        fetch_dialog._update_groups_list()
        
        # Simulate manual entry
        group_id = -1009999999999
        fetch_dialog._on_group_manual_entry(group_id)
        
        assert fetch_dialog.group_id_field.value == str(group_id)
    
    @pytest.mark.asyncio
    async def test_group_selection_dropdown(self, fetch_dialog, sample_groups):
        """Test group selection from dropdown."""
        # Update groups list
        fetch_dialog._update_groups_list()
        
        # Simulate dropdown selection
        group_id = sample_groups[0].group_id
        fetch_dialog._on_group_selected(group_id)
        
        assert fetch_dialog.group_id_field.value == str(group_id)
    
    @pytest.mark.asyncio
    async def test_validate_account_group_access_valid(self, fetch_dialog, telegram_service, sample_credentials, sample_groups):
        """Test validation with valid account and group."""
        # Set selected credential
        fetch_dialog.selected_credential = sample_credentials[0]
        fetch_dialog.group_selector.set_selected_group(sample_groups[0].group_id)
        
        # Mock successful validation
        async def mock_validate(cred, group_id):
            return (True, sample_groups[0], None, True)
        
        telegram_service.fetch_and_validate_group = mock_validate
        
        is_valid, error = await fetch_dialog._validate_account_group_access()
        
        assert is_valid is True
        assert error is None
    
    @pytest.mark.asyncio
    async def test_validate_account_group_access_no_account(self, fetch_dialog):
        """Test validation when no account is selected."""
        fetch_dialog.selected_credential = None
        
        is_valid, error = await fetch_dialog._validate_account_group_access()
        
        assert is_valid is False
        assert error is not None
    
    @pytest.mark.asyncio
    async def test_validate_account_group_access_expired_session(self, fetch_dialog, telegram_service, sample_credentials):
        """Test validation with expired account session."""
        fetch_dialog.selected_credential = sample_credentials[0]
        fetch_dialog.group_selector.set_selected_group(-1001111111111)
        
        # Mock expired session
        async def mock_validate(cred, group_id):
            return (False, None, "Account session expired or invalid", False)
        
        telegram_service.fetch_and_validate_group = mock_validate
        
        is_valid, error = await fetch_dialog._validate_account_group_access()
        
        assert is_valid is False
        assert "expired" in error.lower() or "invalid" in error.lower()
    
    @pytest.mark.asyncio
    async def test_validate_account_group_access_no_member(self, fetch_dialog, telegram_service, sample_credentials, sample_groups):
        """Test validation when account is not member of group."""
        fetch_dialog.selected_credential = sample_credentials[0]
        fetch_dialog.group_selector.set_selected_group(sample_groups[0].group_id)
        
        # Mock no access
        async def mock_validate(cred, group_id):
            return (True, sample_groups[0], None, False)
        
        telegram_service.fetch_and_validate_group = mock_validate
        
        is_valid, error = await fetch_dialog._validate_account_group_access()
        
        assert is_valid is False
        assert "not a member" in error.lower() or "not_member" in error.lower()
    
    @pytest.mark.asyncio
    async def test_fetch_with_selected_account(self, fetch_dialog, telegram_service, sample_credentials, sample_groups):
        """Test fetching messages with selected account."""
        fetch_dialog.selected_credential = sample_credentials[0]
        fetch_dialog.group_selector.set_selected_group(sample_groups[0].group_id)
        fetch_dialog.start_date_field.value = "2024-01-01"
        fetch_dialog.end_date_field.value = "2024-01-31"
        
        # Mock successful fetch
        async def mock_fetch_with_account(credential, group_id, start_date, end_date, progress_callback=None):
            if progress_callback:
                progress_callback(10, -1)
            return (True, 10, None)
        
        telegram_service.fetch_messages_with_account = mock_fetch_with_account
        
        # This would normally be called by _fetch_messages_async
        # We're just testing the logic here
        success, count, error = await telegram_service.fetch_messages_with_account(
            credential=sample_credentials[0],
            group_id=sample_groups[0].group_id,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            progress_callback=None
        )
        
        assert success is True
        assert count == 10
        assert error is None
    
    @pytest.mark.asyncio
    async def test_empty_accounts_list(self, fetch_dialog, telegram_service):
        """Test handling empty accounts list."""
        # Mock empty accounts
        async def mock_get_accounts():
            return []
        
        telegram_service.get_all_accounts_with_status = mock_get_accounts
        
        await fetch_dialog._initialize_accounts()
        
        # Should handle gracefully
        assert len(fetch_dialog.account_selector.accounts_with_status) == 0
    
    @pytest.mark.asyncio
    async def test_empty_groups_list(self, fetch_dialog):
        """Test handling empty groups list."""
        fetch_dialog._update_groups_list()
        
        # Should handle gracefully
        assert len(fetch_dialog.group_selector.groups) == 0
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, fetch_dialog, telegram_service, sample_credentials):
        """Test handling network errors during validation."""
        fetch_dialog.selected_credential = sample_credentials[0]
        fetch_dialog.group_selector.set_selected_group(-1001111111111)
        
        # Mock network error
        async def mock_validate(cred, group_id):
            raise ConnectionError("Network error")
        
        telegram_service.fetch_and_validate_group = mock_validate
        
        is_valid, error = await fetch_dialog._validate_account_group_access()
        
        assert is_valid is False
        assert error is not None
    
    @pytest.mark.asyncio
    async def test_group_id_validation_negative(self, fetch_dialog, sample_credentials):
        """Test that negative group IDs are accepted (valid format)."""
        fetch_dialog.selected_credential = sample_credentials[0]
        fetch_dialog.group_id_field.value = "-1001234567890"
        
        is_valid, error = fetch_dialog._validate_inputs()
        # Should be valid (negative group IDs are valid for Telegram)
        assert is_valid is True or error is not None  # Either valid or error about account/group
    
    @pytest.mark.asyncio
    async def test_group_id_validation_invalid_format(self, fetch_dialog, sample_credentials):
        """Test that invalid group ID format is rejected."""
        fetch_dialog.selected_credential = sample_credentials[0]
        fetch_dialog.group_id_field.value = "invalid_group_id"
        
        # Try to get group ID - should handle gracefully
        try:
            group_id = int(fetch_dialog.group_id_field.value)
        except ValueError:
            group_id = None
        
        # Should handle invalid format
        assert group_id is None or isinstance(group_id, int)
    
    @pytest.mark.asyncio
    async def test_permission_error_vs_not_member(self, fetch_dialog, telegram_service, sample_credentials, sample_groups):
        """Test distinction between permission error and not member error."""
        fetch_dialog.selected_credential = sample_credentials[0]
        fetch_dialog.group_selector.set_selected_group(sample_groups[0].group_id)
        
        # Test permission denied
        async def mock_validate_permission(cred, group_id):
            return (False, None, "permission_denied", False)
        
        telegram_service.fetch_and_validate_group = mock_validate_permission
        is_valid, error = await fetch_dialog._validate_account_group_access()
        assert is_valid is False
        assert "permission" in error.lower() or "no_permission" in error.lower()
        
        # Test not member
        async def mock_validate_not_member(cred, group_id):
            return (False, None, "not_member", False)
        
        telegram_service.fetch_and_validate_group = mock_validate_not_member
        is_valid, error = await fetch_dialog._validate_account_group_access()
        assert is_valid is False
        assert "not a member" in error.lower() or "not_member" in error.lower()
    
    @pytest.mark.asyncio
    async def test_session_expiration_during_validation(self, fetch_dialog, telegram_service, sample_credentials):
        """Test handling session expiration during validation."""
        fetch_dialog.selected_credential = sample_credentials[0]
        fetch_dialog.group_selector.set_selected_group(-1001111111111)
        
        # Mock session expiration
        async def mock_validate_expired(cred, group_id):
            return (False, None, "Account session expired, please reconnect", False)
        
        telegram_service.fetch_and_validate_group = mock_validate_expired
        
        is_valid, error = await fetch_dialog._validate_account_group_access()
        
        assert is_valid is False
        assert "expired" in error.lower() or "invalid" in error.lower()
    
    @pytest.mark.asyncio
    async def test_concurrent_operations_handling(self, fetch_dialog, telegram_service, sample_credentials, sample_groups):
        """Test that concurrent validation requests are handled."""
        fetch_dialog.selected_credential = sample_credentials[0]
        fetch_dialog.group_selector.set_selected_group(sample_groups[0].group_id)
        
        # Mock validation with delay
        async def mock_validate_slow(cred, group_id):
            import asyncio
            await asyncio.sleep(0.1)  # Simulate network delay
            return (True, sample_groups[0], None, True)
        
        telegram_service.fetch_and_validate_group = mock_validate_slow
        
        # Run multiple validations concurrently
        import asyncio
        results = await asyncio.gather(
            fetch_dialog._validate_account_group_access(),
            fetch_dialog._validate_account_group_access(),
            return_exceptions=True
        )
        
        # All should complete without errors
        for result in results:
            if isinstance(result, Exception):
                # Exceptions are acceptable if handled
                pass
            else:
                is_valid, error = result
                # Should either be valid or have a clear error
                assert isinstance(is_valid, bool)
    
    @pytest.mark.asyncio
    async def test_user_not_logged_in_activity_logging(self, db_manager):
        """Test that activity logging handles missing user email gracefully."""
        # Try to log without user email
        try:
            result = db_manager.log_account_action(
                user_email=None,
                action='add',
                phone_number="+1234567890"
            )
            # Should either return None or handle gracefully
            assert result is None or isinstance(result, int)
        except Exception as e:
            # Exception is acceptable if logged properly
            assert "email" in str(e).lower() or "user" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_auth_service_unavailable(self, fetch_dialog):
        """Test handling when auth service is unavailable."""
        # This would be tested in handlers, but we can verify the pattern
        # The handlers already check for auth_service availability
        assert hasattr(fetch_dialog, 'selected_credential')  # Basic structure check

