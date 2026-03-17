---
id: T01
parent: S03
milestone: M002
provides:
  - WEB_CONCURRENCY startup guard in web_app.py (module-level, logger.critical + sys.exit(1))
  - WEB_CONCURRENCY startup guard in admin_dashboard.py (module-level, print + sys.exit(1))
key_files:
  - backend/dashboard/web_app.py
  - backend/dashboard/admin_dashboard.py
key_decisions:
  - Guard placed at module level (not inside __main__) so gunicorn triggers it on WSGI import
  - Both WEB_CONCURRENCY and GUNICORN_WORKERS are checked to cover all gunicorn config styles
  - _parse_worker_count helper handles empty string and non-numeric values by defaulting to 1
  - web_app.py uses logger.critical (matches existing guard pattern in that file)
  - admin_dashboard.py uses print() (matches existing FLASK_SECRET_KEY guard pattern in that file)
patterns_established:
  - _parse_worker_count(env_var) helper: safe int parse with empty-string and ValueError fallback to 1
observability_surfaces:
  - web_app.py: CRITICAL log line "event=startup_aborted reason=multi_worker_forbidden" on bad config
  - admin_dashboard.py: FATAL print lines to stdout on bad config
  - Process exits with code 1 before accepting any requests — no silent split-brain
duration: ~10 minutes
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Add WEB_CONCURRENCY startup guard to web_app.py and admin_dashboard.py

**WEB_CONCURRENCY/GUNICORN_WORKERS hard-fail guard inserted at module level in both WSGI entry points; process exits with code 1 before accepting requests when multi-worker config is detected.**

## What Happened

Inserted the guard block after the FINANCE_PASSWORD guard in `web_app.py` (line ~81) and after the FLASK_SECRET_KEY guard in `admin_dashboard.py` (line ~67). Both insertions follow the style already established by existing guards in each file.

The `_parse_worker_count` helper is defined inline in each file (no shared import needed) to safely parse `WEB_CONCURRENCY` and `GUNICORN_WORKERS` env vars, defaulting to `1` on empty string or non-numeric values.

Placement is at module level — guard executes during WSGI import, before any Flask app object is constructed, ensuring gunicorn fails loudly before forking workers.

## Verification

```
# Syntax checks — both pass:
python -m py_compile backend/dashboard/web_app.py        # OK
python -m py_compile backend/dashboard/admin_dashboard.py # OK

# Structural grep — all 6 pass:
grep WEB_CONCURRENCY|GUNICORN_WORKERS web_app.py         # PASS
grep WEB_CONCURRENCY|GUNICORN_WORKERS admin_dashboard.py # PASS
grep 'FraudDetector requires single-worker' web_app.py   # PASS
grep 'FraudDetector requires single-worker' admin_dashboard.py # PASS
grep 'sys.exit(1)' web_app.py                            # PASS
grep 'sys.exit(1)' admin_dashboard.py                    # PASS

# Module-level placement confirmed:
# Guard at char 2650, __main__ at char 9275 in web_app.py

# Logic tests (isolated _parse_worker_count):
# WEB_CONCURRENCY=2  → guard triggers        PASS
# WEB_CONCURRENCY=1  → guard does NOT trigger PASS
# WEB_CONCURRENCY='' → defaults to 1         PASS
# WEB_CONCURRENCY='bad' → defaults to 1      PASS
```

## Diagnostics

- Startup failure: process exits code 1; check logs for `event=startup_aborted reason=multi_worker_forbidden` (web_app.py) or `FATAL: FraudDetector requires single-worker mode.` (admin_dashboard.py)
- Correct config: ensure `WEB_CONCURRENCY=1` (or unset) in gunicorn/PythonAnywhere config
- Inspection: `grep -n 'WEB_CONCURRENCY guard' backend/dashboard/web_app.py backend/dashboard/admin_dashboard.py`

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `backend/dashboard/web_app.py` — added WEB_CONCURRENCY guard after FINANCE_PASSWORD guard; uses logger.critical + sys.exit(1)
- `backend/dashboard/admin_dashboard.py` — added WEB_CONCURRENCY guard after FLASK_SECRET_KEY guard; uses print() + sys.exit(1)
