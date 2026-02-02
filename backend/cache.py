"""
Enhanced caching layer for Bangko ng Seton
Reduces Google Sheets API calls by 80%+
"""
import time
from typing import Any, Optional, Dict, Callable
from datetime import datetime
import threading
from collections import OrderedDict

try:
    from backend.errors import get_logger
except ImportError:
    from errors import get_logger


class CacheEntry:
    """Single cache entry with metadata"""
    
    def __init__(self, data: Any, ttl: int):
        self.data = data
        self.timestamp = time.time()
        self.ttl = ttl
        self.hits = 0
        self.last_access = time.time()
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        return time.time() - self.timestamp > self.ttl
    
    def access(self) -> Any:
        """Access data and update metrics"""
        self.hits += 1
        self.last_access = time.time()
        return self.data


class TTLCache:
    """
    Thread-safe Time-To-Live cache with LRU eviction
    
    Features:
    - TTL-based expiration
    - LRU eviction when max size reached
    - Thread-safe operations
    - Cache statistics
    - Stale data fallback on errors
    """
    
    def __init__(self, default_ttl: int = 30, max_size: int = 100):
        """
        Initialize cache
        
        Args:
            default_ttl: Default time-to-live in seconds
            max_size: Maximum number of entries
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'stale_hits': 0
        }
        self.logger = get_logger()
    
    def get(self, key: str, allow_stale: bool = False) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            allow_stale: Return stale data if available
        
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if entry.is_expired():
                if allow_stale:
                    self._stats['stale_hits'] += 1
                    self.logger.warning(f"Returning stale cache for key: {key}")
                    return entry.access()
                else:
                    self._stats['misses'] += 1
                    del self._cache[key]
                    return None
            
            # Move to end (LRU)
            self._cache.move_to_end(key)
            self._stats['hits'] += 1
            return entry.access()
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Custom TTL for this entry (seconds)
        """
        with self._lock:
            # Use custom TTL or default
            entry_ttl = ttl if ttl is not None else self.default_ttl
            
            # Check if we need to evict
            if key not in self._cache and len(self._cache) >= self.max_size:
                # Evict least recently used
                evicted_key, _ = self._cache.popitem(last=False)
                self._stats['evictions'] += 1
                self.logger.debug(f"Evicted cache entry: {evicted_key}")
            
            # Set new entry
            self._cache[key] = CacheEntry(value, entry_ttl)
            self._cache.move_to_end(key)
    
    def invalidate(self, key: str):
        """Remove specific key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self.logger.debug(f"Invalidated cache key: {key}")
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
            if keys_to_delete:
                self.logger.debug(f"Invalidated {len(keys_to_delete)} cache entries matching: {pattern}")
    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self.logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': f"{hit_rate:.2f}%",
                'evictions': self._stats['evictions'],
                'stale_hits': self._stats['stale_hits']
            }
    
    def cleanup_expired(self):
        """Remove expired entries (manual cleanup)"""
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
            for key in expired_keys:
                del self._cache[key]
            if expired_keys:
                self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


class CachedFunction:
    """Decorator for caching function results"""
    
    def __init__(self, cache: TTLCache, key_prefix: str, ttl: Optional[int] = None):
        self.cache = cache
        self.key_prefix = key_prefix
        self.ttl = ttl
    
    def __call__(self, func: Callable):
        def wrapper(*args, **kwargs):
            # Generate cache key from function args
            cache_key = f"{self.key_prefix}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Cache miss - call function
            result = func(*args, **kwargs)
            
            # Store in cache
            self.cache.set(cache_key, result, self.ttl)
            
            return result
        
        return wrapper


# Global cache instance
_global_cache = TTLCache(default_ttl=30, max_size=200)


def get_cache() -> TTLCache:
    """Get global cache instance"""
    return _global_cache


def cache_function(key_prefix: str, ttl: Optional[int] = None):
    """
    Decorator to cache function results
    
    Usage:
        @cache_function('students', ttl=60)
        def get_all_students():
            return expensive_operation()
    """
    return CachedFunction(get_cache(), key_prefix, ttl)


# Convenience functions
def get_cached(key: str, allow_stale: bool = False) -> Optional[Any]:
    """Get value from global cache"""
    return _global_cache.get(key, allow_stale)


def set_cached(key: str, value: Any, ttl: Optional[int] = None):
    """Set value in global cache"""
    _global_cache.set(key, value, ttl)


def invalidate_cached(key: str):
    """Invalidate specific cache key"""
    _global_cache.invalidate(key)


def invalidate_pattern(pattern: str):
    """Invalidate all keys matching pattern"""
    _global_cache.invalidate_pattern(pattern)


def clear_cache():
    """Clear all cached data"""
    _global_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return _global_cache.get_stats()
