"""
Advanced Fraud Detection System
Detects suspicious transactions and triggers alerts
"""
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
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


class RiskLevel(Enum):
    """Transaction risk level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FraudType(Enum):
    """Types of fraud patterns"""
    VELOCITY = "velocity"           # Too many transactions in short time
    UNUSUAL_AMOUNT = "unusual_amount"  # Amount outside normal range
    UNUSUAL_TIME = "unusual_time"    # Transaction at unusual hours
    LOCATION_MISMATCH = "location_mismatch"  # Different stations rapidly
    RAPID_SPENDING = "rapid_spending"  # Spending too fast
    CARD_CLONING = "card_cloning"    # Multiple locations same time
    DORMANT_ACTIVATION = "dormant_activation"  # Sudden activity after long dormancy


class FraudAlert:
    """Represents a fraud alert"""
    
    def __init__(
        self,
        money_card: str,
        fraud_type: FraudType,
        risk_level: RiskLevel,
        description: str,
        details: Optional[Dict] = None
    ):
        self.id = f"ALERT-{int(time.time() * 1000)}"
        self.money_card = money_card
        self.fraud_type = fraud_type
        self.risk_level = risk_level
        self.description = description
        self.details = details or {}
        self.created_at = get_philippines_time()
        self.resolved = False
        self.resolved_at = None
        self.resolution_notes = None
        self.auto_action_taken = None
    
    def resolve(self, notes: str = None):
        """Mark alert as resolved"""
        self.resolved = True
        self.resolved_at = get_philippines_time()
        self.resolution_notes = notes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'money_card': self.money_card,
            'fraud_type': self.fraud_type.value,
            'risk_level': self.risk_level.value,
            'description': self.description,
            'details': self.details,
            'created_at': self.created_at.isoformat(),
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_notes': self.resolution_notes,
            'auto_action_taken': self.auto_action_taken
        }


class FraudDetector:
    """
    Detects fraudulent transaction patterns
    
    Detection rules:
    1. Velocity: More than 5 transactions in 5 minutes
    2. Unusual Amount: Transaction > ₱200 or > 3x average
    3. Unusual Time: Transactions between 10 PM - 6 AM
    4. Rapid Spending: Spending > 50% of balance in 1 hour
    5. Dormant Activation: First transaction after 30+ days of inactivity
    """
    
    # Configuration thresholds
    VELOCITY_LIMIT = 5  # Max transactions
    VELOCITY_WINDOW = 5 * 60  # 5 minutes in seconds
    
    UNUSUAL_AMOUNT_ABSOLUTE = 200.0  # Absolute threshold
    UNUSUAL_AMOUNT_MULTIPLIER = 3.0  # Times average
    
    UNUSUAL_TIME_START = 22  # 10 PM
    UNUSUAL_TIME_END = 6     # 6 AM
    
    RAPID_SPENDING_PERCENT = 50  # Percent of balance
    RAPID_SPENDING_WINDOW = 60 * 60  # 1 hour in seconds
    
    DORMANT_DAYS = 30  # Days of inactivity
    
    # Auto-suspend thresholds
    AUTO_SUSPEND_VELOCITY = 10  # More than 10 transactions in 5 min
    AUTO_SUSPEND_RAPID_SPENDING = 80  # More than 80% balance in 1 hour
    
    def __init__(self):
        self.logger = get_logger()
        
        # Track transaction history per card
        self.transaction_history: Dict[str, List[Dict]] = defaultdict(list)
        
        # Track last activity per card
        self.last_activity: Dict[str, datetime] = {}
        
        # Track spending patterns per card
        self.spending_averages: Dict[str, float] = {}
        
        # Active alerts
        self.alerts: List[FraudAlert] = []
        
        # Suspended cards
        self.suspended_cards: Dict[str, Dict[str, Any]] = {}
        
        # Station locations (for location-based detection)
        self.station_locations: Dict[str, str] = {}
    
    def analyze_transaction(
        self,
        money_card: str,
        amount: float,
        transaction_type: str,
        station_id: str = "MAIN",
        current_balance: float = 0.0
    ) -> List[FraudAlert]:
        """
        Analyze a transaction for fraud patterns
        
        Returns:
            List of fraud alerts generated
        """
        alerts = []
        now = get_philippines_time()
        
        # Check if card is suspended
        if money_card in self.suspended_cards:
            alert = FraudAlert(
                money_card=money_card,
                fraud_type=FraudType.CARD_CLONING,
                risk_level=RiskLevel.CRITICAL,
                description="Transaction attempted on suspended card",
                details={'reason': self.suspended_cards[money_card].get('reason')}
            )
            alerts.append(alert)
            self._add_alert(alert)
            return alerts
        
        # Record transaction
        transaction = {
            'timestamp': now,
            'amount': amount,
            'type': transaction_type,
            'station_id': station_id,
            'balance_after': current_balance - amount if transaction_type == 'SPEND' else current_balance + amount
        }
        self.transaction_history[money_card].append(transaction)
        
        # Clean old history (keep last 24 hours)
        cutoff = now - timedelta(hours=24)
        self.transaction_history[money_card] = [
            t for t in self.transaction_history[money_card]
            if t['timestamp'] > cutoff
        ]
        
        # Run detection checks
        if transaction_type == 'SPEND':
            alerts.extend(self._check_velocity(money_card, now))
            alerts.extend(self._check_unusual_amount(money_card, amount))
            alerts.extend(self._check_unusual_time(money_card, now))
            alerts.extend(self._check_rapid_spending(money_card, current_balance))
            alerts.extend(self._check_dormant_activation(money_card, now))
            alerts.extend(self._check_location_mismatch(money_card, station_id, now))
        
        # Update last activity
        self.last_activity[money_card] = now
        
        # Update spending average
        self._update_spending_average(money_card, amount, transaction_type)
        
        # Check for auto-suspend conditions
        self._check_auto_suspend(money_card, alerts)
        
        return alerts
    
    def _check_velocity(
        self,
        money_card: str,
        now: datetime
    ) -> List[FraudAlert]:
        """Check for too many transactions in short time"""
        alerts = []
        
        window_start = now - timedelta(seconds=self.VELOCITY_WINDOW)
        recent = [
            t for t in self.transaction_history[money_card]
            if t['timestamp'] > window_start
        ]
        
        if len(recent) > self.VELOCITY_LIMIT:
            risk = RiskLevel.HIGH if len(recent) > self.AUTO_SUSPEND_VELOCITY else RiskLevel.MEDIUM
            
            alert = FraudAlert(
                money_card=money_card,
                fraud_type=FraudType.VELOCITY,
                risk_level=risk,
                description=f"High transaction velocity: {len(recent)} transactions in {self.VELOCITY_WINDOW // 60} minutes",
                details={
                    'transaction_count': len(recent),
                    'window_minutes': self.VELOCITY_WINDOW // 60,
                    'threshold': self.VELOCITY_LIMIT
                }
            )
            alerts.append(alert)
            self._add_alert(alert)
        
        return alerts
    
    def _check_unusual_amount(
        self,
        money_card: str,
        amount: float
    ) -> List[FraudAlert]:
        """Check for unusually large transaction amounts"""
        alerts = []
        
        # Check absolute threshold
        if amount > self.UNUSUAL_AMOUNT_ABSOLUTE:
            alert = FraudAlert(
                money_card=money_card,
                fraud_type=FraudType.UNUSUAL_AMOUNT,
                risk_level=RiskLevel.MEDIUM,
                description=f"Large transaction: ₱{amount:.2f} exceeds ₱{self.UNUSUAL_AMOUNT_ABSOLUTE}",
                details={
                    'amount': amount,
                    'threshold': self.UNUSUAL_AMOUNT_ABSOLUTE
                }
            )
            alerts.append(alert)
            self._add_alert(alert)
            return alerts
        
        # Check relative to average
        avg = self.spending_averages.get(money_card, 0)
        if avg > 0 and amount > avg * self.UNUSUAL_AMOUNT_MULTIPLIER:
            alert = FraudAlert(
                money_card=money_card,
                fraud_type=FraudType.UNUSUAL_AMOUNT,
                risk_level=RiskLevel.LOW,
                description=f"Transaction ₱{amount:.2f} is {amount/avg:.1f}x above average (₱{avg:.2f})",
                details={
                    'amount': amount,
                    'average': avg,
                    'multiplier': amount / avg
                }
            )
            alerts.append(alert)
            self._add_alert(alert)
        
        return alerts
    
    def _check_unusual_time(
        self,
        money_card: str,
        now: datetime
    ) -> List[FraudAlert]:
        """Check for transactions at unusual hours"""
        alerts = []
        
        hour = now.hour
        
        is_unusual = (hour >= self.UNUSUAL_TIME_START or hour < self.UNUSUAL_TIME_END)
        
        if is_unusual:
            alert = FraudAlert(
                money_card=money_card,
                fraud_type=FraudType.UNUSUAL_TIME,
                risk_level=RiskLevel.LOW,
                description=f"Transaction at unusual hour: {hour:02d}:00 (outside {self.UNUSUAL_TIME_END}AM-{self.UNUSUAL_TIME_START-12}PM)",
                details={
                    'hour': hour,
                    'normal_start': self.UNUSUAL_TIME_END,
                    'normal_end': self.UNUSUAL_TIME_START
                }
            )
            alerts.append(alert)
            self._add_alert(alert)
        
        return alerts
    
    def _check_rapid_spending(
        self,
        money_card: str,
        current_balance: float
    ) -> List[FraudAlert]:
        """Check for rapid spending of balance"""
        alerts = []
        
        if current_balance <= 0:
            return alerts
        
        now = get_philippines_time()
        window_start = now - timedelta(seconds=self.RAPID_SPENDING_WINDOW)
        
        # Calculate total spent in window
        recent_spending = sum(
            t['amount'] for t in self.transaction_history[money_card]
            if t['timestamp'] > window_start and t['type'] == 'SPEND'
        )
        
        # Calculate as percentage of (current + spent)
        total_balance = current_balance + recent_spending
        if total_balance > 0:
            percent_spent = (recent_spending / total_balance) * 100
            
            if percent_spent >= self.RAPID_SPENDING_PERCENT:
                risk = RiskLevel.HIGH if percent_spent >= self.AUTO_SUSPEND_RAPID_SPENDING else RiskLevel.MEDIUM
                
                alert = FraudAlert(
                    money_card=money_card,
                    fraud_type=FraudType.RAPID_SPENDING,
                    risk_level=risk,
                    description=f"Rapid spending: {percent_spent:.0f}% of balance in 1 hour",
                    details={
                        'spent': recent_spending,
                        'balance_before': total_balance,
                        'percent': percent_spent,
                        'window_hours': self.RAPID_SPENDING_WINDOW // 3600
                    }
                )
                alerts.append(alert)
                self._add_alert(alert)
        
        return alerts
    
    def _check_dormant_activation(
        self,
        money_card: str,
        now: datetime
    ) -> List[FraudAlert]:
        """Check for sudden activity after dormancy"""
        alerts = []
        
        if money_card in self.last_activity:
            last = self.last_activity[money_card]
            days_inactive = (now - last).days
            
            if days_inactive >= self.DORMANT_DAYS:
                alert = FraudAlert(
                    money_card=money_card,
                    fraud_type=FraudType.DORMANT_ACTIVATION,
                    risk_level=RiskLevel.MEDIUM,
                    description=f"Card activated after {days_inactive} days of inactivity",
                    details={
                        'days_inactive': days_inactive,
                        'last_activity': last.isoformat(),
                        'threshold_days': self.DORMANT_DAYS
                    }
                )
                alerts.append(alert)
                self._add_alert(alert)
        
        return alerts
    
    def _check_location_mismatch(
        self,
        money_card: str,
        station_id: str,
        now: datetime
    ) -> List[FraudAlert]:
        """Check for transactions at different locations in short time"""
        alerts = []
        
        # Need at least 2 transactions
        if len(self.transaction_history[money_card]) < 2:
            return alerts
        
        # Check last transaction's station
        recent = sorted(
            self.transaction_history[money_card],
            key=lambda t: t['timestamp'],
            reverse=True
        )
        
        if len(recent) >= 2:
            current = recent[0]
            previous = recent[1]
            
            # Different stations within 5 minutes
            time_diff = (current['timestamp'] - previous['timestamp']).total_seconds()
            
            if time_diff < 300 and current['station_id'] != previous['station_id']:
                alert = FraudAlert(
                    money_card=money_card,
                    fraud_type=FraudType.LOCATION_MISMATCH,
                    risk_level=RiskLevel.HIGH,
                    description=f"Transaction at different station within {time_diff:.0f} seconds",
                    details={
                        'current_station': current['station_id'],
                        'previous_station': previous['station_id'],
                        'time_diff_seconds': time_diff
                    }
                )
                alerts.append(alert)
                self._add_alert(alert)
        
        return alerts
    
    def _update_spending_average(
        self,
        money_card: str,
        amount: float,
        transaction_type: str
    ):
        """Update spending average for a card"""
        if transaction_type != 'SPEND':
            return
        
        current_avg = self.spending_averages.get(money_card, 0)
        
        # Simple moving average (last 20 transactions)
        spend_history = [
            t['amount'] for t in self.transaction_history[money_card]
            if t['type'] == 'SPEND'
        ][-20:]
        
        if spend_history:
            self.spending_averages[money_card] = sum(spend_history) / len(spend_history)
    
    def _add_alert(self, alert: FraudAlert):
        """Add alert to list"""
        self.alerts.append(alert)
        self.logger.warning(
            f"Fraud alert [{alert.risk_level.value}]: {alert.description}"
        )
        
        # Trim old alerts (keep last 1000)
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
    
    def _check_auto_suspend(
        self,
        money_card: str,
        alerts: List[FraudAlert]
    ):
        """Check if card should be auto-suspended"""
        critical_alerts = [
            a for a in alerts
            if a.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        ]
        
        if len(critical_alerts) >= 2:
            self.suspend_card(
                money_card,
                reason="Multiple high-risk alerts",
                auto=True
            )
            
            for alert in alerts:
                alert.auto_action_taken = "Card suspended"
    
    def suspend_card(
        self,
        money_card: str,
        reason: str,
        auto: bool = False
    ):
        """Suspend a card"""
        self.suspended_cards[money_card] = {
            'reason': reason,
            'suspended_at': get_philippines_time().isoformat(),
            'auto_suspended': auto
        }
        self.logger.warning(
            f"Card suspended: {money_card} - {reason} (auto={auto})"
        )
    
    def unsuspend_card(self, money_card: str) -> bool:
        """Unsuspend a card"""
        if money_card in self.suspended_cards:
            del self.suspended_cards[money_card]
            self.logger.info(f"Card unsuspended: {money_card}")
            return True
        return False
    
    def get_alerts(
        self,
        money_card: Optional[str] = None,
        risk_level: Optional[RiskLevel] = None,
        unresolved_only: bool = False,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get fraud alerts with optional filters"""
        alerts = self.alerts
        
        if money_card:
            alerts = [a for a in alerts if a.money_card == money_card]
        
        if risk_level:
            alerts = [a for a in alerts if a.risk_level == risk_level]
        
        if unresolved_only:
            alerts = [a for a in alerts if not a.resolved]
        
        return [a.to_dict() for a in alerts[-limit:]]
    
    def resolve_alert(
        self,
        alert_id: str,
        notes: str = None
    ) -> bool:
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolve(notes)
                return True
        return False
    
    def get_suspended_cards(self) -> Dict[str, Dict[str, Any]]:
        """Get all suspended cards"""
        return self.suspended_cards.copy()
    
    def is_card_suspended(self, money_card: str) -> bool:
        """Check if a card is suspended"""
        return money_card in self.suspended_cards
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fraud detection statistics"""
        now = get_philippines_time()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        today_alerts = [
            a for a in self.alerts
            if a.created_at >= today_start
        ]
        
        by_type = defaultdict(int)
        by_risk = defaultdict(int)
        
        for alert in today_alerts:
            by_type[alert.fraud_type.value] += 1
            by_risk[alert.risk_level.value] += 1
        
        return {
            'total_alerts': len(self.alerts),
            'unresolved_alerts': sum(1 for a in self.alerts if not a.resolved),
            'today_alerts': len(today_alerts),
            'alerts_by_type': dict(by_type),
            'alerts_by_risk': dict(by_risk),
            'suspended_cards': len(self.suspended_cards),
            'cards_monitored': len(self.transaction_history)
        }


# Global fraud detector instance
_fraud_detector: Optional[FraudDetector] = None


def get_fraud_detector() -> FraudDetector:
    """Get global fraud detector instance"""
    global _fraud_detector
    if _fraud_detector is None:
        _fraud_detector = FraudDetector()
    return _fraud_detector
