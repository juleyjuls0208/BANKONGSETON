"""
Tests for cashier routes: api_login and complete_sale.

Slice S04 / Task T02 — ~18 unit tests covering JWT auth gate (api_login)
and the money-moving core (complete_sale).

Key mechanics:
  - JWT cookie: set via client.set_cookie('jwt_token', token) using
    _make_cashier_token() — no need to go through login endpoint.
  - sys.modules['admin_dashboard']: set by flask_app fixture so
    cashier_routes' inline `from admin_dashboard import ...` resolves
    to the mocked module without re-importing.
  - db fixture: function-scoped fresh MagicMock spreadsheet; configure
    db.worksheet.side_effect per test to return named worksheet mocks.
  - Offline fallback: patch time.sleep (avoids 6s wait) and
    offline_queue.get_offline_queue (prevents SQLite file creation).
"""

import os
import sys
import json
import types

import pytest
import jwt
import bcrypt
import gspread
from unittest.mock import MagicMock, patch

# Import module-level helpers from conftest (not fixtures — must be imported)
sys.path.insert(0, os.path.dirname(__file__))
from conftest import _make_cashier_token, _set_pending


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ws_factory(**sheets):
    """Build a side_effect for db.worksheet that maps sheet name → mock.

    Any name not explicitly listed returns a generic MagicMock with
    get_all_records() → [] so iteration is always safe.
    """
    fallback = MagicMock()
    fallback.get_all_records.return_value = []

    def _factory(name):
        return sheets.get(name, fallback)

    return _factory


def _money_ws(records, *, update_cell_side_effect=None):
    """Return a configured Money Accounts worksheet mock."""
    ws = MagicMock()
    ws.get_all_records.return_value = records
    if update_cell_side_effect is not None:
        ws.update_cell.side_effect = update_cell_side_effect
    return ws


def _safe_users_ws(card_uid=None, phone=None):
    """Return a Users worksheet mock.

    If card_uid and phone are provided, includes a matching user record
    so the email/SMS sections run. Otherwise returns empty list so those
    sections are skipped gracefully.
    """
    ws = MagicMock()
    if card_uid and phone:
        ws.get_all_records.return_value = [
            {
                'MoneyCardNumber': card_uid,
                'Name': 'Test Student',
                'ParentEmail': 'parent@test.com',
                'Email': 'student@test.com',
                'ParentPhone': phone,
            }
        ]
    else:
        ws.get_all_records.return_value = []
    return ws


# ---------------------------------------------------------------------------
# TestApiLogin — 5 tests
# ---------------------------------------------------------------------------


class TestApiLogin:
    """Test POST /cashier/api/login."""

    def test_login_success_via_sheets(self, flask_app, db):
        """Active cashier account in Sheets → 200 + jwt_token cookie."""
        app, _ = flask_app
        pw_hash = bcrypt.hashpw(b"testpass", bcrypt.gensalt()).decode()

        cashier_ws = MagicMock()
        cashier_ws.get_all_records.return_value = [
            {
                "Username": "testcashier",
                "PasswordHash": pw_hash,
                "Status": "Active",
                "DisplayName": "Test Cashier",
            }
        ]
        db.worksheet.side_effect = _ws_factory(**{"Cashier Accounts": cashier_ws})

        client = app.test_client()
        resp = client.post(
            "/cashier/api/login",
            json={"username": "testcashier", "password": "testpass"},
        )

        assert resp.status_code == 200
        # JWT cookie must be set in the response
        assert "jwt_token" in resp.headers.get("Set-Cookie", "")

    def test_login_legacy_fallback(self, flask_app, db):
        """When Cashier Accounts sheet raises, legacy creds still log in."""
        app, _ = flask_app

        cashier_ws = MagicMock()
        cashier_ws.get_all_records.side_effect = Exception("Sheet not found")
        db.worksheet.side_effect = _ws_factory(**{"Cashier Accounts": cashier_ws})

        client = app.test_client()
        resp = client.post(
            "/cashier/api/login",
            json={"username": "cashier", "password": "cashier123"},
        )

        assert resp.status_code == 200

    def test_login_bad_credentials(self, flask_app, db):
        """Wrong password → 401."""
        app, _ = flask_app
        wrong_hash = bcrypt.hashpw(b"differentpass", bcrypt.gensalt()).decode()

        cashier_ws = MagicMock()
        cashier_ws.get_all_records.return_value = [
            {"Username": "testcashier", "PasswordHash": wrong_hash, "Status": "Active"}
        ]
        db.worksheet.side_effect = _ws_factory(**{"Cashier Accounts": cashier_ws})

        client = app.test_client()
        resp = client.post(
            "/cashier/api/login",
            json={"username": "testcashier", "password": "testpass"},
        )

        assert resp.status_code == 401

    def test_login_inactive_account(self, flask_app, db):
        """Inactive account returns 401 — actual code, not 403 as roadmap spec says."""
        app, _ = flask_app
        pw_hash = bcrypt.hashpw(b"testpass", bcrypt.gensalt()).decode()

        cashier_ws = MagicMock()
        cashier_ws.get_all_records.return_value = [
            {
                "Username": "inactivecashier",
                "PasswordHash": pw_hash,
                "Status": "Inactive",
            }
        ]
        db.worksheet.side_effect = _ws_factory(**{"Cashier Accounts": cashier_ws})

        client = app.test_client()
        resp = client.post(
            "/cashier/api/login",
            json={"username": "inactivecashier", "password": "testpass"},
        )

        # Actual route: return jsonify({'error': 'Account is inactive'}), 401
        assert resp.status_code == 401

    def test_login_missing_fields(self, flask_app, db):
        """Empty JSON body → no credentials → 401 (invalid creds path)."""
        app, _ = flask_app
        db.worksheet.return_value.get_all_records.return_value = []

        client = app.test_client()
        resp = client.post("/cashier/api/login", json={})

        assert resp.status_code in (400, 401)


# ---------------------------------------------------------------------------
# TestCompleteSale — 13 tests
# ---------------------------------------------------------------------------

_VALID_UID = "5F6E7D8C"   # 8-char hex, passes UID_PATTERN
_INVALID_UID = "ZZZZZZZZ"  # 8 chars but not hex — fails UID_PATTERN
_BALANCE_HIGH = 500
_TOTAL = 50
_ITEMS = [{"name": "Snack", "price": _TOTAL, "qty": 1}]


class TestCompleteSale:
    """Tests for POST /cashier/api/complete-sale."""

    # ------------------------------------------------------------------
    # Happy path and auth (~4 tests)
    # ------------------------------------------------------------------

    def test_complete_sale_success(self, flask_app, db):
        """Active card, balance=500, total=50 → 200, new_balance=450.0."""
        app, _ = flask_app
        token = _make_cashier_token("cashier1", "cashier")

        money_ws = _money_ws(
            [{"MoneyCardNumber": _VALID_UID, "Balance": _BALANCE_HIGH, "Status": "active"}]
        )
        trans_ws = MagicMock()
        db.worksheet.side_effect = _ws_factory(
            **{
                "Money Accounts": money_ws,
                "Transactions Log": trans_ws,
                "Users": _safe_users_ws(),  # empty — skip email/SMS
            }
        )

        client = app.test_client()
        client.set_cookie("jwt_token", token)
        _set_pending(client, _ITEMS, float(_TOTAL))

        resp = client.post(
            "/cashier/api/complete-sale", json={"card_uid": _VALID_UID}
        )

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["new_balance"] == pytest.approx(450.0)
        trans_ws.append_row.assert_called_once()

    def test_complete_sale_requires_jwt(self, flask_app, db):
        """No JWT cookie → route redirects to login (302 — jwt_required decorator)."""
        app, _ = flask_app
        db.worksheet.return_value.get_all_records.return_value = []

        client = app.test_client()
        # No cookie set
        _set_pending(client, _ITEMS, float(_TOTAL))
        resp = client.post(
            "/cashier/api/complete-sale", json={"card_uid": _VALID_UID}
        )

        # jwt_required returns redirect(url_for('cashier.login')) — status 302
        assert resp.status_code == 302

    def test_complete_sale_no_pending_transaction(self, flask_app, db):
        """Valid JWT but no pending_transaction in session → 400."""
        app, _ = flask_app
        token = _make_cashier_token("cashier1", "cashier")
        db.worksheet.return_value.get_all_records.return_value = []

        client = app.test_client()
        client.set_cookie("jwt_token", token)
        # Do NOT call _set_pending

        resp = client.post(
            "/cashier/api/complete-sale", json={"card_uid": _VALID_UID}
        )

        assert resp.status_code == 400
        assert "pending" in resp.get_json().get("error", "").lower()

    def test_complete_sale_missing_card_uid(self, flask_app, db):
        """Valid JWT + pending seeded, but POST body has no card_uid → 400."""
        app, _ = flask_app
        token = _make_cashier_token("cashier1", "cashier")
        db.worksheet.return_value.get_all_records.return_value = []

        client = app.test_client()
        client.set_cookie("jwt_token", token)
        _set_pending(client, _ITEMS, float(_TOTAL))

        resp = client.post("/cashier/api/complete-sale", json={})

        assert resp.status_code == 400
        assert "uid" in resp.get_json().get("error", "").lower() or \
               "card" in resp.get_json().get("error", "").lower()

    # ------------------------------------------------------------------
    # Card status and balance guards (~5 tests)
    # ------------------------------------------------------------------

    def test_complete_sale_card_not_found(self, flask_app, db):
        """Money Accounts empty list → 404."""
        app, _ = flask_app
        token = _make_cashier_token("cashier1", "cashier")

        money_ws = _money_ws([])
        db.worksheet.side_effect = _ws_factory(**{"Money Accounts": money_ws})

        client = app.test_client()
        client.set_cookie("jwt_token", token)
        _set_pending(client, _ITEMS, float(_TOTAL))

        resp = client.post(
            "/cashier/api/complete-sale", json={"card_uid": _VALID_UID}
        )

        assert resp.status_code == 404

    def test_complete_sale_invalid_uid_format(self, flask_app, db):
        """card_uid with non-hex characters fails UID_PATTERN → 400."""
        app, _ = flask_app
        token = _make_cashier_token("cashier1", "cashier")
        db.worksheet.return_value.get_all_records.return_value = []

        client = app.test_client()
        client.set_cookie("jwt_token", token)
        _set_pending(client, _ITEMS, float(_TOTAL))

        resp = client.post(
            "/cashier/api/complete-sale", json={"card_uid": _INVALID_UID}
        )

        assert resp.status_code == 400
        assert "invalid" in resp.get_json().get("error", "").lower() or \
               "format" in resp.get_json().get("error", "").lower()

    def test_complete_sale_suspended_card(self, flask_app, db):
        """Card status 'suspended' → 403."""
        app, _ = flask_app
        token = _make_cashier_token("cashier1", "cashier")

        money_ws = _money_ws(
            [{"MoneyCardNumber": _VALID_UID, "Balance": _BALANCE_HIGH, "Status": "suspended"}]
        )
        db.worksheet.side_effect = _ws_factory(**{"Money Accounts": money_ws})

        client = app.test_client()
        client.set_cookie("jwt_token", token)
        _set_pending(client, _ITEMS, float(_TOTAL))

        resp = client.post(
            "/cashier/api/complete-sale", json={"card_uid": _VALID_UID}
        )

        assert resp.status_code == 403

    def test_complete_sale_lost_card(self, flask_app, db):
        """Card status 'lost' → 403."""
        app, _ = flask_app
        token = _make_cashier_token("cashier1", "cashier")

        money_ws = _money_ws(
            [{"MoneyCardNumber": _VALID_UID, "Balance": _BALANCE_HIGH, "Status": "lost"}]
        )
        db.worksheet.side_effect = _ws_factory(**{"Money Accounts": money_ws})

        client = app.test_client()
        client.set_cookie("jwt_token", token)
        _set_pending(client, _ITEMS, float(_TOTAL))

        resp = client.post(
            "/cashier/api/complete-sale", json={"card_uid": _VALID_UID}
        )

        assert resp.status_code == 403

    def test_complete_sale_insufficient_balance(self, flask_app, db):
        """balance=30 < total=50 → 400 with 'Insufficient' in error message."""
        app, _ = flask_app
        token = _make_cashier_token("cashier1", "cashier")

        money_ws = _money_ws(
            [{"MoneyCardNumber": _VALID_UID, "Balance": 30, "Status": "active"}]
        )
        db.worksheet.side_effect = _ws_factory(**{"Money Accounts": money_ws})

        client = app.test_client()
        client.set_cookie("jwt_token", token)
        _set_pending(client, _ITEMS, float(_TOTAL))  # total = 50

        resp = client.post(
            "/cashier/api/complete-sale", json={"card_uid": _VALID_UID}
        )

        assert resp.status_code == 400
        assert "Insufficient" in resp.get_json().get("error", "")

    # ------------------------------------------------------------------
    # Resilience paths (~4 tests)
    # ------------------------------------------------------------------

    def test_complete_sale_offline_fallback(self, flask_app, db):
        """All 3 update_cell retries raise APIError → offline queue path, 200 + offline=True."""
        app, _ = flask_app
        token = _make_cashier_token("cashier1", "cashier")

        # APIError that looks like a 429 rate-limit response
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.headers = {}
        mock_resp.json.return_value = {
            "error": {
                "code": 429,
                "message": "Rate limit exceeded",
                "status": "RESOURCE_EXHAUSTED",
            }
        }
        api_error = gspread.exceptions.APIError(mock_resp)

        money_ws = _money_ws(
            [{"MoneyCardNumber": _VALID_UID, "Balance": _BALANCE_HIGH, "Status": "active"}],
            update_cell_side_effect=api_error,
        )
        db.worksheet.side_effect = _ws_factory(
            **{
                "Money Accounts": money_ws,
                "Transactions Log": MagicMock(),
                "Users": _safe_users_ws(),
            }
        )

        mock_queue = MagicMock()

        with (
            patch("time.sleep"),  # skip 2s / 4s exponential back-off
            patch("offline_queue.get_offline_queue", return_value=mock_queue),
        ):
            client = app.test_client()
            client.set_cookie("jwt_token", token)
            _set_pending(client, _ITEMS, float(_TOTAL))

            resp = client.post(
                "/cashier/api/complete-sale", json={"card_uid": _VALID_UID}
            )

        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get("offline") is True
        # enqueue must have been called with the transaction row
        mock_queue.enqueue.assert_called_once()

    def test_complete_sale_sms_failure_nonfatal(self, flask_app, db):
        """SMS notifier raises → sale still returns 200 (non-fatal)."""
        app, _ = flask_app
        token = _make_cashier_token("cashier1", "cashier")

        money_ws = _money_ws(
            [{"MoneyCardNumber": _VALID_UID, "Balance": _BALANCE_HIGH, "Status": "active"}]
        )
        # Users returns a matching user with a phone number so SMS path is reached
        users_ws = _safe_users_ws(card_uid=_VALID_UID, phone="+639123456789")

        db.worksheet.side_effect = _ws_factory(
            **{
                "Money Accounts": money_ws,
                "Transactions Log": MagicMock(),
                "Users": users_ws,
            }
        )

        # Patch email to succeed (so matched_user stays set for SMS check)
        # Patch SMS to raise so the non-fatal path is exercised.
        # Use patch.dict(sys.modules) because the imports happen via inline
        # sys.path.insert(...) + from X import Y, not through a pre-importable path.
        fake_email_mod = types.ModuleType("email_service")
        fake_email_cls = MagicMock()
        fake_email_cls.return_value.send_receipt.return_value = None
        fake_email_mod.EmailService = fake_email_cls

        fake_notifs_mod = types.ModuleType("notifications")
        fake_notifs_mod.get_sms_notifier = MagicMock(
            side_effect=Exception("SMS service down")
        )

        with patch.dict(
            "sys.modules",
            {"email_service": fake_email_mod, "notifications": fake_notifs_mod},
        ):
            client = app.test_client()
            client.set_cookie("jwt_token", token)
            _set_pending(client, _ITEMS, float(_TOTAL))

            resp = client.post(
                "/cashier/api/complete-sale", json={"card_uid": _VALID_UID}
            )

        # Sale must succeed despite SMS failure
        assert resp.status_code == 200

    def test_complete_sale_blocked_card(self, flask_app, db):
        """Card status 'blocked' → 403 (not active → generic status check)."""
        app, _ = flask_app
        token = _make_cashier_token("cashier1", "cashier")

        money_ws = _money_ws(
            [{"MoneyCardNumber": _VALID_UID, "Balance": _BALANCE_HIGH, "Status": "blocked"}]
        )
        db.worksheet.side_effect = _ws_factory(**{"Money Accounts": money_ws})

        client = app.test_client()
        client.set_cookie("jwt_token", token)
        _set_pending(client, _ITEMS, float(_TOTAL))

        resp = client.post(
            "/cashier/api/complete-sale", json={"card_uid": _VALID_UID}
        )

        assert resp.status_code == 403

    def test_complete_sale_email_failure_nonfatal(self, flask_app, db):
        """Email service raises → sale still returns 200 (non-fatal)."""
        app, _ = flask_app
        token = _make_cashier_token("cashier1", "cashier")

        money_ws = _money_ws(
            [{"MoneyCardNumber": _VALID_UID, "Balance": _BALANCE_HIGH, "Status": "active"}]
        )
        # Users returns matching user — email section runs and fails
        users_ws = _safe_users_ws(card_uid=_VALID_UID, phone="+639000000000")

        db.worksheet.side_effect = _ws_factory(
            **{
                "Money Accounts": money_ws,
                "Transactions Log": MagicMock(),
                "Users": users_ws,
            }
        )

        # Use sys.modules patching so the inline `from email_service import EmailService`
        # picks up our mock without needing email_service to be on sys.path.
        fake_email_mod = types.ModuleType("email_service")
        fake_email_mod.EmailService = MagicMock(side_effect=Exception("SMTP down"))

        with patch.dict("sys.modules", {"email_service": fake_email_mod}):
            client = app.test_client()
            client.set_cookie("jwt_token", token)
            _set_pending(client, _ITEMS, float(_TOTAL))

            resp = client.post(
                "/cashier/api/complete-sale", json={"card_uid": _VALID_UID}
            )

        # Sale must succeed despite email failure
        assert resp.status_code == 200
