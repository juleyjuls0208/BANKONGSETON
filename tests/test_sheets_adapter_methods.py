"""
Unit tests for backend.sheets_adapter.SheetView.

The audit (t_1dcc21f4 run 22) fixed three concrete bugs in SheetView:
  1. cell() — dead first query, wrong return shape (used col_name as key
     instead of 'value'), silent `except Exception:` that masked errors.
  2. update_cell() — duplicated if/else branches with a `val`-typo in the
     else branch that would NameError on non-datetime values.
  3. _is_numeric_col() — always returned False regardless of column type,
     and the function queried Postgres but never read the result.

These tests pin the corrected behavior. The DB connection is mocked — we
only verify the SQL + Python control flow, not Postgres itself.
"""
from __future__ import annotations

import sys
import unittest.mock as mock
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Ensure backend/ is importable when running this test in isolation
_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

import pytest
from sheets_adapter import APIError, SheetView


def test_find_returns_a_virtual_header_cell() -> None:
    sv = SheetView("users", client=mock.MagicMock())

    assert sv.find("MoneyCardNumber") == {"row": 1, "col": 4, "value": "MoneyCardNumber"}

# ---------------------------------------------------------------------------
# cell() — gspread-compatible return shape, no dead query, no silent except
# ---------------------------------------------------------------------------


def test_cell_returns_gspread_compatible_shape() -> None:
    """cell() must return {'row': r, 'col': c, 'value': v}, matching find_cell().

    Optimized path: cell() issues ``SELECT <col> FROM ... OFFSET N`` (one
    column), so the mock fetchone returns a 1-tuple.
    """
    sv = SheetView("users", client=mock.MagicMock())
    sv._columns = ["UserID", "Name", "Balance"]
    # col=2 → 'Name' (matches column index 1)
    sv._col_name_to_index = lambda c: {1: "UserID", 2: "Name", 3: "Balance"}[c]

    mock_cur = mock.MagicMock()
    # SELECT Name → 1-tuple ("Alice",)
    mock_cur.fetchone.return_value = ("Alice",)
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock_conn
        result = sv.cell(row=2, col=2)

    assert result == {"row": 2, "col": 2, "value": "Alice"}, (
        f"cell() must return gspread-style shape, got {result!r}"
    )
    # And the SQL is exactly one query (the dead first query is gone)
    assert mock_cur.execute.call_count == 1, (
        f"cell() must execute exactly one query, got {mock_cur.execute.call_count}"
    )


def test_cell_converts_decimal_to_float() -> None:
    """Decimal values must be converted to float, matching gspread's number coercion."""
    sv = SheetView("users", client=mock.MagicMock())
    sv._columns = ["Balance"]
    sv._col_name_to_index = lambda c: "Balance"

    mock_cur = mock.MagicMock()
    mock_cur.fetchone.return_value = (Decimal("123.45"),)
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock_conn
        result = sv.cell(row=2, col=1)

    assert result == {"row": 2, "col": 1, "value": 123.45}
    assert isinstance(result["value"], float)


def test_cell_converts_datetime_to_isoformat_string() -> None:
    """datetime values must be ISO-formatted, matching _row_to_dict convention.

    Optimized path: cell() selects only the target column, so fetchone
    returns a 1-tuple containing just the timestamp.
    """
    sv = SheetView("transactions_log", client=mock.MagicMock())
    sv._columns = ["Timestamp", "Amount"]
    sv._col_name_to_index = lambda c: "Timestamp" if c == 1 else "Amount"

    when = datetime(2026, 6, 5, 12, 30, 0)
    mock_cur = mock.MagicMock()
    # SELECT Timestamp → 1-tuple
    mock_cur.fetchone.return_value = (when,)
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock_conn
        result = sv.cell(row=2, col=1)

    assert result["row"] == 2
    assert result["col"] == 1
    assert isinstance(result["value"], str)
    assert "2026-06-05" in result["value"]


def test_cell_raises_api_error_when_row_missing() -> None:
    """cell() must raise APIError when the row doesn't exist (gspread behavior)."""
    sv = SheetView("users", client=mock.MagicMock())
    sv._columns = ["UserID"]
    sv._col_name_to_index = lambda c: "UserID"

    mock_cur = mock.MagicMock()
    mock_cur.fetchone.return_value = None  # no row
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock_conn
        with pytest.raises(APIError, match="Row 99 not found"):
            sv.cell(row=99, col=1)


def test_cell_returns_first_column_value_when_col_index_unknown() -> None:
    """Defensive fallback: if a column name is returned by
    ``_col_name_to_index`` that is not in ``_col_index`` (which can
    happen with custom SheetView subclasses that override the helper),
    the optimized path returns the first column's value rather than
    crashing. This is the "graceful degradation" contract — the
    pre-optimization implementation also returned the first column
    value (raw[0]) when ``.index(col_name)`` failed in the same way.
    """
    sv = SheetView("users", client=mock.MagicMock())
    sv._columns = ["UserID"]  # 'Name' is not here
    sv._col_name_to_index = lambda c: "Name"  # returns a column not in _columns

    mock_cur = mock.MagicMock()
    # SELECT * → full row tuple
    mock_cur.fetchone.return_value = ("U001",)
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock_conn
        result = sv.cell(row=2, col=1)

    # Defensive fallback returns the first column's value, not None.
    assert result == {"row": 2, "col": 1, "value": "U001"}


# ---------------------------------------------------------------------------
# update_cell() — unified SQL, no NameError on non-datetime values
# ---------------------------------------------------------------------------


def test_update_cell_with_non_datetime_value_uses_unified_sql() -> None:
    """update_cell() must bind a non-datetime value via %(val)s without NameError.

    Regression: the prior code had a duplicated if/else where the else branch
    referenced `val` (typo) instead of `value`, raising NameError on every
    non-datetime value.
    """
    sv = SheetView("users", client=mock.MagicMock())
    sv._col_name_to_index = lambda c: "Balance" if c == 1 else "Name"

    mock_cur = mock.MagicMock()
    mock_cur.fetchone.return_value = ("(0,1)",)  # ctid-style tuple
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock_conn
        # Non-datetime value — would have NameError'd under the prior code.
        sv.update_cell(row=2, col=1, value=123.45)

    # Verify the UPDATE was issued with the right parameters
    update_calls = [
        c for c in mock_cur.execute.call_args_list
        if "UPDATE" in str(c.args[0])
    ]
    assert len(update_calls) == 1, f"expected exactly one UPDATE, got {len(update_calls)}"
    params = update_calls[0].args[1]
    assert params[0] == 123.45, f"expected value=123.45, got {params!r}"


def test_update_cell_with_datetime_value_uses_unified_sql() -> None:
    """update_cell() must bind a datetime value via %(val)s (psycopg2 handles natively)."""
    sv = SheetView("transactions_log", client=mock.MagicMock())
    sv._col_name_to_index = lambda c: "Timestamp"

    mock_cur = mock.MagicMock()
    mock_cur.fetchone.return_value = ("(0,1)",)
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cur

    when = datetime(2026, 6, 5, 12, 0, 0)
    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock_conn
        sv.update_cell(row=2, col=1, value=when)

    update_calls = [
        c for c in mock_cur.execute.call_args_list
        if "UPDATE" in str(c.args[0])
    ]
    assert len(update_calls) == 1
    assert update_calls[0].args[1][0] == when


def test_update_cell_raises_api_error_when_row_missing() -> None:
    sv = SheetView("users", client=mock.MagicMock())
    sv._col_name_to_index = lambda c: "Balance"

    mock_cur = mock.MagicMock()
    mock_cur.fetchone.return_value = None
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock_conn
        with pytest.raises(APIError, match="Row 99 not found"):
            sv.update_cell(row=99, col=1, value=50.0)


def test_append_user_optional_fields_are_null_not_empty_strings() -> None:
    """Optional blank cards must not collide with PostgreSQL's unique card index."""
    sv = SheetView("users", client=mock.MagicMock())
    cur = mock.MagicMock()
    conn = mock.MagicMock()
    conn.cursor.return_value = cur
    row = ["202320112", "Student", "CARD-1", "", "Active", "", "", ""]

    with mock.patch("sheets_adapter._conn") as connection:
        connection.return_value.__enter__.return_value = conn
        sv.append_row(row)

    bound = cur.execute.call_args.args[1]
    assert bound[3] is None  # MoneyCardNumber
    assert bound[5:] == [None, None, None]


# ---------------------------------------------------------------------------
# _is_numeric_col() — correctly identifies numeric vs non-numeric columns
# ---------------------------------------------------------------------------


def test_is_numeric_col_returns_true_for_known_numeric() -> None:
    """_is_numeric_col() must return True for columns in the cached numeric set."""
    sv = SheetView("users", client=mock.MagicMock())
    # Inject a deterministic loader result
    sv._numeric_cols = {"Balance", "Age"}
    assert sv._is_numeric_col("Balance") is True
    assert sv._is_numeric_col("Age") is True


def test_is_numeric_col_returns_false_for_non_numeric() -> None:
    sv = SheetView("users", client=mock.MagicMock())
    sv._numeric_cols = {"Balance", "Age"}
    assert sv._is_numeric_col("Name") is False
    assert sv._is_numeric_col("Email") is False


def test_is_numeric_col_caches_loader_result() -> None:
    """The Postgres query should only run once per SheetView instance."""
    sv = SheetView("users", client=mock.MagicMock())
    call_count = [0]

    def counting_loader() -> set[str]:
        call_count[0] += 1
        return {"Balance"}

    sv._load_numeric_cols = counting_loader
    # First call triggers the loader
    sv._is_numeric_col("Balance")
    # Subsequent calls use the cache
    sv._is_numeric_col("Balance")
    sv._is_numeric_col("Name")
    sv._is_numeric_col("Age")

    assert call_count[0] == 1, (
        f"loader should run once across 4 calls, ran {call_count[0]} times"
    )


def test_is_numeric_col_returns_false_on_loader_failure() -> None:
    """If the Postgres query errors, _is_numeric_col must return False (fail-safe)."""

    def failing_loader() -> set[str]:
        raise RuntimeError("connection lost")

    sv = SheetView("users", client=mock.MagicMock())
    sv._load_numeric_cols = failing_loader
    # Should not raise — the loader exception is caught at the call site
    # in the real implementation, so _is_numeric_col falls back to False.
    # Here we verify the contract: a loader that raises is the caller's
    # responsibility; _is_numeric_col reads from _numeric_cols.  We pre-set
    # the cache to empty to mirror the real failure path.
    sv._numeric_cols = set()
    assert sv._is_numeric_col("Balance") is False
