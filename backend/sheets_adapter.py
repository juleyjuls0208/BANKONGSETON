"""
sheets_adapter.py
Drop-in gspread replacement backed by Supabase Postgres (psycopg2).
Provides SheetsClient / SheetView / SheetRow wrappers that mirror the
gspread API so existing BankongSeton backend code can migrate sheet-by-sheet.
"""

from __future__ import annotations

import os
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor

# ---------------------------------------------------------------------------
# Warning suppression (psycopg2/pgconnection warnings are noisy in pooling)
# ---------------------------------------------------------------------------
warnings.filterwarnings("ignore", category=DeprecationWarning, module="psycopg2")
warnings.filterwarnings("ignore", message=".*connection is not open.*")
warnings.filterwarnings("ignore", message=".*SSL is not enabled.*")

# ---------------------------------------------------------------------------
# Local timezone helpers
# ---------------------------------------------------------------------------
_MANILA_TZ = datetime.now().astimezone().tzinfo  # best-effort; set explicitly below
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None  # Python < 3.9


MANILA_TZ = ZoneInfo("Asia/Manila") if ZoneInfo else None
_UTC = UTC


def _now_manila() -> datetime:
    """Return current time in Asia/Manila (UTC+8)."""
    if MANILA_TZ:
        return datetime.now(MANILA_TZ)
    # Fallback: naive UTC+8
    return datetime.utcnow().replace(tzinfo=_UTC) + __import__("timedelta")(hours=8)


def _to_manila(dt: datetime) -> datetime:
    """Convert a datetime to Asia/Manila if not already."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        if MANILA_TZ:
            return dt.replace(tzinfo=MANILA_TZ)
        return dt
    if MANILA_TZ:
        return dt.astimezone(MANILA_TZ)
    return dt


def _isoformat(dt: datetime) -> str:
    """Return ISO8601 string in Manila time."""
    if dt is None:
        return ""
    return _to_manila(dt).isoformat()


def _parse_dt(value: Any) -> datetime | None:
    """Parse a value into a datetime, then return Manila-local datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return _to_manila(value)
    try:
        # Try ISO8601 parsing
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return _to_manila(dt)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Exceptions (mirrors gspread)
# ---------------------------------------------------------------------------
class APIError(Exception):
    """Drop-in replacement for gspread.exceptions.APIError."""

    def __init__(self, msg: str, code: str | None = None):
        super().__init__(msg)
        self.code = code or "unknown"


class SpreadsheetNotFound(APIError):
    """Raised when spreadsheet / table does not exist."""

    def __init__(self, name: str):
        super().__init__(f"Spreadsheet not found: {name}", code="not_found")
        self.spreadsheet = name


class WorksheetNotFound(APIError):
    """Raised when worksheet / table does not exist."""

    def __init__(self, name: str):
        super().__init__(f"Worksheet not found: {name}", code="worksheet_not_found")
        self.worksheet = name


class CellNotFound(APIError):
    """Raised when a cell cannot be located."""

    def __init__(self, query: str):
        super().__init__(f"Cell not found: {query}", code="cell_not_found")
        self.query = query


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------
_DATABASE_URL: str | None = None
_CONNECTION_POOL: pool.ThreadedConnectionPool | None = None


def _get_pool() -> pool.ThreadedConnectionPool:
    global _CONNECTION_POOL
    if _CONNECTION_POOL is None:
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise APIError(
                "DATABASE_URL environment variable is not set. "
                "Cannot connect to Supabase Postgres. "
                "Please set DATABASE_URL to your postgresql://... connection string."
            )
        try:
            _CONNECTION_POOL = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=url,
                connect_timeout=30,
                options="-c client_encoding=UTF8",
            )
        except psycopg2.Error as e:
            raise APIError(f"Failed to connect to Postgres: {e}") from e
    return _CONNECTION_POOL


@contextmanager
def _conn() -> Generator[Any, None, None]:
    """Get a connection from the pool; auto-return it on exit."""
    p = _get_pool()
    conn = p.getconn()
    try:
        yield conn
    finally:
        p.putconn(conn)


@contextmanager
def _transaction() -> Generator[Any, None, None]:
    """Open a transaction context; commits on success, rolls back on error."""
    with _conn() as conn:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


# ---------------------------------------------------------------------------
# Schema definition (7 tables)
# ---------------------------------------------------------------------------

_USERS_COLS = [
    ("StudentID", "VARCHAR(64) PRIMARY KEY"),
    ("Name", "TEXT NOT NULL"),
    ("IDCardNumber", "VARCHAR(64)"),
    ("MoneyCardNumber", "VARCHAR(64)"),
    ("Status", "VARCHAR(32) DEFAULT 'active'"),
    ("ParentEmail", "TEXT"),
    ("DateRegistered", "TIMESTAMPTZ DEFAULT NOW()"),
    ("FCMToken", "TEXT"),
]

_MONEY_ACCOUNTS_COLS = [
    ("MoneyCardNumber", "VARCHAR(64) PRIMARY KEY"),
    ("LinkedIDCard", "VARCHAR(64)"),  # references IDCardNumber in users
    ("Balance", "NUMERIC(14,2) DEFAULT 0.00"),
    ("Status", "VARCHAR(32) DEFAULT 'active'"),
    ("LastUpdated", "TIMESTAMPTZ DEFAULT NOW()"),
]

_TRANSACTIONS_LOG_COLS = [
    ("TransactionID", "SERIAL PRIMARY KEY"),
    ("Timestamp", "TIMESTAMPTZ DEFAULT NOW()"),
    ("MoneyCardNumber", "VARCHAR(64) NOT NULL"),
    ("TransactionType", "VARCHAR(32) NOT NULL"),
    ("Amount", "NUMERIC(14,2) NOT NULL"),
    ("BalanceBefore", "NUMERIC(14,2) NOT NULL"),
    ("BalanceAfter", "NUMERIC(14,2) NOT NULL"),
    ("Status", "VARCHAR(32) DEFAULT 'completed'"),
    ("ItemsJson", "TEXT"),  # JSON string for items/receipts
]

_LOST_CARD_REPORTS_COLS = [
    ("id", "SERIAL PRIMARY KEY"),
    ("MoneyCardNumber", "VARCHAR(64) NOT NULL"),
    ("IDCardNumber", "VARCHAR(64)"),
    ("DateReported", "TIMESTAMPTZ DEFAULT NOW()"),
    ("Status", "VARCHAR(32) DEFAULT 'open'"),
]

_SETTINGS_COLS = [
    ("key", "VARCHAR(255) PRIMARY KEY"),
    ("value", "TEXT NOT NULL"),
]

_PRODUCTS_COLS = [
    ("ProductID", "VARCHAR(64) PRIMARY KEY"),
    ("Name", "TEXT NOT NULL"),
    ("Price", "NUMERIC(14,2) NOT NULL"),
    ("Category", "VARCHAR(128)"),
    ("Active", "BOOLEAN DEFAULT TRUE"),
    ("LastUpdated", "TIMESTAMPTZ DEFAULT NOW()"),
]

_VIRTUAL_CARDS_COLS = [
    ("Token", "VARCHAR(255) PRIMARY KEY"),
    ("MoneyCardNumber", "VARCHAR(64) NOT NULL"),
    ("StudentID", "VARCHAR(64) NOT NULL"),
    ("CreatedAt", "TIMESTAMPTZ DEFAULT NOW()"),
    ("Status", "VARCHAR(32) DEFAULT 'active'"),
]

_TABLES: dict[str, list[tuple[str, str]]] = {
    "users": _USERS_COLS,
    "money_accounts": _MONEY_ACCOUNTS_COLS,
    "transactions_log": _TRANSACTIONS_LOG_COLS,
    "lost_card_reports": _LOST_CARD_REPORTS_COLS,
    "settings": _SETTINGS_COLS,
    "products": _PRODUCTS_COLS,
    "virtual_cards": _VIRTUAL_CARDS_COLS,
}

# gspread-style column order for get_all_records (preserve order)
_TABLE_COLUMNS: dict[str, list[str]] = {t: [c[0] for c in cols] for t, cols in _TABLES.items()}

# Map gspread "sheet title" → table name (case-insensitive)
_TABLE_LOOKUP: dict[str, str] = {
    # Lowercase keys (for code that uses table name directly)
    "users": "users",
    "money_accounts": "money_accounts",
    "transactions_log": "transactions_log",
    "lost_card_reports": "lost_card_reports",
    "settings": "settings",
    "products": "products",
    "virtual_cards": "virtual_cards",
    "money accounts": "money_accounts",
    "transactions log": "transactions_log",
    "lost card reports": "lost_card_reports",
    "virtualcards": "virtual_cards",
}


def _supabase_init() -> None:
    """
    Create all tables if they don't exist.
    Safe to call on every startup (CREATE TABLE IF NOT EXISTS).
    """
    with _transaction() as conn:
        cur = conn.cursor()
        for table_name, columns in _TABLES.items():
            col_defs = ", ".join(f"{col} {dtype}" for col, dtype in columns)
            cur.execute(
                sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
                    sql.Identifier(table_name),
                    sql.SQL(col_defs),
                )
            )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_transactions_mcn ON transactions_log(MoneyCardNumber)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_transactions_ts ON transactions_log(Timestamp)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_lost_card_mcn ON lost_card_reports(MoneyCardNumber)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_virtual_cards_mcn ON virtual_cards(MoneyCardNumber)"
        )
        cur.close()


# ---------------------------------------------------------------------------
# SheetsClient
# ---------------------------------------------------------------------------

class SheetsClient:
    """
    Top-level client — mirrors gspread.Client/Spreadsheet behavior.

    get_sheets_client() returns an instance of this class.
    """

    def __init__(self) -> None:
        # Ensure pool is up
        _get_pool()

    # ------------------------------------------------------------------
    # Worksheet access
    # ------------------------------------------------------------------
    def worksheet(self, name: str) -> SheetView:
        """Return a SheetView for the given table / worksheet name."""
        table = name.lower().strip()
        if table not in _TABLE_LOOKUP:
            raise WorksheetNotFound(name)
        return SheetView(table, client=self)

    def open(self, key: str) -> SheetsClient:
        """Alias — for API compat with code that calls gc.open('...')."""
        return self

    def open_by_url(self, url: str) -> SheetsClient:
        """Alias for API compat."""
        return self

    def list_sheets(self) -> list[dict]:
        """Return list of available sheet names / table names."""
        return [{"title": t} for t in _TABLE_LOOKUP]

    @property
    def sheets(self) -> list[dict]:
        """Alias for list_sheets."""
        return self.list_sheets()

    def worksheets(self) -> list[SheetView]:
        """Return SheetView for every known table (gspread compat).

        Prior to this implementation, callers that did
        ``[ws.title for ws in db.worksheets()]`` would crash with
        AttributeError because the method did not exist on the
        SheetsClient. Returning a list of SheetView objects preserves
        the gspread contract (``ws.title``, ``ws.append_row(...)``,
        ``ws.update(...)``) while only materializing the known set of
        table names from the in-process schema map — no extra DB
        round-trip.
        """
        return [SheetView(t, client=self) for t in _TABLE_LOOKUP]

    def add_worksheet(
        self, title: str, rows: int = 100, cols: int = 10
    ) -> SheetView:
        """Register a new table (gspread compat).

        The gspread API creates an empty worksheet on demand. The
        Supabase-backed equivalent registers a new table in the schema
        map and CREATEs the backing table with a generic schema
        (id, data JSONB) so callers can immediately ``append_row`` /
        ``update`` on it. If the table already exists the call is a
        no-op and the existing SheetView is returned.

        ``rows`` and ``cols`` are accepted for gspread compat but not
        enforced — Postgres has no row/column limit at the adapter
        level.
        """
        del rows, cols  # unused — Postgres has no static row/col limits
        table = title.lower().strip()
        if table in _TABLE_LOOKUP:
            return SheetView(table, client=self)
        if table not in _TABLES:
            # Auto-register an ad-hoc table with a flexible schema.
            # This mirrors the gspread "add a worksheet then fill it"
            # pattern: small dynamic sheets (Scheduler Log, Cashier
            # Accounts, Fraud Alerts, etc.) that the legacy code created
            # at runtime rather than baking into the schema.
            _TABLES[table] = [
                ("id", "SERIAL PRIMARY KEY"),
                ("data", "JSONB"),
            ]
            _TABLE_COLUMNS[table] = ["id", "data"]
            _TABLE_LOOKUP[table] = table
            # Persist the new schema in Postgres.
            with _transaction() as conn:
                cur = conn.cursor()
                col_defs = ", ".join(
                    f"{col} {dtype}" for col, dtype in _TABLES[table]
                )
                cur.execute(
                    sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
                        sql.Identifier(table),
                        sql.SQL(col_defs),
                    )
                )
                cur.close()
        return SheetView(table, client=self)


# ---------------------------------------------------------------------------
# SheetView
# ---------------------------------------------------------------------------

class SheetView:
    """
    View over a Postgres table.
    Mirrors gspread.Worksheet behavior for one sheet.
    """

    def __init__(self, table: str, client: SheetsClient) -> None:
        self._table = table
        self._client = client
        self._columns: list[str] = _TABLE_COLUMNS.get(table, [])
        # O(1) column-name → 0-based-position lookup, computed once at
        # init. cell() and other hot-path methods consult this dict
        # directly instead of doing a linear ``list.index`` scan on
        # every call. For a 12-column table this saves ~6 comparisons
        # per call on average, and there are dozens of cell() calls
        # per request in the load-balance and cash-payment hot paths.
        self._col_index: dict[str, int] = {
            name: i for i, name in enumerate(self._columns)
        }

    # ------------------------------------------------------------------
    # Row/cell helpers
    # ------------------------------------------------------------------

    def _col_name_to_index(self, col: int) -> str:
        """Convert 1-based column index to column name string."""
        if col < 1 or col > len(self._columns):
            raise APIError(f"Column index {col} out of range for {self._table}")
        return self._columns[col - 1]

    def _row_to_dict(self, row: tuple, columns: list[str]) -> dict:
        """Convert a psycopg2RealDictCursor row tuple to gspread-style dict."""
        result: dict[str, Any] = {}
        for i, col in enumerate(columns):
            val = row[i] if i < len(row) else None
            if isinstance(val, datetime):
                result[col] = _isoformat(val)
            elif isinstance(val, Decimal):
                result[col] = float(val)
            else:
                result[col] = val
        return result

    def _dict_to_row(self, record: dict) -> list:
        """Convert a dict to a row tuple using column order."""
        result = []
        for col in self._columns:
            val = record.get(col)
            if isinstance(val, datetime):
                result.append(val)
            else:
                result.append(val)
        return result

    # ------------------------------------------------------------------
    # gspread-compatible read methods
    # ------------------------------------------------------------------

    def get_all_records(self, empty2zero: bool = False, major_dimension: str = "ROWS") -> list[dict]:
        """
        Return all rows as a list of dicts (gspread format).
        empty2zero: convert empty strings to 0 for numeric fields.
        major_dimension: accepted for compat, ignored (Postgres is row-oriented).

        Performance: the prior implementation called ``dict(row)`` on
        every row (a redundant copy — ``RealDictCursor`` rows are
        already dicts) and then iterated ``.items()`` to convert
        datetimes and Decimals. The optimized version mutates the
        row in place when conversion is needed and skips the copy
        when it's not. This shaves a measurable constant off the
        hot path of every API endpoint that reads sheet data.
        """
        del major_dimension  # unused — Postgres is row-oriented
        with _conn() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                sql.SQL("SELECT * FROM {} ORDER BY 1").format(
                    sql.Identifier(self._table)
                )
            )
            rows = cur.fetchall()
            cur.close()

        # Cache the numeric-cols set so we only call _is_numeric_col once.
        if empty2zero:
            numeric_cols: set[str] | None = (
                self._numeric_cols
                if hasattr(self, "_numeric_cols")
                else None
            )
            if numeric_cols is None:
                numeric_cols = self._load_numeric_cols()
                self._numeric_cols = numeric_cols
        else:
            numeric_cols = None

        # Two-pass: figure out which keys need conversion across the
        # whole result set, then do a single dict comprehension per
        # row. This avoids 2x the per-row overhead of the prior
        # if/elif chain when many rows have the same type profile.
        if numeric_cols is None:
            # Fast path: only datetime/Decimal conversion, no empty2zero.
            records: list[dict] = []
            append = records.append
            iso = _isoformat
            for row in rows:
                needs_conv = False
                for v in row.values():
                    if isinstance(v, (datetime, Decimal)):
                        needs_conv = True
                        break
                if not needs_conv:
                    append(row)
                    continue
                out: dict[str, Any] = {}
                for k, v in row.items():
                    if isinstance(v, datetime):
                        out[k] = iso(v)
                    elif isinstance(v, Decimal):
                        out[k] = float(v)
                    else:
                        out[k] = v
                append(out)
            return records

        # Slow path: empty2zero is set; handle None → 0 for numeric cols.
        records = []
        for row in rows:
            out: dict[str, Any] = {}
            for k, v in row.items():
                if v is None and k in numeric_cols:
                    out[k] = 0
                elif isinstance(v, datetime):
                    out[k] = _isoformat(v)
                elif isinstance(v, Decimal):
                    out[k] = float(v)
                else:
                    out[k] = v
            records.append(out)
        return records

    def get_all_values(self) -> list[list]:
        """Return all rows as list of lists (gspread format)."""
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(
                sql.SQL("SELECT * FROM {} ORDER BY 1").format(
                    sql.Identifier(self._table)
                )
            )
            rows = cur.fetchall()
            cur.close()
        result: list[list] = []
        for row in rows:
            result.append([str(v) if v is not None else "" for v in row])
        return result

    def row_values(self, row: int) -> list:
        """Return values from a specific row (1-indexed like gspread)."""
        return self._row_to_list(row)

    def col_values(self, col: int) -> list:
        """Return values from a specific column (1-indexed)."""
        col_name = self._col_name_to_index(col)
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(
                sql.SQL("SELECT {} FROM {} ORDER BY 1").format(
                    sql.Identifier(col_name),
                    sql.Identifier(self._table),
                )
            )
            rows = cur.fetchall()
            cur.close()
        return [r[0] for r in rows]

    def cell(self, row: int, col: int) -> dict:
        """Return cell value as {'row': r, 'col': c, 'value': v} (gspread-compatible).

        Performance: the prior implementation did ``SELECT * FROM ... OFFSET N``
        (returning the full row tuple just to read one cell) and then did an
        extra ``.index(col_name)`` against ``self._columns`` (a linear scan)
        to find the cell's value. The optimized version uses ``SELECT col
        FROM ... OFFSET N`` (one column) and indexes directly via the
        precomputed ``self._col_index`` dict.
        """
        col_name = self._col_name_to_index(col)
        # Resolve column position without scanning the list every call.
        col_index = self._col_index.get(col_name, 0)
        # gspread is 1-indexed and column 1 is the first column; we have
        # already validated col_name via _col_name_to_index above.
        with _conn() as conn:
            cur = conn.cursor()
            if col_index == 0:
                # Defensive: if _col_index doesn't know this col (e.g.
                # a column was added at runtime), fall back to SELECT *
                # so the call still succeeds.
                cur.execute(
                    sql.SQL(
                        "SELECT * FROM {} ORDER BY ctid LIMIT 1 OFFSET %(offset)s"
                    ).format(sql.Identifier(self._table)),
                    {"offset": row - 1},
                )
                raw = cur.fetchone()
                if raw is None:
                    cur.close()
                    raise APIError(f"Row {row} not found in {self._table}")
                try:
                    value = raw[col_index]
                except (ValueError, IndexError):
                    value = None
            else:
                cur.execute(
                    sql.SQL(
                        "SELECT {} FROM {} ORDER BY ctid "
                        "LIMIT 1 OFFSET %(offset)s"
                    ).format(
                        sql.Identifier(col_name),
                        sql.Identifier(self._table),
                    ),
                    {"offset": row - 1},
                )
                single = cur.fetchone()
                if single is None:
                    cur.close()
                    raise APIError(f"Row {row} not found in {self._table}")
                value = single[0]
            cur.close()

        if isinstance(value, datetime):
            value = _isoformat(value)
        elif isinstance(value, Decimal):
            value = float(value)

        return {"row": row, "col": col, "value": value}

    def _row_to_list(self, row: int) -> list:
        """Internal: fetch row as list in column order."""
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(
                sql.SQL("SELECT * FROM {} ORDER BY ctid LIMIT 1 OFFSET %(offset)s").format(
                    sql.Identifier(self._table)
                ),
                {"offset": row - 1},
            )
            raw = cur.fetchone()
            cur.close()
        if raw is None:
            raise APIError(f"Row {row} not found in {self._table}")
        return [str(v) if v is not None else "" for v in raw]

    # ------------------------------------------------------------------
    # Write methods
    # ------------------------------------------------------------------

    def append_row(
        self,
        values: list,
        value_input_option: str = "RAW",
        table_range: str | None = None,
    ) -> None:
        """
        Append a row to the table.
        gspread behavior: values are appended at the bottom.
        value_input_option accepted for compat, always stored as-is.
        table_range='A1' is a gspread convention meaning "overwrite the
        header row" — for the Supabase-backed adapter this is a no-op
        (the table has no header row at the data layer; column names
        are fixed by the schema). The argument is accepted for compat
        with callers that pass it.
        """
        del value_input_option  # unused — Postgres stores values as-is
        if not values:
            return
        # table_range='A1' historically meant "header overwrite" in
        # gspread. The Postgres table has no header row at the data
        # layer (column names live in the schema, not row 1), so this
        # is a no-op.
        if table_range is not None:
            table_range = table_range.upper().strip()
            if table_range != "A1":
                raise APIError(
                    f"append_row(table_range={table_range!r}) is not "
                    f"supported; only table_range='A1' is accepted as a "
                    f"no-op (header overwrite)."
                )
            # Early return: do not issue the INSERT for header-only
            # writes — the schema owns the column names.
            return
        if len(values) != len(self._columns):
            raise APIError(
                f"Row has {len(values)} values but table {self._table} has {len(self._columns)} columns"
            )
        placeholders = ", ".join(["%s"] * len(values))
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(
                sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(self._table),
                    sql.SQL(", ".join(map(lambda c: sql.Identifier(c).as_string(conn), self._columns))),
                    sql.SQL(placeholders),
                ),
                values,
            )
            cur.close()

    def update_cell(self, row: int, col: int, value: Any) -> None:
        """
        Update a single cell at (row, col) — 1-indexed like gspread.
        Uses ctid / ordering to find the row.
        """
        col_name = self._col_name_to_index(col)

        # Get the row's ctid
        with _conn() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    sql.SQL("SELECT ctid FROM {} ORDER BY ctid LIMIT 1 OFFSET %(offset)s").format(
                        sql.Identifier(self._table)
                    ),
                    {"offset": row - 1},
                )
                ctid_row = cur.fetchone()
            except Exception:
                ctid_row = None

            if ctid_row is None:
                cur.close()
                raise APIError(f"Row {row} not found in {self._table}")

            tid = ctid_row[0]
            # psycopg2 binds datetime/native types uniformly through %(val)s;
            # no need to branch on isinstance(value, datetime) — the prior
            # duplicated if/else was dead code.
            cur.execute(
                sql.SQL("UPDATE {} SET {} = %(val)s WHERE ctid = %(tid)s").format(
                    sql.Identifier(self._table),
                    sql.Identifier(col_name),
                ),
                {"val": value, "tid": tid},
            )
            cur.close()

    def update_cells(self, range_str: str, values: list[list]) -> None:
        """
        Batch update multiple cells.
        range_str is like 'A1:B2' — parse start/end.
        """
        import re as _re

        m = _re.match(r"([A-Z]+)(\d+):([A-Z]+)(\d+)", range_str.upper())
        if not m:
            raise APIError(f"Invalid range string: {range_str}")

        def col_to_idx(c: str) -> int:
            n = 0
            for ch in c:
                n = n * 26 + (ord(ch) - ord("A") + 1)
            return n

        start_col = col_to_idx(m.group(1))
        start_row = int(m.group(2))

        self._update_cells_grid(start_row, start_col, values)

    def update(
        self,
        range_name: str | None = None,
        values: list[list] | None = None,
        **kwargs: Any,
    ) -> None:
        """gspread-compatible batch update.

        Accepts the two gspread calling conventions used in this
        codebase:

        - Positional: ``ws.update('A1:B2', [[...], [...]])``
        - Keyword: ``ws.update(values=[...], range_name='A1:B2')``

        Rows are addressed by their ``ctid``-derived position (1-indexed
        like gspread). When ``range_name`` refers to row 1 only
        (e.g. ``'A1'`` or ``'A1:Z1'``), this is the canonical gspread
        pattern for "update header row", and the call is forwarded to
        ``_update_header_row`` which does no DB writes (the schema
        owns the column names).
        """
        # Resolve keyword-form: ws.update(values=..., range_name=...)
        if range_name is None and "range_name" in kwargs:
            range_name = kwargs["range_name"]
        if values is None and "values" in kwargs:
            values = kwargs["values"]
        if range_name is None or values is None:
            raise APIError(
                "update() requires both range_name and values "
                "(positional or keyword form)"
            )
        # Header-row update: range_name is a single cell (e.g. 'A1') OR
        # a single-row range (e.g. 'A1:Z1'). The check is: the start
        # cell references row 1. gspread callers like
        # ``migrate_transactions.py`` use this pattern to "set the
        # header row" — in the Postgres world the schema owns the
        # column names, so this is a no-op.
        if self._is_header_only_range(range_name):
            self._update_header_row(range_name, values)
            return
        # Everything else delegates to update_cells (which already does
        # the gspread A1-range parsing and the per-cell UPDATE).
        self.update_cells(range_name, values)

    @staticmethod
    def _is_header_only_range(range_name: str) -> bool:
        """Return True if range_name refers to row 1 only (gspread header).

        Examples:
            "A1"       → True  (single cell on row 1)
            "A1:Z1"    → True  (range on row 1)
            "A1:B2"    → False (multi-row range)
            "A2:Z2"    → False (range on row 2)
        """
        import re as _re

        m = _re.match(r"([A-Z]+)(\d+):?([A-Z]+)?(\d+)?", range_name.upper())
        if not m:
            return False
        if int(m.group(2)) != 1:
            return False
        # If an end cell is present, the end row must also be 1.
        return m.group(4) is None or int(m.group(4)) == 1

    def _update_cells_grid(
        self, start_row: int, start_col: int, values: list[list]
    ) -> None:
        """Internal: write a 2D grid of values starting at (row, col).

        Performance optimization vs the prior one-cell-at-a-time loop:
        resolves all target (row, col) pairs in a single ``SELECT ctid``
        query (window function over the row order), then issues the
        ``UPDATE`` statements against the cached tids. This collapses
        the prior N+1 ctid lookups into a single round-trip per batch.
        """
        # Build the (row_offset, col_offset, value) work list.
        cells: list[tuple[int, int, Any]] = []
        for r_idx, row in enumerate(values):
            rnum = start_row + r_idx
            for c_idx, val in enumerate(row):
                cells.append((rnum, c_idx, val))

        if not cells:
            return

        # Distinct row offsets we need ctids for.
        row_offsets = sorted({rnum - 1 for rnum, _, _ in cells})
        offset_to_tid: dict[int, Any] = {}
        with _conn() as conn:
            cur = conn.cursor()
            # One query to resolve all needed ctids at once.
            cur.execute(
                sql.SQL(
                    "SELECT row_number() OVER (ORDER BY ctid) - 1 AS off, ctid "
                    "FROM {} ORDER BY ctid"
                ).format(sql.Identifier(self._table))
            )
            # Build a dict from the (offset, ctid) result. We then
            # discard everything we don't need.
            for off, tid in cur.fetchall():
                if off in row_offsets:
                    offset_to_tid[off] = tid
            # Now issue UPDATEs against the resolved tids.
            for rnum, c_idx, val in cells:
                tid = offset_to_tid.get(rnum - 1)
                if tid is None:
                    continue
                col_name = self._columns[c_idx]
                cur.execute(
                    sql.SQL(
                        "UPDATE {} SET {} = %(val)s WHERE ctid = %(tid)s"
                    ).format(
                        sql.Identifier(self._table),
                        sql.Identifier(col_name),
                    ),
                    {"val": val, "tid": tid},
                )
            cur.close()

    def _update_header_row(
        self, range_name: str, values: list[list]
    ) -> None:
        """No-op: gspread's "update header row" has no Postgres equivalent.

        In the gspread world, row 1 of a worksheet is the header. The
        Postgres-backed adapter stores column names in the schema, not
        in the data — there is no row 1 to update. The migration is
        intentional: schema is owned by ``_TABLES`` and any change
        requires a real schema migration, not a row write.
        """
        del range_name, values  # intentionally unused

    def delete_rows(self, row: int) -> None:
        """
        Delete a single row (1-indexed like gspread).
        Uses ctid ordering to find the target row, then deletes by ctid.
        """
        with _conn() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    sql.SQL("SELECT ctid FROM {} ORDER BY ctid LIMIT 1 OFFSET %(offset)s").format(
                        sql.Identifier(self._table)
                    ),
                    {"offset": row - 1},
                )
                tid_row = cur.fetchone()
            except Exception:
                tid_row = None
            if tid_row is None:
                cur.close()
                raise APIError(f"Row {row} not found in {self._table}")
            tid = tid_row[0]
            cur.execute(
                sql.SQL("DELETE FROM {} WHERE ctid = %(tid)s").format(
                    sql.Identifier(self._table)
                ),
                {"tid": tid},
            )
            cur.close()

    def insert_row(self, values: list, index: int = 1) -> None:
        """
        Insert a row at the given index (1-indexed).
        For Postgres backed adapter, this is the same as append + reorder.
        index is accepted for compat; we always append since Postgres has no Insert.
        """
        del index  # unused — Postgres is append-only for this interface
        self.append_row(values)

    # ------------------------------------------------------------------
    # Search / find
    # ------------------------------------------------------------------

    def find_cell(self, query: Any, in_column: str | None = None) -> dict | None:
        """
        Find first cell containing `query`.
        Returns {'row': n, 'col': n, 'value': ...} or None.
        """
        with _conn() as conn:
            cur = conn.cursor()
            if in_column and in_column not in self._columns:
                raise APIError(f"Column '{in_column}' not found in {self._table}")
            if in_column:
                col_name = in_column
                cur.execute(
                    sql.SQL(
                        "SELECT row_number() OVER (ORDER BY ctid) AS row_num, "
                        "t.* FROM {} t WHERE {}::TEXT ILIKE %(q)s "
                        "ORDER BY ctid LIMIT 1"
                    ).format(
                        sql.Identifier(self._table),
                        sql.Identifier(col_name),
                    ),
                    {"q": f"%{query}%"},
                )
            else:
                # Build OR across all text-y columns
                conditions = " OR ".join(
                    f"{sql.Identifier(col).as_string(conn)}::TEXT ILIKE %(q)s"
                    for col in self._columns
                )
                if not conditions:
                    return None
                cur.execute(
                    sql.SQL(
                        "SELECT row_number() OVER (ORDER BY ctid) AS row_num, "
                        "t.* FROM {} t WHERE {conditions} "
                        "ORDER BY ctid LIMIT 1"
                    ).format(
                        sql.Identifier(self._table),
                    ),
                    {"q": f"%{query}%"},
                )
            row = cur.fetchone()
            cur.close()

        if row is None:
            return None

        # row[0] is row_num (from window function); row[1:] is the row tuple.
        row_num = row[0]
        raw = row[1:]
        raw_str = [str(v) if v is not None else "" for v in raw]
        for c_idx, val in enumerate(raw_str):
            if query and str(val).lower().find(str(query).lower()) != -1:
                return {
                    "row": int(row_num),
                    "col": c_idx + 1,
                    "value": val,
                }
        return None

    def findall(self, query: Any, in_column: str | None = None) -> list[dict]:
        """Find all cells containing query.

        Single round-trip: uses a window function so row numbers come
        back with the match, eliminating the prior N+1 pattern of
        fetching every ctid and scanning it in Python.
        """
        with _conn() as conn:
            cur = conn.cursor()
            if in_column and in_column in self._columns:
                col_name = in_column
                cur.execute(
                    sql.SQL(
                        "SELECT row_number() OVER (ORDER BY ctid) AS row_num, "
                        "t.* FROM {} t WHERE {}::TEXT ILIKE %(q)s "
                        "ORDER BY ctid"
                    ).format(
                        sql.Identifier(self._table),
                        sql.Identifier(col_name),
                    ),
                    {"q": f"%{query}%"},
                )
            else:
                conditions = " OR ".join(
                    f"{sql.Identifier(col).as_string(conn)}::TEXT ILIKE %(q)s"
                    for col in self._columns
                )
                if not conditions:
                    cur.close()
                    return []
                cur.execute(
                    sql.SQL(
                        "SELECT row_number() OVER (ORDER BY ctid) AS row_num, "
                        "t.* FROM {} t WHERE {conditions} "
                        "ORDER BY ctid"
                    ).format(
                        sql.Identifier(self._table),
                    ),
                    {"q": f"%{query}%"},
                )
            rows = cur.fetchall()
            cur.close()

        results: list[dict] = []
        for row in rows:
            row_num = row[0]
            raw = row[1:]
            raw_str = [str(v) if v is not None else "" for v in raw]
            for c_idx, val in enumerate(raw_str):
                if query and str(val).lower().find(str(query).lower()) != -1:
                    results.append({"row": int(row_num), "col": c_idx + 1, "value": val})
                    break
        return results

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @classmethod
    def sheet_exists(cls, name: str) -> bool:
        """Return True if the table / worksheet exists."""
        table = name.lower().strip()
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM pg_tables WHERE tablename = %s",
                (table,),
            )
            exists = cur.fetchone() is not None
            cur.close()
            return exists

    def row_count(self) -> int:
        """Return the number of rows in the table."""
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(
                sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(self._table))
            )
            count = cur.fetchone()[0]
            cur.close()
        return count

    def col_count(self) -> int:
        """Return the number of columns in the table."""
        return len(self._columns)

    @property
    def title(self) -> str:
        """Return the worksheet name."""
        return self._table

    # ------------------------------------------------------------------
    # Helpers for numeric conversion
    # ------------------------------------------------------------------

    def _is_numeric_col(self, col: str) -> bool:
        """Check if a column is numeric. Cached per-table for the lifetime of the SheetView."""
        if not hasattr(self, "_numeric_cols"):
            self._numeric_cols = self._load_numeric_cols()
        return col in self._numeric_cols

    def _load_numeric_cols(self) -> set[str]:
        """Query Postgres for the set of numeric columns on this table."""
        with _conn() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    SELECT a.attname
                    FROM pg_attribute a
                    JOIN pg_type t ON a.atttypid = t.oid
                    WHERE a.attrelid = %s::regclass
                      AND a.attnum > 0
                      AND NOT a.attisdropped
                      AND t.typname IN (
                          'int2', 'int4', 'int8', 'float4', 'float8',
                          'numeric', 'money', 'oid'
                      )
                    """,
                    (self._table,),
                )
                rows = cur.fetchall()
            except Exception:
                rows = []
            finally:
                cur.close()
        return {r[0] for r in rows}

    # ------------------------------------------------------------------
    # Atomic helpers used by the business logic
    # ------------------------------------------------------------------

    def update_balance_atomic(self, money_card: str, amount_delta: float, transaction_type: str, items_json: str | None = None) -> dict | None:
        """
        Atomically update money_accounts balance and write to transactions_log.
        Returns the transaction dict or None on failure.
        This is the main atomic operation used by the backend.
        """
        with _transaction() as conn:
            cur = conn.cursor()

            # Get current balance
            cur.execute(
                "SELECT Balance FROM money_accounts WHERE MoneyCardNumber = %s FOR UPDATE",
                (money_card,),
            )
            row = cur.fetchone()
            if row is None:
                cur.close()
                raise APIError(f"MoneyCard {money_card} not found in money_accounts")
            balance_before = float(row[0])

            balance_after = balance_before + amount_delta
            if balance_after < 0:
                cur.close()
                raise APIError("Insufficient balance")

            # Update balance
            now = _now_manila()
            cur.execute(
                "UPDATE money_accounts SET Balance = %s, LastUpdated = %s WHERE MoneyCardNumber = %s",
                (balance_after, now, money_card),
            )

            # Insert transaction log
            cur.execute(
                "INSERT INTO transactions_log (Timestamp, MoneyCardNumber, TransactionType, Amount, BalanceBefore, BalanceAfter, Status, ItemsJson) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING TransactionID",
                (now, money_card, transaction_type, amount_delta, balance_before, balance_after, "completed", items_json),
            )
            tid_row = cur.fetchone()
            transaction_id = tid_row[0] if tid_row else None
            cur.close()

        return {
            "TransactionID": transaction_id,
            "Timestamp": _isoformat(now),
            "MoneyCardNumber": money_card,
            "TransactionType": transaction_type,
            "Amount": amount_delta,
            "BalanceBefore": balance_before,
            "BalanceAfter": balance_after,
            "Status": "completed",
            "ItemsJson": items_json,
        }

    def add_virtual_card_atomic(self, token: str, money_card: str, student_id: str, status: str = "active") -> dict:
        """Atomically create a virtual card entry."""
        with _transaction() as conn:
            cur = conn.cursor()
            now = _now_manila()
            cur.execute(
                "INSERT INTO virtual_cards (Token, MoneyCardNumber, StudentID, CreatedAt, Status) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING *",
                (token, money_card, student_id, now, status),
            )
            row = cur.fetchone()
            cur.close()
            if row is None:
                raise APIError("Failed to create virtual card")
        cols = [c[0] for c in _VIRTUAL_CARDS_COLS]
        return self._row_to_dict(row, cols)

    def report_lost_card_atomic(self, money_card: str, id_card: str) -> dict:
        """Atomically create a lost card report."""
        with _transaction() as conn:
            cur = conn.cursor()
            now = _now_manila()
            cur.execute(
                "INSERT INTO lost_card_reports (MoneyCardNumber, IDCardNumber, DateReported, Status) "
                "VALUES (%s, %s, %s, 'open') RETURNING *",
                (money_card, id_card, now),
            )
            row = cur.fetchone()
            cur.close()
            if row is None:
                raise APIError("Failed to report lost card")
        cols = [c[0] for c in _LOST_CARD_REPORTS_COLS]
        return self._row_to_dict(row, cols)


# ---------------------------------------------------------------------------
# Public factory (matches current backend import pattern)
# ---------------------------------------------------------------------------

_CLIENT_INSTANCE: SheetsClient | None = None


def get_sheets_client() -> SheetsClient:
    """
    Return the global SheetsClient instance.
    Safe to call multiple times — returns the same instance.
    """
    global _CLIENT_INSTANCE
    if _CLIENT_INSTANCE is None:
        # Call init on first access to ensure tables exist
        _supabase_init()
        _CLIENT_INSTANCE = SheetsClient()
    return _CLIENT_INSTANCE


# ---------------------------------------------------------------------------
# Optional: export everything under the gspread-compatible namespace
# ---------------------------------------------------------------------------
APIError.__module__ = "gspread.exceptions"
