"""
Phase 4 Tests: Scale & Advanced Features
Tests for NFC payments, multi-station sync, fraud detection, and performance
"""
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pytz

# Import Phase 4 modules
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.nfc_payments import (
    VirtualCard, NFCPaymentManager, get_nfc_manager
)
from backend.sync import (
    TransactionIDGenerator, DistributedLock, SyncManager,
    LockStatus, get_sync_manager
)
from backend.fraud_detection import (
    FraudDetector, FraudAlert, FraudType, RiskLevel,
    get_fraud_detector
)
from backend.connection_pool import (
    QueryProfiler, ConnectionPool, LazyLoader, PerformanceOptimizer,
    get_profiler, get_optimizer
)

PHILIPPINES_TZ = pytz.timezone('Asia/Manila')


# =============================================================================
# NFC Payment Tests
# =============================================================================

class TestVirtualCard:
    """Tests for VirtualCard class"""
    
    def test_virtual_card_creation(self):
        """Test creating a virtual card"""
        card = VirtualCard(
            student_id="S001",
            money_card="MC001",
            device_id="device123",
            device_name="Samsung Galaxy"
        )
        
        assert card.student_id == "S001"
        assert card.money_card == "MC001"
        assert card.device_id == "device123"
        assert card.is_active == True
        assert len(card.token) == 48  # 32 hex + 16 hash
        assert card.pin_hash is None
        assert card.biometric_enabled == False
    
    def test_set_pin(self):
        """Test PIN setup and verification"""
        card = VirtualCard("S001", "MC001", "device123")
        
        # Invalid PIN (too short)
        assert card.set_pin("123") == False
        
        # Valid PIN
        assert card.set_pin("1234") == True
        assert card.pin_hash is not None
        
        # Verify correct PIN
        assert card.verify_pin("1234") == True
        
        # Verify incorrect PIN
        assert card.verify_pin("0000") == False
    
    def test_biometric_enable(self):
        """Test enabling biometric authentication"""
        card = VirtualCard("S001", "MC001", "device123")
        
        assert card.biometric_enabled == False
        card.enable_biometric()
        assert card.biometric_enabled == True
    
    def test_record_use(self):
        """Test recording card usage"""
        card = VirtualCard("S001", "MC001", "device123")
        
        assert card.last_used is None
        assert card.transaction_count == 0
        
        card.record_use()
        
        assert card.last_used is not None
        assert card.transaction_count == 1


class TestNFCPaymentManager:
    """Tests for NFCPaymentManager"""
    
    def setup_method(self):
        """Reset manager before each test"""
        self.manager = NFCPaymentManager()
    
    def test_register_device(self):
        """Test device registration"""
        success, card, message = self.manager.register_device(
            student_id="S001",
            money_card="MC001",
            device_id="device123",
            device_name="Test Phone"
        )
        
        assert success == True
        assert card is not None
        assert card.student_id == "S001"
        assert "success" in message.lower()
    
    def test_register_duplicate_device(self):
        """Test registering same device twice"""
        self.manager.register_device("S001", "MC001", "device123")
        
        success, card, message = self.manager.register_device(
            "S001", "MC001", "device123"
        )
        
        assert success == False
        assert "already registered" in message.lower()
    
    def test_device_limit_per_student(self):
        """Test max devices per student"""
        # Register max devices
        for i in range(NFCPaymentManager.MAX_CARDS_PER_STUDENT):
            self.manager.register_device(
                "S001", "MC001", f"device{i}"
            )
        
        # Try to register one more
        success, _, message = self.manager.register_device(
            "S001", "MC001", "device_extra"
        )
        
        assert success == False
        assert "maximum" in message.lower()
    
    def test_validate_payment_success(self):
        """Test successful payment validation"""
        _, card, _ = self.manager.register_device(
            "S001", "MC001", "device123"
        )
        
        valid, money_card, message = self.manager.validate_payment(
            token=card.token,
            amount=50.0
        )
        
        assert valid == True
        assert money_card == "MC001"
        assert "authorized" in message.lower()
    
    def test_validate_payment_requires_pin(self):
        """Test PIN requirement for high-value transactions"""
        _, card, _ = self.manager.register_device(
            "S001", "MC001", "device123"
        )
        card.set_pin("1234")
        
        # Without PIN
        valid, _, message = self.manager.validate_payment(
            token=card.token,
            amount=150.0  # Above threshold
        )
        
        assert valid == False
        assert "pin required" in message.lower()
        
        # With correct PIN
        valid, money_card, _ = self.manager.validate_payment(
            token=card.token,
            amount=150.0,
            pin="1234"
        )
        
        assert valid == True
        assert money_card == "MC001"
    
    def test_validate_payment_biometric(self):
        """Test biometric authentication for high-value"""
        _, card, _ = self.manager.register_device(
            "S001", "MC001", "device123"
        )
        card.enable_biometric()
        
        # With biometric verified
        valid, money_card, _ = self.manager.validate_payment(
            token=card.token,
            amount=150.0,
            biometric_verified=True
        )
        
        assert valid == True
        assert money_card == "MC001"
    
    def test_deactivate_device(self):
        """Test device deactivation"""
        _, card, _ = self.manager.register_device(
            "S001", "MC001", "device123"
        )
        
        success, _ = self.manager.deactivate_device(
            student_id="S001",
            device_id="device123"
        )
        
        assert success == True
        
        # Try to use deactivated card
        valid, _, message = self.manager.validate_payment(
            token=card.token,
            amount=10.0
        )
        
        assert valid == False
        assert "deactivated" in message.lower()


# =============================================================================
# Synchronization Tests
# =============================================================================

class TestTransactionIDGenerator:
    """Tests for TransactionIDGenerator"""
    
    def test_generate_unique_ids(self):
        """Test generating unique transaction IDs"""
        generator = TransactionIDGenerator("ST01")
        
        ids = [generator.generate() for _ in range(100)]
        
        # All IDs should be unique
        assert len(ids) == len(set(ids))
    
    def test_id_format(self):
        """Test transaction ID format"""
        generator = TransactionIDGenerator("ST01")
        
        tx_id = generator.generate()
        parts = tx_id.split('-')
        
        assert len(parts) == 4
        assert len(parts[0]) == 8  # YYYYMMDD
        assert len(parts[1]) == 6  # HHMMSS
        assert len(parts[2]) == 4  # Station ID
        assert len(parts[3]) == 4  # Random
    
    def test_validate_id(self):
        """Test ID validation"""
        generator = TransactionIDGenerator()
        
        valid_id = generator.generate()
        assert generator.validate(valid_id) == True
        
        assert generator.validate("invalid") == False
        assert generator.validate("") == False
        assert generator.validate(None) == False


class TestDistributedLock:
    """Tests for DistributedLock"""
    
    def setup_method(self):
        """Create fresh lock manager"""
        self.lock = DistributedLock()
    
    def test_acquire_and_release(self):
        """Test basic lock acquire and release"""
        status, token = self.lock.acquire("resource1", "station1")
        
        assert status == LockStatus.ACQUIRED
        assert token is not None
        
        # Release
        released = self.lock.release("resource1", token)
        assert released == True
    
    def test_lock_blocks_others(self):
        """Test that lock prevents concurrent access"""
        # Station 1 acquires lock
        status1, token1 = self.lock.acquire("resource1", "station1")
        assert status1 == LockStatus.ACQUIRED
        
        # Station 2 cannot acquire (no wait)
        status2, token2 = self.lock.acquire(
            "resource1", "station2", wait=False
        )
        assert status2 == LockStatus.BUSY
        assert token2 is None
        
        # Release station 1's lock
        self.lock.release("resource1", token1)
        
        # Now station 2 can acquire
        status3, token3 = self.lock.acquire("resource1", "station2")
        assert status3 == LockStatus.ACQUIRED
    
    def test_lock_expiration(self):
        """Test that locks expire"""
        # Acquire with very short timeout
        status, token = self.lock.acquire(
            "resource1", "station1", timeout=0.1
        )
        assert status == LockStatus.ACQUIRED
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Another station can now acquire
        status2, _ = self.lock.acquire("resource1", "station2", wait=False)
        assert status2 == LockStatus.ACQUIRED
    
    def test_invalid_release_token(self):
        """Test that wrong token cannot release lock"""
        _, token = self.lock.acquire("resource1", "station1")
        
        # Try to release with wrong token
        released = self.lock.release("resource1", "wrong_token")
        assert released == False
        
        # Lock still held
        assert self.lock.is_locked("resource1") == True


class TestSyncManager:
    """Tests for SyncManager"""
    
    def setup_method(self):
        """Create fresh sync manager"""
        self.sync = SyncManager("MAIN")
    
    def test_transaction_recording(self):
        """Test recording transactions"""
        tx_id = self.sync.generate_transaction_id()
        
        recorded = self.sync.record_transaction(
            transaction_id=tx_id,
            money_card="MC001",
            operation="SPEND",
            amount=25.0
        )
        
        assert recorded == True
        
        # Duplicate should fail
        recorded2 = self.sync.record_transaction(
            transaction_id=tx_id,
            money_card="MC001",
            operation="SPEND",
            amount=25.0
        )
        
        assert recorded2 == False
    
    def test_perform_synchronized_transaction(self):
        """Test synchronized transaction execution"""
        # Mock executor
        executor = Mock(return_value={"status": "success"})
        
        success, message, result = self.sync.perform_transaction(
            money_card="MC001",
            operation="SPEND",
            amount=25.0,
            executor=executor
        )
        
        assert success == True
        assert result == {"status": "success"}
        executor.assert_called_once()


# =============================================================================
# Fraud Detection Tests
# =============================================================================

class TestFraudDetector:
    """Tests for FraudDetector"""
    
    def setup_method(self):
        """Create fresh fraud detector"""
        self.detector = FraudDetector()
    
    def test_velocity_detection(self):
        """Test detection of high transaction velocity"""
        # Make many transactions quickly
        for i in range(10):
            alerts = self.detector.analyze_transaction(
                money_card="MC001",
                amount=10.0,
                transaction_type="SPEND",
                current_balance=100.0
            )
        
        # Should have velocity alert
        velocity_alerts = [
            a for a in alerts
            if a.fraud_type == FraudType.VELOCITY
        ]
        assert len(velocity_alerts) > 0
    
    def test_unusual_amount_detection(self):
        """Test detection of unusual amounts"""
        alerts = self.detector.analyze_transaction(
            money_card="MC001",
            amount=250.0,  # Above threshold
            transaction_type="SPEND",
            current_balance=500.0
        )
        
        amount_alerts = [
            a for a in alerts
            if a.fraud_type == FraudType.UNUSUAL_AMOUNT
        ]
        assert len(amount_alerts) > 0
    
    def test_unusual_time_detection(self):
        """Test detection of unusual transaction times"""
        # Mock time to be 11 PM
        with patch('backend.fraud_detection.get_philippines_time') as mock_time:
            mock_time.return_value = datetime(2026, 2, 2, 23, 0, 0, tzinfo=PHILIPPINES_TZ)
            
            alerts = self.detector.analyze_transaction(
                money_card="MC001",
                amount=10.0,
                transaction_type="SPEND",
                current_balance=100.0
            )
            
            time_alerts = [
                a for a in alerts
                if a.fraud_type == FraudType.UNUSUAL_TIME
            ]
            assert len(time_alerts) > 0
    
    def test_card_suspension(self):
        """Test automatic card suspension"""
        self.detector.suspend_card("MC001", "Test suspension")
        
        assert self.detector.is_card_suspended("MC001") == True
        
        # Transaction on suspended card generates alert
        alerts = self.detector.analyze_transaction(
            money_card="MC001",
            amount=10.0,
            transaction_type="SPEND",
            current_balance=100.0
        )
        
        assert len(alerts) > 0
        assert alerts[0].risk_level == RiskLevel.CRITICAL
    
    def test_unsuspend_card(self):
        """Test unsuspending a card"""
        self.detector.suspend_card("MC001", "Test")
        assert self.detector.is_card_suspended("MC001") == True
        
        self.detector.unsuspend_card("MC001")
        assert self.detector.is_card_suspended("MC001") == False
    
    def test_alert_resolution(self):
        """Test resolving fraud alerts"""
        # Use a unique card number to avoid any cross-test pollution
        test_card = "MC_RESOLUTION_TEST"
        
        # Create an alert
        alerts = self.detector.analyze_transaction(
            money_card=test_card,
            amount=250.0,
            transaction_type="SPEND",
            current_balance=500.0
        )
        
        assert len(alerts) > 0
        
        # Resolve just the first alert
        first_alert_id = alerts[0].id
        resolved = self.detector.resolve_alert(first_alert_id, "False positive")
        assert resolved == True
        
        # Verify the specific alert is resolved
        all_alerts = self.detector.get_alerts(money_card=test_card)
        first_alert_dict = next((a for a in all_alerts if a['id'] == first_alert_id), None)
        assert first_alert_dict is not None
        assert first_alert_dict['resolved'] == True
    
    def test_location_mismatch_detection(self):
        """Test detection of location mismatch"""
        # Transaction at station 1
        self.detector.analyze_transaction(
            money_card="MC001",
            amount=10.0,
            transaction_type="SPEND",
            station_id="STATION1",
            current_balance=100.0
        )
        
        # Quick transaction at different station
        alerts = self.detector.analyze_transaction(
            money_card="MC001",
            amount=10.0,
            transaction_type="SPEND",
            station_id="STATION2",
            current_balance=90.0
        )
        
        location_alerts = [
            a for a in alerts
            if a.fraud_type == FraudType.LOCATION_MISMATCH
        ]
        assert len(location_alerts) > 0


# =============================================================================
# Performance Optimization Tests
# =============================================================================

class TestQueryProfiler:
    """Tests for QueryProfiler"""
    
    def setup_method(self):
        """Create fresh profiler"""
        self.profiler = QueryProfiler()
    
    def test_profile_decorator(self):
        """Test profiling a function"""
        @self.profiler.profile("test_query")
        def slow_function():
            time.sleep(0.1)
            return "result"
        
        result = slow_function()
        
        assert result == "result"
        
        stats = self.profiler.get_stats("test_query")
        assert stats['count'] == 1
        assert stats['avg_ms'] >= 100
    
    def test_slow_query_detection(self):
        """Test detection of slow queries"""
        @self.profiler.profile("slow_query")
        def very_slow():
            time.sleep(0.6)  # Above 500ms threshold
            return True
        
        very_slow()
        
        slow = self.profiler.get_slow_queries()
        assert len(slow) > 0
        assert slow[0]['query_name'] == "slow_query"
    
    def test_query_breakdown(self):
        """Test getting stats by query name"""
        @self.profiler.profile("query_a")
        def query_a():
            return 1
        
        @self.profiler.profile("query_b")
        def query_b():
            return 2
        
        query_a()
        query_a()
        query_b()
        
        breakdown = self.profiler.get_query_breakdown()
        
        assert 'query_a' in breakdown
        assert 'query_b' in breakdown
        assert breakdown['query_a']['count'] == 2
        assert breakdown['query_b']['count'] == 1


class TestConnectionPool:
    """Tests for ConnectionPool"""
    
    def test_connection_creation(self):
        """Test creating connections"""
        factory = Mock(return_value="connection")
        pool = ConnectionPool(max_connections=3, connection_factory=factory)
        
        conn = pool.get_connection()
        
        assert conn == "connection"
        factory.assert_called_once()
    
    def test_connection_reuse(self):
        """Test connection reuse"""
        factory = Mock(return_value="connection")
        pool = ConnectionPool(max_connections=3, connection_factory=factory)
        
        conn1 = pool.get_connection()
        pool.release_connection(conn1, healthy=True)
        conn2 = pool.get_connection()
        
        # Factory should only be called once (reused connection)
        assert factory.call_count == 1
        
        stats = pool.get_stats()
        assert stats['reused'] == 1
    
    def test_pool_limit(self):
        """Test pool size limit"""
        factory = Mock(side_effect=lambda: object())
        pool = ConnectionPool(max_connections=2, connection_factory=factory)
        
        conn1 = pool.get_connection()
        conn2 = pool.get_connection()
        conn3 = pool.get_connection()  # Should return None
        
        assert conn1 is not None
        assert conn2 is not None
        assert conn3 is None


class TestLazyLoader:
    """Tests for LazyLoader"""
    
    def test_pagination(self):
        """Test lazy loading with pagination"""
        data = list(range(250))
        fetch = Mock(return_value=data)
        
        loader = LazyLoader(fetch, chunk_size=100, cache_chunks=False)
        
        page1 = loader.get_page(1)
        
        assert len(page1['data']) == 100
        assert page1['total'] == 250
        assert page1['total_pages'] == 3
        assert page1['has_next'] == True
        assert page1['has_prev'] == False
    
    def test_iterator(self):
        """Test iterating through pages"""
        data = list(range(250))
        fetch = Mock(return_value=data)
        
        loader = LazyLoader(fetch, chunk_size=100, cache_chunks=False)
        
        all_data = []
        for page_data in loader.iterate():
            all_data.extend(page_data)
        
        assert len(all_data) == 250


class TestPerformanceOptimizer:
    """Tests for PerformanceOptimizer"""
    
    def test_optimization_suggestions(self):
        """Test getting optimization suggestions"""
        optimizer = PerformanceOptimizer()
        
        suggestions = optimizer.get_optimization_suggestions()
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
    
    def test_performance_report(self):
        """Test generating performance report"""
        optimizer = PerformanceOptimizer()
        
        report = optimizer.get_performance_report()
        
        assert 'cache' in report
        assert 'queries' in report
        assert 'targets' in report
        assert 'health' in report


# =============================================================================
# Integration Tests
# =============================================================================

class TestPhase4Integration:
    """Integration tests for Phase 4 features"""
    
    def test_nfc_with_fraud_detection(self):
        """Test NFC payment with fraud detection"""
        nfc = NFCPaymentManager()
        fraud = FraudDetector()
        
        # Register device
        success, card, _ = nfc.register_device(
            "S001", "MC001", "device123"
        )
        assert success
        
        # Validate payment
        valid, money_card, _ = nfc.validate_payment(
            card.token, 50.0
        )
        assert valid
        
        # Check for fraud
        alerts = fraud.analyze_transaction(
            money_card=money_card,
            amount=50.0,
            transaction_type="SPEND",
            current_balance=200.0
        )
        
        # Normal transaction shouldn't trigger high-risk alerts
        high_risk = [a for a in alerts if a.risk_level == RiskLevel.HIGH]
        assert len(high_risk) == 0
    
    def test_sync_with_profiling(self):
        """Test synchronized transaction with profiling"""
        sync = SyncManager("TEST")
        profiler = QueryProfiler()
        
        @profiler.profile("sync_transaction")
        def execute_sync():
            return sync.perform_transaction(
                money_card="MC001",
                operation="SPEND",
                amount=25.0,
                executor=lambda: {"success": True}
            )
        
        success, _, result = execute_sync()
        
        assert success == True
        
        stats = profiler.get_stats("sync_transaction")
        assert stats['count'] == 1
    
    def test_global_instances(self):
        """Test global instance getters"""
        nfc1 = get_nfc_manager()
        nfc2 = get_nfc_manager()
        assert nfc1 is nfc2
        
        sync1 = get_sync_manager("MAIN")
        sync2 = get_sync_manager("MAIN")
        assert sync1 is sync2
        
        fraud1 = get_fraud_detector()
        fraud2 = get_fraud_detector()
        assert fraud1 is fraud2
        
        profiler1 = get_profiler()
        profiler2 = get_profiler()
        assert profiler1 is profiler2
        
        optimizer1 = get_optimizer()
        optimizer2 = get_optimizer()
        assert optimizer1 is optimizer2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
