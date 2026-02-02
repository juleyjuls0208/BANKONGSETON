"""
Health monitoring and system status tracking
"""
import time
import psutil
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import pytz

try:
    from backend.errors import get_logger
    from backend.cache import get_cache_stats
    from backend.resilience import get_rate_limiter, get_queue_status
except ImportError:
    from errors import get_logger
    from cache import get_cache_stats
    from resilience import get_rate_limiter, get_queue_status


PHILIPPINES_TZ = pytz.timezone('Asia/Manila')


class HealthMonitor:
    """
    System health monitoring
    Tracks uptime, API status, cache performance, etc.
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.logger = get_logger()
        self._google_sheets_status = 'unknown'
        self._last_sheets_check = None
        self._arduino_status = {}
        self._metrics = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_failed': 0,
            'api_errors': 0,
            'cache_saves': 0
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status
        
        Returns:
            Health status dictionary
        """
        return {
            'status': self._get_overall_status(),
            'timestamp': datetime.now(PHILIPPINES_TZ).isoformat(),
            'uptime': self._get_uptime(),
            'components': {
                'google_sheets': self._check_google_sheets(),
                'cache': self._check_cache(),
                'arduino': self._check_arduino(),
                'system': self._check_system()
            },
            'metrics': self._get_metrics(),
            'queue': get_queue_status()
        }
    
    def _get_overall_status(self) -> str:
        """
        Determine overall system status
        
        Returns:
            'healthy', 'degraded', or 'unhealthy'
        """
        sheets_ok = self._google_sheets_status in ['connected', 'unknown']
        cache_ok = True  # Cache failures are non-critical
        
        if sheets_ok and cache_ok:
            return 'healthy'
        elif sheets_ok or cache_ok:
            return 'degraded'
        else:
            return 'unhealthy'
    
    def _get_uptime(self) -> Dict[str, Any]:
        """Get system uptime"""
        uptime_seconds = time.time() - self.start_time
        uptime_timedelta = timedelta(seconds=int(uptime_seconds))
        
        return {
            'seconds': int(uptime_seconds),
            'formatted': str(uptime_timedelta),
            'start_time': datetime.fromtimestamp(self.start_time, PHILIPPINES_TZ).isoformat()
        }
    
    def _check_google_sheets(self) -> Dict[str, Any]:
        """Check Google Sheets API status"""
        rate_limiter_stats = get_rate_limiter().get_stats()
        
        return {
            'status': self._google_sheets_status,
            'last_check': self._last_sheets_check.isoformat() if self._last_sheets_check else None,
            'rate_limiter': rate_limiter_stats
        }
    
    def _check_cache(self) -> Dict[str, Any]:
        """Check cache health"""
        cache_stats = get_cache_stats()
        
        # Determine cache health
        hit_rate_str = cache_stats['hit_rate'].rstrip('%')
        hit_rate = float(hit_rate_str) if hit_rate_str else 0
        
        if hit_rate >= 70:
            status = 'optimal'
        elif hit_rate >= 40:
            status = 'good'
        else:
            status = 'poor'
        
        return {
            'status': status,
            'stats': cache_stats
        }
    
    def _check_arduino(self) -> Dict[str, Any]:
        """Check Arduino connection status"""
        if not self._arduino_status:
            return {
                'status': 'disconnected',
                'ports': []
            }
        
        return {
            'status': 'connected' if any(self._arduino_status.values()) else 'disconnected',
            'ports': self._arduino_status
        }
    
    def _check_system(self) -> Dict[str, Any]:
        """Check system resources"""
        try:
            return {
                'status': 'healthy',
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
                'process': {
                    'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024,
                    'threads': psutil.Process().num_threads()
                }
            }
        except Exception as e:
            self.logger.error(f"Error checking system resources: {e}")
            return {
                'status': 'unknown',
                'error': str(e)
            }
    
    def _get_metrics(self) -> Dict[str, Any]:
        """Get application metrics"""
        total_requests = self._metrics['requests_total']
        success_rate = (
            self._metrics['requests_success'] / total_requests * 100
            if total_requests > 0 else 0
        )
        
        return {
            'requests': {
                'total': total_requests,
                'success': self._metrics['requests_success'],
                'failed': self._metrics['requests_failed'],
                'success_rate': f"{success_rate:.2f}%"
            },
            'errors': {
                'api_errors': self._metrics['api_errors']
            },
            'cache': {
                'saves': self._metrics['cache_saves']
            }
        }
    
    def update_sheets_status(self, status: str):
        """Update Google Sheets connection status"""
        self._google_sheets_status = status
        self._last_sheets_check = datetime.now(PHILIPPINES_TZ)
    
    def update_arduino_status(self, port: str, connected: bool):
        """Update Arduino connection status"""
        self._arduino_status[port] = connected
    
    def increment_metric(self, metric: str):
        """Increment a metric counter"""
        if metric in self._metrics:
            self._metrics[metric] += 1
    
    def record_request(self, success: bool):
        """Record API request"""
        self._metrics['requests_total'] += 1
        if success:
            self._metrics['requests_success'] += 1
        else:
            self._metrics['requests_failed'] += 1


class UptimeTracker:
    """
    Track system uptime and calculate availability percentage
    Target: 99% uptime
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.downtime_periods = []
        self.current_downtime_start = None
        self.logger = get_logger()
    
    def mark_down(self):
        """Mark system as down"""
        if self.current_downtime_start is None:
            self.current_downtime_start = time.time()
            self.logger.warning("System marked as DOWN")
    
    def mark_up(self):
        """Mark system as up"""
        if self.current_downtime_start is not None:
            downtime_duration = time.time() - self.current_downtime_start
            self.downtime_periods.append({
                'start': self.current_downtime_start,
                'end': time.time(),
                'duration': downtime_duration
            })
            self.current_downtime_start = None
            self.logger.info(f"System marked as UP (downtime: {downtime_duration:.2f}s)")
    
    def get_uptime_percentage(self) -> float:
        """
        Calculate uptime percentage
        
        Returns:
            Uptime percentage (0-100)
        """
        total_time = time.time() - self.start_time
        
        # Calculate total downtime
        total_downtime = sum(p['duration'] for p in self.downtime_periods)
        
        # Add current downtime if system is down
        if self.current_downtime_start is not None:
            total_downtime += time.time() - self.current_downtime_start
        
        uptime_percentage = ((total_time - total_downtime) / total_time * 100) if total_time > 0 else 100
        return uptime_percentage
    
    def get_stats(self) -> Dict[str, Any]:
        """Get uptime statistics"""
        uptime_pct = self.get_uptime_percentage()
        total_time = time.time() - self.start_time
        total_downtime = sum(p['duration'] for p in self.downtime_periods)
        
        return {
            'uptime_percentage': f"{uptime_pct:.4f}%",
            'target': "99.00%",
            'meeting_target': uptime_pct >= 99.0,
            'total_time_seconds': int(total_time),
            'total_downtime_seconds': int(total_downtime),
            'downtime_incidents': len(self.downtime_periods),
            'currently_down': self.current_downtime_start is not None
        }


# Global instances
_health_monitor = HealthMonitor()
_uptime_tracker = UptimeTracker()


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor instance"""
    return _health_monitor


def get_uptime_tracker() -> UptimeTracker:
    """Get global uptime tracker instance"""
    return _uptime_tracker


def get_health_status() -> Dict[str, Any]:
    """Convenience function to get health status"""
    return _health_monitor.get_health_status()


def get_uptime_stats() -> Dict[str, Any]:
    """Convenience function to get uptime stats"""
    return _uptime_tracker.get_stats()


def update_sheets_status(status: str):
    """Update Google Sheets status"""
    _health_monitor.update_sheets_status(status)
    
    if status == 'connected':
        _uptime_tracker.mark_up()
    else:
        _uptime_tracker.mark_down()


def update_arduino_status(port: str, connected: bool):
    """Update Arduino status"""
    _health_monitor.update_arduino_status(port, connected)


def record_request(success: bool):
    """Record API request"""
    _health_monitor.record_request(success)


def increment_metric(metric: str):
    """Increment metric counter"""
    _health_monitor.increment_metric(metric)
