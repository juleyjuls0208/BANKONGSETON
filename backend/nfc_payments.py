"""
NFC Phone Payments - Host Card Emulation (HCE) Support
Allows students to use their phone as a virtual money card
"""
import uuid
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pytz

try:
    from backend.errors import BankoError, ErrorCode, get_logger
except ImportError:
    from errors import BankoError, ErrorCode, get_logger

PHILIPPINES_TZ = pytz.timezone('Asia/Manila')

def get_philippines_time():
    """Get current time in Philippine timezone"""
    return datetime.now(PHILIPPINES_TZ)


class VirtualCard:
    """Represents a virtual NFC card linked to a student's account"""
    
    def __init__(
        self,
        student_id: str,
        money_card: str,
        device_id: str,
        device_name: str = "Unknown Device"
    ):
        self.id = str(uuid.uuid4())
        self.student_id = student_id
        self.money_card = money_card  # Links to physical card's balance
        self.device_id = device_id
        self.device_name = device_name
        self.created_at = get_philippines_time()
        self.last_used = None
        self.is_active = True
        self.token = self._generate_secure_token()
        self.pin_hash: Optional[str] = None
        self.biometric_enabled = False
        self.transaction_count = 0
        
    def _generate_secure_token(self) -> str:
        """Generate a secure HCE token for NFC communication"""
        # Token format: timestamp + random + hash
        timestamp = str(int(time.time()))
        random_part = secrets.token_hex(16)
        data = f"{self.student_id}:{self.money_card}:{timestamp}:{random_part}"
        hash_part = hashlib.sha256(data.encode()).hexdigest()[:16]
        return f"{random_part}{hash_part}"
    
    def set_pin(self, pin: str) -> bool:
        """Set PIN for high-value transactions"""
        if len(pin) < 4 or len(pin) > 6:
            return False
        self.pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        return True
    
    def verify_pin(self, pin: str) -> bool:
        """Verify PIN"""
        if not self.pin_hash:
            return True  # No PIN set
        return self.pin_hash == hashlib.sha256(pin.encode()).hexdigest()
    
    def enable_biometric(self) -> None:
        """Enable biometric authentication"""
        self.biometric_enabled = True
    
    def record_use(self) -> None:
        """Record card usage"""
        self.last_used = get_philippines_time()
        self.transaction_count += 1
    
    def deactivate(self) -> None:
        """Deactivate the virtual card"""
        self.is_active = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'money_card': self.money_card,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'is_active': self.is_active,
            'token': self.token,
            'pin_set': self.pin_hash is not None,
            'biometric_enabled': self.biometric_enabled,
            'transaction_count': self.transaction_count
        }


class NFCPaymentManager:
    """
    Manages NFC phone payments using Host Card Emulation (HCE)
    
    Security features:
    - Secure token generation per device
    - PIN required for transactions > ₱100
    - Biometric authentication support
    - Device binding (one phone per student)
    - Token expiration and refresh
    """
    
    # Threshold for requiring PIN authentication
    PIN_REQUIRED_THRESHOLD = 100.0
    
    # Maximum virtual cards per student
    MAX_CARDS_PER_STUDENT = 2
    
    # Token validity period (hours)
    TOKEN_VALIDITY_HOURS = 24 * 7  # 7 days
    
    def __init__(self):
        self.logger = get_logger()
        # In-memory storage (in production, use database)
        self.virtual_cards: Dict[str, VirtualCard] = {}  # token -> VirtualCard
        self.student_cards: Dict[str, List[str]] = {}  # student_id -> [card_ids]
        self.device_bindings: Dict[str, str] = {}  # device_id -> student_id
    
    def register_device(
        self,
        student_id: str,
        money_card: str,
        device_id: str,
        device_name: str = "Unknown Device"
    ) -> Tuple[bool, Optional[VirtualCard], str]:
        """
        Register a new device for NFC payments
        
        Returns:
            Tuple of (success, virtual_card, message)
        """
        # Check if device is already registered to another student
        if device_id in self.device_bindings:
            existing_student = self.device_bindings[device_id]
            if existing_student != student_id:
                return (
                    False,
                    None,
                    "Device is already registered to another student"
                )
        
        # Check card limit per student
        student_cards = self.student_cards.get(student_id, [])
        if len(student_cards) >= self.MAX_CARDS_PER_STUDENT:
            return (
                False,
                None,
                f"Maximum {self.MAX_CARDS_PER_STUDENT} devices allowed per student"
            )
        
        # Check if this device already has a card for this student
        for card_id in student_cards:
            for token, card in self.virtual_cards.items():
                if card.id == card_id and card.device_id == device_id:
                    if card.is_active:
                        return (False, card, "Device already registered")
        
        # Create new virtual card
        virtual_card = VirtualCard(
            student_id=student_id,
            money_card=money_card,
            device_id=device_id,
            device_name=device_name
        )
        
        # Store the card
        self.virtual_cards[virtual_card.token] = virtual_card
        
        # Update student's card list
        if student_id not in self.student_cards:
            self.student_cards[student_id] = []
        self.student_cards[student_id].append(virtual_card.id)
        
        # Bind device to student
        self.device_bindings[device_id] = student_id
        
        self.logger.info(
            f"Registered NFC device for student {student_id}: "
            f"{device_name} ({device_id[:8]}...)"
        )
        
        return (True, virtual_card, "Device registered successfully")
    
    def validate_payment(
        self,
        token: str,
        amount: float,
        pin: Optional[str] = None,
        biometric_verified: bool = False
    ) -> Tuple[bool, Optional[str], str]:
        """
        Validate an NFC payment request
        
        Args:
            token: HCE token from the phone
            amount: Transaction amount
            pin: PIN if required for high-value transactions
            biometric_verified: Whether biometric was verified on device
        
        Returns:
            Tuple of (valid, money_card_number, message)
        """
        # Find virtual card by token
        if token not in self.virtual_cards:
            return (False, None, "Invalid or expired token")
        
        virtual_card = self.virtual_cards[token]
        
        # Check if card is active
        if not virtual_card.is_active:
            return (False, None, "Virtual card is deactivated")
        
        # Check token age
        token_age = get_philippines_time() - virtual_card.created_at
        if token_age.total_seconds() > self.TOKEN_VALIDITY_HOURS * 3600:
            return (False, None, "Token expired. Please re-authenticate")
        
        # Check if PIN/biometric required for high-value transactions
        if amount >= self.PIN_REQUIRED_THRESHOLD:
            if virtual_card.biometric_enabled and biometric_verified:
                # Biometric verified, proceed
                pass
            elif virtual_card.pin_hash:
                if not pin:
                    return (False, None, f"PIN required for amounts ≥₱{self.PIN_REQUIRED_THRESHOLD}")
                if not virtual_card.verify_pin(pin):
                    return (False, None, "Invalid PIN")
            elif not virtual_card.biometric_enabled and not virtual_card.pin_hash:
                return (
                    False,
                    None,
                    f"Please set up PIN or biometric for amounts ≥₱{self.PIN_REQUIRED_THRESHOLD}"
                )
        
        # Record usage
        virtual_card.record_use()
        
        self.logger.info(
            f"NFC payment validated: {virtual_card.student_id} - ₱{amount:.2f}"
        )
        
        return (True, virtual_card.money_card, "Payment authorized")
    
    def get_student_devices(self, student_id: str) -> List[Dict[str, Any]]:
        """Get all registered devices for a student"""
        devices = []
        card_ids = self.student_cards.get(student_id, [])
        
        for token, card in self.virtual_cards.items():
            if card.id in card_ids:
                devices.append(card.to_dict())
        
        return devices
    
    def deactivate_device(
        self,
        student_id: str,
        device_id: Optional[str] = None,
        card_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Deactivate a virtual card by device ID or card ID
        
        Returns:
            Tuple of (success, message)
        """
        card_ids = self.student_cards.get(student_id, [])
        
        for token, card in self.virtual_cards.items():
            if card.id in card_ids:
                if (device_id and card.device_id == device_id) or \
                   (card_id and card.id == card_id):
                    card.deactivate()
                    self.logger.info(
                        f"Deactivated NFC device for {student_id}: {card.device_name}"
                    )
                    return (True, "Device deactivated successfully")
        
        return (False, "Device not found")
    
    def deactivate_all_devices(self, student_id: str) -> Tuple[bool, str]:
        """Deactivate all devices for a student (e.g., when card is reported lost)"""
        card_ids = self.student_cards.get(student_id, [])
        count = 0
        
        for token, card in self.virtual_cards.items():
            if card.id in card_ids and card.is_active:
                card.deactivate()
                count += 1
        
        if count > 0:
            self.logger.warning(
                f"Deactivated all {count} NFC devices for student {student_id}"
            )
            return (True, f"Deactivated {count} devices")
        
        return (False, "No active devices found")
    
    def refresh_token(
        self,
        old_token: str,
        device_id: str
    ) -> Tuple[bool, Optional[str], str]:
        """
        Refresh an expired or expiring token
        
        Returns:
            Tuple of (success, new_token, message)
        """
        if old_token not in self.virtual_cards:
            return (False, None, "Invalid token")
        
        old_card = self.virtual_cards[old_token]
        
        # Verify device ownership
        if old_card.device_id != device_id:
            return (False, None, "Device mismatch")
        
        if not old_card.is_active:
            return (False, None, "Card is deactivated")
        
        # Generate new token
        new_token = old_card._generate_secure_token()
        old_card.token = new_token
        old_card.created_at = get_philippines_time()  # Reset token age
        
        # Update storage
        del self.virtual_cards[old_token]
        self.virtual_cards[new_token] = old_card
        
        self.logger.info(f"Refreshed NFC token for {old_card.student_id}")
        
        return (True, new_token, "Token refreshed successfully")
    
    def set_pin(
        self,
        token: str,
        pin: str
    ) -> Tuple[bool, str]:
        """Set PIN for a virtual card"""
        if token not in self.virtual_cards:
            return (False, "Invalid token")
        
        card = self.virtual_cards[token]
        
        if not card.is_active:
            return (False, "Card is deactivated")
        
        if card.set_pin(pin):
            return (True, "PIN set successfully")
        else:
            return (False, "PIN must be 4-6 digits")
    
    def enable_biometric(self, token: str) -> Tuple[bool, str]:
        """Enable biometric authentication for a virtual card"""
        if token not in self.virtual_cards:
            return (False, "Invalid token")
        
        card = self.virtual_cards[token]
        
        if not card.is_active:
            return (False, "Card is deactivated")
        
        card.enable_biometric()
        return (True, "Biometric authentication enabled")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get NFC payment statistics"""
        total_cards = len(self.virtual_cards)
        active_cards = sum(1 for c in self.virtual_cards.values() if c.is_active)
        total_transactions = sum(c.transaction_count for c in self.virtual_cards.values())
        
        return {
            'total_virtual_cards': total_cards,
            'active_virtual_cards': active_cards,
            'total_students_enrolled': len(self.student_cards),
            'total_nfc_transactions': total_transactions,
            'devices_bound': len(self.device_bindings)
        }


# Global NFC payment manager instance
_nfc_manager: Optional[NFCPaymentManager] = None


def get_nfc_manager() -> NFCPaymentManager:
    """Get global NFC payment manager instance"""
    global _nfc_manager
    if _nfc_manager is None:
        _nfc_manager = NFCPaymentManager()
    return _nfc_manager
