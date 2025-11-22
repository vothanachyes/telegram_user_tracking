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
            lock_file_path: Path to lock file. If None, uses default in user data directory.
        """
        if lock_file_path is None:
            # Use user data directory for lock file (works in both dev and bundled executable)
            from utils.constants import USER_DATA_DIR
            # USER_DATA_DIR is already created in constants.py, so we can use it directly
            lock_file_path = USER_DATA_DIR / "app.lock"
        
        # Convert to Path if it's a string, expand user home directory, and resolve to absolute path
        if isinstance(lock_file_path, str):
            lock_file_path = Path(lock_file_path)
        self.lock_file_path = lock_file_path.expanduser().resolve()
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
        """
        Release the lock file.
        
        Cross-platform implementation that handles cleanup gracefully.
        Errors during release are non-critical (file may already be unlocked,
        process terminated, etc.) and are logged as debug messages.
        """
        if self.lock_file and self._is_locked:
            try:
                if self._system == "Windows":
                    import msvcrt
                    try:
                        msvcrt.locking(
                            self.lock_file.fileno(),
                            msvcrt.LK_UNLCK,  # Unlock
                            1
                        )
                    except (IOError, OSError) as e:
                        # On Windows, msvcrt.locking can raise IOError or OSError
                        # if file is already unlocked or process terminated
                        logger.debug(f"Could not unlock file on Windows (may already be unlocked): {e}")
                else:
                    # Unix (macOS, Linux): use fcntl
                    import fcntl
                    try:
                        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                    except (IOError, OSError) as e:
                        # On Unix, fcntl.flock can raise IOError or OSError
                        # if file is already unlocked or process terminated
                        logger.debug(f"Could not unlock file on Unix (may already be unlocked): {e}")
                
                # Always try to close the file, even if unlock failed
                try:
                    self.lock_file.close()
                except Exception:
                    pass  # Ignore errors when closing
                
                # Mark as unlocked to prevent retry loops
                self._is_locked = False
                
                # Optionally remove the lock file (best effort)
                try:
                    if self.lock_file_path.exists():
                        self.lock_file_path.unlink()
                except Exception:
                    pass  # Ignore errors when removing lock file
                    
            except Exception as e:
                # Catch-all for any other unexpected errors during cleanup
                # This is non-critical cleanup code, so log as debug
                logger.debug(f"Unexpected error during lock release (non-critical): {e}")
                # Still mark as unlocked and try to close file
                self._is_locked = False
                try:
                    if self.lock_file:
                        self.lock_file.close()
                except Exception:
                    pass
            finally:
                # Always clear the file reference, even if errors occurred
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

