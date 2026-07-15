"""Self-check for the stale-connection retry in sheets_adapter._conn.

Runs connectionless: we monkeypatch the pool so getconn() hands a fake
connection that raises psycopg2.OperationalError once, then works. This
proves the retry guard yields a live conn instead of propagating the error.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # repo root

import psycopg2
from backend import sheets_adapter as sa


class _FakeConn:
    def __init__(self):
        self.calls = 0
        self.closed = False

    def rollback(self):
        self.calls += 1
        # first attempt across the whole pool is dead; a fresh (post-rebuild)
        # attempt is alive. Mirrors a stale pooled conn vs a new socket.
        if _FakeConn._global_calls < 1:
            _FakeConn._global_calls += 1
            raise psycopg2.OperationalError("server closed the connection")
        _FakeConn._global_calls += 1

    def close(self):
        self.closed = True


_FakeConn._global_calls = 0


class _FakePool:
    def getconn(self):
        return _FakeConn()  # each new socket gets a fresh counter-gated fate

    def putconn(self, conn, close=False):
        if close:
            conn.close()

    def closeall(self):
        pass


def test_conn_retry_survives_one_dead_connection():
    _FakeConn._global_calls = 0
    real_pool = sa._CONNECTION_POOL
    real_get = sa._get_pool
    fake = _FakePool()
    try:
        sa._CONNECTION_POOL = fake
        sa._get_pool = lambda: fake
        with sa._conn() as conn:
            assert conn is not None
            assert _FakeConn._global_calls >= 2  # 1 dead + 1 alive probe ran
    finally:
        sa._CONNECTION_POOL = real_pool
        sa._get_pool = real_get


if __name__ == "__main__":
    test_conn_retry_survives_one_dead_connection()
    print("OK: _conn() retries past one dead pooled connection")
