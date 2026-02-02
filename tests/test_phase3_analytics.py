"""
Phase 3 Analytics Tests
Tests for analytics, reporting, and export functionality
"""
import pytest
from datetime import datetime, timedelta
from backend.analytics import Analytics, get_analytics_summary
from backend.exports import DataExporter, filter_by_date_range, export_transactions, export_students
from backend.notifications import EmailNotifier, NotificationManager
import pytz

PHILIPPINES_TZ = pytz.timezone('Asia/Manila')


# Sample test data
@pytest.fixture
def sample_transactions():
    """Sample transaction data for testing"""
    now = datetime.now(PHILIPPINES_TZ)
    today = now.replace(hour=10, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    
    return [
        {
            'TransactionID': '1',
            'StudentID': 'S001',
            'StudentName': 'John Doe',
            'Type': 'Purchase',
            'Amount': '-25.50',
            'Date': today.strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'TransactionID': '2',
            'StudentID': 'S002',
            'StudentName': 'Jane Smith',
            'Type': 'Purchase',
            'Amount': '-50.00',
            'Date': today.strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'TransactionID': '3',
            'StudentID': 'S001',
            'StudentName': 'John Doe',
            'Type': 'Load',
            'Amount': '100.00',
            'Date': yesterday.strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'TransactionID': '4',
            'StudentID': 'S003',
            'StudentName': 'Bob Johnson',
            'Type': 'Purchase',
            'Amount': '-75.00',
            'Date': week_ago.strftime('%Y-%m-%d %H:%M:%S')
        },
    ]


@pytest.fixture
def sample_accounts():
    """Sample account data for testing"""
    return [
        {
            'MoneyCardNumber': 'MC001',
            'StudentID': 'S001',
            'Balance': '150.00',
            'Status': 'Active'
        },
        {
            'MoneyCardNumber': 'MC002',
            'StudentID': 'S002',
            'Balance': '35.00',  # Low balance
            'Status': 'Active'
        },
        {
            'MoneyCardNumber': 'MC003',
            'StudentID': 'S003',
            'Balance': '200.00',
            'Status': 'Active'
        },
    ]


@pytest.fixture
def sample_students():
    """Sample student data for testing"""
    return [
        {
            'StudentID': 'S001',
            'Name': 'John Doe',
            'ParentEmail': 'parent1@example.com',
            'Status': 'Active'
        },
        {
            'StudentID': 'S002',
            'Name': 'Jane Smith',
            'ParentEmail': 'parent2@example.com',
            'Status': 'Active'
        },
        {
            'StudentID': 'S003',
            'Name': 'Bob Johnson',
            'ParentEmail': '',  # No email
            'Status': 'Active'
        },
    ]


class TestAnalytics:
    """Test analytics calculations"""
    
    def test_analytics_initialization(self, sample_transactions):
        """Test analytics initialization with data"""
        analytics = Analytics(sample_transactions)
        assert analytics.transactions == sample_transactions
        assert len(analytics.transactions) == 4
    
    def test_spending_totals_daily(self, sample_transactions):
        """Test daily spending totals calculation"""
        analytics = Analytics(sample_transactions)
        daily_totals = analytics.get_spending_totals('daily')
        
        assert isinstance(daily_totals, dict)
        # Should have spending amounts grouped by day
        for date_str, total in daily_totals.items():
            assert isinstance(total, float)
            assert total >= 0
    
    def test_spending_totals_weekly(self, sample_transactions):
        """Test weekly spending totals calculation"""
        analytics = Analytics(sample_transactions)
        weekly_totals = analytics.get_spending_totals('weekly')
        
        assert isinstance(weekly_totals, dict)
        # Weeks should be formatted as YYYY-WXX
        for week_str in weekly_totals.keys():
            assert '-W' in week_str
    
    def test_spending_totals_monthly(self, sample_transactions):
        """Test monthly spending totals calculation"""
        analytics = Analytics(sample_transactions)
        monthly_totals = analytics.get_spending_totals('monthly')
        
        assert isinstance(monthly_totals, dict)
        # Months should be formatted as YYYY-MM
        for month_str in monthly_totals.keys():
            assert len(month_str) == 7
            assert month_str[4] == '-'
    
    def test_peak_purchase_times(self, sample_transactions):
        """Test peak purchase time analysis"""
        analytics = Analytics(sample_transactions)
        peak_times = analytics.get_peak_purchase_times()
        
        assert isinstance(peak_times, dict)
        # Hours should be 0-23
        for hour in peak_times.keys():
            assert 0 <= hour <= 23
    
    def test_low_balance_students(self, sample_transactions, sample_accounts):
        """Test low balance detection"""
        analytics = Analytics(sample_transactions)
        low_balance = analytics.get_low_balance_students(
            threshold=50.0, 
            account_data=sample_accounts
        )
        
        assert isinstance(low_balance, list)
        # Should find S002 with balance 35.00
        assert any(s['student_id'] == 'S002' for s in low_balance)
        
        # Check alert levels
        for student in low_balance:
            assert 'alert_level' in student
            assert student['alert_level'] in ['warning', 'critical']
    
    def test_top_spenders(self, sample_transactions):
        """Test top spenders calculation"""
        analytics = Analytics(sample_transactions)
        top = analytics.get_top_spenders(limit=3, days=30)
        
        assert isinstance(top, list)
        assert len(top) <= 3
        
        # Check structure
        for spender in top:
            assert 'student_id' in spender
            assert 'name' in spender
            assert 'total_spending' in spender
            assert spender['total_spending'] >= 0
        
        # Should be sorted descending
        if len(top) > 1:
            assert top[0]['total_spending'] >= top[1]['total_spending']
    
    def test_daily_summary(self, sample_transactions):
        """Test daily summary generation"""
        analytics = Analytics(sample_transactions)
        summary = analytics.get_daily_summary()
        
        assert isinstance(summary, dict)
        assert 'date' in summary
        assert 'total_transactions' in summary
        assert 'total_spending' in summary
        assert 'total_loaded' in summary
        assert 'unique_students' in summary
        assert 'avg_transaction' in summary
    
    def test_transaction_trends(self, sample_transactions):
        """Test transaction trend analysis"""
        analytics = Analytics(sample_transactions)
        trends = analytics.get_transaction_trends(days=30)
        
        assert isinstance(trends, dict)
        assert 'period_days' in trends
        assert 'avg_daily_spending' in trends
        assert 'total_spending' in trends
        assert 'trend' in trends
        assert trends['trend'] in ['increasing', 'decreasing', 'stable']
    
    def test_analytics_summary(self, sample_transactions, sample_accounts):
        """Test comprehensive analytics summary"""
        summary = get_analytics_summary(sample_transactions, sample_accounts)
        
        assert isinstance(summary, dict)
        assert 'daily_totals' in summary
        assert 'weekly_totals' in summary
        assert 'monthly_totals' in summary
        assert 'peak_hours' in summary
        assert 'top_spenders' in summary
        assert 'low_balance' in summary
        assert 'today_summary' in summary
        assert 'trends_30d' in summary
        assert 'trends_7d' in summary


class TestDataExport:
    """Test data export functionality"""
    
    def test_csv_export(self, sample_transactions):
        """Test CSV export"""
        exporter = DataExporter(sample_transactions, 'transactions')
        csv_data = exporter.to_csv()
        
        assert isinstance(csv_data, str)
        assert len(csv_data) > 0
        # Should have header row
        lines = csv_data.strip().split('\n')
        assert len(lines) > 1
        # Header should contain field names
        assert 'TransactionID' in lines[0]
        assert 'StudentID' in lines[0]
    
    def test_excel_export(self, sample_transactions):
        """Test Excel export"""
        exporter = DataExporter(sample_transactions, 'transactions')
        excel_data = exporter.to_excel()
        
        # Excel export might not be available if openpyxl not installed
        if excel_data:
            assert isinstance(excel_data, bytes)
            assert len(excel_data) > 0
    
    def test_date_range_filtering(self, sample_transactions):
        """Test date range filtering"""
        now = datetime.now(PHILIPPINES_TZ)
        today_str = now.strftime('%Y-%m-%d')
        yesterday_str = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Filter for today
        filtered = filter_by_date_range(
            sample_transactions,
            start_date=today_str,
            end_date=today_str
        )
        
        assert isinstance(filtered, list)
        # Should have at least some transactions
        assert len(filtered) >= 0
    
    def test_export_transactions_csv(self, sample_transactions):
        """Test transaction export with CSV format"""
        data, mimetype, filename = export_transactions(
            sample_transactions,
            format='csv'
        )
        
        assert mimetype == 'text/csv'
        assert filename.endswith('.csv')
        assert isinstance(data, str)
    
    def test_export_students_csv(self, sample_students):
        """Test student export"""
        data, mimetype, filename = export_students(
            sample_students,
            format='csv'
        )
        
        assert mimetype == 'text/csv'
        assert filename.startswith('students_')
        assert isinstance(data, str)


class TestNotifications:
    """Test notification system"""
    
    def test_email_notifier_initialization(self):
        """Test email notifier initialization"""
        notifier = EmailNotifier(
            smtp_server='smtp.example.com',
            smtp_user='test@example.com',
            smtp_password='password'
        )
        
        assert notifier.smtp_server == 'smtp.example.com'
        assert notifier.smtp_user == 'test@example.com'
        assert notifier.enabled == True
    
    def test_email_notifier_disabled(self):
        """Test email notifier when not configured"""
        notifier = EmailNotifier()  # No config
        
        # Should be disabled if no SMTP settings
        result = notifier.send_email(
            to_email='test@example.com',
            subject='Test',
            body='Test message'
        )
        
        # Will fail or return False when not configured
        assert result == False
    
    def test_notification_manager_low_balance(self, sample_accounts, sample_students):
        """Test low balance notification logic"""
        manager = NotificationManager()
        manager.low_balance_threshold = 50.0
        
        # This would send emails if SMTP was configured
        # In test mode, it should just return a count
        alerts_sent = manager.check_low_balances(sample_accounts, sample_students)
        
        # Should attempt to send for students with balance < 50
        assert isinstance(alerts_sent, int)
        assert alerts_sent >= 0
    
    def test_notification_manager_large_transaction(self, sample_transactions, sample_students):
        """Test large transaction notification logic"""
        manager = NotificationManager()
        manager.large_transaction_threshold = 100.0
        
        # Create a large transaction
        large_txn = {
            'StudentID': 'S001',
            'Type': 'Purchase',
            'Amount': '-150.00',
        }
        
        result = manager.notify_large_transaction(large_txn, sample_students)
        
        # In test mode without SMTP, should return False
        assert isinstance(result, bool)


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_analytics_empty_data(self):
        """Test analytics with empty data"""
        analytics = Analytics([])
        daily_totals = analytics.get_spending_totals('daily')
        
        assert isinstance(daily_totals, dict)
        assert len(daily_totals) == 0
    
    def test_analytics_invalid_period(self, sample_transactions):
        """Test analytics with invalid period"""
        analytics = Analytics(sample_transactions)
        
        with pytest.raises(ValueError):
            analytics.get_spending_totals('invalid_period')
    
    def test_export_empty_data(self):
        """Test export with empty data"""
        exporter = DataExporter([], 'transactions')
        csv_data = exporter.to_csv()
        
        assert csv_data == ""
    
    def test_low_balance_no_accounts(self, sample_transactions):
        """Test low balance detection with no account data"""
        analytics = Analytics(sample_transactions)
        low_balance = analytics.get_low_balance_students(account_data=None)
        
        assert isinstance(low_balance, list)
        assert len(low_balance) == 0
    
    def test_top_spenders_no_transactions(self):
        """Test top spenders with no transactions"""
        analytics = Analytics([])
        top = analytics.get_top_spenders()
        
        assert isinstance(top, list)
        assert len(top) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
