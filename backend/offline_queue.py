"""
Offline Write Queue — SQLite-backed
Buffers cashier transactions when Google Sheets is unreachable.
Syncs automatically on the next successful Sheets operation.
"""
import sqlite3
import json
import os
import logging
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from errors import get_logger
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)

# DB file sits next to this module
_DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), 'offline_queue.db')


class SQLiteWriteQueue:
    """
    Persistent offline queue backed by SQLite.

    Operations are stored as JSON blobs with status 'pending', 'synced', or 'failed'.
    A background thread attempts to drain the queue whenever connectivity is restored.

    Usage:
        queue = get_offline_queue()
        queue.enqueue('append_row', 'Transactions Log', [...row data...])

        # After Sheets reconnects:
        synced, failed = queue.process_queue(sheets_client)
    """

    STATUS_PENDING = 'pending'
    STATUS_SYNCED  = 'synced'
    STATUS_FAILED  = 'failed'

    def __init__(self, db_path: str = _DEFAULT_DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA foreign_keys=ON')
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS write_queue (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation   TEXT    NOT NULL,
                    sheet_name  TEXT    NOT NULL,
                    data        TEXT    NOT NULL,
                    status      TEXT    NOT NULL DEFAULT 'pending',
                    created_at  TEXT    NOT NULL,
                    synced_at   TEXT,
                    error_msg   TEXT,
                    retry_count INTEGER NOT NULL DEFAULT 0
                )
            ''')
            conn.commit()

    def enqueue(self, operation: str, sheet_name: str, data: Any) -> int:
        """
        Add a write operation to the queue.

        Args:
            operation:  'append_row' or 'update_cell'
            sheet_name: Google Sheets worksheet name
            data:       For append_row: list of values.
                        For update_cell: {'row': int, 'col': int, 'value': Any}

        Returns:
            Row ID of the queued item.
        """
        ts = datetime.now().isoformat()
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                '''INSERT INTO write_queue (operation, sheet_name, data, status, created_at)
                   VALUES (?, ?, ?, ?, ?)''',
                (operation, sheet_name, json.dumps(data), self.STATUS_PENDING, ts)
            )
            conn.commit()
            row_id = cur.lastrowid
        logger.info("event=queue_enqueue id=%d op=%s sheet=%s", row_id, operation, sheet_name)
        return row_id

    def get_pending(self) -> List[Dict]:
        """Return all pending items in insertion order."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM write_queue WHERE status=? ORDER BY id ASC",
                (self.STATUS_PENDING,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_status(self) -> Dict[str, Any]:
        """Return queue health summary."""
        with self._connect() as conn:
            pending = conn.execute(
                "SELECT COUNT(*) FROM write_queue WHERE status=?", (self.STATUS_PENDING,)
            ).fetchone()[0]
            failed = conn.execute(
                "SELECT COUNT(*) FROM write_queue WHERE status=?", (self.STATUS_FAILED,)
            ).fetchone()[0]
            synced = conn.execute(
                "SELECT COUNT(*) FROM write_queue WHERE status=?", (self.STATUS_SYNCED,)
            ).fetchone()[0]
            last_sync_row = conn.execute(
                "SELECT synced_at FROM write_queue WHERE status=? ORDER BY id DESC LIMIT 1",
                (self.STATUS_SYNCED,)
            ).fetchone()
        return {
            'pending': pending,
            'failed': failed,
            'synced': synced,
            'last_sync_at': last_sync_row[0] if last_sync_row else None,
            'db_path': self.db_path,
        }

    def process_queue(self, sheets_client) -> tuple:
        """
        Drain the pending queue using the provided Google Sheets client.

        Returns:
            (synced_count, failed_count)
        """
        pending = self.get_pending()
        if not pending:
            return 0, 0

        synced = 0
        failed = 0

        for item in pending:
            success = self._execute_item(sheets_client, item)
            ts = datetime.now().isoformat()
            status = self.STATUS_SYNCED if success else self.STATUS_FAILED
            with self._lock, self._connect() as conn:
                conn.execute(
                    '''UPDATE write_queue
                       SET status=?, synced_at=?, retry_count=retry_count+1
                       WHERE id=?''',
                    (status, ts, item['id'])
                )
                conn.commit()
            if success:
                synced += 1
                logger.info("event=queue_synced id=%d", item['id'])
            else:
                failed += 1
                logger.warning("event=queue_sync_failed id=%d", item['id'])

        return synced, failed

    def _execute_item(self, sheets_client, item: Dict) -> bool:
        try:
            data = json.loads(item['data'])
            ws = sheets_client.worksheet(item['sheet_name'])
            if item['operation'] == 'append_row':
                ws.append_row(data)
            elif item['operation'] == 'update_cell':
                ws.update_cell(data['row'], data['col'], data['value'])
            else:
                logger.warning("event=queue_unknown_op op=%s", item['operation'])
                return False
            return True
        except Exception as e:
            with self._lock, self._connect() as conn:
                conn.execute(
                    "UPDATE write_queue SET error_msg=? WHERE id=?",
                    (str(e)[:500], item['id'])
                )
                conn.commit()
            logger.warning("event=queue_exec_failed id=%d error=%s", item['id'], e)
            return False

    def clear_synced(self) -> int:
        """Delete synced records older than 7 days to keep DB small."""
        cutoff = datetime.now().replace(hour=0, minute=0).isoformat()
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM write_queue WHERE status=? AND synced_at < ?",
                (self.STATUS_SYNCED, cutoff)
            )
            conn.commit()
        return cur.rowcount


# Singleton
_offline_queue: Optional[SQLiteWriteQueue] = None


def get_offline_queue(db_path: str = _DEFAULT_DB_PATH) -> SQLiteWriteQueue:
    """Get or create the SQLiteWriteQueue singleton."""
    global _offline_queue
    if _offline_queue is None:
        _offline_queue = SQLiteWriteQueue(db_path)
    return _offline_queue
