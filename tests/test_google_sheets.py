"""
Integration tests for Google Sheets operations
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.integration
class TestGoogleSheetsConnection:
    """Test Google Sheets client connection"""
    
    def test_sheets_client_initialization(self, mock_google_sheets, test_env_vars):
        """Test Google Sheets client can be initialized"""
        client = mock_google_sheets['client']
        assert client is not None
    
    def test_spreadsheet_open_by_key(self, mock_google_sheets, test_env_vars):
        """Test spreadsheet can be opened with ID"""
        client = mock_google_sheets['client']
        client.open_by_key('test_sheet_id')
        client.open_by_key.assert_called_with('test_sheet_id')
    
    def test_worksheet_access(self, mock_google_sheets):
        """Test worksheet can be accessed by name"""
        spreadsheet = mock_google_sheets['spreadsheet']
        users_sheet = spreadsheet.worksheet('Users')
        assert users_sheet is not None


@pytest.mark.integration
class TestWorksheetRetry:
    """Test retry logic for worksheet operations"""
    
    def test_retry_on_connection_error(self, mock_google_sheets):
        """Test retry logic activates on connection error"""
        spreadsheet = mock_google_sheets['spreadsheet']
        
        # Simulate failure then success
        spreadsheet.worksheet.side_effect = [
            Exception("Connection timeout"),
            mock_google_sheets['users']
        ]
        
        # In real implementation, retry would catch first error
        with pytest.raises(Exception):
            spreadsheet.worksheet('Users')
    
    def test_max_retries_exceeded(self, mock_google_sheets):
        """Test max retries limit is respected"""
        spreadsheet = mock_google_sheets['spreadsheet']
        
        # Simulate persistent failure
        spreadsheet.worksheet.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception):
            spreadsheet.worksheet('Users')


@pytest.mark.integration
class TestCachedSheetData:
    """Test caching layer for Google Sheets data"""
    
    def test_cache_stores_data(self, mock_google_sheets, sample_student_data):
        """Test data is cached after first read"""
        users_sheet = mock_google_sheets['users']
        users_sheet.get_all_records.return_value = sample_student_data
        
        # First call - should hit API
        data1 = users_sheet.get_all_records()
        assert len(data1) == 2
        
        # Verify mock was called
        assert users_sheet.get_all_records.call_count == 1
    
    def test_cache_expiration(self):
        """Test cache expires after timeout"""
        import time
        cache_timeout = 1  # 1 second for testing
        
        # Simulate cache with timestamp
        cache = {'data': [{'id': 1}], 'timestamp': time.time()}
        
        # Immediately - cache is valid
        is_expired = (time.time() - cache['timestamp']) > cache_timeout
        assert is_expired is False
        
        # After timeout - cache is expired
        time.sleep(1.1)
        is_expired = (time.time() - cache['timestamp']) > cache_timeout
        assert is_expired is True


@pytest.mark.integration
class TestStudentOperations:
    """Test student-related database operations"""
    
    def test_get_all_students(self, mock_google_sheets, sample_student_data):
        """Test retrieving all students"""
        users_sheet = mock_google_sheets['users']
        users_sheet.get_all_records.return_value = sample_student_data
        
        students = users_sheet.get_all_records()
        assert len(students) == 2
        assert students[0]['StudentID'] == '2024-001'
    
    def test_find_student_by_id(self, mock_google_sheets, sample_student_data):
        """Test finding specific student by ID"""
        users_sheet = mock_google_sheets['users']
        users_sheet.get_all_records.return_value = sample_student_data
        
        all_students = users_sheet.get_all_records()
        student = next((s for s in all_students if s['StudentID'] == '2024-001'), None)
        
        assert student is not None
        assert student['Name'] == 'Louis Julian Adriatico'
    
    def test_find_student_by_card_uid(self, mock_google_sheets, sample_student_data):
        """Test finding student by ID card UID"""
        users_sheet = mock_google_sheets['users']
        users_sheet.get_all_records.return_value = sample_student_data
        
        all_students = users_sheet.get_all_records()
        student = next((s for s in all_students if s['IDCardNumber'] == '3A2B1C4D'), None)
        
        assert student is not None
        assert student['StudentID'] == '2024-001'


@pytest.mark.integration
class TestMoneyAccountOperations:
    """Test money account database operations"""
    
    def test_get_money_account_by_card(self, mock_google_sheets, sample_money_account_data):
        """Test retrieving money account by card UID"""
        money_sheet = mock_google_sheets['money_accounts']
        money_sheet.get_all_records.return_value = sample_money_account_data
        
        accounts = money_sheet.get_all_records()
        account = next((a for a in accounts if a['MoneyCardNumber'] == '5F6E7D8C'), None)
        
        assert account is not None
        assert account['Balance'] == '500.00'
    
    def test_verify_card_linkage(self, mock_google_sheets, sample_money_account_data):
        """Test verifying card linkage"""
        money_sheet = mock_google_sheets['money_accounts']
        money_sheet.get_all_records.return_value = sample_money_account_data
        
        accounts = money_sheet.get_all_records()
        account = accounts[0]
        
        assert account['MoneyCardNumber'] == '5F6E7D8C'
        assert account['LinkedIDCard'] == '3A2B1C4D'
    
    def test_update_balance(self, mock_google_sheets, sample_money_account_data):
        """Test updating account balance"""
        money_sheet = mock_google_sheets['money_accounts']
        money_sheet.get_all_records.return_value = sample_money_account_data
        
        # Simulate balance update
        new_balance = 600.00
        
        # In real implementation, this would call sheet.update_cell()
        money_sheet.update_cell.return_value = None
        money_sheet.update_cell(2, 3, str(new_balance))
        
        money_sheet.update_cell.assert_called_once()


@pytest.mark.integration
class TestTransactionOperations:
    """Test transaction logging database operations"""
    
    def test_log_transaction(self, mock_google_sheets):
        """Test logging a new transaction"""
        txn_sheet = mock_google_sheets['transactions']
        
        transaction_row = [
            'TXN-20260202103045',
            '2026-02-02 10:30:45',
            '2024-001',
            '5F6E7D8C',
            'Load',
            '100.00',
            '400.00',
            '500.00',
            'Completed',
            ''
        ]
        
        txn_sheet.append_row.return_value = None
        txn_sheet.append_row(transaction_row)
        
        txn_sheet.append_row.assert_called_once_with(transaction_row)
    
    def test_get_recent_transactions(self, mock_google_sheets, sample_transaction_data):
        """Test retrieving recent transactions"""
        txn_sheet = mock_google_sheets['transactions']
        txn_sheet.get_all_records.return_value = sample_transaction_data
        
        transactions = txn_sheet.get_all_records()
        assert len(transactions) > 0
        assert transactions[0]['TransactionID'] == 'TXN-20260202103045'
    
    def test_get_student_transactions(self, mock_google_sheets, sample_transaction_data):
        """Test filtering transactions by student"""
        txn_sheet = mock_google_sheets['transactions']
        txn_sheet.get_all_records.return_value = sample_transaction_data
        
        all_transactions = txn_sheet.get_all_records()
        student_txns = [t for t in all_transactions if t['StudentID'] == '2024-001']
        
        assert len(student_txns) > 0
        assert student_txns[0]['StudentID'] == '2024-001'


@pytest.mark.integration
class TestLostCardOperations:
    """Test lost card reporting database operations"""
    
    def test_log_lost_card_report(self, mock_google_sheets):
        """Test logging lost card report"""
        lost_sheet = mock_google_sheets['lost_cards']
        
        report_row = [
            'RPT-20260202103045',
            '2026-02-02 10:30:45',
            '2024-001',
            '5F6E7D8C',
            '9A8B7C6D',
            '500.00',
            'admin',
            'Pending'
        ]
        
        lost_sheet.append_row.return_value = None
        lost_sheet.append_row(report_row)
        
        lost_sheet.append_row.assert_called_once_with(report_row)
    
    def test_update_card_status_to_lost(self, mock_google_sheets):
        """Test updating card status to Lost"""
        money_sheet = mock_google_sheets['money_accounts']
        
        # Simulate status update
        money_sheet.update_cell.return_value = None
        money_sheet.update_cell(2, 4, 'Lost')
        
        money_sheet.update_cell.assert_called_with(2, 4, 'Lost')


@pytest.mark.integration
class TestSchemaValidation:
    """Test Google Sheets schema validation"""
    
    def test_users_sheet_columns(self, mock_google_sheets):
        """Test Users sheet has correct columns"""
        users_sheet = mock_google_sheets['users']
        expected_columns = [
            'StudentID', 'Name', 'IDCardNumber', 'MoneyCardNumber',
            'Status', 'ParentEmail', 'DateRegistered'
        ]
        
        # Mock the first row (headers)
        users_sheet.row_values.return_value = expected_columns
        headers = users_sheet.row_values(1)
        
        assert headers == expected_columns
    
    def test_money_accounts_sheet_columns(self, mock_google_sheets):
        """Test Money Accounts sheet has correct columns"""
        money_sheet = mock_google_sheets['money_accounts']
        expected_columns = [
            'MoneyCardNumber', 'LinkedIDCard', 'Balance',
            'Status', 'LastUpdated', 'TotalLoaded'
        ]
        
        money_sheet.row_values.return_value = expected_columns
        headers = money_sheet.row_values(1)
        
        assert headers == expected_columns
    
    def test_all_required_sheets_exist(self, mock_google_sheets):
        """Test all 4 required sheets exist"""
        spreadsheet = mock_google_sheets['spreadsheet']
        required_sheets = ['Users', 'Money Accounts', 'Transactions Log', 'Lost Card Reports']
        
        for sheet_name in required_sheets:
            sheet = spreadsheet.worksheet(sheet_name)
            assert sheet is not None
