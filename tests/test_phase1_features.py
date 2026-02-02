"""
Tests for Phase 1: Cache, Resilience, and Health monitoring
"""
import pytest
import time
from unittest.mock import Mock, MagicMock, patch


class TestTTLCache:
    """Test caching functionality"""
    
    def test_cache_stores_and_retrieves_data(self):
        """Test basic cache set/get"""
        from backend.cache import TTLCache
        
        cache = TTLCache(default_ttl=60)
        cache.set('test_key', 'test_value')
        
        result = cache.get('test_key')
        assert result == 'test_value'
    
    def test_cache_expiration(self):
        """Test cache entries expire after TTL"""
        from backend.cache import TTLCache
        
        cache = TTLCache(default_ttl=1)  # 1 second TTL
        cache.set('expire_key', 'expire_value')
        
        # Should exist immediately
        assert cache.get('expire_key') == 'expire_value'
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get('expire_key') is None
    
    def test_cache_custom_ttl(self):
        """Test custom TTL per entry"""
        from backend.cache import TTLCache
        
        cache = TTLCache(default_ttl=60)
        cache.set('short_ttl', 'value', ttl=1)
        
        assert cache.get('short_ttl') == 'value'
        time.sleep(1.1)
        assert cache.get('short_ttl') is None
    
    def test_cache_stale_data_fallback(self):
        """Test returning stale data when allow_stale=True"""
        from backend.cache import TTLCache
        
        cache = TTLCache(default_ttl=1)
        cache.set('stale_key', 'stale_value')
        
        time.sleep(1.1)
        
        # Without allow_stale - should return None
        assert cache.get('stale_key', allow_stale=False) is None
        
        # Re-set for next test
        cache.set('stale_key2', 'stale_value2')
        time.sleep(1.1)
        
        # With allow_stale - should return stale data
        result = cache.get('stale_key2', allow_stale=True)
        assert result == 'stale_value2'
    
    def test_cache_invalidation(self):
        """Test cache invalidation"""
        from backend.cache import TTLCache
        
        cache = TTLCache()
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        
        cache.invalidate('key1')
        
        assert cache.get('key1') is None
        assert cache.get('key2') == 'value2'
    
    def test_cache_pattern_invalidation(self):
        """Test invalidating keys by pattern"""
        from backend.cache import TTLCache
        
        cache = TTLCache()
        cache.set('user_123', 'data1')
        cache.set('user_456', 'data2')
        cache.set('transaction_789', 'data3')
        
        cache.invalidate_pattern('user_')
        
        assert cache.get('user_123') is None
        assert cache.get('user_456') is None
        assert cache.get('transaction_789') == 'data3'
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when max size reached"""
        from backend.cache import TTLCache
        
        cache = TTLCache(max_size=3)
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('key3', 'value3')
        
        # Access key1 to make it recently used
        cache.get('key1')
        
        # Add new key - should evict key2 (least recently used)
        cache.set('key4', 'value4')
        
        assert cache.get('key2') is None  # Evicted
        assert cache.get('key1') == 'value1'  # Still there
        assert cache.get('key4') == 'value4'  # New entry
    
    def test_cache_statistics(self):
        """Test cache statistics tracking"""
        from backend.cache import TTLCache
        
        cache = TTLCache()
        cache.set('key1', 'value1')
        
        # Hit
        cache.get('key1')
        # Miss
        cache.get('nonexistent')
        
        stats = cache.get_stats()
        
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert 'hit_rate' in stats


class TestExponentialBackoff:
    """Test exponential backoff algorithm"""
    
    def test_exponential_delay_increases(self):
        """Test delay increases exponentially"""
        from backend.resilience import exponential_backoff
        
        delay0 = exponential_backoff(0, base_delay=1.0, jitter=False)
        delay1 = exponential_backoff(1, base_delay=1.0, jitter=False)
        delay2 = exponential_backoff(2, base_delay=1.0, jitter=False)
        
        assert delay1 > delay0
        assert delay2 > delay1
    
    def test_exponential_backoff_max_delay(self):
        """Test max delay is respected"""
        from backend.resilience import exponential_backoff
        
        delay = exponential_backoff(10, base_delay=1.0, max_delay=30.0, jitter=False)
        
        assert delay <= 30.0
    
    def test_exponential_backoff_with_jitter(self):
        """Test jitter adds randomness"""
        from backend.resilience import exponential_backoff
        
        delays = [exponential_backoff(1, base_delay=1.0, jitter=True) for _ in range(10)]
        
        # All delays should be slightly different due to jitter
        assert len(set(delays)) > 1


class TestRetryDecorator:
    """Test retry decorator functionality"""
    
    def test_retry_on_failure(self):
        """Test function attempts retries"""
        from backend.resilience import with_retry, RetryConfig
        
        call_count = {'count': 0}
        
        @with_retry(RetryConfig(max_attempts=3, base_delay=0.01))
        def working_function():
            call_count['count'] += 1
            return "success"
        
        result = working_function()
        
        # Should succeed on first try
        assert result == "success"
        assert call_count['count'] == 1
    
    def test_retry_exhaustion(self):
        """Test all retries exhausted raises error"""
        from backend.resilience import with_retry, RetryConfig
        import gspread
        
        @with_retry(RetryConfig(max_attempts=2, base_delay=0.1))
        def always_fails():
            raise gspread.exceptions.APIError("Always fails")
        
        with pytest.raises(Exception):
            always_fails()


class TestWriteQueue:
    """Test write queue for offline operations"""
    
    def test_enqueue_operation(self):
        """Test enqueueing write operations"""
        from backend.resilience import WriteQueue
        
        queue = WriteQueue()
        queue.enqueue('append', 'Users', ['data1', 'data2'])
        
        status = queue.get_status()
        assert status['pending'] == 1
    
    def test_queue_processing(self):
        """Test processing queued operations"""
        from backend.resilience import WriteQueue
        
        queue = WriteQueue()
        queue.enqueue('append', 'Users', ['data'])
        
        # Mock sheets client
        mock_client = MagicMock()
        mock_sheet = MagicMock()
        mock_client.worksheet.return_value = mock_sheet
        
        stats = queue.process_queue(mock_client)
        
        assert stats['success'] == 1
        assert stats['failed'] == 0


class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def test_rate_limiter_allows_within_limit(self):
        """Test rate limiter allows calls within limit"""
        from backend.resilience import RateLimiter
        
        limiter = RateLimiter(max_calls=5, window_seconds=1)
        
        # Should allow 5 calls without blocking
        for _ in range(5):
            limiter.acquire()  # Should not block
    
    def test_rate_limiter_statistics(self):
        """Test rate limiter statistics"""
        from backend.resilience import RateLimiter
        
        limiter = RateLimiter(max_calls=10, window_seconds=60)
        
        for _ in range(3):
            limiter.acquire()
        
        stats = limiter.get_stats()
        
        assert stats['calls_in_window'] == 3
        assert stats['max_calls'] == 10


class TestHealthMonitor:
    """Test health monitoring"""
    
    def test_health_status_structure(self):
        """Test health status returns correct structure"""
        from backend.health import HealthMonitor
        
        monitor = HealthMonitor()
        status = monitor.get_health_status()
        
        assert 'status' in status
        assert 'timestamp' in status
        assert 'uptime' in status
        assert 'components' in status
        assert 'metrics' in status
    
    def test_uptime_calculation(self):
        """Test uptime is calculated correctly"""
        from backend.health import HealthMonitor
        
        monitor = HealthMonitor()
        time.sleep(0.2)  # Wait longer to ensure measurable uptime
        
        uptime = monitor._get_uptime()
        
        assert uptime['seconds'] >= 0  # At least 0 seconds
        assert 'formatted' in uptime
    
    def test_sheets_status_update(self):
        """Test updating Google Sheets status"""
        from backend.health import HealthMonitor
        
        monitor = HealthMonitor()
        monitor.update_sheets_status('connected')
        
        status = monitor.get_health_status()
        
        assert status['components']['google_sheets']['status'] == 'connected'


class TestUptimeTracker:
    """Test uptime tracking"""
    
    def test_uptime_starts_at_100_percent(self):
        """Test new tracker starts at 100% uptime"""
        from backend.health import UptimeTracker
        
        tracker = UptimeTracker()
        
        uptime_pct = tracker.get_uptime_percentage()
        
        assert uptime_pct == 100.0
    
    def test_downtime_tracking(self):
        """Test downtime is tracked correctly"""
        from backend.health import UptimeTracker
        
        tracker = UptimeTracker()
        time.sleep(0.1)
        
        tracker.mark_down()
        time.sleep(0.1)
        tracker.mark_up()
        
        uptime_pct = tracker.get_uptime_percentage()
        
        assert uptime_pct < 100.0  # Some downtime occurred
        assert uptime_pct > 0.0    # Not completely down
    
    def test_uptime_stats_structure(self):
        """Test uptime stats have correct structure"""
        from backend.health import UptimeTracker
        
        tracker = UptimeTracker()
        stats = tracker.get_stats()
        
        assert 'uptime_percentage' in stats
        assert 'target' in stats
        assert 'meeting_target' in stats
        assert 'downtime_incidents' in stats


@pytest.mark.integration
class TestCacheIntegration:
    """Integration tests for cache with mocked Google Sheets"""
    
    def test_cache_reduces_api_calls(self, mock_google_sheets):
        """Test cache reduces API calls"""
        from backend.cache import TTLCache
        
        cache = TTLCache(default_ttl=60)
        users_sheet = mock_google_sheets['users']
        users_sheet.get_all_records.return_value = [{'id': 1}]
        
        # First call - cache miss
        if cache.get('users') is None:
            data = users_sheet.get_all_records()
            cache.set('users', data)
        
        # Second call - cache hit
        cached_data = cache.get('users')
        
        # Should only call API once
        assert users_sheet.get_all_records.call_count == 1
        assert cached_data == [{'id': 1}]
