"""
C3 smoke test — student login hardening (PIN + single-device binding).

The Google Sheets / SMTP layers are stubbed so we exercise the auth logic in
isolation. Run from repo root:  pytest backend/tests/test_c3_auth.py -q
"""
import sys
import os
import types
import hashlib

import pytest
from werkzeug.security import generate_password_hash

# ── Stub the heavy, network-dependent dependencies BEFORE importing api_server ──
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API = os.path.join(REPO, "api")
for p in (REPO, API):
    if p not in sys.path:
        sys.path.insert(0, p)

# Fake Sheets "worksheet" storing rows as dicts keyed by header.
class FakeSheet:
    def __init__(self, name, headers, rows):
        self.name = name
        self._headers = list(headers)
        self._rows = [dict(r) for r in rows]

    def row_values(self, n):
        if n == 1:
            return list(self._headers)
        row = self._rows[n - 2]
        return [str(row.get(h, "")) for h in self._headers]

    def get_all_records(self):
        return [dict(r) for r in self._rows]

    def append_row(self, values):
        self._rows.append({h: v for h, v in zip(self._headers, values)})

    def update_cell(self, row, col, value):
        if row == 1:
            # header add
            if col == len(self._headers) + 1:
                self._headers.append(value)
            return
        h = self._headers[col - 1]
        self._rows[row - 2][h] = value

    def worksheet(self, name):
        raise Exception("use db.worksheet via registry")


class FakeDB:
    def __init__(self):
        self._sheets = {}

    def add_sheet(self, name, headers, rows):
        self._sheets[name] = FakeSheet(name, headers, rows)

    def worksheet(self, name):
        if name not in self._sheets:
            raise KeyError(name)
        return self._sheets[name]

    def worksheets(self):
        return list(self._sheets.values())


@pytest.fixture
def app(monkeypatch):
    # Build a fake DB with a Users sheet (no PinHash/DeviceID columns yet).
    db = FakeDB()
    db.add_sheet(
        "Users",
        ["StudentID", "Name", "IDCardNumber", "MoneyCardNumber", "Status", "StudentEmail"],
        [
            {"StudentID": "202501", "Name": "Juan Dela Cruz", "IDCardNumber": "ID001",
             "MoneyCardNumber": "A1B2C3D4", "Status": "Active",
             "StudentEmail": "parent@example.com"},
            {"StudentID": "202502", "Name": "Maria Santos", "IDCardNumber": "ID002",
             "MoneyCardNumber": "E5F6G7H8", "Status": "Active",
             "StudentEmail": "maria.parent@example.com",
             "PinHash": hashlib.sha256(b"1234").hexdigest(), "DeviceID": "PHONE-ALPHA"},
        ],
    )
    db.add_sheet(
        "Money Accounts",
        ["MoneyCardNumber", "Status"],
        [{"MoneyCardNumber": "A1B2C3D4", "Status": "active"},
         {"MoneyCardNumber": "E5F6G7H8", "Status": "active"}],
    )

    db.add_sheet(
        "student_auth",
        ["StudentID", "PinHash", "DeviceId", "UpdatedAt"],
        [{"StudentID": "202502", "PinHash": generate_password_hash("1234"),
          "DeviceId": "PHONE-ALPHA", "UpdatedAt": ""}],
    )

    fake_sheets_mod = types.ModuleType("sheets_adapter")
    fake_sheets_mod.APIError = Exception
    fake_sheets_mod.SpreadsheetNotFound = Exception
    fake_sheets_mod.WorksheetNotFound = Exception
    fake_sheets_mod.get_sheets_client = lambda: db

    cache_mod = types.ModuleType("cache")
    cache_mod.get_cached = lambda k: None
    cache_mod.set_cached = lambda *a, **k: None
    cache_mod.invalidate_cached = lambda *a, **k: None
    cache_mod.invalidate_pattern = lambda *a, **k: None

    notifications_mod = types.ModuleType("notifications")
    class _EmailNotifier:
        enabled = True
        sent = []
        def send_email(self, to_email, subject, body, html_body=None):
            import re as _re
            m = _re.search(r"(\d{6})", body)
            _EmailNotifier.sent.append((to_email, m.group(1) if m else None))
            return True
    notifications_mod.EmailNotifier = _EmailNotifier
    notifications_mod.TwilioSMSNotifier = None

    monkeypatch.setitem(sys.modules, "sheets_adapter", fake_sheets_mod)
    monkeypatch.setitem(sys.modules, "cache", cache_mod)
    monkeypatch.setitem(sys.modules, "notifications", notifications_mod)

    monkeypatch.setenv("JWT_SECRET", "test-secret-not-default")
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret-key-not-default")

    import api_server
    api_server.db = db
    api_server._get_sheets_client = lambda: db
    api_server.get_sheets_client = lambda: db
    # expose db for assertions
    app = api_server.app
    app._test_db = db
    app.config.update(TESTING=True)
    return app


def post(client, path, json=None, headers=None):
    return client.post(path, json=json, headers=headers or {})


def test_first_login_sets_pin_and_device(app):
    client = app.test_client()
    first = post(
        client,
        "/api/auth/login",
        {"student_id": "202501", "device_id": "PHONE-NEW", "pin": "1234"},
    )
    assert first.status_code == 200, first.get_json()
    assert first.get_json()["first_login"] is True

    returning = post(
        client,
        "/api/auth/login",
        {"student_id": "202501", "device_id": "PHONE-NEW", "pin": "1234"},
    )
    assert returning.status_code == 200, returning.get_json()
    assert returning.get_json()["first_login"] is False


def test_existing_user_must_supply_pin(app):
    client = app.test_client()
    r = post(client, "/api/auth/login", {"student_id": "202502", "device_id": "PHONE-ALPHA", "pin": "1234"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["first_login"] is False
    assert body["jwt_token"]


def test_device_conflict_rejects_second_phone(app):
    client = app.test_client()
    r = post(client, "/api/auth/login", {"student_id": "202502", "device_id": "PHONE-BETA", "pin": "1234"})
    assert r.status_code == 401
    assert r.get_json().get("error") == "Invalid credentials"


def test_pin_status_does_not_enumerate_accounts(app):
    client = app.test_client()
    response = post(client, "/api/auth/pin-status", {"student_id": "does-not-exist"})
    assert response.status_code == 200
    assert response.get_json() == {"available": True}


def test_database_outage_returns_service_unavailable(app, monkeypatch):
    import api_server
    from psycopg2 import DatabaseError

    def fail_records(*_args, **_kwargs):
        raise DatabaseError("database connection timed out")

    monkeypatch.setattr(api_server, "get_sheet_records_cached", fail_records)
    response = post(
        app.test_client(),
        "/api/auth/login",
        {"student_id": "202501", "pin": "1234", "device_id": "PHONE-NEW"},
    )

    assert response.status_code == 503
    assert response.get_json() == {"error": "Service unavailable, please try again"}
