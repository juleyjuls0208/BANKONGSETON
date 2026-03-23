"""
FCM push notification sender for Bangko ng Seton.
Sends low-balance alerts to students via Firebase Cloud Messaging.
"""

import os
import logging
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
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
                os.path.dirname(__file__),
                "..",
                "..",
                "config",
                "firebase-credentials.json",
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
                body=f"Your canteen balance is ₱{balance:.2f}. Please top up soon.",
            ),
            token=fcm_token.strip(),
        )
        messaging.send(message)
        logger.info("event=fcm_sent balance=%.2f", balance)
        return True

    except Exception as e:
        # Catch UnregisteredError (stale token) and all other FCM errors
        logger.error("event=fcm_send_failed error=%s", e)
        return False


def send_purchase_push(fcm_token: str, amount: float, new_balance: float) -> bool:
    """
    Send a purchase-confirmed push notification to a student device.
    Args:
        fcm_token: FCM device registration token
        amount: Amount deducted (positive value)
        new_balance: Balance after deduction
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
                title="Purchase Confirmed",
                body=f"₱{amount:.2f} deducted. New balance: ₱{new_balance:.2f}",
            ),
            token=fcm_token.strip(),
        )
        messaging.send(message)
        logger.info(
            "event=fcm_purchase_sent amount=%.2f balance=%.2f", amount, new_balance
        )
        return True
    except Exception as e:
        logger.error("event=fcm_purchase_send_failed error=%s", e)
        return False


def send_load_push(fcm_token: str, amount: float, new_balance: float) -> bool:
    """
    Send a money-loaded push notification to a student device.
    Args:
        fcm_token: FCM device registration token
        amount: Amount loaded (positive value)
        new_balance: Balance after load
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
                title="Money Loaded",
                body=f"₱{amount:.2f} added to your account. Balance: ₱{new_balance:.2f}",
            ),
            token=fcm_token.strip(),
        )
        messaging.send(message)
        logger.info("event=fcm_load_sent amount=%.2f balance=%.2f", amount, new_balance)
        return True
    except Exception as e:
        logger.error("event=fcm_load_send_failed error=%s", e)
        return False


def send_card_replaced_push(fcm_token: str, student_name: str) -> bool:
    """
    Notify student that their lost card replacement has been processed.

    Args:
        fcm_token: FCM device registration token
        student_name: Student's name for personalisation

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
                title="Card Replacement Ready",
                body=f"Hi {student_name}, your new card has been activated. You're all set!",
            ),
            data={"type": "card_replaced"},
            token=fcm_token.strip(),
        )
        messaging.send(message)
        logger.info("event=fcm_card_replaced_sent student=%s", student_name)
        return True
    except Exception as e:
        logger.error("event=fcm_card_replaced_send_failed error=%s", e)
        return False
