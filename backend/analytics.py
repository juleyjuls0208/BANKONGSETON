"""
Analytics Module - Phase 3
Bangko ng Seton

Provides analytics and reporting functions for transaction data
"""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import pytz

PHILIPPINES_TZ = pytz.timezone('Asia/Manila')


def get_philippines_time():
    """Get current time in Philippine timezone"""
    return datetime.now(PHILIPPINES_TZ)


class Analytics:
    """Analytics engine for transaction data"""
    
    def __init__(self, transactions: List[Dict]):
        """
        Initialize analytics with transaction data
        
        Args:
            transactions: List of transaction dictionaries from Google Sheets
        """
        self.transactions = transactions
        self._parse_dates()
    
    def _parse_dates(self):
        """Parse date strings to datetime objects"""
        for txn in self.transactions:
            if 'Date' in txn and isinstance(txn['Date'], str):
                try:
                    # Try ISO format first
                    txn['_parsed_date'] = datetime.fromisoformat(txn['Date'].replace('Z', '+00:00'))
                    # Ensure timezone aware
                    if txn['_parsed_date'].tzinfo is None:
                        txn['_parsed_date'] = PHILIPPINES_TZ.localize(txn['_parsed_date'])
                except:
                    try:
                        # Try common format: "2026-02-02 14:30:00"
                        txn['_parsed_date'] = datetime.strptime(txn['Date'], '%Y-%m-%d %H:%M:%S')
                        txn['_parsed_date'] = PHILIPPINES_TZ.localize(txn['_parsed_date'])
                    except:
                        # Fallback to current time
                        txn['_parsed_date'] = get_philippines_time()
    
    def get_spending_totals(self, period: str = 'daily') -> Dict[str, float]:
        """
        Calculate spending totals by period
        
        Args:
            period: 'daily', 'weekly', or 'monthly'
        
        Returns:
            Dictionary with period labels as keys and total spending as values
        """
        now = get_philippines_time()
        totals = defaultdict(float)
        
        for txn in self.transactions:
            if txn.get('Type') not in ['Purchase', 'Withdrawal']:
                continue  # Skip non-spending transactions
            
            date = txn.get('_parsed_date', now)
            amount = abs(float(txn.get('Amount', 0)))
            
            if period == 'daily':
                key = date.strftime('%Y-%m-%d')
            elif period == 'weekly':
                # Week starting Monday
                week_start = date - timedelta(days=date.weekday())
                key = week_start.strftime('%Y-W%U')
            elif period == 'monthly':
                key = date.strftime('%Y-%m')
            else:
                raise ValueError(f"Invalid period: {period}")
            
            totals[key] += amount
        
        return dict(sorted(totals.items()))
    
    def get_peak_purchase_times(self) -> Dict[str, int]:
        """
        Analyze peak purchase times by hour of day
        
        Returns:
            Dictionary with hour (0-23) as key and transaction count as value
        """
        hour_counts = defaultdict(int)
        
        for txn in self.transactions:
            if txn.get('Type') not in ['Purchase', 'Withdrawal']:
                continue
            
            date = txn.get('_parsed_date', get_philippines_time())
            hour_counts[date.hour] += 1
        
        return dict(sorted(hour_counts.items()))
    
    def get_low_balance_students(self, threshold: float = 50.0, 
                                  account_data: List[Dict] = None) -> List[Dict]:
        """
        Identify students with low balances
        
        Args:
            threshold: Balance threshold (default: ₱50)
            account_data: List of money account dictionaries
        
        Returns:
            List of students with balance below threshold
        """
        if not account_data:
            return []
        
        low_balance = []
        
        for account in account_data:
            try:
                balance = float(account.get('Balance', 0))
                if balance < threshold and account.get('Status') == 'Active':
                    low_balance.append({
                        'student_id': account.get('StudentID'),
                        'money_card': account.get('MoneyCardNumber'),
                        'balance': balance,
                        'alert_level': 'critical' if balance < 20 else 'warning'
                    })
            except (ValueError, TypeError):
                continue
        
        return sorted(low_balance, key=lambda x: x['balance'])
    
    def get_top_spenders(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """
        Get top spenders within date range
        
        Args:
            limit: Number of top spenders to return
            days: Number of days to analyze
        
        Returns:
            List of top spenders with total spending
        """
        now = get_philippines_time()
        cutoff_date = now - timedelta(days=days)
        
        student_spending = defaultdict(float)
        student_names = {}
        
        for txn in self.transactions:
            if txn.get('Type') not in ['Purchase', 'Withdrawal']:
                continue
            
            date = txn.get('_parsed_date', now)
            if date < cutoff_date:
                continue
            
            student_id = txn.get('StudentID', 'Unknown')
            amount = abs(float(txn.get('Amount', 0)))
            
            student_spending[student_id] += amount
            student_names[student_id] = txn.get('StudentName', student_id)
        
        # Sort by spending descending
        top_spenders = [
            {
                'student_id': sid,
                'name': student_names[sid],
                'total_spending': amount,
                'period_days': days
            }
            for sid, amount in sorted(student_spending.items(), 
                                     key=lambda x: x[1], 
                                     reverse=True)[:limit]
        ]
        
        return top_spenders
    
    def get_daily_summary(self, date: Optional[datetime] = None) -> Dict:
        """
        Get summary statistics for a specific day
        
        Args:
            date: Date to analyze (defaults to today)
        
        Returns:
            Dictionary with daily statistics
        """
        if date is None:
            date = get_philippines_time()
        
        date_str = date.strftime('%Y-%m-%d')
        
        summary = {
            'date': date_str,
            'total_transactions': 0,
            'total_spending': 0.0,
            'total_loaded': 0.0,
            'unique_students': set(),
            'peak_hour': None,
            'avg_transaction': 0.0
        }
        
        hour_counts = defaultdict(int)
        
        for txn in self.transactions:
            txn_date = txn.get('_parsed_date', get_philippines_time())
            if txn_date.strftime('%Y-%m-%d') != date_str:
                continue
            
            summary['total_transactions'] += 1
            summary['unique_students'].add(txn.get('StudentID'))
            hour_counts[txn_date.hour] += 1
            
            amount = float(txn.get('Amount', 0))
            txn_type = txn.get('Type', '')
            
            if txn_type in ['Purchase', 'Withdrawal']:
                summary['total_spending'] += abs(amount)
            elif txn_type == 'Load':
                summary['total_loaded'] += amount
        
        # Calculate derived stats
        summary['unique_students'] = len(summary['unique_students'])
        
        if summary['total_transactions'] > 0:
            summary['avg_transaction'] = summary['total_spending'] / summary['total_transactions']
        
        if hour_counts:
            summary['peak_hour'] = max(hour_counts.items(), key=lambda x: x[1])[0]
        
        return summary
    
    def get_transaction_trends(self, days: int = 30) -> Dict:
        """
        Analyze transaction trends over time
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with trend statistics
        """
        now = get_philippines_time()
        cutoff_date = now - timedelta(days=days)
        
        daily_totals = defaultdict(float)
        daily_counts = defaultdict(int)
        
        for txn in self.transactions:
            date = txn.get('_parsed_date', now)
            if date < cutoff_date:
                continue
            
            if txn.get('Type') not in ['Purchase', 'Withdrawal']:
                continue
            
            date_str = date.strftime('%Y-%m-%d')
            amount = abs(float(txn.get('Amount', 0)))
            
            daily_totals[date_str] += amount
            daily_counts[date_str] += 1
        
        # Calculate trends
        if not daily_totals:
            return {
                'period_days': days,
                'avg_daily_spending': 0.0,
                'avg_daily_transactions': 0.0,
                'total_spending': 0.0,
                'total_transactions': 0,
                'trend': 'neutral'
            }
        
        total_spending = sum(daily_totals.values())
        total_transactions = sum(daily_counts.values())
        active_days = len(daily_totals)
        
        # Simple trend: compare first half vs second half
        sorted_dates = sorted(daily_totals.keys())
        midpoint = len(sorted_dates) // 2
        
        first_half_avg = sum(daily_totals[d] for d in sorted_dates[:midpoint]) / max(midpoint, 1)
        second_half_avg = sum(daily_totals[d] for d in sorted_dates[midpoint:]) / max(len(sorted_dates) - midpoint, 1)
        
        if second_half_avg > first_half_avg * 1.1:
            trend = 'increasing'
        elif second_half_avg < first_half_avg * 0.9:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'period_days': days,
            'avg_daily_spending': total_spending / active_days,
            'avg_daily_transactions': total_transactions / active_days,
            'total_spending': total_spending,
            'total_transactions': total_transactions,
            'active_days': active_days,
            'trend': trend
        }


def get_analytics_summary(transactions: List[Dict], 
                         accounts: List[Dict] = None) -> Dict:
    """
    Get comprehensive analytics summary
    
    Args:
        transactions: List of transaction dictionaries
        accounts: List of money account dictionaries
    
    Returns:
        Dictionary with all analytics data
    """
    analytics = Analytics(transactions)
    
    return {
        'daily_totals': analytics.get_spending_totals('daily'),
        'weekly_totals': analytics.get_spending_totals('weekly'),
        'monthly_totals': analytics.get_spending_totals('monthly'),
        'peak_hours': analytics.get_peak_purchase_times(),
        'top_spenders': analytics.get_top_spenders(limit=10),
        'low_balance': analytics.get_low_balance_students(threshold=50, account_data=accounts),
        'today_summary': analytics.get_daily_summary(),
        'trends_30d': analytics.get_transaction_trends(days=30),
        'trends_7d': analytics.get_transaction_trends(days=7)
    }
