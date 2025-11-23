"""
Configurable page caching service with TTL support.
"""

import logging
import time
from typing import Any, Optional, Dict
from threading import Lock
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with data and expiration time."""
    data: Any
    expires_at: float
    created_at: float


class PageCacheService:
    """
    Configurable page caching service with TTL support.
    Singleton pattern for global cache management.
    """
    
    _instance: Optional['PageCacheService'] = None
    _lock = Lock()
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize cache service."""
        if self._initialized:
            return
        
        self._cache: Dict[str, CacheEntry] = {}
        self._enabled = True
        self._default_ttl = 300  # 5 minutes default
        self._lock = Lock()
        self._initialized = True
        
        # Load settings from config (will be called after settings are available)
        self._load_settings()
    
    def _load_settings(self):
        """Load cache settings from app settings."""
        try:
            from config.settings import settings
            if settings.db_manager:
                app_settings = settings.load_settings()
                self._enabled = app_settings.page_cache_enabled
                self._default_ttl = app_settings.page_cache_ttl_seconds
                logger.debug(f"Loaded cache settings: enabled={self._enabled}, ttl={self._default_ttl}s")
        except Exception as e:
            logger.warning(f"Could not load cache settings: {e}, using defaults")
    
    def configure(self, enabled: bool = True, default_ttl: int = 300):
        """
        Configure cache settings.
        
        Args:
            enabled: Whether caching is enabled
            default_ttl: Default TTL in seconds
        """
        with self._lock:
            self._enabled = enabled
            self._default_ttl = default_ttl
            logger.info(f"Cache configured: enabled={enabled}, default_ttl={default_ttl}s")
    
    def is_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._enabled
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get cached data by key.
        
        Args:
            key: Cache key
            default: Default value if not found or expired
            
        Returns:
            Cached data or default
        """
        if not self._enabled:
            return default
        
        with self._lock:
            if key not in self._cache:
                return default
            
            entry = self._cache[key]
            
            # Check if expired
            if time.time() > entry.expires_at:
                del self._cache[key]
                return default
            
            return entry.data
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """
        Set cached data with TTL.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if cached, False if caching is disabled
        """
        if not self._enabled:
            return False
        
        ttl = ttl or self._default_ttl
        expires_at = time.time() + ttl
        
        with self._lock:
            self._cache[key] = CacheEntry(
                data=data,
                expires_at=expires_at,
                created_at=time.time()
            )
        
        logger.debug(f"Cached data for key: {key} (TTL: {ttl}s)")
        return True
    
    def delete(self, key: str) -> bool:
        """
        Delete cached data by key.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Deleted cache entry: {key}")
                return True
            return False
    
    def clear(self, pattern: Optional[str] = None):
        """
        Clear cache entries.
        
        Args:
            pattern: Optional pattern to match keys (if None, clears all)
        """
        with self._lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                logger.info(f"Cleared all cache entries ({count} entries)")
            else:
                # Clear entries matching pattern
                keys_to_delete = [k for k in self._cache.keys() if pattern in k]
                for key in keys_to_delete:
                    del self._cache[key]
                logger.info(f"Cleared {len(keys_to_delete)} cache entries matching pattern: {pattern}")
    
    def invalidate(self, pattern: str):
        """
        Invalidate cache entries matching pattern.
        Alias for clear() with pattern.
        
        Args:
            pattern: Pattern to match keys
        """
        self.clear(pattern=pattern)
    
    def cleanup_expired(self):
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, entry in self._cache.items():
                if current_time > entry.expires_at:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            total_entries = len(self._cache)
            expired_count = sum(
                1 for entry in self._cache.values()
                if time.time() > entry.expires_at
            )
            
            return {
                "enabled": self._enabled,
                "total_entries": total_entries,
                "expired_entries": expired_count,
                "active_entries": total_entries - expired_count,
                "default_ttl": self._default_ttl
            }
    
    def generate_key(self, page_name: str, **params) -> str:
        """
        Generate cache key from page name and parameters.
        
        Args:
            page_name: Name of the page
            **params: Additional parameters for cache key
            
        Returns:
            Cache key string
        """
        if not params:
            return f"page:{page_name}"
        
        # Sort params for consistent keys
        sorted_params = sorted(params.items())
        param_str = ":".join(f"{k}={v}" for k, v in sorted_params)
        return f"page:{page_name}:{param_str}"


# Global singleton instance
page_cache_service = PageCacheService()

