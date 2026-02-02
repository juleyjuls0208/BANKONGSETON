"""
Notifications Module - Phase 3
Bangko ng Seton

Handles email and push notifications for alerts and updates
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Optional
import os
import pytz

PHILIPPINES_TZ = pytz.timezone('Asia/Manila')


def get_philippines_time():
    """Get current time in Philippine timezone"""
    return datetime.now(PHILIPPINES_TZ)


class EmailNotifier:
    """Handles email notifications"""
    
    def __init__(self, smtp_server: str = None, smtp_port: int = 587,
                 smtp_user: str = None, smtp_password: str = None,
                 from_email: str = None):
        """
        Initialize email notifier
        
        Args:
            smtp_server: SMTP server address (e.g., smtp.gmail.com)
            smtp_port: SMTP port (default: 587 for TLS)
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_email: Sender email address
        """
        self.smtp_server = smtp_server or os.getenv('SMTP_SERVER', '')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = smtp_user or os.getenv('SMTP_USER', '')
        self.smtp_password = smtp_password or os.getenv('SMTP_PASSWORD', '')
        self.from_email = from_email or os.getenv('FROM_EMAIL', self.smtp_user)
        
        self.enabled = all([self.smtp_server, self.smtp_user, self.smtp_password])
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   html_body: Optional[str] = None) -> bool:
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            print(f"[Email] Would send to {to_email}: {subject}")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Attach plain text
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach HTML if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
        
        except Exception as e:
            print(f"[Email Error] Failed to send to {to_email}: {e}")
            return False
    
    def send_low_balance_alert(self, student_name: str, student_id: str,
                               balance: float, to_email: str) -> bool:
        """
        Send low balance alert email
        
        Args:
            student_name: Student's full name
            student_id: Student ID
            balance: Current balance
            to_email: Parent/guardian email
        
        Returns:
            True if sent successfully
        """
        subject = f"Low Balance Alert - {student_name}"
        
        body = f"""
Dear Parent/Guardian,

This is to inform you that the account balance for {student_name} (ID: {student_id}) 
is currently low.

Current Balance: ₱{balance:.2f}

We recommend loading more funds to ensure your child can continue to make purchases 
at school.

You can load funds by:
1. Visiting the Finance Office during school hours
2. Using the online dashboard (if available)

Thank you,
Bangko ng Seton Finance Office
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f8f9fa; }}
        .balance {{ font-size: 24px; color: #dc3545; font-weight: bold; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>⚠️ Low Balance Alert</h2>
        </div>
        <div class="content">
            <p>Dear Parent/Guardian,</p>
            <p>The account balance for <strong>{student_name}</strong> (ID: {student_id}) is currently low.</p>
            <p class="balance">Current Balance: ₱{balance:.2f}</p>
            <p>We recommend loading more funds to ensure your child can continue to make purchases at school.</p>
            <h3>How to Load Funds:</h3>
            <ul>
                <li>Visit the Finance Office during school hours</li>
                <li>Use the online dashboard (if available)</li>
            </ul>
        </div>
        <div class="footer">
            <p>Bangko ng Seton Finance Office</p>
            <p>This is an automated notification. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return self.send_email(to_email, subject, body, html_body)
    
    def send_load_confirmation(self, student_name: str, student_id: str,
                               amount: float, new_balance: float,
                               to_email: str) -> bool:
        """
        Send load/top-up confirmation email to parent
        
        Args:
            student_name: Student's full name
            student_id: Student ID
            amount: Amount loaded
            new_balance: New balance after load
            to_email: Parent/guardian email
        
        Returns:
            True if sent successfully
        """
        now = get_philippines_time()
        
        subject = f"Balance Loaded - {student_name}"
        
        body = f"""
Dear Parent/Guardian,

This is to confirm that funds have been loaded to {student_name}'s account (ID: {student_id}).

Load Details:
- Amount Loaded: ₱{amount:.2f}
- New Balance: ₱{new_balance:.2f}
- Date/Time: {now.strftime('%Y-%m-%d %H:%M:%S')}

Thank you for using Bangko ng Seton!

Best regards,
Bangko ng Seton Finance Office
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #22C55E; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f8f9fa; }}
        .success {{ background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0; }}
        .details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .amount {{ font-size: 24px; color: #22C55E; font-weight: bold; }}
        .balance {{ font-size: 20px; color: #4F46E5; font-weight: bold; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>✅ Balance Loaded Successfully</h2>
        </div>
        <div class="content">
            <p>Dear Parent/Guardian,</p>
            <p>Funds have been loaded to <strong>{student_name}</strong>'s account (ID: {student_id}).</p>
            
            <div class="details">
                <h3>Load Details:</h3>
                <p class="amount">Amount Loaded: ₱{amount:.2f}</p>
                <p class="balance">New Balance: ₱{new_balance:.2f}</p>
                <p><strong>Date/Time:</strong> {now.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="success">
                <strong>✓</strong> Transaction completed successfully!
            </div>
            
            <p>Thank you for using Bangko ng Seton!</p>
        </div>
        <div class="footer">
            <p>Bangko ng Seton Finance Office</p>
            <p>This is an automated notification. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return self.send_email(to_email, subject, body, html_body)
    
    def send_card_lost_alert(self, student_name: str, student_id: str,
                            old_card: str, balance: float,
                            to_email: str) -> bool:
        """
        Send card lost alert email to parent
        
        Args:
            student_name: Student's full name
            student_id: Student ID
            old_card: Lost card number
            balance: Balance preserved
            to_email: Parent/guardian email
        
        Returns:
            True if sent successfully
        """
        now = get_philippines_time()
        
        subject = f"Card Reported Lost - {student_name}"
        
        body = f"""
Dear Parent/Guardian,

This is to inform you that the money card for {student_name} (ID: {student_id}) 
has been reported as lost.

Card Details:
- Lost Card Number: {old_card}
- Balance Preserved: ₱{balance:.2f}
- Reported: {now.strftime('%Y-%m-%d %H:%M:%S')}

The card has been deactivated for security. The balance of ₱{balance:.2f} has been 
preserved and will be transferred to a replacement card.

Next Steps:
1. Visit the Finance Office to get a replacement card
2. The preserved balance will be transferred to the new card
3. Your child can continue using Bangko ng Seton with the new card

Thank you,
Bangko ng Seton Finance Office
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #DC2626; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f8f9fa; }}
        .warning {{ background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 15px; margin: 15px 0; }}
        .details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .balance {{ font-size: 20px; color: #059669; font-weight: bold; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>⚠️ Card Reported Lost</h2>
        </div>
        <div class="content">
            <p>Dear Parent/Guardian,</p>
            <p>The money card for <strong>{student_name}</strong> (ID: {student_id}) has been reported as lost.</p>
            
            <div class="details">
                <h3>Card Details:</h3>
                <p><strong>Lost Card Number:</strong> {old_card}</p>
                <p class="balance">Balance Preserved: ₱{balance:.2f}</p>
                <p><strong>Reported:</strong> {now.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="warning">
                <strong>🔒 Security:</strong> The card has been deactivated and cannot be used. 
                The balance is safe and preserved.
            </div>
            
            <h3>Next Steps:</h3>
            <ol>
                <li>Visit the Finance Office to get a replacement card</li>
                <li>The preserved balance will be transferred to the new card</li>
                <li>Your child can continue using Bangko ng Seton with the new card</li>
            </ol>
        </div>
        <div class="footer">
            <p>Bangko ng Seton Finance Office</p>
            <p>This is an automated notification. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return self.send_email(to_email, subject, body, html_body)
    
    def send_card_replaced_confirmation(self, student_name: str, student_id: str,
                                       new_card: str, balance: float,
                                       to_email: str) -> bool:
        """
        Send card replacement confirmation email to parent
        
        Args:
            student_name: Student's full name
            student_id: Student ID
            new_card: New card number
            balance: Balance transferred
            to_email: Parent/guardian email
        
        Returns:
            True if sent successfully
        """
        now = get_philippines_time()
        
        subject = f"Replacement Card Issued - {student_name}"
        
        body = f"""
Dear Parent/Guardian,

This is to confirm that a replacement money card has been issued for {student_name} 
(ID: {student_id}).

Replacement Details:
- New Card Number: {new_card}
- Balance Transferred: ₱{balance:.2f}
- Issued: {now.strftime('%Y-%m-%d %H:%M:%S')}

The card is now active and ready to use. The balance of ₱{balance:.2f} from the 
lost card has been successfully transferred to this new card.

Your child can now use the new card at school immediately.

Thank you,
Bangko ng Seton Finance Office
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #059669; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f8f9fa; }}
        .success {{ background: #D1FAE5; border-left: 4px solid #059669; padding: 15px; margin: 15px 0; }}
        .details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .card-number {{ font-family: monospace; font-size: 20px; color: #4F46E5; font-weight: bold; }}
        .balance {{ font-size: 20px; color: #059669; font-weight: bold; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>✅ Replacement Card Issued</h2>
        </div>
        <div class="content">
            <p>Dear Parent/Guardian,</p>
            <p>A replacement money card has been issued for <strong>{student_name}</strong> (ID: {student_id}).</p>
            
            <div class="details">
                <h3>Replacement Details:</h3>
                <p class="card-number">New Card: {new_card}</p>
                <p class="balance">Balance Transferred: ₱{balance:.2f}</p>
                <p><strong>Issued:</strong> {now.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="success">
                <strong>✓ Active:</strong> The card is now active and ready to use. 
                The balance has been successfully transferred.
            </div>
            
            <p>Your child can use the new card at school immediately.</p>
        </div>
        <div class="footer">
            <p>Bangko ng Seton Finance Office</p>
            <p>This is an automated notification. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return self.send_email(to_email, subject, body, html_body)
    
    def send_large_transaction_alert(self, student_name: str, student_id: str,
                                    amount: float, transaction_type: str,
                                    to_email: str) -> bool:
        """
        Send large transaction alert email
        
        Args:
            student_name: Student's full name
            student_id: Student ID
            amount: Transaction amount
            transaction_type: Type of transaction
            to_email: Parent/guardian email
        
        Returns:
            True if sent successfully
        """
        now = get_philippines_time()
        
        subject = f"Large Transaction Alert - {student_name}"
        
        body = f"""
Dear Parent/Guardian,

A large transaction was made on the account of {student_name} (ID: {student_id}).

Transaction Details:
- Type: {transaction_type}
- Amount: ₱{abs(amount):.2f}
- Date/Time: {now.strftime('%Y-%m-%d %H:%M:%S')}

If you did not authorize this transaction, please contact the Finance Office immediately.

Thank you,
Bangko ng Seton Finance Office
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f8f9fa; }}
        .alert {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; }}
        .transaction {{ background: white; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .amount {{ font-size: 24px; color: #dc3545; font-weight: bold; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>💳 Large Transaction Alert</h2>
        </div>
        <div class="content">
            <p>Dear Parent/Guardian,</p>
            <p>A large transaction was made on the account of <strong>{student_name}</strong> (ID: {student_id}).</p>
            
            <div class="transaction">
                <h3>Transaction Details:</h3>
                <p><strong>Type:</strong> {transaction_type}</p>
                <p class="amount">Amount: ₱{abs(amount):.2f}</p>
                <p><strong>Date/Time:</strong> {now.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="alert">
                <strong>⚠️ Important:</strong> If you did not authorize this transaction, 
                please contact the Finance Office immediately.
            </div>
        </div>
        <div class="footer">
            <p>Bangko ng Seton Finance Office</p>
            <p>This is an automated notification. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return self.send_email(to_email, subject, body, html_body)
    
    def send_daily_summary(self, to_email: str, summary_data: Dict) -> bool:
        """
        Send daily transaction summary email
        
        Args:
            to_email: Recipient email
            summary_data: Dictionary with summary statistics
        
        Returns:
            True if sent successfully
        """
        date = summary_data.get('date', datetime.now().strftime('%Y-%m-%d'))
        total_txns = summary_data.get('total_transactions', 0)
        total_spending = summary_data.get('total_spending', 0.0)
        total_loaded = summary_data.get('total_loaded', 0.0)
        unique_students = summary_data.get('unique_students', 0)
        
        subject = f"Daily Summary - {date}"
        
        body = f"""
Bangko ng Seton - Daily Summary
Date: {date}

Summary:
- Total Transactions: {total_txns}
- Unique Students: {unique_students}
- Total Spending: ₱{total_spending:.2f}
- Total Loaded: ₱{total_loaded:.2f}

Thank you,
Bangko ng Seton System
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .stat-card {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #4F46E5; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>📊 Daily Summary</h2>
            <p>{date}</p>
        </div>
        <div class="content">
            <div class="stat-card">
                <p>Total Transactions</p>
                <p class="stat-value">{total_txns}</p>
            </div>
            <div class="stat-card">
                <p>Unique Students</p>
                <p class="stat-value">{unique_students}</p>
            </div>
            <div class="stat-card">
                <p>Total Spending</p>
                <p class="stat-value">₱{total_spending:.2f}</p>
            </div>
            <div class="stat-card">
                <p>Total Loaded</p>
                <p class="stat-value">₱{total_loaded:.2f}</p>
            </div>
        </div>
        <div class="footer">
            <p>Bangko ng Seton Automated System</p>
        </div>
    </div>
</body>
</html>
        """
        
        return self.send_email(to_email, subject, body, html_body)


class NotificationManager:
    """Manages all notification triggers and delivery"""
    
    def __init__(self, email_notifier: EmailNotifier = None):
        """
        Initialize notification manager
        
        Args:
            email_notifier: EmailNotifier instance (creates default if None)
        """
        self.email_notifier = email_notifier or EmailNotifier()
        self.low_balance_threshold = float(os.getenv('LOW_BALANCE_THRESHOLD', 50))
        self.large_transaction_threshold = float(os.getenv('LARGE_TRANSACTION_THRESHOLD', 100))
    
    def check_low_balances(self, accounts: List[Dict], students: List[Dict]) -> int:
        """
        Check for low balances and send alerts
        
        Args:
            accounts: List of money account dictionaries
            students: List of student dictionaries
        
        Returns:
            Number of alerts sent
        """
        alerts_sent = 0
        
        # Create student lookup
        student_lookup = {s['StudentID']: s for s in students}
        
        for account in accounts:
            try:
                balance = float(account.get('Balance', 0))
                student_id = account.get('StudentID')
                
                if balance < self.low_balance_threshold and account.get('Status') == 'Active':
                    student = student_lookup.get(student_id)
                    if not student:
                        continue
                    
                    parent_email = student.get('ParentEmail', '').strip()
                    if not parent_email or '@' not in parent_email:
                        continue
                    
                    success = self.email_notifier.send_low_balance_alert(
                        student_name=student.get('Name', 'Unknown'),
                        student_id=student_id,
                        balance=balance,
                        to_email=parent_email
                    )
                    
                    if success:
                        alerts_sent += 1
            
            except (ValueError, TypeError):
                continue
        
        return alerts_sent
    
    def notify_large_transaction(self, transaction: Dict, students: List[Dict]) -> bool:
        """
        Send notification for large transaction
        
        Args:
            transaction: Transaction dictionary
            students: List of student dictionaries
        
        Returns:
            True if notification sent
        """
        try:
            amount = abs(float(transaction.get('Amount', 0)))
            
            if amount < self.large_transaction_threshold:
                return False
            
            student_id = transaction.get('StudentID')
            student = next((s for s in students if s['StudentID'] == student_id), None)
            
            if not student:
                return False
            
            parent_email = student.get('ParentEmail', '').strip()
            if not parent_email or '@' not in parent_email:
                return False
            
            return self.email_notifier.send_large_transaction_alert(
                student_name=student.get('Name', 'Unknown'),
                student_id=student_id,
                amount=amount,
                transaction_type=transaction.get('Type', 'Unknown'),
                to_email=parent_email
            )
        
        except (ValueError, TypeError):
            return False


# Singleton instance
_notification_manager = None


def get_notification_manager() -> NotificationManager:
    """Get or create notification manager singleton"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
