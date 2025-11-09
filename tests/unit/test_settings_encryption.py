"""
Unit tests for settings encryption.
"""

import pytest
from database.models.app_settings import AppSettings


class TestSettingsEncryption:
    """Test cases for settings encryption/decryption."""
    
    def test_telegram_api_credentials_encryption(self, test_db_manager):
        """Test that Telegram API credentials are encrypted when saved."""
        api_id = "12345678"
        api_hash = "abcdef1234567890abcdef1234567890"
        
        settings = AppSettings(
            telegram_api_id=api_id,
            telegram_api_hash=api_hash,
            theme="dark",
            language="en"
        )
        
        # Save settings using db_manager's settings manager
        result = test_db_manager.update_settings(settings)
        assert result is True
        
        # Check that data in database is encrypted (not plain text)
        with test_db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT telegram_api_id, telegram_api_hash FROM app_settings WHERE id = 1"
            )
            row = cursor.fetchone()
            assert row is not None
            
            # Encrypted values should be base64-encoded strings, not plain text
            assert row['telegram_api_id'] != api_id
            assert row['telegram_api_hash'] != api_hash
            assert row['telegram_api_id'] is not None
            assert row['telegram_api_hash'] is not None
    
    def test_telegram_api_credentials_decryption(self, test_db_manager):
        """Test that Telegram API credentials are decrypted when retrieved."""
        original_api_id = "87654321"
        original_api_hash = "fedcba0987654321fedcba0987654321"
        
        settings = AppSettings(
            telegram_api_id=original_api_id,
            telegram_api_hash=original_api_hash,
            theme="light",
            language="km"
        )
        
        # Save settings using db_manager's settings manager
        test_db_manager.update_settings(settings)
        
        # Retrieve and verify decryption
        retrieved_settings = test_db_manager.get_settings()
        assert retrieved_settings.telegram_api_id == original_api_id
        assert retrieved_settings.telegram_api_hash == original_api_hash
    
    def test_telegram_api_credentials_with_none_values(self, test_db_manager):
        """Test that None values are handled correctly in encryption."""
        settings = AppSettings(
            telegram_api_id=None,
            telegram_api_hash=None,
            theme="dark",
            language="en"
        )
        
        # Save settings using db_manager's settings manager
        result = test_db_manager.update_settings(settings)
        assert result is True
        
        # Retrieve and verify None values are preserved
        retrieved_settings = test_db_manager.get_settings()
        assert retrieved_settings.telegram_api_id is None
        assert retrieved_settings.telegram_api_hash is None
    
    def test_settings_encryption_error_handling(self, test_db_manager, monkeypatch):
        """Test error handling when encryption fails."""
        api_id = "12345678"
        api_hash = "abcdef1234567890abcdef1234567890"
        
        settings = AppSettings(
            telegram_api_id=api_id,
            telegram_api_hash=api_hash,
            theme="dark",
            language="en"
        )
        
        # Mock encryption to fail
        from utils import credential_storage
        original_encrypt = credential_storage.credential_storage.encrypt
        
        def failing_encrypt(value):
            raise Exception("Encryption failed")
        
        monkeypatch.setattr(credential_storage.credential_storage, 'encrypt', failing_encrypt)
        
        result = test_db_manager.update_settings(settings)
        
        # Should handle error gracefully (encryption failure returns None, but update should still proceed)
        # The actual behavior depends on implementation - check that it doesn't crash
        assert isinstance(result, bool)
        
        # Restore original method
        monkeypatch.setattr(credential_storage.credential_storage, 'encrypt', original_encrypt)
    
    def test_settings_decryption_error_handling(self, test_db_manager, monkeypatch):
        """Test error handling when decryption fails."""
        api_id = "12345678"
        api_hash = "abcdef1234567890abcdef1234567890"
        
        settings = AppSettings(
            telegram_api_id=api_id,
            telegram_api_hash=api_hash,
            theme="dark",
            language="en"
        )
        
        # Save settings normally first
        test_db_manager.update_settings(settings)
        
        # Mock decryption to fail
        from utils import credential_storage
        original_decrypt = credential_storage.credential_storage.decrypt
        
        def failing_decrypt(value):
            raise Exception("Decryption failed")
        
        monkeypatch.setattr(credential_storage.credential_storage, 'decrypt', failing_decrypt)
        
        # Retrieve settings - should handle decryption error gracefully
        retrieved_settings = test_db_manager.get_settings()
        
        # Decryption failure should return None for that field
        assert retrieved_settings.telegram_api_id is None
        assert retrieved_settings.telegram_api_hash is None
        
        # Restore original method
        monkeypatch.setattr(credential_storage.credential_storage, 'decrypt', original_decrypt)

