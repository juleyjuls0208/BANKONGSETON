"""
Tests for the BANKONGSETON app split (kiosk / tech / dashboard web-only).

These exercise the three deployed Flask apps against an in-memory fake of the
Supabase/Sheets backend (same shape the production code expects), so they run
with no live DATABASE_URL. Run from repo root:

    pytest tests/test_app_split.py -q
"""

import os
import sys
import re
from unittest.mock import MagicMock

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(REPO, "backend")
DASHBOARD = os.path.join(BACKEND, "dashboard")
API = os.path.join(BACKEND, "api")
KIOSK = os.path.join(BACKEND, "kiosk")
TECH = os.path.join(BACKEND, "tech")
for p in (REPO, BACKEND, DASHBOARD, API, KIOSK, TECH):
    if p not in sys.path:
        sys.path.insert(0, p)

# Stub the heavy Supabase client so importing apps does not hit the network.
import sheets_adapter as _sa
_sa_client = MagicMock()
_sa_client.worksheets.return_value = []
_sa_client.add_worksheet.return_value = MagicMock()
_sa_client.worksheet.return_value = MagicMock()
_sa.get_sheets_client = lambda: _sa_client


class FakeSheet:
    """Minimal worksheet stub mirroring gspread/sheets_adapter behaviour."""

    def __init__(self, name, headers, rows):
        self.name = name
        self.id = name  # sheets_adapter worksheet id (used by cache keys)
        self._headers = list(headers)
        self._rows = [dict(r) for r in rows]

    def row_values(self, n):
        if n == 1:
            return list(self._headers)
        row = self._rows[n - 2]
        return [str(row.get(h, "")) for h in self._headers]

    def get_all_records(self):
        return [dict(r) for r in self._rows]

    def append_row(self, values, table_range=None):
        self._rows.append({h: v for h, v in zip(self._headers, values)})

    def update_cell(self, row, col, value):
        if row >= 2:
            self._rows[row - 2][self._headers[col - 1]] = value

    def find(self, header):
        class C:
            pass
        c = C()
        c.col = self._headers.index(header) + 1
        return c

    def batch_update(self, cells):
        for cell in cells:
            m = re.match(r"([A-Z]+)(\d+)", cell["range"])
            col = 0
            for ch in m.group(1):
                col = col * 26 + (ord(ch) - 64)
            self._rows[int(m.group(2)) - 2][self._headers[col - 1]] = cell["values"][0][0]


@pytest.fixture
def fake_db():
    money_row = {
        "MoneyCardNumber": "5F6E7D8C", "LinkedIDCard": "3A2B1C4D",
        "Balance": "500", "Status": "Active", "LastUpdated": "", "TotalLoaded": "1000",
    }
    users = FakeSheet("Users",
        ["StudentID", "Name", "IDCardNumber", "MoneyCardNumber", "StudentEmail", "Status"],
        [{"StudentID": "2024-001", "Name": "Juan", "IDCardNumber": "3A2B1C4D",
          "MoneyCardNumber": "5F6E7D8C", "StudentEmail": "", "Status": "Active"}])
    money = FakeSheet("Money Accounts",
        ["MoneyCardNumber", "LinkedIDCard", "Balance", "Status", "LastUpdated", "TotalLoaded"],
        [dict(money_row)])
    tx = FakeSheet("Transactions Log",
        ["TransactionID", "Timestamp", "StudentID", "MoneyCardNumber", "TransactionType",
         "Amount", "BalanceBefore", "BalanceAfter", "Status", "ErrorMessage"], [])
    lost = FakeSheet("Lost Card Reports",
        ["ReportID", "ReportDate", "StudentID", "OldCardNumber", "NewCardNumber",
         "TransferredBalance", "ReportedBy", "Status"], [])

    sheets = {"Users": users, "Money Accounts": money, "Transactions Log": tx,
              "Lost Card Reports": lost}

    def fake_ws(name, *a, **k):
        return sheets[name]

    import services.loading_service as ls
    ls.get_worksheet_with_retry = fake_ws
    return {"users": users, "money": money, "tx": tx, "lost": lost, "money_row": money_row}


def _set_env():
    os.environ["FLASK_SECRET_KEY"] = "test-secret-key-0123456789abcdef"
    os.environ["JWT_SECRET"] = "test-jwt-secret-0123456789abcdef"
    os.environ["FINANCE_PASSWORD"] = "test-finance-password"
    os.environ["ADMIN_PASSWORD"] = "test-admin-password"
    os.environ["WEB_CONCURRENCY"] = "1"
    os.environ["GUNICORN_WORKERS"] = "1"
    os.environ["KIOSK_UNLOCK_PIN"] = "654321"
    import gspread
    gspread.service_account = lambda **_kwargs: _sa_client


def test_kiosk_card_topup(fake_db):
    """Kiosk: tap money card -> identify -> confirm load credits the balance."""
    _set_env()
    import kiosk_app
    c = kiosk_app.app.test_client()

    assert c.post("/api/kiosk/unlock", json={"pin": "654321"}).status_code == 200
    r = c.post("/api/kiosk/topup/card-scan", json={"uid": "5F6E7D8C"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["success"] is True
    assert body["student"]["student_id"] == "2024-001"

    pending_id = body["pending_id"]
    assert c.post("/api/kiosk/topup/cash-accept", json={"pending_id": pending_id, "amount": 200}).status_code == 200
    r2 = c.post("/api/kiosk/topup/confirm", json={"pending_id": pending_id})
    assert r2.status_code == 200
    assert r2.get_json()["new_balance"] == 700.0
    assert float(fake_db["money"]._rows[0]["Balance"]) == 700.0
    assert len(fake_db["tx"]._rows) == 1


def test_kiosk_cardless_qr_topup(fake_db):
    """Kiosk: scan a student JWT QR -> identify -> confirm load."""
    _set_env()
    import jwt, kiosk_app
    token = jwt.encode(
        {"user_id": "2024-001", "role": "student", "scope": "topup",
         "exp": __import__("datetime").datetime.utcnow() + __import__("datetime").timedelta(minutes=2)},
        os.environ["JWT_SECRET"], algorithm="HS256")

    c = kiosk_app.app.test_client()
    assert c.post("/api/kiosk/unlock", json={"pin": "654321"}).status_code == 200
    r = c.post("/api/kiosk/topup/qr-scan", json={"qr_data": token})
    assert r.status_code == 200
    assert r.get_json()["student"]["student_id"] == "2024-001"

    pending_id = r.get_json()["pending_id"]
    assert c.post("/api/kiosk/topup/cash-accept", json={"pending_id": pending_id, "amount": 100}).status_code == 200
    r2 = c.post("/api/kiosk/topup/confirm", json={"pending_id": pending_id})
    assert r2.status_code == 200
    assert r2.get_json()["new_balance"] == 600.0


def test_kiosk_rejects_bad_qr(fake_db):
    _set_env()
    import kiosk_app
    c = kiosk_app.app.test_client()
    assert c.post("/api/kiosk/unlock", json={"pin": "654321"}).status_code == 200
    r = c.post("/api/kiosk/topup/qr-scan", json={"qr_data": "not-a-real-token"})
    assert r.status_code == 400


def test_kiosk_requires_positive_amount(fake_db):
    _set_env()
    import kiosk_app
    c = kiosk_app.app.test_client()
    assert c.post("/api/kiosk/unlock", json={"pin": "654321"}).status_code == 200
    r = c.post("/api/kiosk/topup/confirm",
                json={"student_id": "2024-001", "amount": 0, "payment_method": "cash"})
    assert r.status_code == 400


def test_tech_app_is_hardware_only(fake_db):
    """Tech app must expose RFID/card-lifecycle routes but NOT finance routes."""
    _set_env()
    import tech_app
    app = tech_app.app
    rules = {r.rule for r in app.url_map.iter_rules()}
    assert "/api/card/start-register" in rules
    assert "/api/card/report-lost" in rules
    assert "/api/serial/connect" in rules
    # finance/dashboard routes must be pruned
    assert "/api/load-balance" not in rules
    assert "/api/students" not in rules
    assert "/api/products" not in rules


def test_dashboard_web_app_is_finance_only(fake_db):
    """Cloud web_app must expose finance routes but NOT serial/RFID routes."""
    _set_env()
    import web_app
    rules = {r.rule for r in web_app.app.url_map.iter_rules()}
    assert "/api/load-balance" in rules
    assert "/api/students" in rules
    assert "/api/products" in rules
    # hardware surface removed
    assert not any("serial" in r for r in rules)
    assert "/api/card/start-register" not in rules


def test_api_topup_qr_endpoint(fake_db):
    """Mobile API mints a cardless top-up QR for an authenticated student."""
    _set_env()
    import api_server
    tok = api_server.generate_jwt_token("2024-001", role="student")
    c = api_server.app.test_client()
    r = c.get("/api/topup/qr", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    body = r.get_json()
    assert "qr_data" in body
    assert body["student_id"] == "2024-001"


def test_web_app_has_no_arduino_or_cashier(fake_db):
    """Cloud dashboard must NOT expose Arduino WiFi, serial, or cashier POS routes."""
    _set_env()
    import dashboard_core as _dc
    _dc.get_sheets_client = lambda: MagicMock()
    import web_app
    rules = {r.rule for r in web_app.app.url_map.iter_rules()}
    assert not any("arduino" in r.lower() for r in rules)
    assert not any("serial" in r.lower() for r in rules)
    # cashier POS blueprint (prefix /cashier) must be gone; only the admin
    # cashier-accounts management page remains
    assert not any(r.startswith("/cashier/") or r == "/cashier" for r in rules)


def test_registration_app_holds_card_tap_routes(fake_db):
    """On-prem registration_app must own the Arduino/serial + card-tap routes
    that were removed from the cloud dashboard."""
    _set_env()
    import dashboard_core as _dc
    _dc.get_sheets_client = lambda: MagicMock()
    import registration_app
    rules = {r.rule for r in registration_app.app.url_map.iter_rules()}
    assert "/api/serial/connect" in rules
    assert "/api/student/register" in rules
    assert "/api/card/link-money" in rules
    assert "/api/card/report-lost" in rules
    assert "/api/card/replace-lost" in rules
    assert "/panel" in rules
    # it must not carry the cloud cashier POS blueprint either
    assert not any(r.startswith("/cashier/") or r == "/cashier" for r in rules)
