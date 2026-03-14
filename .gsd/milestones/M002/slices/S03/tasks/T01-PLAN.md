---
estimated_steps: 4
estimated_files: 2
---

# T01: Add WEB_CONCURRENCY startup guard to web_app.py and admin_dashboard.py

**Slice:** S03 — FraudDetector Constraint & Health Standardization
**Milestone:** M002

## Description

FraudDetector keeps module-level singleton state (`_fraud_sheets_initialized`, the `_fraud_detector` object). When gunicorn forks multiple workers, each worker gets its own copy of this state — Sheets writes from one worker are invisible to others, so alert state diverges silently. The fix is a hard-fail guard at WSGI import time that exits with code 1 and a human-readable message if `WEB_CONCURRENCY > 1` or `GUNICORN_WORKERS > 1`.

Two entry points must be guarded:
- `web_app.py` — the PythonAnywhere production WSGI entry point (imported by `wsgi.py`); this is the one gunicorn actually runs.
- `admin_dashboard.py` — the local dev entry point; guards local misconfig and keeps behavior consistent.

## Steps

1. Open `backend/dashboard/web_app.py`. After the FINANCE_PASSWORD guard block (around line 80), insert the WEB_CONCURRENCY guard. Follow the established `logger.critical(...) ; sys.exit(1)` pattern used by the existing three guards:

```python
# --- WEB_CONCURRENCY guard (R016 / FraudDetector Worker Safety) ---
def _parse_worker_count(env_var: str) -> int:
    try:
        return int(os.environ.get(env_var, "1") or "1")
    except (ValueError, TypeError):
        return 1

if _parse_worker_count("WEB_CONCURRENCY") > 1 or _parse_worker_count("GUNICORN_WORKERS") > 1:
    logger.critical(
        "event=startup_aborted reason=multi_worker_forbidden "
        "message=\"FraudDetector requires single-worker mode. "
        "Set WEB_CONCURRENCY=1 in your gunicorn config.\""
    )
    sys.exit(1)
```

2. Open `backend/dashboard/admin_dashboard.py`. After the FLASK_SECRET_KEY guard block (around line 66), insert the same guard using the `print()` + `sys.exit(1)` style already used in that file:

```python
# --- WEB_CONCURRENCY guard (R016 / FraudDetector Worker Safety) ---
def _parse_worker_count(env_var: str) -> int:
    try:
        return int(os.environ.get(env_var, "1") or "1")
    except (ValueError, TypeError):
        return 1

if _parse_worker_count("WEB_CONCURRENCY") > 1 or _parse_worker_count("GUNICORN_WORKERS") > 1:
    print("FATAL: FraudDetector requires single-worker mode.")
    print("Set WEB_CONCURRENCY=1 in your gunicorn config.")
    sys.exit(1)
```

3. Verify both files compile and the guard fires correctly (see Verification section).

## Must-Haves

- [ ] Guard is at module level — NOT inside `if __name__ == '__main__':` — so gunicorn triggers it on WSGI module import
- [ ] `WEB_CONCURRENCY=2` causes `sys.exit(1)` on import of `web_app.py`
- [ ] `GUNICORN_WORKERS=2` also causes `sys.exit(1)` (both env vars checked)
- [ ] `WEB_CONCURRENCY=1` (default) does NOT cause exit — normal startup continues
- [ ] Non-numeric value for `WEB_CONCURRENCY` (e.g. empty string) defaults to 1 — no crash
- [ ] `python -m py_compile` exits 0 on both files

## Verification

```bash
# Syntax check
python -m py_compile backend/dashboard/web_app.py
python -m py_compile backend/dashboard/admin_dashboard.py

# Guard fires with WEB_CONCURRENCY=2 (web_app.py requires FLASK_SECRET_KEY etc. to be set; test via grep instead)
grep -q 'WEB_CONCURRENCY\|GUNICORN_WORKERS' backend/dashboard/web_app.py
grep -q 'WEB_CONCURRENCY\|GUNICORN_WORKERS' backend/dashboard/admin_dashboard.py
grep -q 'FraudDetector requires single-worker' backend/dashboard/web_app.py
grep -q 'FraudDetector requires single-worker' backend/dashboard/admin_dashboard.py
grep -q 'sys.exit(1)' backend/dashboard/web_app.py
grep -q 'sys.exit(1)' backend/dashboard/admin_dashboard.py
```

Note: Full import-level testing (setting env vars and importing the module) is impractical here because `web_app.py` requires FLASK_SECRET_KEY, JWT_SECRET, FINANCE_PASSWORD, and live Sheets credentials. Grep-based structural checks confirm the guard is present and in the right place. The verify-s03.sh script (T02) will perform the comprehensive check.

## Observability Impact

- Signals added: `CRITICAL event=startup_aborted reason=multi_worker_forbidden` log line in `web_app.py`; plain `print()` in `admin_dashboard.py`
- How a future agent inspects this: Check process exit code; check for guard message in startup logs
- Failure state exposed: Process exits immediately with code 1 before accepting any requests — no silent split-brain

## Inputs

- `backend/dashboard/web_app.py` — existing FINANCE_PASSWORD guard at ~line 78 establishes exact pattern to follow
- `backend/dashboard/admin_dashboard.py` — existing FLASK_SECRET_KEY guard at ~line 59 establishes print-based pattern to follow
- S03-RESEARCH.md — confirms guard must be at module level, not in `__main__`

## Expected Output

- `backend/dashboard/web_app.py` — new WEB_CONCURRENCY guard block after FINANCE_PASSWORD guard; uses `logger.critical` + `sys.exit(1)`
- `backend/dashboard/admin_dashboard.py` — new WEB_CONCURRENCY guard block after FLASK_SECRET_KEY guard; uses `print()` + `sys.exit(1)`
