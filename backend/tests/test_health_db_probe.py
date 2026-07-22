"""Ponytail check: every health route probes the DB for real, never lies.

Run: .venv/Scripts/python -m pytest backend/tests/test_health_db_probe.py -o addopts=""
"""
import re
import pathlib
from contextlib import contextmanager

import sheets_adapter as s

_BACKEND = pathlib.Path(__file__).resolve().parent.parent


class _DummyPool:
    pass


@contextmanager
def _raising_conn():
    raise s.APIError("DB down")
    yield  # pragma: no cover


def test_test_connection_false_on_dead_db(monkeypatch):
    monkeypatch.setattr(s, "_supabase_init", lambda: None)
    monkeypatch.setattr(s, "_CONNECTION_POOL", _DummyPool())
    monkeypatch.setattr(s, "_get_pool", lambda: _DummyPool())
    monkeypatch.setattr(s, "get_sheets_client", lambda: s.SheetsClient())
    monkeypatch.setattr(s, "_conn", _raising_conn)
    assert s.get_sheets_client().test_connection() is False


_HEALTH_DEF = re.compile(r"def (health|tech_health)\(")
_ROUTE_OR_DEF = re.compile(r"^(@app\.route|^def |^    def )")


def test_no_health_route_fakes_db():
    """Inside a health-route body, no worksheets()/db-is-not-None fake check."""
    offenders = []
    for path in (_BACKEND / "kiosk", _BACKEND / "dashboard",
                 _BACKEND / "tech", _BACKEND / "api"):
        for f in path.glob("*.py"):
            lines = f.read_text(encoding="utf-8").splitlines()
            in_health = False
            for ln in lines:
                if _HEALTH_DEF.search(ln):
                    in_health = True
                    continue
                if in_health and _ROUTE_OR_DEF.match(ln):
                    in_health = False
                    continue
                if in_health and ("worksheets()" in ln or "db is not None" in ln):
                    offenders.append(f"{f.name}: {ln.strip()}")
    assert not offenders, "health route still fakes DB:\n" + "\n".join(offenders)
