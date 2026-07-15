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
        ["StudentID", "Name", "IDCardNumber", "MoneyCardNumber", "Status", "ParentEmail"],
        [
            {"StudentID": "202501", "Name": "Juan Dela Cruz", "IDCardNumber": "ID001",
             "MoneyCardNumber": "A1B2C3D4", "Status": "Active",
             "ParentEmail": "parent@example.com"},
            {"StudentID": "202502", "Name": "Maria Santos", "IDCardNumber": "ID002",
             "MoneyCardNumber": "E5F6G7H8", "Status": "Active",
             "ParentEmail": "maria.parent@example.com",
             "PinHash": hashlib.sha256(b"1234").hexdigest(), "DeviceID": "PHONE-ALPHA"},
        ],
    )
    db.add_sheet(
        "Money Accounts",
        ["MoneyCardNumber", "Status"],
        [{"MoneyCardNumber": "A1B2C3D4", "Status": "active"},
         {"MoneyCardNumber": "E5F6G7H8", "Status": "active"}],
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


def test_new_user_first_login_sets_pin_and_binds_device(app):
    client = app.test_client()
    r = post(client, "/api/auth/login", {"student_id": "202501", "device_id": "PHONE-NEW"})
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["needs_pin_setup"] is True
    assert body["device_bound"] is False
    assert body["pin_required"] is False

    # Create PIN
    r2 = post(client, "/api/auth/pin-verify",
              {"student_id": "202501", "device_id": "PHONE-NEW", "new_pin": "1234"})
    assert r2.status_code == 200, r2.get_json()
    tok = r2.get_json()["token"]
    assert tok

    # PinHash + DeviceID persisted on the Users row
    users = app._test_db.worksheet("Users")
    row = [x for x in users.get_all_records() if x["StudentID"] == "202501"][0]
    assert row.get("PinHash") and row.get("DeviceID") == "PHONE-NEW"


def test_existing_user_must_supply_pin(app):
    client = app.test_client()
    r = post(client, "/api/auth/login", {"student_id": "202502", "device_id": "PHONE-ALPHA"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["needs_pin_setup"] is False
    assert body["pin_required"] is True

    # Wrong PIN rejected
    bad = post(client, "/api/auth/pin-verify",
               {"student_id": "202502", "device_id": "PHONE-ALPHA", "pin": "0000"})
    assert bad.status_code == 401

    # Correct PIN issues token
    ok = post(client, "/api/auth/pin-verify",
              {"student_id": "202502", "device_id": "PHONE-ALPHA", "pin": "1234"})
    assert ok.status_code == 200, ok.get_json()


def test_device_conflict_rejects_second_phone(app):
    client = app.test_client()
    r = post(client, "/api/auth/login", {"student_id": "202502", "device_id": "PHONE-BETA"})
    assert r.status_code == 423
    assert r.get_json().get("code") == "DEVICE_CONFLICT"


def test_pin_change_via_email_code(app):
    import api_server as srv
    client = app.test_client()
    # request change (must supply current PIN)
    req = post(client, "/api/auth/pin-change-request",
               {"student_id": "202502", "device_id": "PHONE-ALPHA", "pin": "1234"})
    assert req.status_code == 200, req.get_json()
    # code is stored server-side regardless of email delivery
    assert "202502" in srv._pin_change_codes, "no pending code stored"
    code = srv._pin_change_codes["202502"]["code"]
    assert code and len(code) == 6

    # confirm with code + new pin
    conf = post(client, "/api/auth/pin-change-confirm",
                {"student_id": "202502", "device_id": "PHONE-ALPHA",
                 "code": code, "new_pin": "5678"})
    assert conf.status_code == 200, conf.get_json()

    # old pin no longer works
    old = post(client, "/api/auth/pin-verify",
               {"student_id": "202502", "device_id": "PHONE-ALPHA", "pin": "1234"})
    assert old.status_code == 401
