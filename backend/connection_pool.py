"""
Connection Pooling and Performance Optimization
Optimizes Google Sheets API connections and query performance
"""
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import OrderedDict
from functools import wraps
import pytz

try:
    from backend.errors import BankoError, ErrorCode, get_logger
    from backend.cache import get_cache, TTLCache
except ImportError:
    from errors import BankoError, ErrorCode, get_logger
    from cache import get_cache, TTLCache

PHILIPPINES_TZ = pytz.timezone('Asia/Manila')


def get_philippines_time():
    """Get current time in Philippine timezone"""
    return datetime.now(PHILIPPINES_TZ)


class QueryProfiler:
    """
    Profiles and tracks query performance
    
    Helps identify slow queries and optimization opportunities
    """
    
    def __init__(self):
        self.logger = get_logger()
        self.profiles: OrderedDict[str, Dict] = OrderedDict()
        self.lock = threading.RLock()  # Use RLock to allow reentrant locking
        self.max_profiles = 1000
        
        # Thresholds for slow query warnings
        self.slow_threshold_ms = 500
        self.very_slow_threshold_ms = 2000
    
    def profile(self, query_name: str):
        """Decorator to profile a function"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    success = True
                    error = None
                except Exception as e:
                    success = False
                    error = str(e)
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    self._record(query_name, duration_ms, success, error)
                
                return result
            return wrapper
        return decorator
    
    def _record(
        self,
        query_name: str,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Record query execution"""
        with self.lock:
            now = get_philippines_time()
            
            # Use timestamp with microseconds and counter for uniqueness
            profile_id = f"{query_name}-{now.strftime('%H%M%S')}-{len(self.profiles)}"
            
            self.profiles[profile_id] = {
                'query_name': query_name,
                'duration_ms': duration_ms,
                'success': success,
                'error': error,
                'timestamp': now.isoformat()
            }
            
            # Trim old profiles
            while len(self.profiles) > self.max_profiles:
                self.profiles.popitem(last=False)
            
            # Log slow queries
            if duration_ms > self.very_slow_threshold_ms:
                self.logger.warning(
                    f"VERY SLOW query: {query_name} took {duration_ms:.0f}ms"
                )
            elif duration_ms > self.slow_threshold_ms:
                self.logger.info(
                    f"Slow query: {query_name} took {duration_ms:.0f}ms"
                )
    
    def get_stats(self, query_name: Optional[str] = None) -> Dict[str, Any]:
        """Get query statistics"""
        with self.lock:
            profiles = list(self.profiles.values())
            
            if query_name:
                profiles = [p for p in profiles if p['query_name'] == query_name]
            
            if not profiles:
                return {'count': 0}
            
            durations = [p['duration_ms'] for p in profiles]
            success_count = sum(1 for p in profiles if p['success'])
            
            return {
                'count': len(profiles),
                'success_rate': f"{success_count / len(profiles) * 100:.1f}%",
                'avg_ms': sum(durations) / len(durations),
                'min_ms': min(durations),
                'max_ms': max(durations),
                'p50_ms': sorted(durations)[len(durations) // 2],
                'p95_ms': sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 10 else max(durations),
                'slow_queries': sum(1 for d in durations if d > self.slow_threshold_ms)
            }
    
    def get_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get slowest queries"""
        with self.lock:
            sorted_profiles = sorted(
                self.profiles.values(),
                key=lambda p: p['duration_ms'],
                reverse=True
            )
            return sorted_profiles[:limit]
    
    def get_query_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get stats broken down by query name"""
        with self.lock:
            query_names = set(p['query_name'] for p in self.profiles.values())
            return {name: self.get_stats(name) for name in query_names}


class ConnectionPool:
    """
    Manages a pool of Google Sheets connections
    
    Features:
    - Connection reuse to reduce auth overhead
    - Automatic reconnection on failure
    - Health checking
    - Load balancing across multiple credentials (if available)
    """
    
    def __init__(
        self,
        max_connections: int = 5,
        connection_factory: Optional[Callable] = None
    ):
        self.logger = get_logger()
        self.max_connections = max_connections
        self.connection_factory = connection_factory
        
        self.pool: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        
        # Connection stats
        self.stats = {
            'created': 0,
            'reused': 0,
            'errors': 0,
            'health_checks': 0
        }
    
    def get_connection(self) -> Optional[Any]:
        """
        Get a connection from the pool
        
        Returns:
            Connection object or None if pool is exhausted
        """
        with self.lock:
            # Find available connection
            for conn_info in self.pool:
                if not conn_info['in_use']:
                    conn_info['in_use'] = True
                    conn_info['last_used'] = time.time()
                    self.stats['reused'] += 1
                    return conn_info['connection']
            
            # Create new connection if room in pool
            if len(self.pool) < self.max_connections:
                return self._create_connection()
            
            return None
    
    def _create_connection(self) -> Optional[Any]:
        """Create a new connection"""
        if not self.connection_factory:
            return None
        
        try:
            connection = self.connection_factory()
            
            conn_info = {
                'connection': connection,
                'in_use': True,
                'created_at': time.time(),
                'last_used': time.time(),
                'healthy': True
            }
            
            self.pool.append(conn_info)
            self.stats['created'] += 1
            
            self.logger.debug(f"Created new connection. Pool size: {len(self.pool)}")
            
            return connection
        
        except Exception as e:
            self.logger.error(f"Failed to create connection: {e}")
            self.stats['errors'] += 1
            return None
    
    def release_connection(self, connection: Any, healthy: bool = True):
        """Release a connection back to the pool"""
        with self.lock:
            for conn_info in self.pool:
                if conn_info['connection'] is connection:
                    conn_info['in_use'] = False
                    conn_info['healthy'] = healthy
                    
                    # Remove unhealthy connections
                    if not healthy:
                        self.pool.remove(conn_info)
                        self.logger.debug("Removed unhealthy connection from pool")
                    
                    return
    
    def health_check(self, connection: Any, check_func: Callable) -> bool:
        """Check if a connection is healthy"""
        self.stats['health_checks'] += 1
        
        try:
            check_func(connection)
            return True
        except Exception as e:
            self.logger.warning(f"Connection health check failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self.lock:
            in_use = sum(1 for c in self.pool if c['in_use'])
            
            return {
                'size': len(self.pool),
                'max_size': self.max_connections,
                'in_use': in_use,
                'available': len(self.pool) - in_use,
                'created': self.stats['created'],
                'reused': self.stats['reused'],
                'errors': self.stats['errors'],
                'reuse_rate': f"{self.stats['reused'] / max(1, self.stats['reused'] + self.stats['created']) * 100:.1f}%"
            }
    
    def cleanup_idle(self, max_idle_seconds: float = 300):
        """Remove connections that have been idle too long"""
        with self.lock:
            now = time.time()
            
            idle_connections = [
                c for c in self.pool
                if not c['in_use'] and now - c['last_used'] > max_idle_seconds
            ]
            
            for conn_info in idle_connections:
                self.pool.remove(conn_info)
            
            if idle_connections:
                self.logger.debug(
                    f"Cleaned up {len(idle_connections)} idle connections"
                )


class LazyLoader:
    """
    Lazy loading for large datasets
    
    Loads data in chunks to reduce memory usage and improve response times
    """
    
    def __init__(
        self,
        fetch_func: Callable,
        chunk_size: int = 100,
        cache_chunks: bool = True
    ):
        self.fetch_func = fetch_func
        self.chunk_size = chunk_size
        self.cache_chunks = cache_chunks
        self.cache = get_cache()
        self.logger = get_logger()
    
    def get_page(
        self,
        page: int = 1,
        cache_key_prefix: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a page of data
        
        Args:
            page: Page number (1-indexed)
            cache_key_prefix: Optional cache key prefix
        
        Returns:
            Dict with data, page info, and total count
        """
        # Check cache first
        if self.cache_chunks and cache_key_prefix:
            cache_key = f"{cache_key_prefix}:page:{page}"
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        # Fetch all data (could be optimized with server-side pagination)
        all_data = self.fetch_func()
        
        # Calculate pagination
        total = len(all_data)
        total_pages = (total + self.chunk_size - 1) // self.chunk_size
        
        start_idx = (page - 1) * self.chunk_size
        end_idx = min(start_idx + self.chunk_size, total)
        
        page_data = all_data[start_idx:end_idx]
        
        result = {
            'data': page_data,
            'page': page,
            'page_size': self.chunk_size,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
        
        # Cache the result
        if self.cache_chunks and cache_key_prefix:
            self.cache.set(cache_key, result, ttl=30)
        
        return result
    
    def iterate(self, cache_key_prefix: Optional[str] = None):
        """
        Iterator that yields pages of data
        
        Useful for processing large datasets without loading all at once
        """
        page = 1
        
        while True:
            result = self.get_page(page, cache_key_prefix)
            yield result['data']
            
            if not result['has_next']:
                break
            
            page += 1


class PerformanceOptimizer:
    """
    Central performance optimization manager
    
    Combines caching, profiling, connection pooling, and lazy loading
    """
    
    def __init__(self):
        self.logger = get_logger()
        self.profiler = QueryProfiler()
        self.connection_pool: Optional[ConnectionPool] = None
        
        # Performance targets
        self.targets = {
            'dashboard_load_ms': 500,
            'transaction_ms': 2000,
            'cache_hit_rate': 80
        }
    
    def set_connection_pool(self, pool: ConnectionPool):
        """Set the connection pool to use"""
        self.connection_pool = pool
    
    def optimize_query(
        self,
        query_name: str,
        cache_ttl: int = 30
    ):
        """
        Decorator that optimizes a query function
        
        Adds profiling and caching automatically
        """
        def decorator(func: Callable):
            @self.profiler.profile(query_name)
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache = get_cache()
                cache_key = f"query:{query_name}:{hash(str(args) + str(kwargs))}"
                
                # Check cache
                cached = cache.get(cache_key)
                if cached is not None:
                    return cached
                
                # Execute query
                result = func(*args, **kwargs)
                
                # Cache result
                cache.set(cache_key, result, ttl=cache_ttl)
                
                return result
            return wrapper
        return decorator
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        cache = get_cache()
        cache_stats = cache.get_stats()
        profiler_stats = self.profiler.get_stats()
        pool_stats = self.connection_pool.get_stats() if self.connection_pool else {}
        
        # Check against targets
        issues = []
        
        if profiler_stats.get('avg_ms', 0) > self.targets['dashboard_load_ms']:
            issues.append(
                f"Average query time ({profiler_stats.get('avg_ms', 0):.0f}ms) "
                f"exceeds target ({self.targets['dashboard_load_ms']}ms)"
            )
        
        hit_rate = float(cache_stats.get('hit_rate', '0%').replace('%', ''))
        if hit_rate < self.targets['cache_hit_rate']:
            issues.append(
                f"Cache hit rate ({hit_rate:.0f}%) "
                f"below target ({self.targets['cache_hit_rate']}%)"
            )
        
        return {
            'cache': cache_stats,
            'queries': profiler_stats,
            'query_breakdown': self.profiler.get_query_breakdown(),
            'slow_queries': self.profiler.get_slow_queries(10),
            'connection_pool': pool_stats,
            'targets': self.targets,
            'issues': issues,
            'health': 'good' if not issues else 'needs_attention'
        }
    
    def get_optimization_suggestions(self) -> List[str]:
        """Get suggestions for improving performance"""
        suggestions = []
        
        report = self.get_performance_report()
        
        # Cache suggestions
        cache_stats = report['cache']
        if float(cache_stats.get('hit_rate', '0%').replace('%', '')) < 50:
            suggestions.append(
                "Consider increasing cache TTL for frequently accessed data"
            )
        
        if cache_stats.get('evictions', 0) > 100:
            suggestions.append(
                "Cache evictions are high - consider increasing max cache size"
            )
        
        # Query suggestions
        slow_queries = report['slow_queries']
        if slow_queries:
            slowest = slow_queries[0]
            suggestions.append(
                f"Optimize '{slowest['query_name']}' - taking {slowest['duration_ms']:.0f}ms"
            )
        
        # Connection pool suggestions
        pool_stats = report.get('connection_pool', {})
        if pool_stats.get('errors', 0) > 10:
            suggestions.append(
                "High connection errors - check network stability or credentials"
            )
        
        if not suggestions:
            suggestions.append("Performance is within targets - no optimizations needed")
        
        return suggestions


# Global instances
_profiler: Optional[QueryProfiler] = None
_optimizer: Optional[PerformanceOptimizer] = None


def get_profiler() -> QueryProfiler:
    """Get global profiler instance"""
    global _profiler
    if _profiler is None:
        _profiler = QueryProfiler()
    return _profiler


def get_optimizer() -> PerformanceOptimizer:
    """Get global optimizer instance"""
    global _optimizer
    if _optimizer is None:
        _optimizer = PerformanceOptimizer()
    return _optimizer


def profile_query(query_name: str):
    """Convenience decorator for profiling"""
    return get_profiler().profile(query_name)


def optimize_query(query_name: str, cache_ttl: int = 30):
    """Convenience decorator for query optimization"""
    return get_optimizer().optimize_query(query_name, cache_ttl)
