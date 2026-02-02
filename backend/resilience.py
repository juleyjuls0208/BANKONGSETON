"""
Google Sheets API resilience with retry logic and request batching
"""
import time
import random
from typing import Any, Callable, Optional, List, Dict
from functools import wraps
import gspread
from queue import Queue
import threading

try:
    from backend.errors import BankoError, ErrorCode, get_logger, handle_sheets_error
    from backend.cache import get_cache
except ImportError:
    from errors import BankoError, ErrorCode, get_logger, handle_sheets_error
    from cache import get_cache


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> float:
    """
    Calculate delay for exponential backoff
    
    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        jitter: Add random jitter to prevent thundering herd
    
    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (exponential_base ** attempt), max_delay)
    
    if jitter:
        # Add random jitter (±25%)
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)
    
    return max(0, delay)


def with_retry(config: Optional[RetryConfig] = None):
    """
    Decorator to add retry logic to functions
    
    Usage:
        @with_retry(RetryConfig(max_attempts=5))
        def fetch_data():
            return sheets_api_call()
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            last_error = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                
                except gspread.exceptions.APIError as e:
                    last_error = e
                    error_str = str(e).lower()
                    
                    # Don't retry on certain errors
                    if 'not found' in error_str or 'invalid' in error_str:
                        raise handle_sheets_error(e)
                    
                    # Calculate backoff delay
                    if attempt < config.max_attempts - 1:
                        delay = exponential_backoff(
                            attempt,
                            config.base_delay,
                            config.max_delay,
                            config.exponential_base,
                            config.jitter
                        )
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                
                except Exception as e:
                    last_error = e
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                    raise
            
            # All retries exhausted
            logger.error(f"All {config.max_attempts} attempts failed for {func.__name__}")
            raise handle_sheets_error(last_error)
        
        return wrapper
    return decorator


class WriteQueue:
    """
    Queue for offline write operations
    Stores writes when API is unavailable and retries later
    """
    
    def __init__(self):
        self.queue: Queue = Queue()
        self.failed_queue: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.logger = get_logger()
        self._processing = False
    
    def enqueue(self, operation: str, sheet_name: str, data: Any, metadata: Optional[Dict] = None):
        """
        Add write operation to queue
        
        Args:
            operation: Type of operation (append, update, delete)
            sheet_name: Target sheet name
            data: Data to write
            metadata: Additional context
        """
        write_item = {
            'operation': operation,
            'sheet_name': sheet_name,
            'data': data,
            'metadata': metadata or {},
            'timestamp': time.time(),
            'attempts': 0
        }
        
        self.queue.put(write_item)
        self.logger.info(f"Queued {operation} for {sheet_name}. Queue size: {self.queue.qsize()}")
    
    def process_queue(self, sheets_client) -> Dict[str, int]:
        """
        Process pending write operations
        
        Returns:
            Statistics dict with success/failure counts
        """
        if self._processing:
            self.logger.warning("Queue processing already in progress")
            return {'success': 0, 'failed': 0, 'skipped': 0}
        
        self._processing = True
        stats = {'success': 0, 'failed': 0, 'skipped': 0}
        
        try:
            while not self.queue.empty():
                try:
                    item = self.queue.get_nowait()
                    item['attempts'] += 1
                    
                    # Execute the write operation
                    success = self._execute_write(sheets_client, item)
                    
                    if success:
                        stats['success'] += 1
                    else:
                        # Max 3 attempts
                        if item['attempts'] < 3:
                            self.queue.put(item)  # Re-queue
                        else:
                            self.failed_queue.append(item)
                            stats['failed'] += 1
                            self.logger.error(f"Write failed after 3 attempts: {item}")
                    
                    self.queue.task_done()
                
                except Exception as e:
                    self.logger.error(f"Error processing queue item: {e}")
                    stats['failed'] += 1
        
        finally:
            self._processing = False
        
        return stats
    
    def _execute_write(self, sheets_client, item: Dict) -> bool:
        """Execute a single write operation"""
        try:
            sheet = sheets_client.worksheet(item['sheet_name'])
            
            if item['operation'] == 'append':
                sheet.append_row(item['data'])
            elif item['operation'] == 'update':
                row, col = item['metadata']['row'], item['metadata']['col']
                sheet.update_cell(row, col, item['data'])
            elif item['operation'] == 'batch_update':
                sheet.batch_update(item['data'])
            else:
                self.logger.error(f"Unknown operation: {item['operation']}")
                return False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to execute {item['operation']}: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get queue status"""
        return {
            'pending': self.queue.qsize(),
            'failed': len(self.failed_queue),
            'processing': self._processing
        }


class BatchRequest:
    """
    Batch multiple Google Sheets requests to reduce API calls
    """
    
    def __init__(self, sheet):
        self.sheet = sheet
        self.updates = []
        self.logger = get_logger()
    
    def add_update(self, row: int, col: int, value: Any):
        """Add cell update to batch"""
        self.updates.append({
            'range': self._cell_address(row, col),
            'values': [[value]]
        })
    
    def execute(self):
        """Execute all batched updates"""
        if not self.updates:
            return
        
        try:
            # Use batch_update for efficiency
            self.sheet.batch_update(self.updates)
            self.logger.info(f"Batch updated {len(self.updates)} cells")
            self.updates.clear()
        
        except Exception as e:
            self.logger.error(f"Batch update failed: {e}")
            raise
    
    @staticmethod
    def _cell_address(row: int, col: int) -> str:
        """Convert row/col to A1 notation"""
        col_letter = chr(64 + col)  # A=65, B=66, etc.
        return f"{col_letter}{row}"


# Global write queue instance
_write_queue = WriteQueue()


def get_write_queue() -> WriteQueue:
    """Get global write queue instance"""
    return _write_queue


def enqueue_write(operation: str, sheet_name: str, data: Any, metadata: Optional[Dict] = None):
    """Convenience function to enqueue write operation"""
    _write_queue.enqueue(operation, sheet_name, data, metadata)


def process_write_queue(sheets_client) -> Dict[str, int]:
    """Convenience function to process write queue"""
    return _write_queue.process_queue(sheets_client)


def get_queue_status() -> Dict[str, Any]:
    """Convenience function to get queue status"""
    return _write_queue.get_status()


class RateLimiter:
    """
    Simple rate limiter for API calls
    Prevents hitting Google Sheets API quota
    """
    
    def __init__(self, max_calls: int = 60, window_seconds: int = 60):
        """
        Args:
            max_calls: Maximum calls allowed in window
            window_seconds: Time window in seconds
        """
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.calls = []
        self.lock = threading.Lock()
        self.logger = get_logger()
    
    def acquire(self):
        """
        Acquire permission to make API call
        Blocks if rate limit exceeded
        """
        with self.lock:
            now = time.time()
            
            # Remove old calls outside window
            self.calls = [t for t in self.calls if now - t < self.window_seconds]
            
            # Check if we can make call
            if len(self.calls) >= self.max_calls:
                # Calculate wait time
                oldest_call = min(self.calls)
                wait_time = self.window_seconds - (now - oldest_call)
                
                if wait_time > 0:
                    self.logger.warning(f"Rate limit reached. Waiting {wait_time:.2f}s...")
                    time.sleep(wait_time)
                    # Recursively try again
                    return self.acquire()
            
            # Record this call
            self.calls.append(now)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        with self.lock:
            now = time.time()
            recent_calls = [t for t in self.calls if now - t < self.window_seconds]
            
            return {
                'calls_in_window': len(recent_calls),
                'max_calls': self.max_calls,
                'window_seconds': self.window_seconds,
                'usage_percent': f"{len(recent_calls) / self.max_calls * 100:.1f}%"
            }


# Global rate limiter (60 calls per minute per Google Sheets quota)
_rate_limiter = RateLimiter(max_calls=60, window_seconds=60)


def rate_limited(func: Callable):
    """Decorator to apply rate limiting to function"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        _rate_limiter.acquire()
        return func(*args, **kwargs)
    return wrapper


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    return _rate_limiter
