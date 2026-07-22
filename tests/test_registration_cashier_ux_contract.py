"""Small regression checks for the operator-facing registration and POS flows."""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

from backend.cashier_app.offline_queue import SQLiteWriteQueue


ROOT = Path(__file__).resolve().parents[1]
REGISTRATION_TEMPLATE = ROOT / "backend" / "dashboard" / "templates" / "registration.html"
CASHIER_TEMPLATE = ROOT / "backend" / "cashier_app" / "templates" / "cashier_index.html"
DASHBOARD_TEMPLATE = ROOT / "backend" / "dashboard" / "templates" / "dashboard.html"
BASE_TEMPLATE = ROOT / "backend" / "dashboard" / "templates" / "base.html"
CASHIER_LOGIN_TEMPLATE = ROOT / "backend" / "dashboard" / "cashier" / "templates" / "cashier_login.html"
CASHIER_PANEL_CSS = ROOT / "backend" / "cashier_app" / "static" / "css" / "panel.css"
REGISTRATION_APP = ROOT / "backend" / "dashboard" / "registration_app.py"


def test_registration_only_shows_success_after_the_submit_response():
    content = REGISTRATION_TEMPLATE.read_text(encoding="utf-8")

    assert 'class="reg-step" data-step="2" id="registerForm" hidden' in content
    assert 'class="reg-step reg-success" data-step="3" hidden' in content
    assert "if (res.ok)" in content
    assert "setStep(3);" in content


class _CardlessExistingStudentSheet:
    def __init__(self):
        self.records = [{
            "StudentID": "201420029",
            "Name": "Ivan Gabriel Lara",
            "IDCardNumber": None,
            "MoneyCardNumber": None,
            "Status": "Inactive",
        }]
        self.updated = []
        self.appended = []

    def get_all_records(self):
        return self.records

    def update_where(self, column, value, set_column, set_value):
        self.updated.append((column, value, set_column, set_value))
        for record in self.records:
            if str(record.get(column, "")) == str(value):
                record[set_column] = set_value
        return 1

    def append_row(self, row):
        self.appended.append(row)


def test_registration_reactivates_an_existing_student_without_an_id_card(monkeypatch):
    import sys

    dashboard_dir = str(ROOT / "backend" / "dashboard")
    if dashboard_dir not in sys.path:
        sys.path.insert(0, dashboard_dir)
    import registration_app

    users_sheet = _CardlessExistingStudentSheet()
    monkeypatch.setattr(registration_app, "get_worksheet_with_retry", lambda name: users_sheet)
    monkeypatch.setattr(registration_app.socketio, "emit", lambda *args, **kwargs: None)
    monkeypatch.setattr(registration_app, "send_success", lambda *args, **kwargs: None)

    client = registration_app.app.test_client()
    with client.session_transaction() as session:
        session["admin_logged_in"] = True
        session["role"] = "admin"

    response = client.post("/api/student/register", json={
        "student_id": "201420029",
        "name": "Ivan Gabriel Lara",
        "id_card_uid": "03916831",
        "parent_email": "ivan@example.test",
    })

    assert response.status_code == 200
    assert response.get_json() == {"success": True}
    assert users_sheet.appended == []
    assert ("StudentID", "201420029", "IDCardNumber", "03916831") in users_sheet.updated
    assert ("StudentID", "201420029", "Status", "Active") in users_sheet.updated


class _MoneyLinkUsersSheet:
    def __init__(self):
        self.records = [
            {"StudentID": "eligible", "Name": "Ready Student", "Status": "Active", "IDCardNumber": "A1B2C3D4", "MoneyCardNumber": None},
            {"StudentID": "no-id", "Name": "Cardless Student", "Status": "Active", "IDCardNumber": None, "MoneyCardNumber": None},
            {"StudentID": "inactive", "Name": "Inactive Student", "Status": "Inactive", "IDCardNumber": "B1C2D3E4", "MoneyCardNumber": None},
            {"StudentID": "already-linked", "Name": "Linked Student", "Status": "Active", "IDCardNumber": "C1D2E3F4", "MoneyCardNumber": "D1E2F3A4"},
        ]
        self.updated = []

    def get_all_records(self):
        return self.records

    def update_where(self, column, value, set_column, set_value):
        matches = [r for r in self.records if str(r.get(column, "")) == str(value)]
        for record in matches:
            record[set_column] = set_value
        self.updated.append((column, value, set_column, set_value))
        return len(matches)


class _MoneyLinkAccountsSheet:
    def __init__(self):
        self.records = []
        self.appended = []

    def get_all_records(self):
        return self.records

    def append_row(self, row):
        self.appended.append(row)


def test_money_card_link_only_allows_active_students_with_id_cards(monkeypatch):
    import sys

    dashboard_dir = str(ROOT / "backend" / "dashboard")
    if dashboard_dir not in sys.path:
        sys.path.insert(0, dashboard_dir)
    import registration_app

    users_sheet = _MoneyLinkUsersSheet()
    money_sheet = _MoneyLinkAccountsSheet()
    monkeypatch.setattr(
        registration_app,
        "get_worksheet_with_retry",
        lambda name: users_sheet if name == "Users" else money_sheet,
    )
    monkeypatch.setattr(registration_app.socketio, "emit", lambda *args, **kwargs: None)
    monkeypatch.setattr(registration_app, "send_success", lambda *args, **kwargs: None)

    client = registration_app.app.test_client()
    with client.session_transaction() as session:
        session["admin_logged_in"] = True
        session["role"] = "admin"

    response = client.get("/api/students/without-cards")
    assert response.status_code == 200
    assert response.get_json()["students"] == [{"student_id": "eligible", "name": "Ready Student", "status": "Active"}]

    registration_app.pending_student_id = "eligible"
    registration_app.handle_money_card("65D7FD5C")

    assert users_sheet.updated == [("StudentID", "eligible", "MoneyCardNumber", "65D7FD5C")]
    assert money_sheet.appended and money_sheet.appended[0][0] == "65D7FD5C"


def test_signed_offline_recovery_rejects_tampered_ledger(tmp_path):
    queue = SQLiteWriteQueue(tmp_path / "offline_queue.db", signing_key=b"test-signing-key")
    queue.enqueue_transaction_log("TXN-TEST-1", ["TXN-TEST-1", "2026-07-19", "S1", "CARD", "Purchase", 50])

    with sqlite3.connect(queue.db_path) as conn:
        conn.execute("UPDATE write_queue SET data=?", ('["FORGED"]',))

    worksheet = MagicMock()
    worksheet.get_all_records.return_value = []
    db = MagicMock()
    db.worksheet.return_value = worksheet

    synced, failed = queue.process_queue(db)

    assert (synced, failed) == (0, 1)
    worksheet.append_row.assert_not_called()


def test_signed_recovery_syncs_once_when_the_server_returns(tmp_path):
    queue = SQLiteWriteQueue(tmp_path / "recovery.db", signing_key=b"test-signing-key")
    queue.enqueue_transaction_log("TXN-TEST-2", ["TXN-TEST-2", "2026-07-19", "S1", "CARD", "Purchase", 50])
    worksheet = MagicMock()
    worksheet.get_all_records.return_value = []
    db = MagicMock()
    db.worksheet.return_value = worksheet

    assert queue.process_queue(db) == (1, 0)
    assert queue.process_queue(db) == (0, 0)
    worksheet.append_row.assert_called_once()
    assert queue.get_status()["pending"] == 0
    assert queue.get_status()["synced"] == 1


def test_operator_templates_do_not_show_fake_student_or_dead_navigation():
    cashier = CASHIER_TEMPLATE.read_text(encoding="utf-8")
    dashboard = DASHBOARD_TEMPLATE.read_text(encoding="utf-8")
    registration_source = REGISTRATION_APP.read_text(encoding="utf-8")

    assert "Gabriel Santos" not in cashier
    assert "Cashier #042" not in cashier
    assert 'href="#" class="nav-link"' not in cashier
    assert "endpoint('/queue/sync')" in cashier
    assert "function setSaleInProgress" in cashier
    assert "if (saleInProgress) return;" in cashier
    assert "seededQty" not in cashier
    assert "Quick actions" in dashboard
    assert "host='127.0.0.1'" in registration_source


def test_dashboard_and_cashier_present_only_the_requested_operator_controls():
    dashboard = DASHBOARD_TEMPLATE.read_text(encoding="utf-8")
    base = BASE_TEMPLATE.read_text(encoding="utf-8")
    cashier = CASHIER_TEMPLATE.read_text(encoding="utf-8")
    login = CASHIER_LOGIN_TEMPLATE.read_text(encoding="utf-8")

    for removed in ("Generate Report", "Settings", "Card Registration", "System Live: Branch 001", "Type to search", "Results appear here."):
        assert removed not in base + dashboard
    assert "Bangko <span>ng Seton</span>" in base
    assert "topbar-search" not in base
    assert "sidebar-brand-icon" not in base

    for removed in ("SERIAL:", "SYNC:", "SCANNER: READY", "Station 04", "Close Shift", "Subtotal", "Tax (VAT 12%)", "Total Ledger", "tapDisabledReason", "WALLET BALANCE"):
        assert removed not in cashier
    assert "{{ user.display_name or user.username or 'Cashier' }}" in cashier
    assert "ID: {{ user.username or 'Cashier' }}" in cashier
    assert "function updateWifiBadge(data, endpointReachable = false)" in cashier
    assert "Boolean(endpointReachable && data && data.online === true)" in cashier
    assert "Cashier terminal" in login
    assert 'href="/static/css/panel.css"' in login
    assert CASHIER_PANEL_CSS.is_file()


def _cashier_test_client(monkeypatch, standalone=False):
    """Register a production cashier blueprint without the unrelated dashboard app."""
    import jwt
    from datetime import datetime
    from flask import Flask
    if standalone:
        from backend.cashier_app import cashier_routes as routes
    else:
        from backend.dashboard.cashier import cashier_routes as routes

    routes.JWT_SECRET = "cashier-contract-test-secret"
    monkeypatch.setattr(routes, "_get_philippines_time", lambda: datetime(2026, 7, 19, 9, 0, 0))
    app = Flask(__name__)
    app.secret_key = "cashier-contract-test-secret"
    app.socketio = MagicMock()
    app.register_blueprint(routes.cashier_bp)
    token = jwt.encode({"username": "cashier", "role": "cashier"}, routes.JWT_SECRET, algorithm="HS256")
    return app.test_client(), routes, token


def _retryable_api_error():
    from unittest.mock import MagicMock
    import gspread

    response = MagicMock()
    response.status_code = 429
    response.headers = {}
    response.json.return_value = {"error": {"code": 429, "message": "temporary outage"}}
    return gspread.exceptions.APIError(response)


def _cashier_db(money_sheet, transaction_sheet):
    db = MagicMock()
    users_sheet = MagicMock()
    users_sheet.get_all_records.return_value = []
    db.worksheet.side_effect = {
        "Money Accounts": money_sheet,
        "Transactions Log": transaction_sheet,
        "Users": users_sheet,
    }.get
    return db


def _seed_pending_sale(client):
    with client.session_transaction() as session:
        session["pending_transaction"] = {"items": [{"name": "Snack", "price": 50, "qty": 1}], "total": 50}


def test_cashier_refuses_an_unconfirmed_offline_debit(monkeypatch):
    for standalone in (False, True):
        client, routes, token = _cashier_test_client(monkeypatch, standalone=standalone)
        money_sheet = MagicMock()
        money_sheet.update_balance_atomic = None
        money_sheet.get_all_records.return_value = [{"MoneyCardNumber": "5F6E7D8C", "Balance": 500, "Status": "active"}]
        money_sheet.update_cell.side_effect = _retryable_api_error()
        transaction_sheet = MagicMock()
        transaction_sheet.row_values.return_value = ["TransactionID"]
        monkeypatch.setattr(routes, "_get_sheets_client", lambda: _cashier_db(money_sheet, transaction_sheet))
        _seed_pending_sale(client)
        client.set_cookie("jwt_token", token)

        response = client.post("/cashier/api/complete-sale", json={"card_uid": "5F6E7D8C"})

        assert response.status_code == 503
        assert "not completed" in response.get_json()["error"].lower()


def test_cashier_queues_only_a_signed_receipt_after_a_confirmed_debit(monkeypatch):
    import sys
    from backend import offline_queue as dashboard_queue
    from backend.cashier_app import offline_queue as standalone_queue

    for standalone, queue_module in ((False, dashboard_queue), (True, standalone_queue)):
        client, routes, token = _cashier_test_client(monkeypatch, standalone=standalone)
        money_sheet = MagicMock()
        money_sheet.update_balance_atomic = None
        money_sheet.get_all_records.return_value = [{"MoneyCardNumber": "5F6E7D8C", "Balance": 500, "Status": "active"}]
        transaction_sheet = MagicMock()
        transaction_sheet.row_values.return_value = ["TransactionID"]
        transaction_sheet.append_row.side_effect = _retryable_api_error()
        monkeypatch.setattr(routes, "_get_sheets_client", lambda: _cashier_db(money_sheet, transaction_sheet))
        recovery_queue = MagicMock()
        monkeypatch.setattr(queue_module, "get_offline_queue", lambda: recovery_queue)
        monkeypatch.setitem(sys.modules, "offline_queue", queue_module)
        _seed_pending_sale(client)
        client.set_cookie("jwt_token", token)

        response = client.post("/cashier/api/complete-sale", json={"card_uid": "5F6E7D8C"})

        assert response.status_code == 200
        assert response.get_json()["ledger_pending"] is True
        recovery_queue.enqueue_transaction_log.assert_called_once()
        assert money_sheet.update_cell.call_count == 1
