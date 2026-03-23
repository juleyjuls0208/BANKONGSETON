from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from flask import Flask

import backend.dashboard.dashboard_core as core


@pytest.fixture
def core_client():
    app = Flask(__name__)
    app.secret_key = "test-dashboard-core"
    socketio = MagicMock()
    core.register_routes(app, socketio)

    client = app.test_client()
    with client.session_transaction() as sess:
        sess["admin_logged_in"] = True
        sess["role"] = "admin"
        sess["admin_username"] = "admin"
    return client


def test_load_balance_writes_to_transactions_log_sheet(monkeypatch, core_client):
    money_ws = MagicMock()
    money_ws.id = 101
    money_ws.get_all_records.return_value = [
        {
            "MoneyCardNumber": "5F6E7D8C",
            "Balance": "500",
            "TotalLoaded": "1000",
            "Status": "Active",
        }
    ]

    header_cols = {"Balance": 3, "TotalLoaded": 6, "LastUpdated": 5}
    money_ws.find.side_effect = lambda header: SimpleNamespace(col=header_cols[header])

    users_ws = MagicMock()
    users_ws.get_all_records.return_value = [
        {
            "StudentID": "2024-001",
            "Name": "Juan dela Cruz",
            "MoneyCardNumber": "5F6E7D8C",
            "ParentEmail": "",
        }
    ]

    transactions_log_ws = MagicMock()

    def fake_get_ws(name, *args, **kwargs):
        if name == "Users":
            return users_ws
        if name == "Money Accounts":
            return money_ws
        if name == "Transactions Log":
            return transactions_log_ws
        raise AssertionError(f"Unexpected worksheet requested: {name}")

    monkeypatch.setattr(core, "get_worksheet_with_retry", fake_get_ws)

    resp = core_client.post(
        "/api/load-balance",
        json={"student_id": "2024-001", "amount": 150.0, "payment_method": "cash"},
    )

    assert resp.status_code == 200
    transactions_log_ws.append_row.assert_called_once()


def test_get_transactions_reads_transactions_log_sheet(monkeypatch, core_client):
    transactions_log_ws = MagicMock()
    transactions_log_ws.get_all_records.return_value = [
        {
            "TransactionID": "TXN-001",
            "Timestamp": "2026-03-20 12:00:00",
            "StudentID": "2024-001",
            "TransactionType": "Load",
            "Amount": 100.0,
        }
    ]

    def fake_get_ws(name, *args, **kwargs):
        if name == "Transactions Log":
            return transactions_log_ws
        raise AssertionError(f"Unexpected worksheet requested: {name}")

    monkeypatch.setattr(core, "get_worksheet_with_retry", fake_get_ws)

    resp = core_client.get("/api/transactions?limit=1")

    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["transactions"][0]["TransactionID"] == "TXN-001"
