"""
Tests for the gspread-compat surface added during the spreadsheet-to-Supabase
optimization pass (kanban t_9bc66cad).

The legacy backend code in api_server.py, dashboard_core.py, fraud_detection.py
and others calls gspread-style methods that were not implemented in the initial
sheets_adapter drop-in:

  - SheetsClient.worksheets()         — was AttributeError
  - SheetsClient.add_worksheet()      — was AttributeError
  - SheetView.update(range, values)   — was AttributeError
  - SheetView.append_row(table_range) — extra kwarg not in signature

These tests pin the new implementations. The DB connection is mocked —
we verify the SQL + Python control flow, not Postgres itself.
"""
from __future__ import annotations

import sys
import unittest.mock as mock
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

import pytest
from sheets_adapter import (
    _TABLE_LOOKUP,
    APIError,
    SheetsClient,
    SheetView,
)

# ---------------------------------------------------------------------------
# worksheets() — was previously AttributeError on SheetsClient
# ---------------------------------------------------------------------------


def test_worksheets_returns_view_per_known_table() -> None:
    """SheetsClient.worksheets() must return a SheetView for every known
    table, with .title matching the table name (gspread contract).

    Regression: prior to the fix, the dashboard / scheduler / api_server
    code did ``[ws.title for ws in db.worksheets()]`` and would crash
    with AttributeError because the method did not exist.
    """
    client = SheetsClient.__new__(SheetsClient)  # skip _get_pool() init
    views = client.worksheets()
    assert isinstance(views, list)
    # Every known table must have a corresponding view.
    titles = {v.title for v in views}
    assert "users" in titles
    assert "money_accounts" in titles
    assert "transactions_log" in titles
    assert "settings" in titles
    # And every view must be a SheetView instance with the correct title.
    for v in views:
        assert isinstance(v, SheetView)
        assert v.title in _TABLE_LOOKUP


def test_worksheets_makes_no_db_roundtrip() -> None:
    """worksheets() must NOT issue a SELECT to enumerate tables — the
    schema is already known in-process via _TABLE_LOOKUP, and a real
    enumeration query would be wasted I/O on every call (and the
    scheduler.py hot path calls this).
    """
    client = SheetsClient.__new__(SheetsClient)
    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock.MagicMock()
        client.worksheets()
        mc.assert_not_called()


# ---------------------------------------------------------------------------
# add_worksheet() — was previously AttributeError
# ---------------------------------------------------------------------------


def test_add_worksheet_returns_existing_view_if_table_known() -> None:
    """If the requested title is already in _TABLE_LOOKUP, add_worksheet
    is a no-op and returns the existing SheetView. No CREATE TABLE call.
    """
    client = SheetsClient.__new__(SheetsClient)
    with mock.patch("sheets_adapter._transaction") as mt:
        view = client.add_worksheet(title="users", rows=500, cols=10)
        mt.assert_not_called()
    assert isinstance(view, SheetView)
    assert view.title == "users"


def test_add_worksheet_registers_new_table_with_id_and_data_columns() -> None:
    """If the title is unknown, add_worksheet must:

    1. Register the table in _TABLES / _TABLE_COLUMNS / _TABLE_LOOKUP.
    2. Issue a CREATE TABLE IF NOT EXISTS with an id + data JSONB schema.
    3. Return a SheetView for the new table.
    """
    client = SheetsClient.__new__(SheetsClient)

    # Mock _transaction() to be a context manager that yields a mock conn.
    mock_cur = mock.MagicMock()
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cur

    @mock.patch("sheets_adapter._transaction")
    def run(mt: mock.MagicMock) -> SheetView:
        mt.return_value.__enter__.return_value = mock_conn
        return client.add_worksheet(title="custom_log", rows=10, cols=2)

    view = run()
    assert isinstance(view, SheetView)
    assert view.title == "custom_log"
    # Verify the CREATE TABLE SQL was issued.
    create_calls = [
        c for c in mock_cur.execute.call_args_list
        if "CREATE TABLE" in str(c.args[0])
    ]
    assert len(create_calls) == 1
    sql_text = str(create_calls[0].args[0])
    assert "custom_log" in sql_text
    assert "JSONB" in sql_text
    # The new table must be discoverable via worksheets() afterwards.
    new_titles = {v.title for v in client.worksheets()}
    assert "custom_log" in new_titles


# ---------------------------------------------------------------------------
# update() — gspread batch update. The legacy backend calls this in two forms.
# ---------------------------------------------------------------------------


def test_update_with_header_only_range_is_noop() -> None:
    """``ws.update('A1:Z1', [headers])`` is the canonical gspread
    "overwrite header row" pattern. For the Postgres-backed adapter the
    schema owns the column names; the call must do no DB writes.
    """
    sv = SheetView("users", client=mock.MagicMock())
    sv._columns = ["UserID", "Name"]

    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock.MagicMock()
        # Must not raise, must not hit the DB.
        sv.update("A1:Z1", [["UserID", "Name", "Email"]])
        mc.assert_not_called()


def test_update_with_keyword_arguments_also_works() -> None:
    """``ws.update(values=..., range_name=...)`` is the keyword form
    used by dashboard_core.py and admin_dashboard.py.
    """
    sv = SheetView("users", client=mock.MagicMock())
    sv._columns = ["UserID", "Name"]
    sv._col_name_to_index = lambda c: ["UserID", "Name"][c - 1]

    mock_cur = mock.MagicMock()
    # Window function over ctid — returns the (offset, ctid) pairs.
    mock_cur.fetchall.return_value = [(0, "(0,1)"), (1, "(0,2)")]
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock_conn
        sv.update(values=[["U001", "Alice"], ["U002", "Bob"]], range_name="A1:B2")
    # Two rows by two cols = 4 UPDATEs.
    update_calls = [
        c for c in mock_cur.execute.call_args_list
        if "UPDATE" in str(c.args[0])
    ]
    assert len(update_calls) == 4


def test_update_raises_when_range_or_values_missing() -> None:
    """update() must raise APIError if range_name or values is missing."""
    sv = SheetView("users", client=mock.MagicMock())
    sv._columns = ["UserID"]

    with pytest.raises(APIError, match="requires both"):
        sv.update()  # no args
    with pytest.raises(APIError, match="requires both"):
        sv.update(range_name="A1:B2")  # no values
    with pytest.raises(APIError, match="requires both"):
        sv.update(values=[["X"]])  # no range


# ---------------------------------------------------------------------------
# append_row(table_range=...) — gspread convention for "overwrite header".
# ---------------------------------------------------------------------------


def test_append_row_accepts_table_range_a1_as_noop() -> None:
    """``ws.append_row(row, table_range='A1')`` is the gspread pattern
    used in api_server.py / dashboard_core.py / cashier_routes.py to
    mean "this is the header row". For Postgres, headers live in the
    schema, so this is a no-op.
    """
    sv = SheetView("users", client=mock.MagicMock())
    sv._columns = ["UserID", "Name", "Email"]
    # Must not raise, must not hit the DB.
    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock.MagicMock()
        sv.append_row(["U001", "Alice", "[email protected]"], table_range="A1")
        mc.assert_not_called()


def test_append_row_rejects_unknown_table_range() -> None:
    """table_range values other than 'A1' (e.g. 'B2', 'A1:D1') must
    raise APIError — they would have semantic meaning in gspread that
    the Postgres adapter can't honor.
    """
    sv = SheetView("users", client=mock.MagicMock())
    sv._columns = ["UserID", "Name"]
    with pytest.raises(APIError, match="not supported"):
        sv.append_row(["U001", "Alice"], table_range="B2")
    with pytest.raises(APIError, match="not supported"):
        sv.append_row(["U001", "Alice"], table_range="A1:D1")


# ---------------------------------------------------------------------------
# find_cell / findall — single round-trip via window function
# ---------------------------------------------------------------------------


def test_find_cell_emits_single_query_with_row_number() -> None:
    """find_cell must emit exactly one SELECT that includes the
    row_number() window function (eliminates the prior N+1 ctid scan).
    """
    sv = SheetView("users", client=mock.MagicMock())
    sv._columns = ["UserID", "Name"]
    sv._col_name_to_index = lambda c: "Name"

    mock_cur = mock.MagicMock()
    mock_cur.fetchone.return_value = (5, "U005", "Alice")
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock_conn
        result = sv.find_cell("Alice", in_column="Name")

    # Exactly one SELECT, no second "resolve ctid" query.
    assert mock_cur.execute.call_count == 1
    sql = str(mock_cur.execute.call_args.args[0])
    assert "row_number()" in sql
    # Row number is taken from the window function column, not derived
    # by a second Python-side scan.
    assert result == {"row": 5, "col": 2, "value": "Alice"}


def test_findall_returns_row_numbers_from_window_function() -> None:
    """findall must use row_number() so the returned row indices match
    the actual gspread-style 1-indexed row numbers, not Python's loop
    counter (which would be wrong if the WHERE filter drops rows).
    """
    sv = SheetView("users", client=mock.MagicMock())
    sv._columns = ["UserID", "Name"]
    sv._col_name_to_index = lambda c: "Name"

    mock_cur = mock.MagicMock()
    # Match rows 7 and 12 (not contiguous — the window function must
    # produce the actual row number, not a counter).
    mock_cur.fetchall.return_value = [
        (7, "U007", "Alice"),
        (12, "U012", "Alex"),
    ]
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock_conn
        results = sv.findall("Al", in_column="Name")

    assert len(results) == 2
    assert results[0]["row"] == 7
    assert results[1]["row"] == 12


# ---------------------------------------------------------------------------
# get_all_records — fast-path skips the per-row dict() copy
# ---------------------------------------------------------------------------


def test_get_all_records_fast_path_skips_dict_copy_when_no_conversion() -> None:
    """If the result set has no datetime/Decimal values, the optimized
    path must return the RealDictCursor rows as-is (no ``dict(row)``
    copy and no per-row dict comprehension).
    """
    sv = SheetView("users", client=mock.MagicMock())
    sv._columns = ["UserID", "Name", "Status"]
    # Build rows that need no conversion — plain strings and ints.
    raw_rows = [
        {"UserID": "U001", "Name": "Alice", "Status": "active"},
        {"UserID": "U002", "Name": "Bob", "Status": "active"},
    ]
    mock_cur = mock.MagicMock()
    mock_cur.fetchall.return_value = raw_rows
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock_conn
        out = sv.get_all_records()

    # The fast path returns the rows directly — they should be the
    # same dict objects (no copy).
    assert out[0] is raw_rows[0]
    assert out[1] is raw_rows[1]
    # And the conversion slow path did NOT run.
    assert isinstance(out[0]["UserID"], str)


def test_get_all_records_converts_datetime_and_decimal() -> None:
    """Slow path: datetime → ISO string, Decimal → float. This pins
    the gspread-compat contract that the prior (un-optimized)
    implementation also satisfied.
    """
    import datetime as _dt
    from decimal import Decimal

    sv = SheetView("users", client=mock.MagicMock())
    sv._columns = ["UserID", "Joined", "Balance"]
    when = _dt.datetime(2026, 1, 15, 10, 0, 0)
    raw_rows = [
        {"UserID": "U001", "Joined": when, "Balance": Decimal("50.00")},
    ]
    mock_cur = mock.MagicMock()
    mock_cur.fetchall.return_value = raw_rows
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock_conn
        out = sv.get_all_records()

    assert out[0]["Joined"] != when  # not the raw datetime
    assert isinstance(out[0]["Joined"], str)
    assert "2026-01-15" in out[0]["Joined"]
    assert out[0]["Balance"] == 50.0
    assert isinstance(out[0]["Balance"], float)


def test_get_all_records_empty2zero_replaces_none_for_numeric_cols() -> None:
    """empty2zero=True must convert None → 0 for columns Postgres
    reports as numeric. Uses the precomputed ``_numeric_cols`` cache
    so the check is O(1) per cell.
    """
    from decimal import Decimal

    sv = SheetView("users", client=mock.MagicMock())
    sv._columns = ["UserID", "Balance", "Note"]
    sv._numeric_cols = {"Balance"}  # skip the loader; the contract is
    # what matters.
    raw_rows = [
        {"UserID": "U001", "Balance": None, "Note": "hello"},
    ]
    mock_cur = mock.MagicMock()
    mock_cur.fetchall.return_value = raw_rows
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock_conn
        out = sv.get_all_records(empty2zero=True)

    assert out[0]["Balance"] == 0
    assert out[0]["Note"] == "hello"  # non-numeric: unchanged


# ---------------------------------------------------------------------------
# cell() — single-column SELECT, O(1) col index lookup
# ---------------------------------------------------------------------------


def test_cell_uses_single_column_select() -> None:
    """cell() must issue ``SELECT <col> FROM ...`` (one column), not
    ``SELECT *`` (full row), and consult ``_col_index`` directly
    (O(1)) instead of ``_columns.index(col_name)`` (O(n)).
    """
    sv = SheetView("users", client=mock.MagicMock())
    sv._columns = ["UserID", "Name", "Balance"]
    sv._col_name_to_index = lambda c: ["UserID", "Name", "Balance"][c - 1]

    mock_cur = mock.MagicMock()
    mock_cur.fetchone.return_value = ("Alice",)
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with mock.patch("sheets_adapter._conn") as mc:
        mc.return_value.__enter__.return_value = mock_conn
        result = sv.cell(row=1, col=2)

    # SQL should reference the column name (not "*").
    sql = str(mock_cur.execute.call_args.args[0])
    assert '"Name"' in sql or "'Name'" in sql or "Name" in sql
    assert "*" not in sql
    assert result == {"row": 1, "col": 2, "value": "Alice"}


def test_sheetview_init_builds_col_index() -> None:
    """SheetView.__init__ must precompute the col_index dict for O(1)
    column-name lookups. This is the cache that ``cell()`` and
    ``_update_cells_grid`` depend on.
    """
    sv = SheetView("users", client=mock.MagicMock())
    # _col_index is a dict keyed by column name → 0-based position.
    assert hasattr(sv, "_col_index")
    assert isinstance(sv._col_index, dict)
    # The users table's first column is "StudentID" (per the schema).
    assert sv._col_index["StudentID"] == 0
    assert sv._col_index["Name"] == 1
    # The table has 8 columns per the schema.
    assert len(sv._col_index) == len(sv._columns) == 8


# ---------------------------------------------------------------------------
# Dead-code removal verification
# ---------------------------------------------------------------------------


def test_module_no_longer_exports_unused_regex() -> None:
    """The legacy ``MANILA_SUFFIX_RE`` constant was defined but never
    used in the module. The optimization pass removed it. Pin its
    absence so it doesn't sneak back in.
    """
    import sheets_adapter

    assert not hasattr(sheets_adapter, "MANILA_SUFFIX_RE"), (
        "MANILA_SUFFIX_RE was dead code and has been removed from "
        "sheets_adapter — do not reintroduce."
    )


def test_module_no_longer_imports_re() -> None:
    """``import re`` was only used for the now-removed MANILA_SUFFIX_RE
    and the local ``_re`` inside update_cells. The module-level import
    has been removed; the local alias inside update_cells is fine.
    """
    import inspect

    import sheets_adapter

    source = inspect.getsource(sheets_adapter)
    # Module-level ``import re`` (not the local ``import re as _re``).
    assert "import re\n" not in source, (
        "Module-level `import re` is dead and has been removed; "
        "if you need it, scope the import to the function that uses it."
    )
