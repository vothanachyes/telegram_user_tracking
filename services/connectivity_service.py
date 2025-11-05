"""
Internet connectivity monitoring service.
"""

import socket
import logging
from typing import Callable, Optional
from threading import Thread, Event
import time

logger = logging.getLogger(__name__)


class ConnectivityService:
    """Monitors internet connectivity."""
    
    def __init__(self, check_interval: int = 5):
        self.check_interval = check_interval
        self.is_connected = False
        self._monitoring = False
        self._stop_event = Event()
        self._monitor_thread: Optional[Thread] = None
        self._callback: Optional[Callable[[bool], None]] = None
    
    def check_connection(self, host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> bool:
        """
        Check internet connection by attempting to connect to DNS server.
        Default: Google DNS (8.8.8.8:53)
        """
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except (socket.error, socket.timeout):
            return False
    
    def start_monitoring(self, callback: Optional[Callable[[bool], None]] = None):
        """
        Start monitoring connectivity in background thread.
        Callback will be called with connection status when it changes.
        """
        if self._monitoring:
            logger.warning("Connectivity monitoring already started")
            return
        
        self._callback = callback
        self._stop_event.clear()
        self._monitoring = True
        
        # Initial check
        self.is_connected = self.check_connection()
        if self._callback:
            self._callback(self.is_connected)
        
        # Start monitoring thread
        self._monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info("Connectivity monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring connectivity."""
        if not self._monitoring:
            return
        
        self._stop_event.set()
        self._monitoring = False
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
        
        logger.info("Connectivity monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                # Check connection
                current_status = self.check_connection()
                
                # If status changed, notify
                if current_status != self.is_connected:
                    self.is_connected = current_status
                    logger.info(f"Connectivity status changed: {'Connected' if current_status else 'Disconnected'}")
                    
                    if self._callback:
                        try:
                            self._callback(current_status)
                        except Exception as e:
                            logger.error(f"Error calling connectivity callback: {e}")
                
                # Wait before next check
                self._stop_event.wait(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in connectivity monitoring: {e}")
                time.sleep(self.check_interval)
    
    def wait_for_connection(self, timeout: Optional[int] = None) -> bool:
        """
        Wait for internet connection.
        Returns True if connected, False if timeout reached.
        """
        start_time = time.time()
        
        while True:
            if self.check_connection():
                return True
            
            if timeout and (time.time() - start_time) >= timeout:
                return False
            
            time.sleep(2)


# Global connectivity service instance
connectivity_service = ConnectivityService()

