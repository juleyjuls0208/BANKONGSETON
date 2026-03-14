---
estimated_steps: 7
estimated_files: 4
---

# T02: Standardize /api/health in dashboard_core.py, admin_dashboard.py, and api_server.py; write verify-s03.sh

**Slice:** S03 — FraudDetector Constraint & Health Standardization
**Milestone:** M002

## Description

Three health endpoints currently return wrong shapes or unconditional 200:

- `dashboard_core.py` `/api/health` — calls `get_health_status()` and returns its nested HealthMonitor dict, always 200. Wrong shape, wrong semantics.
- `admin_dashboard.py` `/api/health` — same pattern. Also always 200.
- `api_server.py` `/api/health` — returns `{'status': 'ok', 'service': '...', 'version': '1.0.0'}` unconditionally. Hardcoded, no real check.

All three must be replaced with a real Sheets connectivity probe that returns:
```json
{"status": "ok|degraded", "sheets_ok": true|false, "latency_ms": 123, "queue_pending": 0, "timestamp": "2026-03-15T..."}
```
and respond 503 when Sheets is unreachable.

## Steps

1. **dashboard_core.py** — Locate `health_check()` inside `register_routes()` (~line 2951). Replace its body entirely. Do NOT call `get_health_status()`. New implementation:

```python
def health_check():
    """Health check endpoint — standardized contract (S03/R018)"""
    import time as _time
    t0 = _time.time()
    sheets_ok = False
    latency_ms = 0
    try:
        if db is None:
            sheets_ok = False
            latency_ms = 0
        else:
            db.worksheets()
            latency_ms = int((_time.time() - t0) * 1000)
            sheets_ok = True
    except Exception:
        latency_ms = int((_time.time() - t0) * 1000)
        sheets_ok = False

    try:
        pending = get_queue_status().get("pending", 0)
    except Exception:
        pending = 0

    payload = {
        "status": "ok" if sheets_ok else "degraded",
        "sheets_ok": sheets_ok,
        "latency_ms": latency_ms,
        "queue_pending": pending,
        "timestamp": datetime.now(PHILIPPINES_TZ).isoformat(),
    }
    return jsonify(payload), (200 if sheets_ok else 503)
```

Note: `time` is already imported at the top of `dashboard_core.py`. Use `import time as _time` inside the function body to avoid shadowing if needed, or just use `time.time()` if `time` is already in scope. `datetime`, `PHILIPPINES_TZ`, `get_queue_status`, `db`, `jsonify` are all already in scope.

2. **admin_dashboard.py** — Locate `health_check()` at line ~440. Replace its body with the same logic. Check what imports are in scope: `time`, `datetime`, `PHILIPPINES_TZ`, `db` (module-level at ~line 137), `get_queue_status` (imported from `resilience` at top, or the fallback stub). Use `jsonify` which is already imported. Same 200/503 logic.

3. **api_server.py** — Add `offline_queue` import at module level after the existing try/except imports (~line 27). Pattern to match existing `nfc_payments` try/except import:

```python
try:
    from offline_queue import get_offline_queue as _get_offline_queue
    _OFFLINE_QUEUE_AVAILABLE = True
except ImportError:
    _OFFLINE_QUEUE_AVAILABLE = False
```

Then replace `health_check()` at line 192. New implementation:

```python
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint — standardized contract (S03/R018)"""
    t0 = time.time()
    sheets_ok = False
    latency_ms = 0
    try:
        probe_client = get_sheets_client()
        probe_client.worksheets()
        latency_ms = int((time.time() - t0) * 1000)
        sheets_ok = True
    except Exception:
        latency_ms = int((time.time() - t0) * 1000)
        sheets_ok = False

    queue_pending = 0
    if _OFFLINE_QUEUE_AVAILABLE:
        try:
            queue_pending = _get_offline_queue().get_status().get('pending', 0)
        except Exception:
            pass

    PHILIPPINES_TZ = pytz.timezone('Asia/Manila')
    payload = {
        'status': 'ok' if sheets_ok else 'degraded',
        'sheets_ok': sheets_ok,
        'latency_ms': latency_ms,
        'queue_pending': queue_pending,
        'timestamp': datetime.now(PHILIPPINES_TZ).isoformat(),
    }
    return jsonify(payload), (200 if sheets_ok else 503)
```

Note: `time`, `pytz`, `datetime`, `jsonify`, `get_sheets_client` are all already imported/defined in `api_server.py`. `PHILIPPINES_TZ` is already defined as a module-level variable — reuse it instead of re-defining inline.

4. **Verify all four files compile** with `python -m py_compile`.

5. **Write `scripts/verify-s03.sh`** — 18 structural checks:

```
Group 1 — Syntax (4 checks): py_compile on web_app.py, admin_dashboard.py, dashboard_core.py, api_server.py
Group 2 — WEB_CONCURRENCY guard (4 checks): "WEB_CONCURRENCY" present in web_app.py; "GUNICORN_WORKERS" present in web_app.py; "FraudDetector requires single-worker" in web_app.py; same message in admin_dashboard.py
Group 3 — Health schema fields (dashboard_core.py) (4 checks): sheets_ok, latency_ms, queue_pending, timestamp all present in dashboard_core.py health handler
Group 4 — Health schema fields (api_server.py) (4 checks): sheets_ok, latency_ms, queue_pending, timestamp all present in api_server.py health handler; get_offline_queue import attempted; 503 return present
Group 5 — 503 on failure (2 checks): "503" present in dashboard_core.py health_check function; "503" present in api_server.py health_check function
```

## Must-Haves

- [ ] `dashboard_core.py` health handler does NOT call `get_health_status()` — uses direct `db.worksheets()` ping
- [ ] `dashboard_core.py` health returns 503 when `db is None` or `db.worksheets()` raises
- [ ] `admin_dashboard.py` health handler follows the same pattern (same four fields, same 503 on failure)
- [ ] `api_server.py` health handler calls `get_sheets_client()` fresh — not the stale module-level `db`
- [ ] `api_server.py` imports `get_offline_queue` in a try/except so a missing sqlite3 does not crash the server
- [ ] All four files pass `python -m py_compile`
- [ ] `scripts/verify-s03.sh` reports 18/18 pass

## Verification

```bash
# Compile check
python -m py_compile backend/dashboard/web_app.py
python -m py_compile backend/dashboard/admin_dashboard.py
python -m py_compile backend/dashboard/dashboard_core.py
python -m py_compile backend/api/api_server.py

# Run the full verification script
bash scripts/verify-s03.sh
```

## Observability Impact

- Signals added: `sheets_ok: false` + `latency_ms` in health JSON response body; HTTP 503 status for monitoring/load-balancer alerting
- How a future agent inspects this: `curl /api/health` returns structured JSON; `sheets_ok` boolean is the primary signal; `latency_ms: 0` indicates client was None (not a slow response)
- Failure state exposed: Sheets unreachable → 503 with `sheets_ok: false`; queue backpressure visible via `queue_pending` count

## Inputs

- `backend/dashboard/dashboard_core.py` — existing `health_check()` at ~line 2951 to replace; `db`, `get_queue_status`, `PHILIPPINES_TZ`, `datetime`, `time`, `jsonify` already in scope
- `backend/dashboard/admin_dashboard.py` — existing `health_check()` at ~line 440 to replace; same dependencies in scope
- `backend/api/api_server.py` — existing `health_check()` at line 192 to replace; `get_sheets_client`, `time`, `pytz`, `datetime`, `jsonify` already in scope
- `scripts/verify-s02.sh` — reference pattern for the verification script structure
- T01 completed — `web_app.py` and `admin_dashboard.py` guard changes are already in

## Expected Output

- `backend/dashboard/dashboard_core.py` — `/api/health` handler returns `{status, sheets_ok, latency_ms, queue_pending, timestamp}`; 503 when Sheets down
- `backend/dashboard/admin_dashboard.py` — `/api/health` handler updated to match (same schema, same 503 behavior)
- `backend/api/api_server.py` — `/api/health` handler with real Sheets ping; `get_offline_queue` import; 503 when Sheets down
- `scripts/verify-s03.sh` — 18-check structural verification script; reports PASS/FAIL per check and final count
