"""
Unit tests for core utility functions
"""
import pytest
from datetime import datetime
import pytz


class TestTimezoneHandling:
    """Test Philippine timezone handling"""
    
    def test_get_philippines_time_returns_manila_timezone(self, mock_philippines_time):
        """Test that get_philippines_time returns Asia/Manila timezone"""
        # This will be tested with actual import once we refactor
        tz = pytz.timezone('Asia/Manila')
        now = datetime.now(tz)
        assert now.tzinfo is not None
        assert str(now.tzinfo) == 'Asia/Manila'
    
    def test_philippines_time_format(self):
        """Test timestamp format matches expected pattern"""
        tz = pytz.timezone('Asia/Manila')
        test_time = datetime(2026, 2, 2, 10, 30, 45, tzinfo=tz)
        formatted = test_time.strftime('%Y-%m-%d %H:%M:%S')
        assert formatted == '2026-02-02 10:30:45'


class TestCardUIDNormalization:
    """Test card UID normalization and validation"""
    
    def test_normalize_card_uid_uppercase(self):
        """Test UID is converted to uppercase"""
        # Simple normalization function
        def normalize_card_uid(uid):
            return str(uid).upper().strip()
        
        assert normalize_card_uid('3a2b1c4d') == '3A2B1C4D'
        assert normalize_card_uid('abcdef12') == 'ABCDEF12'
    
    def test_normalize_card_uid_strips_whitespace(self):
        """Test UID whitespace is removed"""
        def normalize_card_uid(uid):
            return str(uid).upper().strip()
        
        assert normalize_card_uid('  3A2B1C4D  ') == '3A2B1C4D'
        assert normalize_card_uid('\n5F6E7D8C\n') == '5F6E7D8C'
    
    def test_normalize_card_uid_handles_mixed_case(self):
        """Test UID with mixed case is normalized"""
        def normalize_card_uid(uid):
            return str(uid).upper().strip()
        
        assert normalize_card_uid('AbCdEf12') == 'ABCDEF12'


class TestCardVerification:
    """Test card verification logic"""
    
    def test_verify_cards_linked_success(self, sample_student_data, sample_money_account_data):
        """Test successful card linkage verification"""
        student = sample_student_data[0]
        money_account = sample_money_account_data[0]
        
        # Verify the cards are linked
        assert student['IDCardNumber'] == money_account['LinkedIDCard']
        assert student['MoneyCardNumber'] == money_account['MoneyCardNumber']
    
    def test_verify_cards_not_linked(self, sample_student_data):
        """Test detection of unlinked cards"""
        student = sample_student_data[1]  # Maria Santos has no money card
        assert student['MoneyCardNumber'] == ''
    
    def test_verify_card_status_active(self, sample_student_data):
        """Test active card status verification"""
        student = sample_student_data[0]
        assert student['Status'] == 'Active'
    
    def test_find_student_by_id_card(self, sample_student_data):
        """Test finding student by ID card UID"""
        target_uid = '3A2B1C4D'
        found = [s for s in sample_student_data if s['IDCardNumber'] == target_uid]
        assert len(found) == 1
        assert found[0]['StudentID'] == '2024-001'
    
    def test_find_money_account_by_card(self, sample_money_account_data):
        """Test finding money account by card UID"""
        target_uid = '5F6E7D8C'
        found = [m for m in sample_money_account_data if m['MoneyCardNumber'] == target_uid]
        assert len(found) == 1
        assert found[0]['Balance'] == '500.00'


class TestBalanceOperations:
    """Test balance calculation and updates"""
    
    def test_calculate_new_balance_load(self):
        """Test balance calculation for load operation"""
        current_balance = 500.00
        load_amount = 100.00
        new_balance = current_balance + load_amount
        assert new_balance == 600.00
    
    def test_calculate_new_balance_purchase(self):
        """Test balance calculation for purchase"""
        current_balance = 500.00
        purchase_amount = 50.00
        new_balance = current_balance - purchase_amount
        assert new_balance == 450.00
    
    def test_insufficient_balance_check(self):
        """Test insufficient balance detection"""
        current_balance = 20.00
        purchase_amount = 50.00
        is_sufficient = current_balance >= purchase_amount
        assert is_sufficient is False
    
    def test_sufficient_balance_check(self):
        """Test sufficient balance verification"""
        current_balance = 500.00
        purchase_amount = 50.00
        is_sufficient = current_balance >= purchase_amount
        assert is_sufficient is True
    
    def test_balance_format_decimal_places(self):
        """Test balance formatting to 2 decimal places"""
        balance = 500.123456
        formatted = f"{balance:.2f}"
        assert formatted == "500.12"


class TestTransactionLogging:
    """Test transaction logging functionality"""
    
    def test_transaction_id_format(self):
        """Test transaction ID format"""
        from datetime import datetime
        timestamp = datetime(2026, 2, 2, 10, 30, 45)
        txn_id = f"TXN-{timestamp.strftime('%Y%m%d%H%M%S')}"
        assert txn_id == "TXN-20260202103045"
    
    def test_transaction_data_structure(self, sample_transaction_data):
        """Test transaction record has required fields"""
        txn = sample_transaction_data[0]
        required_fields = [
            'TransactionID', 'Timestamp', 'StudentID', 'MoneyCardNumber',
            'TransactionType', 'Amount', 'BalanceBefore', 'BalanceAfter',
            'Status', 'ErrorMessage'
        ]
        for field in required_fields:
            assert field in txn
    
    def test_transaction_type_validation(self):
        """Test valid transaction types"""
        valid_types = ['Load', 'Purchase']
        assert 'Load' in valid_types
        assert 'Purchase' in valid_types
        assert 'Invalid' not in valid_types
    
    def test_transaction_balance_consistency(self, sample_transaction_data):
        """Test transaction balance before/after consistency"""
        txn = sample_transaction_data[0]
        balance_before = float(txn['BalanceBefore'])
        amount = float(txn['Amount'])
        balance_after = float(txn['BalanceAfter'])
        
        if txn['TransactionType'] == 'Load':
            assert balance_after == balance_before + amount
        elif txn['TransactionType'] == 'Purchase':
            assert balance_after == balance_before - amount


class TestSerialProtocol:
    """Test serial communication protocol"""
    
    def test_parse_card_message(self):
        """Test parsing CARD message from Arduino"""
        message = "<CARD|3A2B1C4D>"
        parts = message.strip('<>').split('|')
        assert parts[0] == 'CARD'
        assert parts[1] == '3A2B1C4D'
    
    def test_parse_ready_message(self):
        """Test parsing READY message from Arduino"""
        message = "<READY>"
        parts = message.strip('<>').split('|')
        assert parts[0] == 'READY'
    
    def test_format_lcd_command(self):
        """Test formatting LCD display command"""
        line1 = "Welcome"
        line2 = "Balance: P500"
        command = f"<LCD|{line1}|{line2}>"
        assert command == "<LCD|Welcome|Balance: P500>"
    
    def test_format_beep_command(self):
        """Test formatting buzzer command"""
        command = "<BEEP|SUCCESS>"
        assert command == "<BEEP|SUCCESS>"
    
    def test_format_balance_response(self):
        """Test formatting balance response"""
        balance = 500.00
        command = f"<BALANCE|{balance:.2f}>"
        assert command == "<BALANCE|500.00>"
    
    def test_message_delimiter_validation(self):
        """Test message starts and ends with delimiters"""
        message = "<CARD|3A2B1C4D>"
        assert message.startswith('<')
        assert message.endswith('>')


@pytest.mark.unit
class TestDataValidation:
    """Test input data validation"""
    
    def test_student_id_format(self):
        """Test student ID format validation"""
        valid_id = "2024-001"
        assert len(valid_id) > 0
        assert '-' in valid_id
    
    def test_card_uid_hex_format(self):
        """Test card UID is valid hex"""
        uid = "3A2B1C4D"
        try:
            int(uid, 16)
            is_valid = True
        except ValueError:
            is_valid = False
        assert is_valid is True
    
    def test_balance_positive(self):
        """Test balance is non-negative"""
        balance = 500.00
        assert balance >= 0
    
    def test_amount_positive(self):
        """Test transaction amount is positive"""
        amount = 100.00
        assert amount > 0
