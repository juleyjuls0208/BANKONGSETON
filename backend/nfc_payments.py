"""
NFC Payments - Sheets-backed VirtualCard service for Phase 5.

Implements the locked VirtualCard design:
  - UUID v4 virtual card tokens
  - Device tokens via secrets.token_urlsafe(32)
  - One active card per student (silent replace on re-register)
  - No expiry, no PIN, no biometrics
"""

import uuid
import secrets
from datetime import datetime
from typing import Optional

import pytz
import gspread

try:
    from backend.errors import get_logger
except ImportError:
    from errors import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Sheet constants
# ---------------------------------------------------------------------------

VIRTUAL_CARDS_SHEET_NAME = "VirtualCards"
VIRTUAL_CARDS_HEADERS = [
    "StudentID",
    "VirtualCardToken",
    "DeviceToken",
    "MoneyCardNumber",
    "CreatedAt",
    "IsActive",
]

# ---------------------------------------------------------------------------
# Time helper (replicated from api_server.py — no import to avoid circular ref)
# ---------------------------------------------------------------------------

PHILIPPINES_TZ = pytz.timezone("Asia/Manila")


def get_philippines_time() -> datetime:
    """Return current time in the Asia/Manila timezone."""
    return datetime.now(PHILIPPINES_TZ)


# ---------------------------------------------------------------------------
# Sheet bootstrap
# ---------------------------------------------------------------------------


def ensure_virtual_cards_sheet(db):
    """Return the VirtualCards worksheet, creating it with headers if missing.

    Mirrors ensure_products_sheet() in admin_dashboard.py.
    """
    try:
        return db.worksheet(VIRTUAL_CARDS_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        sheet = db.add_worksheet(
            title=VIRTUAL_CARDS_SHEET_NAME,
            rows=200,
            cols=6,
        )
        sheet.update("A1:F1", [VIRTUAL_CARDS_HEADERS])
        logger.info("event=virtual_cards_sheet_created")
        return sheet


# ---------------------------------------------------------------------------
# NFCService
# ---------------------------------------------------------------------------


class NFCService:
    """Stateless service layer for VirtualCard operations backed by Google Sheets.

    All methods accept a ``db`` (gspread Spreadsheet) parameter so there is no
    module-level shared state.
    """

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_virtual_card(
        self,
        student_id: str,
        money_card_number: str,
        db,
    ) -> dict:
        """Register (or replace) a VirtualCard for *student_id*.

        If the student already has an active row in the VirtualCards sheet that
        row's IsActive column is set to ``'FALSE'`` before the new row is
        appended.  Only one active card per student is allowed.

        Returns a dict with keys: virtual_card_token, device_token, money_card.
        """
        vc_sheet = ensure_virtual_cards_sheet(db)
        records = vc_sheet.get_all_records()

        # Deactivate any existing active row for this student.
        for idx, r in enumerate(records, start=2):
            if (
                str(r.get("StudentID")) == str(student_id)
                and str(r.get("IsActive", "")).upper() == "TRUE"
            ):
                # Column 6 = IsActive (A=1, …, F=6)
                vc_sheet.update_cell(idx, 6, "FALSE")

        # Generate new tokens.
        virtual_card_token = str(uuid.uuid4())
        device_token = secrets.token_urlsafe(32)
        timestamp = get_philippines_time().isoformat()

        # Append new active row.
        vc_sheet.append_row(
            [
                student_id,
                virtual_card_token,
                device_token,
                money_card_number,
                timestamp,
                "TRUE",
            ]
        )

        logger.info(f"event=virtual_card_registered student_id={student_id}")

        return {
            "virtual_card_token": virtual_card_token,
            "device_token": device_token,
            "money_card": money_card_number,
        }

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_virtual_card_by_tokens(
        self,
        virtual_card_token: str,
        device_token: str,
        db,
    ) -> Optional[dict]:
        """Return the active VirtualCard row matching both tokens, or ``None``.

        Only rows where IsActive == ``'TRUE'`` (case-insensitive) are
        considered; deactivated rows are silently skipped.
        """
        vc_sheet = ensure_virtual_cards_sheet(db)
        records = vc_sheet.get_all_records()

        for r in records:
            if (
                r.get("VirtualCardToken") == virtual_card_token
                and r.get("DeviceToken") == device_token
                and str(r.get("IsActive", "")).upper() == "TRUE"
            ):
                return r

        return None

    def get_virtual_card_by_token(
        self,
        virtual_card_token: str,
        db,
    ) -> Optional[dict]:
        """Return the active VirtualCard row matching ``virtual_card_token`` alone.

        Used by the payment terminal flow where the client cannot supply
        ``X-Device-Token`` (e.g. Android HCE APDU response contains only the
        virtual card token).  Only rows where IsActive == 'TRUE'
        (case-insensitive) are considered.
        """
        vc_sheet = ensure_virtual_cards_sheet(db)
        records = vc_sheet.get_all_records()

        for r in records:
            if (
                r.get("VirtualCardToken") == virtual_card_token
                and str(r.get("IsActive", "")).upper() == "TRUE"
            ):
                return r

        return None
