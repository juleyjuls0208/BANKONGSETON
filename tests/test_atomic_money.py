from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from sheets_adapter import APIError, SheetView


def _view_and_db(fetches):
    view = SheetView("money_accounts", client=MagicMock())
    cursor = MagicMock()
    cursor.fetchone.side_effect = fetches
    conn = MagicMock()
    conn.cursor.return_value = cursor
    transaction = MagicMock()
    transaction.__enter__.return_value = conn
    return view, cursor, transaction


def test_atomic_money_updates_balance_and_ledger_once():
    view, cursor, transaction = _view_and_db([
        None,
        ("100.00", "10.00", "Active"),
    ])
    with patch("sheets_adapter._transaction", return_value=transaction):
        result = view.update_balance_atomic(
            money_card="AABBCCDD",
            amount_delta=-25,
            transaction_type="Purchase",
            student_id="S001",
            idempotency_key="pos-001",
        )

    updates = [call for call in cursor.execute.call_args_list if "UPDATE money_accounts" in str(call.args[0])]
    inserts = [call for call in cursor.execute.call_args_list if "INSERT INTO transactions_log" in str(call.args[0])]
    assert len(updates) == 1
    assert len(inserts) == 1
    assert result["BalanceBefore"] == 100.0
    assert result["BalanceAfter"] == 75.0
    assert result["TransactionID"] == "pos-001"


def test_atomic_money_duplicate_returns_original_without_mutation():
    existing = ("pos-001", "2026-07-19T10:00:00+08:00", "S001", "AABBCCDD", "Purchase", -25, 100, 75, "Success", "[]")
    view, cursor, transaction = _view_and_db([existing])
    with patch("sheets_adapter._transaction", return_value=transaction):
        result = view.update_balance_atomic(
            money_card="AABBCCDD",
            amount_delta=-25,
            transaction_type="Purchase",
            student_id="S001",
            idempotency_key="pos-001",
        )

    assert result["Idempotent"] is True
    assert result["BalanceAfter"] == 75.0
    assert not any("UPDATE money_accounts" in str(call.args[0]) for call in cursor.execute.call_args_list)
    assert not any("INSERT INTO transactions_log" in str(call.args[0]) for call in cursor.execute.call_args_list)


def test_atomic_money_rejects_insufficient_funds_without_writes():
    view, cursor, transaction = _view_and_db([
        None,
        ("5.00", "0.00", "Active"),
    ])
    with patch("sheets_adapter._transaction", return_value=transaction):
        with pytest.raises(APIError, match="Insufficient"):
            view.update_balance_atomic(
                money_card="AABBCCDD",
                amount_delta=-25,
                transaction_type="Purchase",
                student_id="S001",
                idempotency_key="pos-002",
            )

    assert not any("UPDATE money_accounts" in str(call.args[0]) for call in cursor.execute.call_args_list)
    assert not any("INSERT INTO transactions_log" in str(call.args[0]) for call in cursor.execute.call_args_list)


def test_atomic_money_requires_caller_idempotency_key():
    view = SheetView("money_accounts", client=MagicMock())
    with pytest.raises(APIError, match="Idempotency key"):
        view.update_balance_atomic(
            money_card="AABBCCDD",
            amount_delta=10,
            transaction_type="Load",
            student_id="S001",
        )
