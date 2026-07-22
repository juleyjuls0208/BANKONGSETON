"""
Bangko ng Seton — Shared Loading & Card Service
================================================

One canonical implementation of the money-management operations that the three
web apps all need:

  * Finance/Admin dashboard   -> load balance, report/replace lost cards
  * Loading Kiosk             -> top-up by money-card tap, QR scan, or cardless token
  * Tech/Admin kiosk          -> RFID debug, add new/lost cards

Keeping the real data writes here (and only here) means the kiosk and tech apps
cannot drift from the dashboard, and a fix made once applies everywhere.

The service is deliberately *transport-agnostic*: it talks to `sheets_adapter`
(the Supabase/Postgres backend) via the same primitives the dashboard already
uses (`get_worksheet_with_retry`, `rowcol_to_a1`, `invalidate_pattern`, ...).

A Flask app wires it up by calling ``register_loading_routes(app, socketio,
mode)`` with one of MODE_DASHBOARD / MODE_KIOSK / MODE_TECH — see
loading_routes.py in each app folder.
"""

from __future__ import annotations

import logging
import os
import re
import time
import uuid
from datetime import datetime
from math import isfinite
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("bangko.loading_service")

# Import the same data primitives the dashboard uses so behaviour stays 1:1.
try:
    from cache import invalidate_pattern
except Exception:  # pragma: no cover - cache optional in some test stubs
    def invalidate_pattern(*_args, **_kwargs):
        return None

from sheets_adapter import APIError, SpreadsheetNotFound, WorksheetNotFound
from utils import normalize_card_uid

# Re-use dashboard_core's helpers when importable (same process as dashboard).
try:
    from dashboard_core import (
        get_cached_column_index,
        get_philippines_time,
        get_sheet_records_safe,
        get_worksheet_with_retry,
        rowcol_to_a1,
    )
    _HAS_CORE = True
except Exception:  # pragma: no cover - standalone import (kiosk/tech)
    _HAS_CORE = False

    # Local fallbacks so the service works even without dashboard_core in the path.
    def get_worksheet_with_retry(sheet_name, max_retries=3):
        from sheets_adapter import get_sheets_client

        db = get_sheets_client()
        return db.worksheet(sheet_name)


    def rowcol_to_a1(row, col):
        result = ""
        while col > 0:
            col, rem = divmod(col - 1, 26)
            result = chr(65 + rem) + result
        return f"{result}{row}"

    def get_cached_column_index(worksheet, header_name: str, ttl: int = 300) -> int:
        return worksheet.find(header_name).col

    def get_sheet_records_safe(sheet):
        return sheet.get_all_records()


UID_PATTERN = re.compile(r"^[0-9A-Fa-f]{8}$|^[0-9A-Fa-f]{14}$")

# Transaction-type labels used by each station.
STATION_DASHBOARD = "finance-dashboard"
STATION_KIOSK = "loading-kiosk"
STATION_TECH = "tech-kiosk"


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _student_by_id(student_id: str) -> Optional[dict]:
    users_sheet = get_worksheet_with_retry("Users")
    for record in get_sheet_records_safe(users_sheet):
        if str(record.get("StudentID", "")).strip() == str(student_id).strip():
            return record
    return None


def _student_by_money_card(money_card: str) -> Optional[dict]:
    normalized = normalize_card_uid(str(money_card))
    if not normalized:
        return None
    users_sheet = get_worksheet_with_retry("Users")
    for record in get_sheet_records_safe(users_sheet):
        if normalize_card_uid(str(record.get("MoneyCardNumber", ""))) == normalized:
            return record
    return None


def _money_account_row(money_card: str):
    """Return (row_index_1based, record) for a money account, or (None, None)."""
    normalized = normalize_card_uid(str(money_card))
    money_sheet = get_worksheet_with_retry("Money Accounts")
    for i, record in enumerate(get_sheet_records_safe(money_sheet), start=2):
        if normalize_card_uid(str(record.get("MoneyCardNumber", ""))) == normalized:
            return i, record
    return None, None


def _log_transaction(row_map: dict, station_id: str) -> None:
    """Append a Transactions Log row, aligning to the sheet's real headers."""
    transactions_sheet = get_worksheet_with_retry("Transactions Log")
    row_map = dict(row_map)
    row_map["StationID"] = station_id
    row_map["Status"] = row_map.get("Status", "Completed")

    headers = [
        str(h).strip() for h in transactions_sheet.row_values(1) if str(h).strip()
    ]
    if headers:
        tx_row = [row_map.get(h, "") for h in headers]
    else:
        tx_row = [
            row_map.get("TransactionID", ""),
            row_map.get("Timestamp", ""),
            row_map.get("StudentID", ""),
            row_map.get("MoneyCardNumber", ""),
            row_map.get("TransactionType", ""),
            row_map.get("Amount", ""),
            row_map.get("BalanceBefore", ""),
            row_map.get("BalanceAfter", ""),
            row_map.get("Status", ""),
            row_map.get("ErrorMessage", ""),
        ]

    transactions_sheet.append_row(tx_row)
    invalidate_pattern("transactions")
    invalidate_pattern("sheet_records:Transactions Log")


def _send_balance_loaded_email(student: dict, student_id: str, amount: float,
                               new_balance: float) -> None:
    """Best-effort parent notification. Never raises."""
    try:
        parent_email = student.get("StudentEmail", "").strip()
        if not parent_email or "@" not in parent_email:
            return
        from notifications import get_notification_manager

        mgr = get_notification_manager()
        mgr.email_notifier.send_balance_loaded(
            student_name=student.get("Name", "Unknown"),
            student_id=student_id,
            amount=amount,
            new_balance=new_balance,
            to_email=parent_email,
        )
    except Exception as exc:  # pragma: no cover - network optional
        logger.warning("event=balance_loaded_email_skipped error=%s", exc)


# ---------------------------------------------------------------------------
# Top-level operations
# ---------------------------------------------------------------------------

def load_money(student_id: str, amount: float, *,
               payment_method: str = "cash",
               processed_by: str = "kiosk",
               station_id: str = STATION_KIOSK,
               idempotency_key: str | None = None) -> dict:
    """Credit `amount` to a student's money card. Returns a result dict.

    Mirrors dashboard_core.load_balance() exactly (same columns, same
    transaction log, same email). Used by dashboard, kiosk, and tech apps.
    """
    student_id = str(student_id or "").strip()
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return {"success": False, "error": "Invalid amount", "status": 400}
    if not isfinite(amount) or amount <= 0:
        return {"success": False, "error": "Amount must be positive", "status": 400}
    if not student_id:
        return {"success": False, "error": "student_id is required", "status": 400}

    student = _student_by_id(student_id)
    if not student:
        return {"success": False, "error": "Student not found", "status": 404}

    money_card = student.get("MoneyCardNumber", "")
    if not money_card:
        return {"success": False, "error": "No money card registered", "status": 400}

    row_index, account = _money_account_row(money_card)
    if not row_index:
        return {"success": False, "error": "Money account not found", "status": 404}

    # Supabase path: row lock, balance update, TotalLoaded update, ledger
    # insert, and idempotency all commit together.  The fake/gspread path below
    # remains only for local compatibility tests and legacy deployments.
    atomic = getattr(get_worksheet_with_retry("Money Accounts"), "update_balance_atomic", None)
    if atomic is not None:
        try:
            result = atomic(
                money_card=normalize_card_uid(money_card),
                amount_delta=amount,
                total_loaded_delta=amount,
                transaction_type="Load",
                items_json=payment_method,
                student_id=student_id,
                idempotency_key=idempotency_key,
                station_id=station_id or processed_by,
            )
        except APIError as exc:
            message = str(exc)
            status = 402 if "Insufficient" in message else 400 if "not found" in message or "inactive" in message.lower() else 503
            return {"success": False, "error": message, "status": status}
        _send_balance_loaded_email(student, student_id, amount, result["BalanceAfter"])
        return {
            "success": True,
            "student_id": student_id,
            "student_name": student.get("Name", ""),
            "money_card": normalize_card_uid(money_card),
            "amount_loaded": amount,
            "new_balance": result["BalanceAfter"],
            "transaction_id": result["TransactionID"],
            "idempotent": result.get("Idempotent", False),
        }

    current_balance = float(account.get("Balance", 0))
    total_loaded = float(account.get("TotalLoaded", 0))
    new_balance = current_balance + amount
    new_total = total_loaded + amount
    timestamp = get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")

    money_sheet = get_worksheet_with_retry("Money Accounts")
    balance_col = get_cached_column_index(money_sheet, "Balance")
    total_col = get_cached_column_index(money_sheet, "TotalLoaded")
    updated_col = get_cached_column_index(money_sheet, "LastUpdated")

    money_sheet.batch_update([
        {"range": rowcol_to_a1(row_index, balance_col), "values": [[new_balance]]},
        {"range": rowcol_to_a1(row_index, total_col), "values": [[new_total]]},
        {"range": rowcol_to_a1(row_index, updated_col), "values": [[timestamp]]},
    ])

    transaction_id = f"TXN-{get_philippines_time().strftime('%Y%m%d%H%M%S')}"
    _log_transaction({
        "TransactionID": transaction_id,
        "Timestamp": timestamp,
        "StudentID": student_id,
        "MoneyCardNumber": normalize_card_uid(money_card),
        "TransactionType": "Load",
        "Amount": float(amount),
        "BalanceBefore": float(current_balance),
        "BalanceAfter": float(new_balance),
        "ErrorMessage": "",
        "ProcessedBy": processed_by,
        "PaymentMethod": payment_method,
    }, station_id=station_id)

    _send_balance_loaded_email(student, student_id, amount, new_balance)

    return {
        "success": True,
        "student_id": student_id,
        "student_name": student.get("Name", ""),
        "money_card": normalize_card_uid(money_card),
        "amount_loaded": float(amount),
        "new_balance": float(new_balance),
        "transaction_id": transaction_id,
    }


def get_student_balance(student_id: str = "", money_card: str = "") -> dict:
    """Look up a student and current balance by id or money card."""
    student = None
    if student_id:
        student = _student_by_id(student_id)
    if not student and money_card:
        student = _student_by_money_card(money_card)
    if not student:
        return {"success": False, "error": "Student not found", "status": 404}

    money_card = student.get("MoneyCardNumber", "")
    if not money_card:
        return {
            "success": True,
            "student_id": student.get("StudentID"),
            "student_name": student.get("Name"),
            "balance": 0,
            "has_card": False,
        }

    _, account = _money_account_row(money_card)
    balance = float(account.get("Balance", 0)) if account else 0
    status = account.get("Status", "") if account else ""
    return {
        "success": True,
        "student_id": student.get("StudentID"),
        "student_name": student.get("Name"),
        "money_card": normalize_card_uid(money_card),
        "balance": float(balance),
        "status": status,
        "has_card": True,
    }


def report_lost_card(student_id: str, *, station_id: str = STATION_DASHBOARD) -> dict:
    """Mark a student's money card lost and open a Lost Card Report.

    Mirrors dashboard_core.report_lost_card(): balance is preserved, the card
    is set to 'Lost', and a pending report is created for replacement.
    """
    student_id = str(student_id or "").strip()
    student = _student_by_id(student_id)
    if not student:
        return {"success": False, "error": "Student not found", "status": 404}

    money_card = student.get("MoneyCardNumber", "")
    if not money_card:
        return {"success": False, "error": "No money card registered", "status": 400}

    _, account = _money_account_row(money_card)
    if not account:
        return {"success": False, "error": "Money account not found", "status": 404}

    balance = float(account.get("Balance", 0))
    money_sheet = get_worksheet_with_retry("Money Accounts")
    status_col = get_cached_column_index(money_sheet, "Status")
    money_sheet.update_cell(_money_account_row(money_card)[0], status_col, "Lost")

    timestamp = get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")
    report_id = f"LCR-{get_philippines_time().strftime('%Y%m%d%H%M%S')}"
    lost_sheet = get_worksheet_with_retry("Lost Card Reports")
    lost_sheet.append_row([
        report_id, timestamp, student_id, normalize_card_uid(money_card),
        "", balance, "admin", "Pending",
    ])
    invalidate_pattern("sheet_records:Lost Card Reports")

    try:
        parent_email = student.get("StudentEmail", "").strip()
        if parent_email and "@" in parent_email:
            from notifications import get_notification_manager
            get_notification_manager().email_notifier.send_card_lost_alert(
                student_name=student.get("Name", "Unknown"),
                student_id=student_id,
                card_number=normalize_card_uid(money_card),
                balance_preserved=balance,
                to_email=parent_email,
            )
    except Exception as exc:  # pragma: no cover
        logger.warning("event=lost_card_email_skipped error=%s", exc)

    return {
        "success": True,
        "student_id": student_id,
        "report_id": report_id,
        "balance_preserved": float(balance),
    }


def replace_lost_card(student_id: str, new_card_uid: str,
                      *, station_id: str = STATION_DASHBOARD) -> dict:
    """Issue a replacement money card, transferring the preserved balance."""
    student_id = str(student_id or "").strip()
    new_card = normalize_card_uid(new_card_uid)
    if not new_card or not UID_PATTERN.match(new_card):
        return {"success": False, "error": "Invalid card UID", "status": 400}

    student = _student_by_id(student_id)
    if not student:
        return {"success": False, "error": "Student not found", "status": 404}

    lost_sheet = get_worksheet_with_retry("Lost Card Reports")
    lost_records = get_sheet_records_safe(lost_sheet)
    report = None
    report_row = None
    for i, rec in enumerate(lost_records, start=2):
        if (str(rec.get("StudentID", "")).strip() == student_id
                and str(rec.get("Status", "")).strip() == "Pending"):
            report = rec
            report_row = i
            break
    if not report:
        return {"success": False, "error": "No pending lost card report", "status": 404}

    balance = float(report.get("TransferredBalance", 0))
    old_card = normalize_card_uid(report.get("OldCardNumber", ""))
    timestamp = get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")

    # Deactivate old account row (if present) and create the new one.
    _, old_account = _money_account_row(old_card) if old_card else (None, None)
    if old_account:
        money_sheet = get_worksheet_with_retry("Money Accounts")
        row_idx, _ = _money_account_row(old_card)
        status_col = get_cached_column_index(money_sheet, "Status")
        money_sheet.update_cell(row_idx, status_col, "Replaced")

    money_sheet = get_worksheet_with_retry("Money Accounts")
    money_sheet.append_row([
        new_card, student.get("IDCardNumber", ""), balance,
        "Active", timestamp, balance, timestamp,
    ])
    invalidate_pattern("sheet_records:Money Accounts")

    # Update the Users sheet money card reference.
    users_sheet = get_worksheet_with_retry("Users")
    users_records = get_sheet_records_safe(users_sheet)
    for i, rec in enumerate(users_records, start=2):
        if str(rec.get("StudentID", "")).strip() == student_id:
            col = get_cached_column_index(users_sheet, "MoneyCardNumber")
            users_sheet.update_cell(i, col, new_card)
            break

    # Close out the lost-card report.
    if report_row:
        status_col = get_cached_column_index(lost_sheet, "Status")
        lost_sheet.update_cell(report_row, status_col, "Resolved")
        invalidate_pattern("sheet_records:Lost Card Reports")

    try:
        parent_email = student.get("StudentEmail", "").strip()
        if parent_email and "@" in parent_email:
            from notifications import get_notification_manager
            get_notification_manager().email_notifier.send_card_replaced_confirmation(
                student_name=student.get("Name", "Unknown"),
                student_id=student_id,
                new_card_number=new_card,
                balance_transferred=balance,
                to_email=parent_email,
            )
    except Exception as exc:  # pragma: no cover
        logger.warning("event=replace_card_email_skipped error=%s", exc)

    return {
        "success": True,
        "student_id": student_id,
        "new_card": new_card,
        "balance_transferred": float(balance),
    }


# ---------------------------------------------------------------------------
# Cardless top-up (student app -> kiosk QR)
# ---------------------------------------------------------------------------

class TopupSessionStore:
    """In-memory store of cardless top-up sessions.

    A kiosk mints a session token; the student app shows it as a QR. When the
    student scans the QR at the kiosk, the kiosk resolves the token back to the
    student. The kiosk then credits the student's card after a bill/coin insert.

    Scoped per-kiosk (each app process owns its own store). Satisfies the
    single-worker deployment constraint already enforced by the project.
    """

    def __init__(self, ttl_seconds: int = 120):
        self._ttl = ttl_seconds
        self._sessions: dict[str, dict] = {}

    def create(self, student_id: str, student_name: str = "",
               *, ttl_seconds: Optional[int] = None) -> dict:
        token = uuid.uuid4().hex
        ttl = ttl_seconds if ttl_seconds is not None else self._ttl
        self._sessions[token] = {
            "token": token,
            "student_id": student_id,
            "student_name": student_name,
            "created_at": time.time(),
            "expires_at": time.time() + ttl,
            "redeemed": False,
        }
        self._gc()
        return self._sessions[token]

    def resolve(self, token: str) -> Optional[dict]:
        self._gc()
        sess = self._sessions.get(token)
        if not sess:
            return None
        if sess["expires_at"] < time.time():
            self._sessions.pop(token, None)
            return None
        return sess

    def redeem(self, token: str) -> Optional[dict]:
        sess = self.resolve(token)
        if not sess:
            return None
        sess["redeemed"] = True
        return sess

    def _gc(self) -> None:
        now = time.time()
        expired = [t for t, s in self._sessions.items() if s["expires_at"] < now]
        for t in expired:
            self._sessions.pop(t, None)


# Default process-local store; kiosk app can construct its own if needed.
default_session_store = TopupSessionStore()
