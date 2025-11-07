"""
Unit tests for single instance enforcement.
"""

import pytest
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, Mock

from utils.single_instance import SingleInstance


class TestSingleInstance:
    """Test cases for SingleInstance class."""
    
    def test_single_instance_no_existing_instance(self, tmp_path):
        """Test that first instance can acquire lock."""
        lock_file = tmp_path / "test.lock"
        instance = SingleInstance(lock_file_path=lock_file)
        
        # Should not detect another instance
        assert instance.is_already_running() is False
        assert instance._is_locked is True
        assert instance.lock_file is not None
        
        # Cleanup
        instance.release()
        assert instance._is_locked is False
    
    def test_single_instance_detects_existing_instance(self, tmp_path):
        """Test that second instance detects first instance."""
        lock_file = tmp_path / "test.lock"
        
        # First instance
        instance1 = SingleInstance(lock_file_path=lock_file)
        assert instance1.is_already_running() is False  # First instance succeeds
        
        # Second instance should detect first
        instance2 = SingleInstance(lock_file_path=lock_file)
        assert instance2.is_already_running() is True  # Second instance fails
        
        # Cleanup
        instance1.release()
        instance2.release()
    
    def test_single_instance_release_allows_new_instance(self, tmp_path):
        """Test that releasing lock allows new instance to start."""
        lock_file = tmp_path / "test.lock"
        
        # First instance
        instance1 = SingleInstance(lock_file_path=lock_file)
        assert instance1.is_already_running() is False
        instance1.release()
        
        # After release, new instance should be able to acquire lock
        instance2 = SingleInstance(lock_file_path=lock_file)
        assert instance2.is_already_running() is False
        
        # Cleanup
        instance2.release()
    
    def test_single_instance_context_manager(self, tmp_path):
        """Test SingleInstance as context manager."""
        lock_file = tmp_path / "test.lock"
        
        # First instance with context manager
        with SingleInstance(lock_file_path=lock_file) as instance1:
            assert instance1._is_locked is True
            
            # Second instance should fail
            instance2 = SingleInstance(lock_file_path=lock_file)
            assert instance2.is_already_running() is True
            instance2.release()
        
        # After context exit, lock should be released
        instance3 = SingleInstance(lock_file_path=lock_file)
        assert instance3.is_already_running() is False
        instance3.release()
    
    def test_single_instance_default_lock_file_path(self):
        """Test that default lock file path is created correctly."""
        instance = SingleInstance()
        
        # Should use data directory
        expected_path = Path(__file__).resolve().parent.parent.parent / "data" / "app.lock"
        assert instance.lock_file_path == expected_path
        assert instance.lock_file_path.parent.exists()
    
    def test_single_instance_writes_pid(self, tmp_path):
        """Test that PID is written to lock file."""
        lock_file = tmp_path / "test.lock"
        instance = SingleInstance(lock_file_path=lock_file)
        
        assert instance.is_already_running() is False
        
        # Check that PID was written
        if lock_file.exists():
            pid_content = lock_file.read_text().strip()
            assert pid_content == str(os.getpid())
        
        instance.release()
    
    def test_single_instance_multiple_checks(self, tmp_path):
        """Test that instance maintains lock after first check."""
        lock_file = tmp_path / "test.lock"
        instance = SingleInstance(lock_file_path=lock_file)
        
        # First check should succeed and acquire lock
        assert instance.is_already_running() is False
        assert instance._is_locked is True
        
        # Lock should still be held
        assert instance.lock_file is not None
        
        instance.release()
    
    def test_single_instance_release_idempotent(self, tmp_path):
        """Test that release can be called multiple times safely."""
        lock_file = tmp_path / "test.lock"
        instance = SingleInstance(lock_file_path=lock_file)
        
        assert instance.is_already_running() is False
        
        # Release multiple times should not error
        instance.release()
        instance.release()
        instance.release()
        
        assert instance._is_locked is False
    
    @pytest.mark.skipif(os.name == 'nt', reason="Unix-specific test")
    def test_single_instance_unix_locking(self, tmp_path):
        """Test Unix file locking mechanism."""
        lock_file = tmp_path / "test.lock"
        instance = SingleInstance(lock_file_path=lock_file)
        
        # Should use fcntl on Unix
        assert instance._system in ("Darwin", "Linux")
        assert instance.is_already_running() is False
        
        instance.release()
    
    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    def test_single_instance_windows_locking(self, tmp_path):
        """Test Windows file locking mechanism."""
        lock_file = tmp_path / "test.lock"
        instance = SingleInstance(lock_file_path=lock_file)
        
        # Should use msvcrt on Windows
        assert instance._system == "Windows"
        assert instance.is_already_running() is False
        
        instance.release()

