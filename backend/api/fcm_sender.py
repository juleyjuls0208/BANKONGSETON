"""
FCM push notification sender for Bangko ng Seton.
Sends low-balance alerts to students via Firebase Cloud Messaging.
"""
import os
import logging
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from errors import get_logger
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)

def _init_firebase():
    """Initialize Firebase Admin SDK once. Guard against double-init."""
    try:
        import firebase_admin
        from firebase_admin import credentials
        if not firebase_admin._apps:
            cred_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'config', 'firebase-credentials.json'
            )
            if not os.path.exists(cred_path):
                logger.warning("event=fcm_cred_missing path=%s", cred_path)
                return False
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("event=firebase_initialized")
        return True
    except Exception as e:
        logger.error("event=firebase_init_failed error=%s", e)
        return False


def send_low_balance_push(fcm_token: str, balance: float) -> bool:
    """
    Send a low-balance push notification to a student device.

    Args:
        fcm_token: FCM device registration token (from Students sheet FCMToken column)
        balance: Current balance after the transaction

    Returns:
        True on success, False on failure (never raises).
    """
    if not fcm_token or not fcm_token.strip():
        return False

    try:
        import firebase_admin
        from firebase_admin import messaging

        if not _init_firebase():
            return False

        message = messaging.Message(
            notification=messaging.Notification(
                title="Low Balance",
                body=f"Your canteen balance is ฿{balance:.2f}. Please top up soon."
            ),
            token=fcm_token.strip()
        )
        messaging.send(message)
        logger.info("event=fcm_sent balance=%.2f", balance)
        return True

    except Exception as e:
        # Catch UnregisteredError (stale token) and all other FCM errors
        logger.error("event=fcm_send_failed error=%s", e)
        return False
