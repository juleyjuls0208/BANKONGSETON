import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import threading
from datetime import datetime
import time

try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from errors import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('SMTP_EMAIL')
        self.sender_password = os.getenv('SMTP_PASSWORD')
        self.enabled = bool(self.sender_email and self.sender_password)
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    def send_receipt(self, to_email, student_email, student_name, items, total_amount, new_balance):
        """
        Send a receipt email in a background thread with retry logic.
        Falls back to student email if parent email is not provided.
        """
        if not self.enabled:
            logger.info("event=email_skipped reason=missing_credentials")
            return

        # Fallback to student email if parent email is null
        recipient = to_email if to_email else student_email
        
        if not recipient:
            logger.info("event=email_skipped reason=no_recipient")
            return

        # Run in background to not block the API
        thread = threading.Thread(
            target=self._send_email_with_retry,
            args=(recipient, student_name, items, total_amount, new_balance)
        )
        thread.daemon = True
        thread.start()

    def _send_email_with_retry(self, to_email, student_name, items, total_amount, new_balance):
        """Send email with exponential backoff retry logic"""
        for attempt in range(self.max_retries):
            try:
                self._send_email(to_email, student_name, items, total_amount, new_balance)
                logger.info("event=email_sent to=%s attempt=%d", to_email, attempt + 1)
                return  # Success
            except Exception as e:
                logger.warning("event=email_attempt_failed attempt=%d/%d error=%s", attempt + 1, self.max_retries, e)
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info("event=email_retry delay=%ds", delay)
                    time.sleep(delay)
                else:
                    logger.error("event=email_exhausted to=%s", to_email)

    def _send_email(self, to_email, student_name, items, total_amount, new_balance):
        """Internal method to send the email"""
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = to_email
        msg['Subject'] = f"Receipt: Purchase for {student_name}"

        # Build Item List HTML
        items_html = ""
        for item in items:
            qty = item.get('qty', 1)
            item_total = item['price'] * qty
            items_html += f"<li>{item['name']} (x{qty}) - ₱{item_total:.2f}</li>"

        body = f"""
        <html>
        <body>
            <h2>Bangko ng Seton - Purchase Receipt</h2>
            <p>Hello,</p>
            <p>Your child <strong>{student_name}</strong> has just made a purchase.</p>
            <hr>
            <h3>Items Bought:</h3>
            <ul>
                {items_html}
            </ul>
            <hr>
            <p><strong>Total: ₱{total_amount:.2f}</strong></p>
            <p>Remaining Balance: ₱{new_balance:.2f}</p>
            <br>
            <p><small>This is an automated message. Please do not reply.</small></p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.starttls()
        server.login(self.sender_email, self.sender_password)
        server.send_message(msg)
        server.quit()

# Global instance
email_service = EmailService()
