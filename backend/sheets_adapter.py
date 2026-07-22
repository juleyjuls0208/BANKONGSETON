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
from uuid import UUID

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


def _to_manila(dt):
    if dt is None or not hasattr(dt, "tzinfo"):
        return dt
    if dt.tzinfo is None:
        return dt.replace(tzinfo=MANILA_TZ) if MANILA_TZ else dt
    return dt.astimezone(MANILA_TZ) if MANILA_TZ else dt


def _isoformat(dt) -> str:
    if dt is None:
        return ""
    converted = _to_manila(dt)
    return converted.isoformat() if hasattr(converted, "isoformat") else str(converted)


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
    discarded = False
    try:
        yield conn
    except Exception:
        # A broken Supabase connection must not be returned to the pool.  The
        # next request gets a fresh connection instead of repeating a timeout.
        p.putconn(conn, close=True)
        discarded = True
        raise
    finally:
        if not discarded:
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
    ("IDCardNumber", "id_card_number", "VARCHAR(14)"),
    ("MoneyCardNumber", "money_card_number", "VARCHAR(14)"),
    ("Status", "status", "user_status DEFAULT 'Active'"),
    ("StudentEmail", "parent_email", "VARCHAR(255)"),
    ("DateRegistered", "date_registered", "DATE"),
    ("FCMToken", "fcm_token", "TEXT"),
]

_MONEY_ACCOUNTS_COLS = [
    ("MoneyCardNumber", "money_card_number", "VARCHAR(14) PRIMARY KEY"),
    ("LinkedIDCard", "student_id_card", "VARCHAR(14) NOT NULL"),
    ("Balance", "balance", "NUMERIC(14,2) DEFAULT 0.00 CHECK (balance >= 0 AND balance <> 'NaN'::numeric AND balance <> 'Infinity'::numeric AND balance <> '-Infinity'::numeric)"),
    ("Status", "status", "account_status DEFAULT 'Active'"),
    ("LastUpdated", "last_updated", "TIMESTAMPTZ DEFAULT NOW()"),
    ("TotalLoaded", "total_loaded", "NUMERIC(14,2) DEFAULT 0.00 CHECK (total_loaded >= 0 AND total_loaded <> 'NaN'::numeric AND total_loaded <> 'Infinity'::numeric AND total_loaded <> '-Infinity'::numeric)"),
    ("CreatedAt", "created_at", "TIMESTAMPTZ DEFAULT NOW()"),
]

_TRANSACTIONS_LOG_COLS = [
    ("TransactionID", "transaction_id", "VARCHAR(50) PRIMARY KEY"),
    ("Timestamp", "timestamp", "TIMESTAMPTZ DEFAULT NOW()"),
    ("StudentID", "student_id", "VARCHAR(50)"),
    ("MoneyCardNumber", "money_card_number", "VARCHAR(14) NOT NULL"),
    ("TransactionType", "transaction_type", "transaction_type NOT NULL"),
    ("Amount", "amount", "NUMERIC(14,2) NOT NULL CHECK (amount <> 'NaN'::numeric AND amount <> 'Infinity'::numeric AND amount <> '-Infinity'::numeric)"),
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
    ("OldCardNumber", "old_card_number", "VARCHAR(14) NOT NULL"),
    ("NewCardNumber", "new_card_number", "VARCHAR(14)"),
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
    ("ID", "product_id", "VARCHAR(20) UNIQUE NOT NULL"),
    ("Name", "name", "VARCHAR(255) NOT NULL"),
    ("Category", "category", "VARCHAR(50)"),
    ("Price", "price", "NUMERIC(14,2) NOT NULL"),
    ("ImageURL", "image_url", "TEXT DEFAULT ''"),
    ("Active", "active", "product_active DEFAULT 'TRUE'"),
    ("DateAdded", "date_added", "TIMESTAMPTZ DEFAULT NOW()"),
    ("CreatedAt", "created_at", "TIMESTAMPTZ DEFAULT NOW()"),
    ("UpdatedAt", "updated_at", "TIMESTAMPTZ DEFAULT NOW()"),
]

_CASHIER_ACCOUNTS_COLS = [
    ("AccountID", "id", "UUID PRIMARY KEY"),
    ("Username", "username", "VARCHAR(100) UNIQUE NOT NULL"),
    ("PasswordHash", "password_hash", "VARCHAR(255) NOT NULL"),
    ("DisplayName", "display_name", "VARCHAR(255)"),
    ("Status", "is_active", "BOOLEAN DEFAULT TRUE"),
    ("CreatedAt", "created_at", "TIMESTAMPTZ DEFAULT NOW()"),
    ("LastLogin", "updated_at", "TIMESTAMPTZ DEFAULT NOW()"),
]

_VIRTUAL_CARDS_COLS = [
    ("StudentID", "student_id", "VARCHAR(50) NOT NULL"),
    ("Token", "virtual_card_token", "VARCHAR(64) PRIMARY KEY"),
    ("DeviceToken", "device_token", "TEXT NOT NULL"),
    ("MoneyCardNumber", "money_card_number", "VARCHAR(14) NOT NULL"),
    ("CreatedAt", "created_at", "TIMESTAMPTZ DEFAULT NOW()"),
    ("Status", "is_active", "virtual_card_status DEFAULT 'TRUE'"),
    ("DeactivatedAt", "deactivated_at", "TIMESTAMPTZ"),
]

# Mobile login security: per-student PIN hash + bound device (one device per account).
_STUDENT_AUTH_COLS = [
    ("StudentID", "student_id", "VARCHAR(50) PRIMARY KEY"),
    ("PinHash", "pin_hash", "TEXT DEFAULT ''"),
    ("DeviceId", "device_id", "TEXT DEFAULT ''"),
    ("UpdatedAt", "updated_at", "TIMESTAMPTZ DEFAULT NOW()"),
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
    "cashier_accounts": _CASHIER_ACCOUNTS_COLS,
    "virtual_cards": _VIRTUAL_CARDS_COLS,
    "student_auth": _STUDENT_AUTH_COLS,
}

_TABLE_COLUMNS: dict[str, list[str]] = {t: [c[0] for c in cols] for t, cols in _TABLES.items()}
_PHYS: dict[str, dict[str, str]] = {t: {c[0]: c[1] for c in cols} for t, cols in _TABLES.items()}
_KEY_COLUMNS = {
    "users": "StudentID", "money_accounts": "MoneyCardNumber",
    "transactions_log": "TransactionID", "lost_card_reports": "ReportID",
    "settings": "Key", "products": "ID", "cashier_accounts": "AccountID",
    "virtual_cards": "Token", "student_auth": "StudentID",
}


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
    "cashier_accounts": "cashier_accounts",
    "cashier accounts": "cashier_accounts",
    "virtual_cards": "virtual_cards",
    "student_auth": "student_auth",
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
            # ponytail: enable RLS at creation so any table added later (e.g.
            # student_auth) can never ship with RLS off. The backend connects
            # as postgres superuser, which bypasses RLS, so app queries are
            # unaffected — this only closes the PostgREST anon/authenticated
            # hole. Mirrors supabase/migrations/*_enable_rls.sql.
            cur.execute(
                sql.SQL("ALTER TABLE {} ENABLE ROW LEVEL SECURITY").format(
                    sql.Identifier(table_name)
                )
            )
            cur.execute(
                sql.SQL(
                    "DROP POLICY IF EXISTS allow_service_role_{} ON {}"
                ).format(sql.SQL(table_name), sql.Identifier(table_name))
            )
            cur.execute(
                sql.SQL(
                    "CREATE POLICY allow_service_role_{} ON {} "
                    "FOR ALL TO postgres, service_role "
                    "USING (true) WITH CHECK (true)"
                ).format(sql.SQL(table_name), sql.Identifier(table_name))
            )
        for index, stmt in enumerate([
                'CREATE INDEX IF NOT EXISTS idx_transactions_mcn ON transactions_log("money_card_number")',
                'CREATE INDEX IF NOT EXISTS idx_transactions_ts ON transactions_log("timestamp")',
                'CREATE INDEX IF NOT EXISTS idx_lost_card_mcn ON lost_card_reports("old_card_number")',
                'CREATE INDEX IF NOT EXISTS idx_virtual_cards_mcn ON virtual_cards("money_card_number")',
                'CREATE UNIQUE INDEX IF NOT EXISTS uq_users_id_card_nonblank ON users("id_card_number") WHERE NULLIF("id_card_number", \'\') IS NOT NULL',
                'CREATE UNIQUE INDEX IF NOT EXISTS uq_users_money_card_nonblank ON users("money_card_number") WHERE NULLIF("money_card_number", \'\') IS NOT NULL',
                'CREATE UNIQUE INDEX IF NOT EXISTS uq_money_accounts_card_nonblank ON money_accounts("money_card_number") WHERE NULLIF(trim("money_card_number"), \'\') IS NOT NULL',
                'ALTER TABLE money_accounts ADD CONSTRAINT money_accounts_balance_nonnegative CHECK (balance >= 0 AND balance <> \'NaN\'::numeric AND balance <> \'Infinity\'::numeric AND balance <> \'-Infinity\'::numeric)',
                'ALTER TABLE money_accounts ADD CONSTRAINT money_accounts_total_loaded_nonnegative CHECK (total_loaded >= 0 AND total_loaded <> \'NaN\'::numeric AND total_loaded <> \'Infinity\'::numeric AND total_loaded <> \'-Infinity\'::numeric)',
            ]):
                try:
                    cur.execute(f"SAVEPOINT schema_guard_{index}")
                    cur.execute(stmt)
                    cur.execute(f"RELEASE SAVEPOINT schema_guard_{index}")
                except Exception:
                    cur.execute(f"ROLLBACK TO SAVEPOINT schema_guard_{index}")
                    cur.execute(f"RELEASE SAVEPOINT schema_guard_{index}")
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
            return SheetView(_TABLE_LOOKUP[table], client=self)
        # Supabase schemas are deployed data contracts.  Creating an untyped
        # ``id/data`` table from a request makes later reads silently use the
        # wrong columns and lets application traffic mutate the schema.
        raise WorksheetNotFound(title)

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

    def _row_offset(self, row: int) -> int:
        if row < 2:
            raise APIError("Spreadsheet row 1 is the read-only header")
        return row - 2

    def _key_name(self) -> str:
        return _KEY_COLUMNS[self._table]

    def _compat_value(self, column: str, value: Any) -> Any:
        if self._table == "cashier_accounts" and column == "Status":
            return "Active" if bool(value) else "Inactive"
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            return _isoformat(value)
        if isinstance(value, Decimal):
            return float(value)
        return value

    def _row_to_dict(self, row: tuple, columns: list[str]) -> dict:
        result: dict[str, Any] = {}
        for i, col in enumerate(columns):
            val = row[i] if i < len(row) else None
            result[col] = self._compat_value(col, val)
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

        records: list[dict] = []
        for row in rows:
            if not hasattr(row, "items"):
                row = dict(zip(self._columns, row))
            out: dict[str, Any] = {}
            for k, v in row.items():
                if numeric_cols is not None and v is None and k in numeric_cols:
                    out[k] = 0
                else:
                    out[k] = self._compat_value(k, v)
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
        if row == 1:
            return {"row": 1, "col": col, "value": col_name}
        offset = self._row_offset(row)
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(
                sql.SQL("SELECT {} FROM {} ORDER BY 1 LIMIT 1 OFFSET %s").format(
                    _phys(self._table, col_name), sql.Identifier(self._table)
                ),
                (offset,),
            )
            single = cur.fetchone()
            cur.close()
        if single is None:
            raise APIError(f"Row {row} not found in {self._table}")
        value = single[0]
        if isinstance(value, datetime):
            value = _isoformat(value)
        elif isinstance(value, Decimal):
            value = float(value)
        return {"row": row, "col": col, "value": value}

    def _row_to_list(self, row: int) -> list:
        if row == 1:
            return list(self._columns)
        offset = self._row_offset(row)
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(sql.SQL("SELECT {} FROM {} ORDER BY 1 LIMIT 1 OFFSET %s").format(
                _proj(self._table), sql.Identifier(self._table)), (offset,))
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
                raise APIError(f"append_row(table_range={table_range!r}) is not supported")
            # ``A1`` is only a header-write convention in gspread.  A business
            # row must never disappear merely because a legacy caller supplied
            # that optional argument.
            if list(values) == self._columns:
                return
            raise APIError("append_row(table_range='A1') is only valid for the canonical header row")
        if len(values) != len(self._columns):
            raise APIError(f"Row has {len(values)} values but table {self._table} has {len(self._columns)} columns")
        values = list(values)
        if self._table == "users":
            for column in ("IDCardNumber", "MoneyCardNumber", "StudentEmail", "DateRegistered", "FCMToken"):
                index = self._col_index[column]
                if values[index] == "":
                    values[index] = None
        if self._table == "cashier_accounts":
            status_idx = self._col_index["Status"]
            values[status_idx] = str(values[status_idx]).strip().lower() in {"active", "true", "1", "yes"}
            last_login_idx = self._col_index["LastLogin"]
            if values[last_login_idx] == "":
                values[last_login_idx] = None
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
        if self._table == "cashier_accounts" and col_name == "Status":
            value = str(value).strip().lower() in {"active", "true", "1", "yes"}
        if self._table == "cashier_accounts" and col_name == "LastLogin" and value == "":
            value = None
        offset = self._row_offset(row)
        key_name = self._key_name()
        key_phys = _phys(self._table, key_name)
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(sql.SQL("SELECT {} FROM {} ORDER BY 1 LIMIT 1 OFFSET %s").format(
                key_phys, sql.Identifier(self._table)), (offset,))
            key_row = cur.fetchone()
            if key_row is None:
                cur.close()
                raise APIError(f"Row {row} not found in {self._table}")
            cur.execute(sql.SQL("UPDATE {} SET {} = %s WHERE {} = %s").format(
                sql.Identifier(self._table), _phys(self._table, col_name), key_phys),
                (value, key_row[0]))
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
                if rnum == 1:
                    continue
                cells.append((rnum, start_col + c_idx, val))
        if not cells:
            return
        key_name = self._key_name()
        key_phys = _phys(self._table, key_name)
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(sql.SQL("SELECT {} FROM {} ORDER BY 1").format(
                key_phys, sql.Identifier(self._table)))
            keys = [row[0] for row in cur.fetchall()]
            for rnum, c_idx, val in cells:
                offset = self._row_offset(rnum)
                if offset < 0 or offset >= len(keys):
                    raise APIError(f"Row {rnum} not found in {self._table}")
                if c_idx < 1 or c_idx > len(self._columns):
                    raise APIError(f"Column index {c_idx} out of range for {self._table}")
                cur.execute(sql.SQL("UPDATE {} SET {} = %s WHERE {} = %s").format(
                    sql.Identifier(self._table), _phys(self._table, self._columns[c_idx - 1]), key_phys),
                    (val, keys[offset]))
            conn.commit()
            cur.close()

    def _update_header_row(self, range_name: str, values: list[list]) -> None:
        del range_name, values

    def delete_rows(self, row: int) -> None:
        offset = self._row_offset(row)
        key_phys = _phys(self._table, self._key_name())
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(sql.SQL("SELECT {} FROM {} ORDER BY 1 LIMIT 1 OFFSET %s").format(
                key_phys, sql.Identifier(self._table)), (offset,))
            key_row = cur.fetchone()
            if key_row is None:
                cur.close()
                raise APIError(f"Row {row} not found in {self._table}")
            cur.execute(sql.SQL("DELETE FROM {} WHERE {} = %s").format(
                sql.Identifier(self._table), key_phys), (key_row[0],))
            conn.commit()
            cur.close()

    def update_where(self, column: str, value: Any, set_column: str, set_value: Any) -> int:
        """Set set_column=set_value on every row where (camelCase) column exactly equals value.

        ponytail: value-based update (mirrors delete_where) so we never depend on
        Stable logical row offset for gspread compatibility. Used for soft-deletes.
        """
        phys = _PHYS[self._table].get(column, column)
        set_phys = _PHYS[self._table].get(set_column, set_column)
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(
                sql.SQL("UPDATE {} SET {} = %(set_val)s WHERE {}::TEXT = %(val)s").format(
                    sql.Identifier(self._table), sql.Identifier(set_phys), sql.Identifier(phys)
                ),
                {"set_val": set_value, "val": str(value)},
            )
            n = cur.rowcount
            conn.commit()
            cur.close()
        return n

    def delete_where(self, column: str, value: Any) -> int:
        """Delete every row where the (camelCase) column exactly equals value.

        ponytail: real fix for the findall/delete_rows off-by-one. findall()
        numbers rows within its FILTERED result, but delete_rows(n) offsets over
        the WHOLE table by physical storage order, so findall's row number is wrong
        whenever the target isn't the first physical row (deletes the wrong row).
        Deleting by column value sidesteps row numbering entirely.
        """
        phys = _PHYS[self._table].get(column, column)
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute(
                sql.SQL("DELETE FROM {} WHERE {}::TEXT = %(val)s").format(
                    sql.Identifier(self._table), sql.Identifier(phys)
                ),
                {"val": str(value)},
            )
            n = cur.rowcount
            conn.commit()
            cur.close()
        return n

    def insert_row(self, values: list, index: int = 1) -> None:
        del index
        self.append_row(values)

    def find_cell(self, query: Any, in_column: str | None = None) -> dict | None:
        matches = self.findall(query, in_column=in_column)
        return matches[0] if matches else None

    def findall(self, query: Any, in_column: str | None = None) -> list[dict]:
        if in_column and in_column not in self._columns:
            raise APIError(f"Column '{in_column}' not found in {self._table}")
        query_text = str(query).lower()
        matches = []
        for row_num, record in enumerate(self.get_all_records(), start=2):
            columns = [in_column] if in_column else self._columns
            for col in columns:
                value = record.get(col)
                if query_text in str(value if value is not None else '').lower():
                    matches.append({"row": row_num, "col": self._columns.index(col) + 1,
                                    "value": '' if value is None else str(value)})
                    break
        return matches

    def find(self, query: Any, in_column: str | None = None) -> dict | None:
        # gspread searches the header row too; our Postgres records do not
        # contain it, so expose the virtual row 1 before searching data.
        if in_column is None:
            query_text = str(query).strip().lower()
            for index, column in enumerate(self._columns, start=1):
                if column.lower() == query_text:
                    return {"row": 1, "col": index, "value": column}
        return self.find_cell(query, in_column=in_column)

    def batch_update(self, data: list[dict]) -> None:
        # gspread drop-in: data is a list of {"range": "A1", "values": [[...]]}.
        # Ranges use A1 notation; translate to (row, col) grid updates.
        import re as _re

        def _a1_to_rc(a1: str) -> tuple[int, int]:
            m = _re.match(r"([A-Z]+)(\d+)", a1.strip().upper())
            if not m:
                raise APIError(f"Invalid A1 range in batch_update: {a1!r}")
            col = 0
            for ch in m.group(1):
                col = col * 26 + (ord(ch) - ord("A") + 1)
            return int(m.group(2)), col

        for item in data:
            rng = (item.get("range") or "").split(":")[0]
            values = item.get("values") or [[]]
            start_row, start_col = _a1_to_rc(rng)
            self._update_cells_grid(start_row, start_col, values)

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

    def update_balance_atomic(
        self,
        money_card: str,
        amount_delta: float,
        transaction_type: str,
        items_json: str | None = None,
        student_id: str | None = None,
        *,
        idempotency_key: str | None = None,
        total_loaded_delta: float = 0,
        station_id: str | None = None,
    ) -> dict:
        """Mutate one account and write its ledger row in one DB transaction."""
        from decimal import Decimal, InvalidOperation
        import math

        try:
            delta = Decimal(str(amount_delta))
            loaded_delta = Decimal(str(total_loaded_delta))
        except (InvalidOperation, ValueError):
            raise APIError("Invalid money amount")
        if not delta.is_finite() or not loaded_delta.is_finite():
            raise APIError("Money amount must be finite")
        if not idempotency_key:
            raise APIError("Idempotency key is required")
        if len(idempotency_key) > 50:
            raise APIError("Idempotency key is too long")

        with _transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT transaction_id, timestamp, student_id, money_card_number, "
                "transaction_type, amount, balance_before, balance_after, status, items_json "
                "FROM transactions_log WHERE transaction_id = %s",
                (idempotency_key,),
            )
            existing = cur.fetchone()
            if existing is not None:
                cur.close()
                return {
                    "TransactionID": existing[0], "Timestamp": _isoformat(existing[1]),
                    "StudentID": existing[2], "MoneyCardNumber": existing[3],
                    "TransactionType": existing[4], "Amount": float(existing[5]),
                    "BalanceBefore": float(existing[6]), "BalanceAfter": float(existing[7]),
                    "Status": existing[8], "ItemsJson": existing[9], "Idempotent": True,
                }

            cur.execute(
                "SELECT balance, total_loaded, status FROM money_accounts "
                "WHERE money_card_number = %s FOR UPDATE",
                (money_card,),
            )
            row = cur.fetchone()
            if row is None:
                cur.close()
                raise APIError(f"MoneyCard {money_card} not found in money_accounts")
            status = str(row[2] or "Active").lower()
            if status not in {"active", "true"}:
                cur.close()
                raise APIError(f"MoneyCard is {row[2]}")
            balance_before = Decimal(str(row[0] or 0))
            balance_after = balance_before + delta
            if balance_after < 0:
                cur.close()
                raise APIError("Insufficient balance")
            loaded_after = Decimal(str(row[1] or 0)) + loaded_delta
            now = _now_manila()
            cur.execute(
                "UPDATE money_accounts SET balance = %s, total_loaded = %s, last_updated = %s "
                "WHERE money_card_number = %s",
                (balance_after, loaded_after, now, money_card),
            )
            cur.execute(
                "INSERT INTO transactions_log "
                "(transaction_id, timestamp, student_id, money_card_number, transaction_type, amount, "
                "balance_before, balance_after, status, items_json, cashier_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Success', %s, %s)",
                (idempotency_key, now, student_id, money_card, transaction_type, delta,
                 balance_before, balance_after, items_json, station_id),
            )
            cur.close()
        return {
            "TransactionID": idempotency_key, "Timestamp": _isoformat(now),
            "StudentID": student_id, "MoneyCardNumber": money_card,
            "TransactionType": transaction_type, "Amount": float(delta),
            "BalanceBefore": float(balance_before), "BalanceAfter": float(balance_after),
            "Status": "Success", "ItemsJson": items_json, "Idempotent": False,
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
