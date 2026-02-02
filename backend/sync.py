"""
Multi-Station Synchronization
Handles concurrent access from multiple cashier stations
"""
import uuid
import time
import threading
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import OrderedDict
from enum import Enum
import pytz

try:
    from backend.errors import BankoError, ErrorCode, get_logger
except ImportError:
    from errors import BankoError, ErrorCode, get_logger

PHILIPPINES_TZ = pytz.timezone('Asia/Manila')


def get_philippines_time():
    """Get current time in Philippine timezone"""
    return datetime.now(PHILIPPINES_TZ)


class LockStatus(Enum):
    """Lock acquisition status"""
    ACQUIRED = "acquired"
    BUSY = "busy"
    TIMEOUT = "timeout"
    EXPIRED = "expired"


class TransactionIDGenerator:
    """
    Generate unique transaction IDs to prevent duplicates
    
    Format: YYYYMMDD-HHMMSS-SSSS-XXXX
    - Date and time component
    - Station ID (4 chars)
    - Random component (4 chars)
    """
    
    def __init__(self, station_id: str = "MAIN"):
        self.station_id = station_id[:4].upper().ljust(4, '0')
        self.counter = 0
        self.lock = threading.Lock()
        self.last_timestamp = ""
        
    def generate(self) -> str:
        """Generate a unique transaction ID"""
        with self.lock:
            now = get_philippines_time()
            timestamp = now.strftime("%Y%m%d-%H%M%S")
            
            # Reset counter if timestamp changed
            if timestamp != self.last_timestamp:
                self.counter = 0
                self.last_timestamp = timestamp
            
            self.counter += 1
            
            # Random component for extra uniqueness
            random_part = hashlib.md5(
                f"{time.time_ns()}{self.counter}".encode()
            ).hexdigest()[:4].upper()
            
            return f"{timestamp}-{self.station_id}-{random_part}"
    
    def validate(self, transaction_id: str) -> bool:
        """Validate transaction ID format"""
        if not transaction_id:
            return False
        
        parts = transaction_id.split('-')
        if len(parts) != 4:
            return False
        
        # Validate date part
        try:
            datetime.strptime(parts[0], "%Y%m%d")
            datetime.strptime(parts[1], "%H%M%S")
        except ValueError:
            return False
        
        return True


class DistributedLock:
    """
    Simple distributed lock for preventing concurrent access to resources
    
    In production, consider using Redis or a database-backed lock.
    This implementation is file-based for simplicity.
    """
    
    # Lock timeout in seconds
    DEFAULT_TIMEOUT = 30
    
    # Lock check interval
    CHECK_INTERVAL = 0.1
    
    def __init__(self):
        self.logger = get_logger()
        self.locks: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
    
    def acquire(
        self,
        resource: str,
        station_id: str,
        timeout: float = DEFAULT_TIMEOUT,
        wait: bool = True,
        max_wait: float = 10.0
    ) -> Tuple[LockStatus, Optional[str]]:
        """
        Acquire a lock on a resource
        
        Args:
            resource: Resource identifier (e.g., money card number)
            station_id: Station requesting the lock
            timeout: How long the lock is valid
            wait: Whether to wait for lock availability
            max_wait: Maximum time to wait for lock
        
        Returns:
            Tuple of (status, lock_token)
        """
        start_time = time.time()
        
        while True:
            with self.lock:
                # Check if resource is currently locked
                if resource in self.locks:
                    lock_info = self.locks[resource]
                    
                    # Check if lock has expired
                    if time.time() > lock_info['expires_at']:
                        # Lock expired, remove it
                        del self.locks[resource]
                        self.logger.debug(f"Expired lock removed: {resource}")
                    else:
                        # Lock is held by another station
                        if not wait:
                            return (LockStatus.BUSY, None)
                
                # Try to acquire lock
                if resource not in self.locks:
                    lock_token = str(uuid.uuid4())
                    self.locks[resource] = {
                        'station_id': station_id,
                        'token': lock_token,
                        'acquired_at': time.time(),
                        'expires_at': time.time() + timeout
                    }
                    self.logger.debug(
                        f"Lock acquired: {resource} by station {station_id}"
                    )
                    return (LockStatus.ACQUIRED, lock_token)
            
            # Check wait timeout
            if time.time() - start_time > max_wait:
                return (LockStatus.TIMEOUT, None)
            
            # Wait before retry
            time.sleep(self.CHECK_INTERVAL)
    
    def release(
        self,
        resource: str,
        lock_token: str
    ) -> bool:
        """
        Release a lock
        
        Args:
            resource: Resource identifier
            lock_token: Token received when lock was acquired
        
        Returns:
            True if lock was released, False if invalid token
        """
        with self.lock:
            if resource not in self.locks:
                return True  # Already released
            
            lock_info = self.locks[resource]
            
            if lock_info['token'] != lock_token:
                self.logger.warning(
                    f"Invalid lock token for {resource}"
                )
                return False
            
            del self.locks[resource]
            self.logger.debug(f"Lock released: {resource}")
            return True
    
    def extend(
        self,
        resource: str,
        lock_token: str,
        extension: float = DEFAULT_TIMEOUT
    ) -> bool:
        """Extend a lock's timeout"""
        with self.lock:
            if resource not in self.locks:
                return False
            
            lock_info = self.locks[resource]
            
            if lock_info['token'] != lock_token:
                return False
            
            lock_info['expires_at'] = time.time() + extension
            return True
    
    def is_locked(self, resource: str) -> bool:
        """Check if resource is currently locked"""
        with self.lock:
            if resource not in self.locks:
                return False
            
            # Check expiration
            if time.time() > self.locks[resource]['expires_at']:
                del self.locks[resource]
                return False
            
            return True
    
    def get_lock_info(self, resource: str) -> Optional[Dict[str, Any]]:
        """Get information about a lock"""
        with self.lock:
            if resource not in self.locks:
                return None
            
            lock_info = self.locks[resource].copy()
            lock_info['remaining'] = max(
                0,
                lock_info['expires_at'] - time.time()
            )
            return lock_info
    
    def cleanup_expired(self) -> int:
        """Remove all expired locks"""
        with self.lock:
            now = time.time()
            expired = [
                r for r, info in self.locks.items()
                if now > info['expires_at']
            ]
            for resource in expired:
                del self.locks[resource]
            
            if expired:
                self.logger.info(f"Cleaned up {len(expired)} expired locks")
            
            return len(expired)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get lock statistics"""
        with self.lock:
            now = time.time()
            active_locks = [
                info for info in self.locks.values()
                if now < info['expires_at']
            ]
            
            return {
                'total_locks': len(self.locks),
                'active_locks': len(active_locks),
                'stations': list(set(l['station_id'] for l in active_locks))
            }


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    FIRST_WINS = "first_wins"  # First write wins
    LAST_WINS = "last_wins"    # Last write wins (dangerous)
    MERGE = "merge"            # Attempt to merge changes
    REJECT = "reject"          # Reject conflicting operation


class SyncManager:
    """
    Manages synchronization between multiple stations
    
    Features:
    - Transaction ID generation
    - Distributed locking
    - Conflict detection
    - Operation logging for audit
    """
    
    def __init__(self, station_id: str = "MAIN"):
        self.station_id = station_id
        self.logger = get_logger()
        self.id_generator = TransactionIDGenerator(station_id)
        self.lock_manager = DistributedLock()
        
        # Track recent transactions for duplicate detection
        self.recent_transactions: OrderedDict[str, Dict] = OrderedDict()
        self.max_recent = 1000
        
        # Operation log
        self.operation_log: List[Dict[str, Any]] = []
        self.max_log_size = 10000
    
    def generate_transaction_id(self) -> str:
        """Generate a unique transaction ID"""
        return self.id_generator.generate()
    
    def is_duplicate(self, transaction_id: str) -> bool:
        """Check if transaction is a duplicate"""
        return transaction_id in self.recent_transactions
    
    def record_transaction(
        self,
        transaction_id: str,
        money_card: str,
        operation: str,
        amount: float,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Record a transaction to prevent duplicates
        
        Returns:
            True if recorded, False if duplicate
        """
        if self.is_duplicate(transaction_id):
            self.logger.warning(f"Duplicate transaction rejected: {transaction_id}")
            return False
        
        # Add to recent transactions
        self.recent_transactions[transaction_id] = {
            'money_card': money_card,
            'operation': operation,
            'amount': amount,
            'station_id': self.station_id,
            'timestamp': get_philippines_time().isoformat(),
            'metadata': metadata or {}
        }
        
        # Trim if too large
        while len(self.recent_transactions) > self.max_recent:
            self.recent_transactions.popitem(last=False)
        
        return True
    
    def acquire_card_lock(
        self,
        money_card: str,
        wait: bool = True
    ) -> Tuple[LockStatus, Optional[str]]:
        """Acquire lock on a money card for exclusive access"""
        resource = f"card:{money_card}"
        return self.lock_manager.acquire(
            resource,
            self.station_id,
            wait=wait
        )
    
    def release_card_lock(
        self,
        money_card: str,
        lock_token: str
    ) -> bool:
        """Release lock on a money card"""
        resource = f"card:{money_card}"
        return self.lock_manager.release(resource, lock_token)
    
    def perform_transaction(
        self,
        money_card: str,
        operation: str,
        amount: float,
        executor: Any,  # Callable that performs the actual operation
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, str, Any]:
        """
        Perform a synchronized transaction
        
        Args:
            money_card: Card to operate on
            operation: Operation type (LOAD, SPEND, etc.)
            amount: Transaction amount
            executor: Callable that performs the operation, returns result
            metadata: Additional transaction metadata
        
        Returns:
            Tuple of (success, message, result)
        """
        # Generate transaction ID
        transaction_id = self.generate_transaction_id()
        
        # Try to acquire lock
        lock_status, lock_token = self.acquire_card_lock(money_card)
        
        if lock_status != LockStatus.ACQUIRED:
            return (
                False,
                f"Could not acquire lock: {lock_status.value}",
                None
            )
        
        try:
            # Check for duplicate
            if not self.record_transaction(
                transaction_id,
                money_card,
                operation,
                amount,
                metadata
            ):
                return (False, "Duplicate transaction", None)
            
            # Log operation start
            self._log_operation(
                transaction_id,
                'start',
                money_card,
                operation,
                amount
            )
            
            # Execute the operation
            result = executor()
            
            # Log operation completion
            self._log_operation(
                transaction_id,
                'complete',
                money_card,
                operation,
                amount,
                result
            )
            
            return (True, transaction_id, result)
        
        except Exception as e:
            # Log operation failure
            self._log_operation(
                transaction_id,
                'error',
                money_card,
                operation,
                amount,
                error=str(e)
            )
            
            self.logger.error(
                f"Transaction {transaction_id} failed: {e}"
            )
            return (False, str(e), None)
        
        finally:
            # Always release the lock
            self.release_card_lock(money_card, lock_token)
    
    def _log_operation(
        self,
        transaction_id: str,
        status: str,
        money_card: str,
        operation: str,
        amount: float,
        result: Any = None,
        error: Optional[str] = None
    ):
        """Log operation for audit"""
        log_entry = {
            'transaction_id': transaction_id,
            'status': status,
            'station_id': self.station_id,
            'money_card': money_card,
            'operation': operation,
            'amount': amount,
            'timestamp': get_philippines_time().isoformat(),
            'result': result,
            'error': error
        }
        
        self.operation_log.append(log_entry)
        
        # Trim if too large
        while len(self.operation_log) > self.max_log_size:
            self.operation_log.pop(0)
    
    def get_recent_transactions(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent transactions"""
        items = list(self.recent_transactions.items())[-limit:]
        return [
            {'transaction_id': tid, **data}
            for tid, data in items
        ]
    
    def get_operation_log(
        self,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get operation log entries"""
        log = self.operation_log[-limit:]
        
        if status:
            log = [e for e in log if e['status'] == status]
        
        return log
    
    def get_stats(self) -> Dict[str, Any]:
        """Get synchronization statistics"""
        lock_stats = self.lock_manager.get_stats()
        
        # Count operations by status
        status_counts = {}
        for entry in self.operation_log:
            status = entry['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'station_id': self.station_id,
            'recent_transactions': len(self.recent_transactions),
            'operation_log_size': len(self.operation_log),
            'operation_counts': status_counts,
            'locks': lock_stats
        }


# Global sync manager instances per station
_sync_managers: Dict[str, SyncManager] = {}


def get_sync_manager(station_id: str = "MAIN") -> SyncManager:
    """Get or create sync manager for a station"""
    global _sync_managers
    if station_id not in _sync_managers:
        _sync_managers[station_id] = SyncManager(station_id)
    return _sync_managers[station_id]


def get_all_stations() -> List[str]:
    """Get list of all active station IDs"""
    return list(_sync_managers.keys())
