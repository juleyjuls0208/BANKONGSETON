"""
sheets_adapter.py
Drop-in gspread replacement backed by Supabase Postgres (psycopg2).

ponytail: the live DB columns are snake_case and differ per table
(app_users: studentid / moneycardnumber; money_accounts: money_card_number /
student_id_card; ...). The in-code contract (the call sites) uses camelCase
dict keys. _TABLES is the single source of truth as (camelKey, snakeColumn,
dtype); every SQL column ref is translated to the real snake column via
_phys(), and reads alias snake -> camel so the dict keys callers expect are
preserved. One mapping, not 381 fixes. The schema is rebuilt from the real
live table definitions (orphan camelCase columns from a prior botched
migration are dropped).
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

warnings.filterwarnings("ignore", category=DeprecationWarning, module="psycopg2")
warnings.filterwarnings("ignore", message=".*connection is not open.*")
warnings.filterwarnings("ignore", message=".*SSL is not enabled.*")

_MANILA_TZ = datetime.now().astimezone().tzinfo
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

MANILA_TZ = ZoneInfo("Asia/Manila") if ZoneInfo else None
_UTC = UTC


def _now_manila() -> datetime:
    if MANILA_TZ:
        return datetime.now(MANILA_TZ)
    return datetime.utcnow().replace(tzinfo=_UTC) + __import__("timedelta")(hours=8)


def _to_manila(dt: datetime) -> datetime:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=MANILA_TZ) if MANILA_TZ else dt
    return dt.astimezone(MANILA_TZ) if MANILA_TZ else dt


def _isoformat(dt: datetime) -> str:
    return _to_manila(dt).isoformat() if dt is not None else ""


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return _to_manila(value)
    try:
        return _to_manila(datetime.fromisoformat(str(value).replace("Z", "+00:00")))
    except Exception:
        return None


class APIError(Exception):
    def __init__(self, msg: str, code: str | None = None):
        super().__init__(msg)
        self.code = code or "unknown"


class SpreadsheetNotFound(APIError):
    def __init__(self, name: str):
        super().__init__(f"Spreadsheet not found: {name}", code="not_found")
        self.spreadsheet = name


class WorksheetNotFound(APIError):
    def __init__(self, name: str):
        super().__init__(f"Worksheet not found: {name}", code="worksheet_not_found")
        self.worksheet = name


class CellNotFound(APIError):
    def __init__(self, query: str):
        super().__init__(f"Cell not found: {query}", code="cell_not_found")
        self.query = query


_DATABASE_URL: str | None = None
_CONNECTION_POOL: pool.ThreadedConnectionPool | None = None


def _get_pool() -> pool.ThreadedConnectionPool:
    global _CONNECTION_POOL
    if _CONNECTION_POOL is None:
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise APIError("DATABASE_URL environment variable is not set.")
        try:
            _CONNECTION_POOL = pool.ThreadedConnectionPool(
                minconn=1, maxconn=10, dsn=url,
                connect_timeout=30, options="-c client_encoding=UTF8",
            )
        except psycopg2.Error as e:
            raise APIError(f"Failed to connect to Postgres: {e}") from e
    return _CONNECTION_POOL


@contextmanager
def _conn() -> Generator[Any, None, None]:
    p = _get_pool()
    conn = p.getconn()
    try:
        yield conn
    finally:
        p.putconn(conn)


@contextmanager
def _transaction() -> Generator[Any, None, None]:
    with _conn() as conn:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


# ---------------------------------------------------------------------------
# Schema definition (rebuilt from the live Supabase tables)
# (camelKey, REAL snake_column, dtype)
# ---------------------------------------------------------------------------

_USERS_COLS = [
    ("StudentID", "student_id", "VARCHAR(50) PRIMARY KEY"),
    ("Name", "name", "VARCHAR(255) NOT NULL"),
    ("IDCardNumber", "id_card_number", "VARCHAR(8)"),
    ("MoneyCardNumber", "money_card_number", "VARCHAR(8)"),
    ("Status", "status", "user_status DEFAULT 'Active'"),
    ("ParentEmail", "parent_email", "VARCHAR(255)"),
    ("DateRegistered", "date_registered", "DATE"),
    ("FCMToken", "fcm_token", "TEXT"),
]

_MONEY_ACCOUNTS_COLS = [
    ("MoneyCardNumber", "money_card_number", "VARCHAR(8) PRIMARY KEY"),
    ("LinkedIDCard", "student_id_card", "VARCHAR(8) NOT NULL"),
    ("Balance", "balance", "NUMERIC(14,2) DEFAULT 0.00"),
    ("Status", "status", "account_status DEFAULT 'Active'"),
    ("LastUpdated", "last_updated", "TIMESTAMPTZ DEFAULT NOW()"),
    ("TotalLoaded", "total_loaded", "NUMERIC(14,2) DEFAULT 0.00"),
    ("CreatedAt", "created_at", "TIMESTAMPTZ DEFAULT NOW()"),
]

_TRANSACTIONS_LOG_COLS = [
    ("TransactionID", "transaction_id", "VARCHAR(50) PRIMARY KEY"),
    ("Timestamp", "timestamp", "TIMESTAMPTZ DEFAULT NOW()"),
    ("StudentID", "student_id", "VARCHAR(50)"),
    ("MoneyCardNumber", "money_card_number", "VARCHAR(8) NOT NULL"),
    ("TransactionType", "transaction_type", "transaction_type NOT NULL"),
    ("Amount", "amount", "NUMERIC(14,2) NOT NULL"),
    ("BalanceBefore", "balance_before", "NUMERIC(14,2)"),
    ("BalanceAfter", "balance_after", "NUMERIC(14,2)"),
    ("Status", "status", "transaction_status DEFAULT 'Success'"),
    ("ErrorMessage", "error_message", "VARCHAR(255) DEFAULT ''"),
    ("ItemsJson", "items_json", "TEXT"),
    ("CashierID", "cashier_id", "VARCHAR(50)"),
    ("CreatedAt", "created_at", "TIMESTAMPTZ DEFAULT NOW()"),
]

_LOST_CARD_REPORTS_COLS = [
    ("ReportID", "report_id", "VARCHAR(20) PRIMARY KEY"),
    ("ReportDate", "report_date", "TIMESTAMPTZ DEFAULT NOW()"),
    ("StudentID", "student_id", "VARCHAR(50) NOT NULL"),
    ("OldCardNumber", "old_card_number", "VARCHAR(8) NOT NULL"),
    ("NewCardNumber", "new_card_number", "VARCHAR(8)"),
    ("TransferredBalance", "transferred_balance", "NUMERIC(14,2)"),
    ("ReportedBy", "reported_by", "VARCHAR(50)"),
    ("Status", "status", "lost_card_status DEFAULT 'Pending'"),
    ("CreatedAt", "created_at", "TIMESTAMPTZ DEFAULT NOW()"),
]

_SETTINGS_COLS = [
    ("Key", "key", "VARCHAR(100) PRIMARY KEY"),
    ("Value", "value", "TEXT NOT NULL"),
    ("Description", "description", "TEXT"),
    ("CreatedAt", "created_at", "TIMESTAMPTZ DEFAULT NOW()"),
    ("UpdatedAt", "updated_at", "TIMESTAMPTZ DEFAULT NOW()"),
]

_PRODUCTS_COLS = [
    ("ProductID", "product_id", "VARCHAR(20) PRIMARY KEY"),
    ("Name", "name", "VARCHAR(255) NOT NULL"),
    ("Category", "category", "VARCHAR(50)"),
    ("Price", "price", "NUMERIC(14,2) NOT NULL"),
    ("ImageURL", "image_url", "TEXT DEFAULT ''"),
    ("Active", "active", "product_active DEFAULT 'TRUE'"),
    ("DateAdded", "date_added", "TIMESTAMPTZ DEFAULT NOW()"),
    ("CreatedAt", "created_at", "TIMESTAMPTZ DEFAULT NOW()"),
    ("UpdatedAt", "updated_at", "TIMESTAMPTZ DEFAULT NOW()"),
]

_VIRTUAL_CARDS_COLS = [
    ("StudentID", "student_id", "VARCHAR(50) NOT NULL"),
    ("Token", "virtual_card_token", "VARCHAR(64) PRIMARY KEY"),
    ("DeviceToken", "device_token", "TEXT NOT NULL"),
    ("MoneyCardNumber", "money_card_number", "VARCHAR(8) NOT NULL"),
    ("CreatedAt", "created_at", "TIMESTAMPTZ DEFAULT NOW()"),
    ("Status", "is_active", "virtual_card_status DEFAULT 'TRUE'"),
    ("DeactivatedAt", "deactivated_at", "TIMESTAMPTZ"),
]

# ponytail: in-code key "users" maps to the real physical table "users"
# (Supabase Auth lives in the auth schema, so public.users is ours).
_TABLES: dict[str, list[tuple[str, str, str]]] = {
    "users": _USERS_COLS,
    "money_accounts": _MONEY_ACCOUNTS_COLS,
    "transactions_log": _TRANSACTIONS_LOG_COLS,
    "lost_card_reports": _LOST_CARD_REPORTS_COLS,
    "settings": _SETTINGS_COLS,
    "products": _PRODUCTS_COLS,
    "virtual_cards": _VIRTUAL_CARDS_COLS,
}

_TABLE_COLUMNS: dict[str, list[str]] = {t: [c[0] for c in cols] for t, cols in _TABLES.items()}
_PHYS: dict[str, dict[str, str]] = {t: {c[0]: c[1] for c in cols} for t, cols in _TABLES.items()}


def _phys(table: str, camel: str) -> Any:
    return sql.Identifier(_PHYS[table].get(camel, camel))


def _proj(table: str) -> Any:
    return sql.SQL(", ").join(
        sql.SQL("{} AS {}").format(_phys(table, c), sql.Identifier(c))
        for c in _TABLE_COLUMNS[table]
    )


_TABLE_LOOKUP: dict[str, str] = {
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
    """Create all tables if they don't exist. Safe to call on every startup."""
    with _transaction() as conn:
        cur = conn.cursor()
        for table_name, columns in _TABLES.items():
            col_defs = sql.SQL(", ").join(
                sql.SQL("{} {}").format(sql.Identifier(p), sql.SQL(d))
                for _, p, d in columns
            )
            cur.execute(
                sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
                    sql.Identifier(table_name), col_defs
                )
            )
        for stmt in [
            'CREATE INDEX IF NOT EXISTS idx_transactions_mcn ON transactions_log("money_card_number")',
            'CREATE INDEX IF NOT EXISTS idx_transactions_ts ON transactions_log("timestamp")',
            'CREATE INDEX IF NOT EXISTS idx_lost_card_mcn ON lost_card_reports("old_card_number")',
            'CREATE INDEX IF NOT EXISTS idx_virtual_cards_mcn ON virtual_cards("money_card_number")',
        ]:
            try:
                cur.execute(stmt)
            except Exception:
                pass
        cur.close()


class SheetsClient:
    def __init__(self) -> None:
        _get_pool()

    def worksheet(self, name: str) -> "SheetView":
        table = name.lower().strip()
        if table not in _TABLE_LOOKUP:
            raise WorksheetNotFound(name)
        return SheetView(_TABLE_LOOKUP[table], client=self)

    def open(self, key: str) -> "SheetsClient":
        return self

    def open_by_url(self, url: str) -> "SheetsClient":
        return self

    def list_sheets(self) -> list[dict]:
        return [{"title": t} for t in _TABLE_LOOKUP]

    @property
    def sheets(self) -> list[dict]:
        return self.list_sheets()

    def worksheets(self) -> list["SheetView"]:
        return [SheetView(t, client=self) for t in _TABLES]

    def add_worksheet(self, title: str, rows: int = 100, cols: int = 10) -> "SheetView":
        del rows, cols
        table = title.lower().strip()
        if table in _TABLE_LOOKUP:
            return SheetView(table, client=self)
        if table not in _TABLES:
            _TABLES[table] = [("id", "id", "SERIAL PRIMARY KEY"), ("data", "data", "JSONB")]
            _TABLE_COLUMNS[table] = ["id", "data"]
            _PHYS[table] = {"id": "id", "data": "data"}
            _TABLE_LOOKUP[table] = table
            with _transaction() as conn:
                cur = conn.cursor()
                cur.execute(
                    sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
                        sql.Identifier(table),
                        sql.SQL(", ").join(
                            sql.SQL("{} {}").format(sql.Identifier(p), sql.SQL(d))
                            for _, p, d in _TABLES[table]
                        ),
                    )
                )
                cur.close()
        return SheetView(table, client=self)

    def test_connection(self) -> bool:
        try:
            with _conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return cur.fetchone()[0] == 1
        except Exception:
            return False


class SheetView:
    def __init__(self, table: str, client: SheetsClient) -> None:
        self._table = table
        self._client = client
        self._columns: list[str] = _TABLE_COLUMNS.get(table, [])
        self._col_index: dict[str, int] = {name: i for i, name in enumerate(self._columns)}

    def _col_name_to_index(self, col: int) -> str:
        if col < 1 or col > len(self._columns):
            raise APIError(f"Column index {col} out of range for {self._table}")
        return self._columns[col - 1]

    def _row_to_dict(self, row: tuple, columns: list[str]) -> dict:
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
        return [record.get(col) for col in self._columns]

    def get_all_records(self, empty2zero: bool = False, major_dimension: str = "ROWS") -> list[dict]:
        del major_dimension
        with _conn() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(sql.SQL("SELECT {} FROM {} ORDER BY 1").format(_proj(self._table), sql.Identifier(self._table)))
            rows = cur.fetchall()
            cur.close()

        if empty2zero:
            numeric_cols = getattr(self, "_numeric_cols", None)
            if numeric_cols is None:
                numeric_cols = self._load_numeric_cols()
                self._numeric_cols = numeric_cols
        else:
            numeric_cols = None

        if numeric_cols is None:
            records: list[dict] = []
            append = records.append
            iso = _isoformat
            for row in rows:
                needs_conv = any(isinstance(v, (datetime, Decimal)) for v in row.values())
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
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(sql.SQL("SELECT {} FROM {} ORDER BY 1").format(_proj(self._table), sql.Identifier(self._table)))
            rows = cur.fetchall()
            cur.close()
        return [[str(v) if v is not None else "" for v in row] for row in rows]

    def row_values(self, row: int) -> list:
        return self._row_to_list(row)

    def col_values(self, col: int) -> list:
        col_name = self._col_name_to_index(col)
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(sql.SQL("SELECT {} FROM {} ORDER BY 1").format(_phys(self._table, col_name), sql.Identifier(self._table)))
            rows = cur.fetchall()
            cur.close()
        return [r[0] for r in rows]

    def cell(self, row: int, col: int) -> dict:
        col_name = self._col_name_to_index(col)
        col_index = self._col_index.get(col_name, 0)
        with _conn() as conn:
            cur = conn.cursor()
            if col_index == 0:
                cur.execute(
                    sql.SQL("SELECT * FROM {} ORDER BY ctid LIMIT 1 OFFSET %(offset)s").format(sql.Identifier(self._table)),
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
                    sql.SQL("SELECT {} FROM {} ORDER BY ctid LIMIT 1 OFFSET %(offset)s").format(_phys(self._table, col_name), sql.Identifier(self._table)),
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
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(sql.SQL("SELECT * FROM {} ORDER BY ctid LIMIT 1 OFFSET %(offset)s").format(sql.Identifier(self._table)), {"offset": row - 1})
            raw = cur.fetchone()
            cur.close()
        if raw is None:
            raise APIError(f"Row {row} not found in {self._table}")
        return [str(v) if v is not None else "" for v in raw]

    def append_row(self, values: list, value_input_option: str = "RAW", table_range: str | None = None) -> None:
        del value_input_option
        if not values:
            return
        if table_range is not None:
            table_range = table_range.upper().strip()
            if table_range != "A1":
                raise APIError(f"append_row(table_range={table_range!r}) is not supported; only table_range='A1' is accepted as a no-op (header overwrite).")
            return
        if len(values) != len(self._columns):
            raise APIError(f"Row has {len(values)} values but table {self._table} has {len(self._columns)} columns")
        placeholders = ", ".join(["%s"] * len(values))
        with _conn() as conn:
            cur = conn.cursor()
            phys_cols = sql.SQL(", ").join(_phys(self._table, c) for c in self._columns)
            cur.execute(
                sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(sql.Identifier(self._table), phys_cols, sql.SQL(placeholders)),
                values,
            )
            conn.commit()
            cur.close()

    def update_cell(self, row: int, col: int, value: Any) -> None:
        col_name = self._col_name_to_index(col)
        with _conn() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    sql.SQL("SELECT ctid FROM {} ORDER BY ctid LIMIT 1 OFFSET %(offset)s").format(sql.Identifier(self._table)),
                    {"offset": row - 1},
                )
                ctid_row = cur.fetchone()
            except Exception:
                ctid_row = None
            if ctid_row is None:
                cur.close()
                raise APIError(f"Row {row} not found in {self._table}")
            tid = ctid_row[0]
            cur.execute(
                sql.SQL("UPDATE {} SET {} = %(val)s WHERE ctid = %(tid)s").format(sql.Identifier(self._table), _phys(self._table, col_name)),
                {"val": value, "tid": tid},
            )
            conn.commit()
            cur.close()

    def update_cells(self, range_str: str, values: list[list]) -> None:
        import re as _re
        m = _re.match(r"([A-Z]+)(\d+):([A-Z]+)(\d+)", range_str.upper())
        if not m:
            raise APIError(f"Invalid range string: {range_str}")

        def col_to_idx(c: str) -> int:
            n = 0
            for ch in c:
                n = n * 26 + (ord(ch) - ord("A") + 1)
            return n

        self._update_cells_grid(int(m.group(2)), col_to_idx(m.group(1)), values)

    def update(self, range_name: str | None = None, values: list[list] | None = None, **kwargs: Any) -> None:
        if range_name is None and "range_name" in kwargs:
            range_name = kwargs["range_name"]
        if values is None and "values" in kwargs:
            values = kwargs["values"]
        if range_name is None or values is None:
            raise APIError("update() requires both range_name and values (positional or keyword form)")
        if self._is_header_only_range(range_name):
            self._update_header_row(range_name, values)
            return
        self.update_cells(range_name, values)

    @staticmethod
    def _is_header_only_range(range_name: str) -> bool:
        import re as _re
        m = _re.match(r"([A-Z]+)(\d+):?([A-Z]+)?(\d+)?", range_name.upper())
        if not m:
            return False
        if int(m.group(2)) != 1:
            return False
        return m.group(4) is None or int(m.group(4)) == 1

    def _update_cells_grid(self, start_row: int, start_col: int, values: list[list]) -> None:
        cells: list[tuple[int, int, Any]] = []
        for r_idx, row in enumerate(values):
            rnum = start_row + r_idx
            for c_idx, val in enumerate(row):
                cells.append((rnum, c_idx, val))
        if not cells:
            return
        row_offsets = sorted({rnum - 1 for rnum, _, _ in cells})
        offset_to_tid: dict[int, Any] = {}
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(sql.SQL("SELECT row_number() OVER (ORDER BY ctid) - 1 AS off, ctid FROM {} ORDER BY ctid").format(sql.Identifier(self._table)))
            for off, tid in cur.fetchall():
                if off in row_offsets:
                    offset_to_tid[off] = tid
            for rnum, c_idx, val in cells:
                tid = offset_to_tid.get(rnum - 1)
                if tid is None:
                    continue
                col_name = self._columns[c_idx]
                cur.execute(
                    sql.SQL("UPDATE {} SET {} = %(val)s WHERE ctid = %(tid)s").format(sql.Identifier(self._table), _phys(self._table, col_name)),
                    {"val": val, "tid": tid},
                )
            conn.commit()
            cur.close()

    def _update_header_row(self, range_name: str, values: list[list]) -> None:
        del range_name, values

    def delete_rows(self, row: int) -> None:
        with _conn() as conn:
            cur = conn.cursor()
            try:
                cur.execute(sql.SQL("SELECT ctid FROM {} ORDER BY ctid LIMIT 1 OFFSET %(offset)s").format(sql.Identifier(self._table)), {"offset": row - 1})
                tid_row = cur.fetchone()
            except Exception:
                tid_row = None
            if tid_row is None:
                cur.close()
                raise APIError(f"Row {row} not found in {self._table}")
            tid = tid_row[0]
            cur.execute(sql.SQL("DELETE FROM {} WHERE ctid = %(tid)s").format(sql.Identifier(self._table)), {"tid": tid})
            conn.commit()
            cur.close()

    def insert_row(self, values: list, index: int = 1) -> None:
        del index
        self.append_row(values)

    def find_cell(self, query: Any, in_column: str | None = None) -> dict | None:
        with _conn() as conn:
            cur = conn.cursor()
            if in_column and in_column not in self._columns:
                raise APIError(f"Column '{in_column}' not found in {self._table}")
            if in_column:
                cur.execute(
                    sql.SQL("SELECT row_number() OVER (ORDER BY ctid) AS row_num, {} FROM {} t WHERE {}::TEXT ILIKE %(q)s ORDER BY ctid LIMIT 1")
                    .format(_proj(self._table), sql.Identifier(self._table), _phys(self._table, in_column)),
                    {"q": f"%{query}%"},
                )
            else:
                conditions = " OR ".join(f"{_phys(self._table, col).as_string(conn)}::TEXT ILIKE %(q)s" for col in self._columns)
                if not conditions:
                    return None
                cur.execute(
                    sql.SQL("SELECT row_number() OVER (ORDER BY ctid) AS row_num, {} FROM {} t WHERE {} ORDER BY ctid LIMIT 1")
                    .format(_proj(self._table), sql.Identifier(self._table), sql.SQL(conditions)),
                    {"q": f"%{query}%"},
                )
            row = cur.fetchone()
            cur.close()
        if row is None:
            return None
        row_num = row[0]
        raw = row[1:]
        raw_str = [str(v) if v is not None else "" for v in raw]
        for c_idx, val in enumerate(raw_str):
            if query and str(val).lower().find(str(query).lower()) != -1:
                return {"row": int(row_num), "col": c_idx + 1, "value": val}
        return None

    def findall(self, query: Any, in_column: str | None = None) -> list[dict]:
        with _conn() as conn:
            cur = conn.cursor()
            if in_column and in_column in self._columns:
                cur.execute(
                    sql.SQL("SELECT row_number() OVER (ORDER BY ctid) AS row_num, {} FROM {} t WHERE {}::TEXT ILIKE %(q)s ORDER BY ctid")
                    .format(_proj(self._table), sql.Identifier(self._table), _phys(self._table, in_column)),
                    {"q": f"%{query}%"},
                )
            else:
                conditions = " OR ".join(f"{_phys(self._table, col).as_string(conn)}::TEXT ILIKE %(q)s" for col in self._columns)
                if not conditions:
                    cur.close()
                    return []
                cur.execute(
                    sql.SQL("SELECT row_number() OVER (ORDER BY ctid) AS row_num, {} FROM {} t WHERE {} ORDER BY ctid")
                    .format(_proj(self._table), sql.Identifier(self._table), sql.SQL(conditions)),
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

    @classmethod
    def sheet_exists(cls, name: str) -> bool:
        table = name.lower().strip()
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM pg_tables WHERE tablename = %s", (table,))
            exists = cur.fetchone() is not None
            cur.close()
            return exists

    def row_count(self) -> int:
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(self._table)))
            count = cur.fetchone()[0]
            cur.close()
        return count

    def col_count(self) -> int:
        return len(self._columns)

    @property
    def title(self) -> str:
        return self._table

    def _is_numeric_col(self, col: str) -> bool:
        if not hasattr(self, "_numeric_cols"):
            self._numeric_cols = self._load_numeric_cols()
        return col in self._numeric_cols

    def _load_numeric_cols(self) -> set[str]:
        with _conn() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    SELECT a.attname FROM pg_attribute a
                    JOIN pg_type t ON a.atttypid = t.oid
                    WHERE a.attrelid = %s::regclass AND a.attnum > 0
                      AND NOT a.attisdropped
                      AND t.typname IN ('int2','int4','int8','float4','float8','numeric','money','oid')
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

    def update_balance_atomic(self, money_card: str, amount_delta: float, transaction_type: str, items_json: str | None = None, student_id: str | None = None) -> dict | None:
        with _transaction() as conn:
            cur = conn.cursor()
            cur.execute("SELECT balance FROM money_accounts WHERE money_card_number = %s FOR UPDATE", (money_card,))
            row = cur.fetchone()
            if row is None:
                cur.close()
                raise APIError(f"MoneyCard {money_card} not found in money_accounts")
            balance_before = float(row[0])
            balance_after = balance_before + amount_delta
            if balance_after < 0:
                cur.close()
                raise APIError("Insufficient balance")
            now = _now_manila()
            cur.execute("UPDATE money_accounts SET balance = %s, last_updated = %s WHERE money_card_number = %s", (balance_after, now, money_card))
            cur.execute(
                "INSERT INTO transactions_log "
                "(transaction_id, timestamp, student_id, money_card_number, transaction_type, amount, balance_before, balance_after, status, items_json) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Success', %s) RETURNING transaction_id",
                ('TXN-' + now.strftime("%Y%m%d%H%M%S") + os.urandom(3).hex(), now, student_id, money_card, transaction_type, amount_delta, balance_before, balance_after, items_json),
            )
            tid_row = cur.fetchone()
            transaction_id = tid_row[0] if tid_row else None
            cur.close()
        return {
            "TransactionID": transaction_id, "Timestamp": _isoformat(now), "StudentID": student_id,
            "MoneyCardNumber": money_card, "TransactionType": transaction_type, "Amount": amount_delta,
            "BalanceBefore": balance_before, "BalanceAfter": balance_after, "Status": "Success", "ItemsJson": items_json,
        }

    def add_virtual_card_atomic(self, token: str, money_card: str, student_id: str, device_token: str = "", status: str = "TRUE") -> dict:
        with _transaction() as conn:
            cur = conn.cursor()
            now = _now_manila()
            cur.execute(
                sql.SQL(
                    "INSERT INTO virtual_cards "
                    "(student_id, virtual_card_token, device_token, money_card_number, created_at, is_active) "
                    "VALUES (%s, %s, %s, %s, %s, %s) RETURNING {}"
                ).format(_proj("virtual_cards")),
                (student_id, token, device_token, money_card, now, status),
            )
            row = cur.fetchone()
            cur.close()
            if row is None:
                raise APIError("Failed to create virtual card")
        return self._row_to_dict(row, _TABLE_COLUMNS["virtual_cards"])

    def report_lost_card_atomic(self, money_card: str, id_card: str, student_id: str | None = None, new_card_number: str | None = None) -> dict:
        with _transaction() as conn:
            cur = conn.cursor()
            now = _now_manila()
            cur.execute(
                sql.SQL(
                    "INSERT INTO lost_card_reports "
                    "(student_id, old_card_number, new_card_number, reported_by, report_date, status) "
                    "VALUES (%s, %s, %s, %s, %s, 'Pending') RETURNING {}"
                ).format(_proj("lost_card_reports")),
                (student_id, money_card, new_card_number, id_card, now),
            )
            row = cur.fetchone()
            cur.close()
            if row is None:
                raise APIError("Failed to report lost card")
        return self._row_to_dict(row, _TABLE_COLUMNS["lost_card_reports"])


_CLIENT_INSTANCE: SheetsClient | None = None


def get_sheets_client() -> SheetsClient:
    global _CLIENT_INSTANCE
    if _CLIENT_INSTANCE is None:
        _supabase_init()
        _CLIENT_INSTANCE = SheetsClient()
    return _CLIENT_INSTANCE


APIError.__module__ = "gspread.exceptions"
