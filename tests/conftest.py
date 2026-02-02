"""
Pytest fixtures and test configuration
"""
import pytest
import os
from unittest.mock import Mock, MagicMock
from dotenv import load_dotenv

# Load test environment variables
load_dotenv()

@pytest.fixture
def mock_google_sheets():
    """Mock Google Sheets client for testing without API calls"""
    mock_client = MagicMock()
    mock_spreadsheet = MagicMock()
    mock_client.open_by_key.return_value = mock_spreadsheet
    
    # Mock worksheets
    users_sheet = MagicMock()
    money_accounts_sheet = MagicMock()
    transactions_sheet = MagicMock()
    lost_cards_sheet = MagicMock()
    
    def get_worksheet(name):
        sheets_map = {
            'Users': users_sheet,
            'Money Accounts': money_accounts_sheet,
            'Transactions Log': transactions_sheet,
            'Lost Card Reports': lost_cards_sheet
        }
        return sheets_map.get(name)
    
    mock_spreadsheet.worksheet.side_effect = get_worksheet
    
    return {
        'client': mock_client,
        'spreadsheet': mock_spreadsheet,
        'users': users_sheet,
        'money_accounts': money_accounts_sheet,
        'transactions': transactions_sheet,
        'lost_cards': lost_cards_sheet
    }

@pytest.fixture
def sample_student_data():
    """Sample student data for testing"""
    return [
        {
            'StudentID': '2024-001',
            'Name': 'Louis Julian Adriatico',
            'IDCardNumber': '3A2B1C4D',
            'MoneyCardNumber': '5F6E7D8C',
            'Status': 'Active',
            'ParentEmail': 'parent@email.com',
            'DateRegistered': '2026-02-02 10:30:45'
        },
        {
            'StudentID': '2024-002',
            'Name': 'Maria Santos',
            'IDCardNumber': '1F2E3D4C',
            'MoneyCardNumber': '',
            'Status': 'Active',
            'ParentEmail': 'maria@email.com',
            'DateRegistered': '2026-02-02 11:00:00'
        }
    ]

@pytest.fixture
def sample_money_account_data():
    """Sample money account data for testing"""
    return [
        {
            'MoneyCardNumber': '5F6E7D8C',
            'LinkedIDCard': '3A2B1C4D',
            'Balance': '500.00',
            'Status': 'Active',
            'LastUpdated': '2026-02-02 10:30:45',
            'TotalLoaded': '1000.00'
        }
    ]

@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing"""
    return [
        {
            'TransactionID': 'TXN-20260202103045',
            'Timestamp': '2026-02-02 10:30:45',
            'StudentID': '2024-001',
            'MoneyCardNumber': '5F6E7D8C',
            'TransactionType': 'Load',
            'Amount': '100.00',
            'BalanceBefore': '400.00',
            'BalanceAfter': '500.00',
            'Status': 'Completed',
            'ErrorMessage': ''
        }
    ]

@pytest.fixture
def mock_serial_port():
    """Mock serial port for Arduino communication testing"""
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mock_serial.in_waiting = 0
    mock_serial.read_until.return_value = b'<CARD|3A2B1C4D>\n'
    return mock_serial

@pytest.fixture
def test_env_vars(monkeypatch):
    """Set up test environment variables"""
    monkeypatch.setenv('GOOGLE_SHEETS_ID', 'test_sheet_id_12345')
    monkeypatch.setenv('FLASK_SECRET_KEY', 'test_secret_key')
    monkeypatch.setenv('ADMIN_USERNAME', 'admin')
    monkeypatch.setenv('ADMIN_PASSWORD', 'testpass')
    monkeypatch.setenv('SERIAL_PORT', 'COM3')
    monkeypatch.setenv('ADMIN_PORT', 'COM4')
    monkeypatch.setenv('BAUD_RATE', '9600')

@pytest.fixture
def mock_philippines_time():
    """Mock Philippine timezone for consistent testing"""
    from datetime import datetime
    import pytz
    tz = pytz.timezone('Asia/Manila')
    return datetime(2026, 2, 2, 10, 30, 45, tzinfo=tz)
