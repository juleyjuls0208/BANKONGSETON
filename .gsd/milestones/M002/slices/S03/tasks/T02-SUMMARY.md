---
id: T02
parent: S03
milestone: M002
provides:
  - Standardized /api/health handler in dashboard_core.py (Sheets probe, 4-field schema, 200/503)
  - Standardized /api/health handler in admin_dashboard.py (same schema, same 503 behavior)
  - Standardized /api/health handler in api_server.py (get_sheets_client() fresh probe, offline_queue pending, 200/503)
  - offline_queue try/except import in api_server.py
  - scripts/verify-s03.sh — 18-check structural verification script
key_files:
  - backend/dashboard/dashboard_core.py
  - backend/dashboard/admin_dashboard.py
  - backend/api/api_server.py
  - scripts/verify-s03.sh
key_decisions:
  - api_server.py health_check calls get_sheets_client() fresh per request (not module-level db) to detect live connectivity rather than stale client state
  - dashboard_core.py / admin_dashboard.py use module-level db with explicit None guard (latency_ms=0 signals client-not-initialized vs slow-response)
  - PHILIPPINES_TZ in api_server.py reuses module-level constant (not re-defined inline) per task plan note
  - Group 4's 4th check in verify-s03.sh is get_offline_queue import presence (more unique than timestamp which all three share)
patterns_established:
  - Health probe pattern: db.worksheets() as liveness signal; latency_ms=0 indicates client None; latency_ms>0 indicates real round-trip time
  - offline_queue import: try/except ImportError sets _OFFLINE_QUEUE_AVAILABLE flag; guarded at call site
observability_surfaces:
  - GET /api/health → {"status":"ok|degraded","sheets_ok":bool,"latency_ms":int,"queue_pending":int,"timestamp":str} — HTTP 200 or 503
  - sheets_ok:false + latency_ms:0 → Sheets client is None (not initialized)
  - sheets_ok:false + latency_ms>0 → Sheets client exists but worksheets() raised
  - queue_pending:N → live backpressure count from resilience queue
duration: ~20 minutes
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Standardize /api/health in dashboard_core.py, admin_dashboard.py, and api_server.py; write verify-s03.sh

**All three /api/health handlers replaced with real Sheets connectivity probes returning `{status, sheets_ok, latency_ms, queue_pending, timestamp}` and HTTP 503 on failure; verify-s03.sh reports 18/18 PASS.**

## What Happened

Three health endpoints were returning wrong shapes or unconditional 200. Replaced all three with a consistent liveness probe:

- **dashboard_core.py** (`~line 2951`): Removed `get_health_status()` call. New body probes `db.worksheets()`, catches all exceptions, computes `latency_ms`, and returns 503 when `db is None` or the probe raises. Uses `import time as _time` locally to avoid shadowing. `get_queue_status()` provides `queue_pending`.

- **admin_dashboard.py** (`~line 452`): Replaced the `get_health_status()` + gspread-specific exception handler with the same pattern. Module-level `db`, `get_queue_status`, `PHILIPPINES_TZ`, `datetime`, `jsonify` all already in scope.

- **api_server.py** (`~line 192`): Replaced hardcoded `{'status':'ok','service':...,'version':...}` stub with a fresh `get_sheets_client()` probe (intentionally fresh — not the stale module-level `db`). Added `offline_queue` try/except import block immediately after the existing `nfc_payments` try/except group. `_OFFLINE_QUEUE_AVAILABLE` flag guards the queue status call.

- **scripts/verify-s03.sh**: 18-check script modeled on verify-s02.sh. Five groups: syntax (4), WEB_CONCURRENCY guard (4), health schema in dashboard_core.py (4), health schema in api_server.py (4), 503 on failure (2).

## Verification

```
bash scripts/verify-s03.sh
→ Results: 18 passed, 0 failed — S03 verification PASSED ✓

python -m py_compile backend/dashboard/web_app.py       → exit 0
python -m py_compile backend/dashboard/admin_dashboard.py → exit 0
python -m py_compile backend/dashboard/dashboard_core.py  → exit 0
python -m py_compile backend/api/api_server.py           → exit 0
```

Must-have checks (manual grep):
- dashboard_core.py health_check does NOT call `get_health_status()` ✓
- `db is None` guard present in dashboard_core.py ✓
- admin_dashboard.py has `sheets_ok` field and 503 return ✓
- api_server.py calls `get_sheets_client()` fresh inside handler ✓
- `offline_queue` import wrapped in `try/except ImportError` ✓

## Diagnostics

- `curl /api/health` → JSON with `sheets_ok`, `latency_ms`, `queue_pending`, `timestamp`; HTTP 200 or 503
- `sheets_ok: false, latency_ms: 0` → Sheets client is None (startup failure or env misconfiguration)
- `sheets_ok: false, latency_ms: N` → Client exists but `worksheets()` raised (network/auth failure)
- `queue_pending: N` → backpressure from resilience write queue
- `bash scripts/verify-s03.sh` → structural regression check (18 checks)

## Deviations

- Group 4's 4th verify-s03.sh check uses `get_offline_queue import presence` rather than `timestamp` (timestamp is present in all three handlers and less diagnostic; import presence confirms the try/except guard exists).
- `PHILIPPINES_TZ` in api_server.py reuses the module-level constant rather than redefining inline (task plan noted this as acceptable).

## Known Issues

none

## Files Created/Modified

- `backend/dashboard/dashboard_core.py` — health_check() body replaced; no longer calls get_health_status()
- `backend/dashboard/admin_dashboard.py` — health_check() body replaced; no longer calls get_health_status()
- `backend/api/api_server.py` — offline_queue try/except import added; health_check() body replaced with Sheets probe
- `scripts/verify-s03.sh` — new 18-check structural verification script
