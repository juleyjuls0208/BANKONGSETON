"""M008/S01 backend budget contract verification tests."""

from __future__ import annotations

import importlib.util
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import gspread
import pytz
import pytest


API_SERVER_PATH = Path("backend/api/api_server.py").resolve()
PH_TZ = pytz.timezone("Asia/Manila")


@dataclass
class InMemoryBudgetSheet:
    """Minimal worksheet double that supports row_values/get_all_records/append/update."""

    headers: list[str]

    def __post_init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self.append_row = MagicMock(side_effect=self._append_row)
        self.update = MagicMock(side_effect=self._update)
        self.row_values = MagicMock(side_effect=self._row_values)
        self.get_all_records = MagicMock(side_effect=self._get_all_records)

    def _row_values(self, index: int) -> list[str]:
        return self.headers[:] if index == 1 else []

    def _get_all_records(self) -> list[dict[str, Any]]:
        return [record.copy() for record in self.records]

    def _append_row(self, values: list[Any], table_range: str | None = None) -> None:
        row = [values[i] if i < len(values) else "" for i in range(len(self.headers))]
        if [str(v).strip() for v in row] == self.headers:
            return
        self.records.append({self.headers[i]: row[i] for i in range(len(self.headers))})

    def _update(self, range_name: str, values: list[list[Any]]) -> None:
        # Format is always expected to be A{row}:D{row} in this contract.
        row_anchor = range_name.split(":", 1)[0]
        row_index = int(row_anchor[1:])
        record_index = row_index - 2
        payload = values[0]
        updated = {self.headers[i]: payload[i] for i in range(len(self.headers))}
        self.records[record_index] = updated


@pytest.fixture
def budget_api_module(monkeypatch):
    """Load backend/api/api_server.py with gspread mocked before import."""
    monkeypatch.setenv("GOOGLE_SHEETS_ID", "test-google-sheet-id")

    users_sheet = MagicMock()
    users_sheet.get_all_records.return_value = [
        {
            "StudentID": "2024-001",
            "Name": "Test Student",
            "MoneyCardNumber": "5F6E7D8C",
        }
    ]

    budget_sheet = InMemoryBudgetSheet(
        headers=["StudentID", "MonthlyLimit", "YearMonth", "UpdatedAt"]
    )

    transactions_sheet = MagicMock()
    transactions_sheet.get_all_records.return_value = []

    spreadsheet = MagicMock()
    state = {"budget_sheet_exists": False}

    def worksheet_side_effect(name: str):
        if name == "Users":
            return users_sheet
        if name == "Student Budgets":
            if not state["budget_sheet_exists"]:
                raise gspread.exceptions.WorksheetNotFound("Student Budgets")
            return budget_sheet
        if name == "Transactions Log":
            return transactions_sheet
        raise gspread.exceptions.WorksheetNotFound(name)

    def add_worksheet_side_effect(*, title: str, rows: int, cols: int):
        assert title == "Student Budgets"
        assert rows >= 1
        assert cols >= 4
        state["budget_sheet_exists"] = True
        return budget_sheet

    spreadsheet.worksheet.side_effect = worksheet_side_effect
    spreadsheet.add_worksheet.side_effect = add_worksheet_side_effect

    service_client = MagicMock()
    service_client.open_by_key.return_value = spreadsheet

    module_name = f"test_api_server_m008_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, API_SERVER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)

    with patch("gspread.service_account", return_value=service_client):
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

    fixed_now = PH_TZ.localize(datetime(2026, 3, 24, 9, 30, 0))
    module.get_philippines_time = lambda: fixed_now
    module.db = spreadsheet
    module.get_sheets_client = lambda: spreadsheet
    module.active_sessions.clear()

    cache_store: dict[str, Any] = {}
    module.get_cached = lambda key: cache_store.get(key)

    def set_cached(key: str, value: Any, ttl: int = 30) -> None:
        cache_store[key] = value

    def invalidate_cached(key: str) -> None:
        cache_store.pop(key, None)

    def invalidate_pattern(pattern: str) -> None:
        for key in list(cache_store.keys()):
            if pattern in key:
                cache_store.pop(key, None)

    module.set_cached = set_cached
    module.invalidate_cached = invalidate_cached
    module.invalidate_pattern = invalidate_pattern

    module.app.config["TESTING"] = True

    yield {
        "module": module,
        "client": module.app.test_client(),
        "users_sheet": users_sheet,
        "budget_sheet": budget_sheet,
        "transactions_sheet": transactions_sheet,
        "spreadsheet": spreadsheet,
        "state": state,
    }

    sys.modules.pop(module_name, None)


def _auth_headers(module, student_id: str = "2024-001") -> dict[str, str]:
    token = f"token-{student_id}"
    module.active_sessions[token] = {
        "student_id": student_id,
        "card_number": "ID-CARD-001",
        "login_time": time.time(),
    }
    return {"Authorization": f"Bearer {token}"}


def test_student_budget_unauthorized_returns_401(budget_api_module):
    client = budget_api_module["client"]

    get_resp = client.get("/api/student/budget")
    post_resp = client.post("/api/student/budget", json={"monthly_limit": 1200})

    assert get_resp.status_code == 401
    assert post_resp.status_code == 401
    assert "Invalid or expired token" in get_resp.get_json()["error"]


def test_student_budget_create_read_update_flow_upserts_single_row_per_month(budget_api_module):
    module = budget_api_module["module"]
    client = budget_api_module["client"]
    budget_sheet = budget_api_module["budget_sheet"]
    state = budget_api_module["state"]

    headers = _auth_headers(module)

    initial_get = client.get("/api/student/budget", headers=headers)
    assert initial_get.status_code == 200
    assert initial_get.get_json()["monthly_limit"] is None
    assert initial_get.get_json()["year_month"] == "2026-03"
    assert state["budget_sheet_exists"] is True

    create_resp = client.post(
        "/api/student/budget",
        headers=headers,
        json={"monthly_limit": 1200},
    )
    assert create_resp.status_code == 200
    assert create_resp.get_json()["success"] is True
    assert create_resp.get_json()["monthly_limit"] == 1200.0

    read_after_create = client.get("/api/student/budget", headers=headers)
    assert read_after_create.status_code == 200
    assert read_after_create.get_json()["monthly_limit"] == 1200.0

    update_resp = client.post(
        "/api/student/budget",
        headers=headers,
        json={"monthly_limit": 1750.25},
    )
    assert update_resp.status_code == 200
    assert update_resp.get_json()["monthly_limit"] == 1750.25

    read_after_update = client.get("/api/student/budget", headers=headers)
    assert read_after_update.status_code == 200
    assert read_after_update.get_json()["monthly_limit"] == 1750.25

    assert len(budget_sheet.records) == 1, "Upsert must not create duplicate month rows"
    assert budget_sheet.records[0]["StudentID"] == "2024-001"
    assert budget_sheet.records[0]["YearMonth"] == "2026-03"


def test_student_budget_unavailable_returns_503_when_sheet_read_fails(budget_api_module):
    module = budget_api_module["module"]
    client = budget_api_module["client"]
    budget_sheet = budget_api_module["budget_sheet"]
    state = budget_api_module["state"]

    state["budget_sheet_exists"] = True
    budget_sheet.get_all_records.side_effect = ConnectionError("sheet backend down")

    headers = _auth_headers(module)
    resp = client.get("/api/student/budget", headers=headers)

    assert resp.status_code == 503
    assert "Service unavailable" in resp.get_json()["error"]


def test_student_budget_malformed_monthly_limit_row_is_nonfatal_and_returns_none(budget_api_module):
    module = budget_api_module["module"]
    client = budget_api_module["client"]
    budget_sheet = budget_api_module["budget_sheet"]
    state = budget_api_module["state"]

    state["budget_sheet_exists"] = True
    budget_sheet.records.append(
        {
            "StudentID": "2024-001",
            "MonthlyLimit": "abc-not-a-number",
            "YearMonth": "2026-03",
            "UpdatedAt": "2026-03-24 09:00:00",
        }
    )

    headers = _auth_headers(module)
    resp = client.get("/api/student/budget", headers=headers)

    assert resp.status_code == 200
    assert resp.get_json()["monthly_limit"] is None


def test_student_budget_missing_money_card_binding_returns_404(budget_api_module):
    module = budget_api_module["module"]
    client = budget_api_module["client"]
    users_sheet = budget_api_module["users_sheet"]

    users_sheet.get_all_records.return_value = [
        {
            "StudentID": "2024-001",
            "Name": "No Card Student",
            "MoneyCardNumber": "",
        }
    ]

    headers = _auth_headers(module)
    resp = client.get("/api/student/budget", headers=headers)

    assert resp.status_code == 404
    assert "No money card registered" in resp.get_json()["error"]


def test_budget_summary_returns_current_month_completed_spend_total(budget_api_module):
    module = budget_api_module["module"]
    client = budget_api_module["client"]
    transactions_sheet = budget_api_module["transactions_sheet"]

    transactions_sheet.get_all_records.return_value = [
        {
            "TransactionID": "TXN-001",
            "Timestamp": "2026-03-03 08:00:00",
            "MoneyCardNumber": "00005f6e7d8c",
            "TransactionType": "Purchase",
            "Status": "Completed",
            "Amount": "120.5",
        },
        {
            "TransactionID": "TXN-002",
            "Timestamp": "2026-03-11 18:30:00",
            "MoneyCardNumber": "5F6E7D8C",
            "TransactionType": "NFC Purchase",
            "Status": "Completed",
            "Amount": "79.5",
        },
        {
            "TransactionID": "TXN-003",
            "Timestamp": "2026-03-12 09:00:00",
            "MoneyCardNumber": "5F6E7D8C",
            "TransactionType": "Top Up",
            "Status": "Completed",
            "Amount": "1000",
        },
        {
            "TransactionID": "TXN-004",
            "Timestamp": "2026-03-18 09:15:00",
            "MoneyCardNumber": "5F6E7D8C",
            "TransactionType": "Purchase",
            "Status": "Failed",
            "Amount": "400",
        },
        {
            "TransactionID": "TXN-005",
            "Timestamp": "2026-02-28 23:59:59",
            "MoneyCardNumber": "5F6E7D8C",
            "TransactionType": "Purchase",
            "Status": "Completed",
            "Amount": "300",
        },
        {
            "TransactionID": "TXN-006",
            "Timestamp": "2026-03-06 11:00:00",
            "MoneyCardNumber": "12345678",
            "TransactionType": "Purchase",
            "Status": "Completed",
            "Amount": "999",
        },
    ]

    headers = _auth_headers(module)
    resp = client.get("/api/budget-summary", headers=headers)

    assert resp.status_code == 200
    assert resp.get_json()["monthly_spend"] == 200.0
    assert resp.get_json()["year_month"] == "2026-03"


def test_budget_summary_skips_malformed_rows_and_keeps_response_retryable(budget_api_module, caplog):
    module = budget_api_module["module"]
    client = budget_api_module["client"]
    transactions_sheet = budget_api_module["transactions_sheet"]

    transactions_sheet.get_all_records.return_value = [
        {
            "TransactionID": "TXN-BAD-TIME",
            "Timestamp": "not-a-real-timestamp",
            "MoneyCardNumber": "5F6E7D8C",
            "TransactionType": "Purchase",
            "Status": "Completed",
            "Amount": "50",
        },
        {
            "TransactionID": "TXN-BAD-AMOUNT",
            "Timestamp": "2026-03-15 10:00:00",
            "MoneyCardNumber": "5F6E7D8C",
            "TransactionType": "Purchase",
            "Status": "Completed",
            "Amount": "amount??",
        },
        {
            "TransactionID": "TXN-EMPTY-AMOUNT",
            "Timestamp": "2026-03-16 10:00:00",
            "MoneyCardNumber": "5F6E7D8C",
            "TransactionType": "Purchase",
            "Status": "Completed",
            "Amount": "",
        },
        {
            "TransactionID": "TXN-GOOD",
            "Timestamp": "2026-03-17 10:00:00",
            "MoneyCardNumber": "5F6E7D8C",
            "Type": "Purchase",
            "Status": "Completed",
            "Amount": "30.00",
        },
    ]

    caplog.set_level("WARNING", logger=module.logger.name)

    headers = _auth_headers(module)
    resp = client.get("/api/budget-summary", headers=headers)

    assert resp.status_code == 200
    assert resp.get_json()["monthly_spend"] == 30.0

    warning_messages = [record.getMessage() for record in caplog.records]
    assert any("budget_summary_malformed_row reason=timestamp" in msg for msg in warning_messages)
    assert any("budget_summary_malformed_row reason=amount" in msg for msg in warning_messages)


def test_budget_summary_unauthorized_returns_401(budget_api_module):
    client = budget_api_module["client"]

    resp = client.get("/api/budget-summary")

    assert resp.status_code == 401
    assert "Invalid or expired token" in resp.get_json()["error"]


def test_budget_summary_missing_money_card_binding_returns_404(budget_api_module):
    module = budget_api_module["module"]
    client = budget_api_module["client"]
    users_sheet = budget_api_module["users_sheet"]

    users_sheet.get_all_records.return_value = [
        {
            "StudentID": "2024-001",
            "Name": "No Card Student",
            "MoneyCardNumber": "",
        }
    ]

    headers = _auth_headers(module)
    resp = client.get("/api/budget-summary", headers=headers)

    assert resp.status_code == 404
    assert "No money card registered" in resp.get_json()["error"]


def test_budget_summary_unavailable_returns_503_when_transactions_sheet_fails(budget_api_module):
    module = budget_api_module["module"]
    client = budget_api_module["client"]
    transactions_sheet = budget_api_module["transactions_sheet"]

    transactions_sheet.get_all_records.side_effect = ConnectionError("transactions backend down")

    headers = _auth_headers(module)
    resp = client.get("/api/budget-summary", headers=headers)

    assert resp.status_code == 503
    assert "Service unavailable" in resp.get_json()["error"]
