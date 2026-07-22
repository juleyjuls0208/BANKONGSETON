"""Tamper-evident recovery queue for a debit already confirmed by the data store.

This queue never authorizes a new offline payment. It only preserves a missing
ledger row after the balance debit already succeeded, then retries that ledger
write when connectivity returns.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from errors import get_logger
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)


_DEFAULT_DB_PATH = Path(__file__).with_name("offline_queue.db")
_TRANSACTION_LOG = "Transactions Log"
_OPERATION = "append_transaction_log"


class SQLiteWriteQueue:
    """Persist signed ledger-recovery records until the data store is reachable."""

    STATUS_PENDING = "pending"
    STATUS_SYNCED = "synced"
    STATUS_FAILED = "failed"

    def __init__(self, db_path: str | Path = _DEFAULT_DB_PATH, *, signing_key: bytes | str | None = None):
        self.db_path = str(db_path)
        self._lock = threading.Lock()
        self._signing_key = self._resolve_signing_key(signing_key)
        self._init_db()

    @staticmethod
    def _resolve_signing_key(signing_key: bytes | str | None) -> bytes:
        key = signing_key or os.getenv("OFFLINE_QUEUE_SIGNING_KEY") or os.getenv("FLASK_SECRET_KEY")
        if isinstance(key, str):
            key = key.encode("utf-8")
        if not key or len(key) < 16:
            raise RuntimeError("A strong FLASK_SECRET_KEY or OFFLINE_QUEUE_SIGNING_KEY is required for offline recovery")
        return key

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS write_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    sheet_name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    transaction_id TEXT,
                    signature TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    synced_at TEXT,
                    error_msg TEXT,
                    retry_count INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            columns = {row[1] for row in conn.execute("PRAGMA table_info(write_queue)")}
            if "transaction_id" not in columns:
                conn.execute("ALTER TABLE write_queue ADD COLUMN transaction_id TEXT")
            if "signature" not in columns:
                conn.execute("ALTER TABLE write_queue ADD COLUMN signature TEXT")
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS write_queue_transaction_id "
                "ON write_queue(transaction_id) WHERE transaction_id IS NOT NULL"
            )

    def _payload(self, transaction_id: str, row: list[Any]) -> bytes:
        return json.dumps(
            {"operation": _OPERATION, "transaction_id": transaction_id, "row": row},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    def _sign(self, transaction_id: str, row: list[Any]) -> str:
        return hmac.new(self._signing_key, self._payload(transaction_id, row), hashlib.sha256).hexdigest()

    def enqueue_transaction_log(self, transaction_id: str, row: list[Any]) -> int:
        """Queue only a completed debit's missing transaction-log row."""
        transaction_id = str(transaction_id or "").strip()
        if not transaction_id or not isinstance(row, list) or not row or str(row[0]).strip() != transaction_id:
            raise ValueError("Offline recovery requires a matching transaction ID and transaction-log row")

        row_json = json.dumps(row, separators=(",", ":"))
        signature = self._sign(transaction_id, row)
        with self._lock, self._connect() as conn:
            existing = conn.execute(
                "SELECT id FROM write_queue WHERE transaction_id=?", (transaction_id,)
            ).fetchone()
            if existing:
                return int(existing[0])
            cur = conn.execute(
                """INSERT INTO write_queue
                   (operation, sheet_name, data, transaction_id, signature, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    _OPERATION,
                    _TRANSACTION_LOG,
                    row_json,
                    transaction_id,
                    signature,
                    self.STATUS_PENDING,
                    datetime.now().isoformat(),
                ),
            )
            return int(cur.lastrowid)

    def get_pending(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM write_queue WHERE status=? ORDER BY id ASC", (self.STATUS_PENDING,)
            ).fetchall()
        return [dict(row) for row in rows]

    def get_status(self) -> Dict[str, Any]:
        with self._connect() as conn:
            counts = {
                status: conn.execute(
                    "SELECT COUNT(*) FROM write_queue WHERE status=?", (status,)
                ).fetchone()[0]
                for status in (self.STATUS_PENDING, self.STATUS_FAILED, self.STATUS_SYNCED)
            }
            last_sync = conn.execute(
                "SELECT synced_at FROM write_queue WHERE status=? ORDER BY id DESC LIMIT 1",
                (self.STATUS_SYNCED,),
            ).fetchone()
        return {
            "pending": counts[self.STATUS_PENDING],
            "failed": counts[self.STATUS_FAILED],
            "synced": counts[self.STATUS_SYNCED],
            "last_sync_at": last_sync[0] if last_sync else None,
        }

    def _mark(self, item_id: int, status: str, *, error: str = "", synced: bool = False) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """UPDATE write_queue
                   SET status=?, synced_at=?, error_msg=?, retry_count=retry_count+1
                   WHERE id=?""",
                (status, datetime.now().isoformat() if synced else None, error[:500] or None, item_id),
            )

    def _verify(self, item: Dict[str, Any]) -> list[Any] | None:
        if item.get("operation") != _OPERATION or item.get("sheet_name") != _TRANSACTION_LOG:
            return None
        try:
            row = json.loads(item["data"])
        except (TypeError, json.JSONDecodeError):
            return None
        transaction_id = str(item.get("transaction_id") or "").strip()
        signature = str(item.get("signature") or "")
        if not transaction_id or not isinstance(row, list) or not row or str(row[0]).strip() != transaction_id:
            return None
        return row if hmac.compare_digest(signature, self._sign(transaction_id, row)) else None

    def process_queue(self, sheets_client) -> tuple[int, int]:
        """Retry signed recovery rows; transient errors stay pending for the next poll."""
        synced = failed = 0
        for item in self.get_pending():
            row = self._verify(item)
            if row is None:
                self._mark(item["id"], self.STATUS_FAILED, error="Integrity check failed")
                failed += 1
                logger.error("event=queue_rejected id=%s reason=integrity_check_failed", item["id"])
                continue
            try:
                worksheet = sheets_client.worksheet(_TRANSACTION_LOG)
                transaction_id = item["transaction_id"]
                existing = worksheet.get_all_records()
                if not any(str(record.get("TransactionID", "")).strip() == transaction_id for record in existing):
                    worksheet.append_row(row)
                self._mark(item["id"], self.STATUS_SYNCED, synced=True)
                synced += 1
            except Exception as exc:
                self._mark(item["id"], self.STATUS_PENDING, error=str(exc))
                failed += 1
                logger.warning("event=queue_sync_deferred id=%s error=%s", item["id"], exc)
        return synced, failed

    def clear_synced(self) -> int:
        cutoff = datetime.now().replace(hour=0, minute=0).isoformat()
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM write_queue WHERE status=? AND synced_at < ?", (self.STATUS_SYNCED, cutoff)
            )
            return cur.rowcount


_offline_queue: Optional[SQLiteWriteQueue] = None


def get_offline_queue(db_path: str | Path = _DEFAULT_DB_PATH) -> SQLiteWriteQueue:
    global _offline_queue
    if _offline_queue is None:
        _offline_queue = SQLiteWriteQueue(db_path)
    return _offline_queue
