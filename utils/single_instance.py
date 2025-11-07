"""
Single instance enforcement utility for cross-platform support.

Ensures only one instance of the application can run at a time.
"""

import os
import platform
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SingleInstance:
    """
    Cross-platform single instance lock using file locking.
    
    Works on Windows, macOS, and Linux by using platform-specific
    file locking mechanisms.
    """
    
    def __init__(self, lock_file_path: Optional[Path] = None):
        """
        Initialize single instance lock.
        
        Args:
            lock_file_path: Path to lock file. If None, uses default in data directory.
        """
        if lock_file_path is None:
            # Use data directory for lock file
            base_dir = Path(__file__).resolve().parent.parent
            data_dir = base_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            lock_file_path = data_dir / "app.lock"
        
        self.lock_file_path = lock_file_path
        self.lock_file: Optional[object] = None
        self._is_locked = False
        self._system = platform.system()
    
    def is_already_running(self) -> bool:
        """
        Check if another instance is already running.
        
        Returns:
            True if another instance is running, False otherwise.
        """
        try:
            # Try to open the lock file
            if self._system == "Windows":
                # Windows: use msvcrt for file locking
                import msvcrt
                
                # Open file in binary mode for Windows
                try:
                    self.lock_file = open(self.lock_file_path, 'w')
                except IOError:
                    # If we can't open the file, assume another instance is running
                    return True
                
                # Try to acquire exclusive lock (non-blocking)
                try:
                    msvcrt.locking(
                        self.lock_file.fileno(),
                        msvcrt.LK_NBLCK,  # Non-blocking lock
                        1  # Lock 1 byte
                    )
                    # Write PID to file for debugging
                    self.lock_file.write(str(os.getpid()))
                    self.lock_file.flush()
                    self._is_locked = True
                    return False  # No other instance running
                except IOError:
                    # Lock failed - another instance is running
                    self.lock_file.close()
                    self.lock_file = None
                    return True
            else:
                # Unix (macOS, Linux): use fcntl for file locking
                import fcntl
                
                # Open file in read-write mode
                try:
                    self.lock_file = open(self.lock_file_path, 'w')
                except IOError:
                    # If we can't open the file, assume another instance is running
                    return True
                
                # Try to acquire exclusive lock (non-blocking)
                try:
                    fcntl.flock(
                        self.lock_file.fileno(),
                        fcntl.LOCK_EX | fcntl.LOCK_NB  # Exclusive, non-blocking
                    )
                    # Write PID to file for debugging
                    self.lock_file.write(str(os.getpid()))
                    self.lock_file.flush()
                    self._is_locked = True
                    return False  # No other instance running
                except (IOError, OSError):
                    # Lock failed - another instance is running
                    self.lock_file.close()
                    self.lock_file = None
                    return True
                    
        except Exception as e:
            logger.error(f"Error checking for existing instance: {e}", exc_info=True)
            # On error, assume no other instance (fail open)
            # Clean up if file was opened
            if self.lock_file:
                try:
                    self.lock_file.close()
                except Exception:
                    pass
                self.lock_file = None
            return False
    
    def release(self):
        """Release the lock file."""
        if self.lock_file and self._is_locked:
            try:
                if self._system == "Windows":
                    import msvcrt
                    msvcrt.locking(
                        self.lock_file.fileno(),
                        msvcrt.LK_UNLCK,  # Unlock
                        1
                    )
                else:
                    import fcntl
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                
                self.lock_file.close()
                self._is_locked = False
                
                # Optionally remove the lock file
                try:
                    if self.lock_file_path.exists():
                        self.lock_file_path.unlink()
                except Exception:
                    pass  # Ignore errors when removing lock file
                    
            except Exception as e:
                logger.error(f"Error releasing lock: {e}", exc_info=True)
            finally:
                self.lock_file = None
    
    def __enter__(self):
        """Context manager entry."""
        if self.is_already_running():
            raise RuntimeError("Another instance is already running")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.release()

