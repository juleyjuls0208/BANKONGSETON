# S03: FraudDetector Constraint & Health Standardization — UAT

**Milestone:** M002
**Written:** 2026-03-15

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S03 produces structural code changes (startup guards and health endpoint implementations) that can be fully verified by static analysis and script execution without a live Sheets connection. The verify-s03.sh script acts as the primary artifact-driven evidence; runtime behavior is deterministic from the code structure. Live runtime verification of the 503 path requires a mocked Sheets failure, which is deferred to S04 unit tests.

## Preconditions

1. Python 3 available on PATH (`python --version` exits 0)
2. All four files present and readable:
   - `backend/dashboard/web_app.py`
   - `backend/dashboard/admin_dashboard.py`
   - `backend/dashboard/dashboard_core.py`
   - `backend/api/api_server.py`
3. `scripts/verify-s03.sh` is executable (`chmod +x scripts/verify-s03.sh` if needed)
4. Working directory is the project root (`BANKONGSETON/`)
5. No `WEB_CONCURRENCY` or `GUNICORN_WORKERS` env vars set in the shell (both should be unset or =1 for normal operation)

## Smoke Test

```bash
bash scripts/verify-s03.sh
```
Expected: `Results: 18 passed, 0 failed — S03 verification PASSED ✓`

If this passes, all S03 deliverables are structurally correct.

## Test Cases

### 1. Syntax: All four files compile cleanly

```bash
python -m py_compile backend/dashboard/web_app.py
python -m py_compile backend/dashboard/admin_dashboard.py
python -m py_compile backend/dashboard/dashboard_core.py
python -m py_compile backend/api/api_server.py
```
1. Run each command.
2. **Expected:** Each exits with code 0 and produces no output. Any non-zero exit or printed traceback indicates a syntax error that blocks deployment.

---

### 2. WEB_CONCURRENCY guard — hard-fail on multi-worker config (web_app.py)

```bash
grep -n 'WEB_CONCURRENCY\|GUNICORN_WORKERS' backend/dashboard/web_app.py | head -20
grep -n 'FraudDetector requires single-worker' backend/dashboard/web_app.py
grep -n 'sys.exit(1)' backend/dashboard/web_app.py
```
1. Run each grep.
2. **Expected:**
   - Line numbers where `WEB_CONCURRENCY` and `GUNICORN_WORKERS` are read are present and appear **before** the `if __name__ == '__main__':` block.
   - The guard message `FraudDetector requires single-worker mode. Set WEB_CONCURRENCY=1 in your gunicorn config.` is present.
   - `sys.exit(1)` appears in the guard block.
3. **Expected (behavior):** With a live Python env containing all deps, running `WEB_CONCURRENCY=2 python -c "import sys; sys.path.insert(0,'backend/dashboard'); sys.path.insert(0,'backend'); import web_app"` exits non-zero before accepting any requests.

---

### 3. WEB_CONCURRENCY guard — hard-fail on multi-worker config (admin_dashboard.py)

```bash
grep -n 'WEB_CONCURRENCY\|GUNICORN_WORKERS' backend/dashboard/admin_dashboard.py | head -20
grep -n 'FraudDetector requires single-worker' backend/dashboard/admin_dashboard.py
grep -n 'sys.exit(1)' backend/dashboard/admin_dashboard.py
```
1. Run each grep.
2. **Expected:**
   - Both env var names are referenced.
   - Guard message is present.
   - `sys.exit(1)` appears in the guard block.
3. **Expected (behavior):** `WEB_CONCURRENCY=2` import triggers a FATAL print and exit code 1.

---

### 4. Health schema fields — dashboard_core.py

```bash
grep -n 'sheets_ok\|latency_ms\|queue_pending\|timestamp' backend/dashboard/dashboard_core.py | grep -A0 'health'
# Or broader:
grep -n 'sheets_ok' backend/dashboard/dashboard_core.py
grep -n 'latency_ms' backend/dashboard/dashboard_core.py
grep -n 'queue_pending' backend/dashboard/dashboard_core.py
grep -n 'timestamp' backend/dashboard/dashboard_core.py
```
1. Run greps.
2. **Expected:** All four field names appear inside or near the `health_check` function in `dashboard_core.py`.
3. **Expected (structure):** The response dict is constructed as:
   ```python
   {
       "status": "ok" if sheets_ok else "degraded",
       "sheets_ok": sheets_ok,
       "latency_ms": latency_ms,
       "queue_pending": <int from get_queue_status()>,
       "timestamp": <datetime with PHILIPPINES_TZ>.isoformat()
   }
   ```
4. **Expected (status code):** `return jsonify(...), 503` is present when `sheets_ok` is False; `return jsonify(...), 200` when True.

---

### 5. Health schema fields — admin_dashboard.py

```bash
grep -n 'sheets_ok\|latency_ms\|queue_pending\|timestamp' backend/dashboard/admin_dashboard.py
grep -n '503' backend/dashboard/admin_dashboard.py
```
1. Run greps.
2. **Expected:** All four field names present in the health handler; `503` status code returned on failure path.
3. **Expected:** Handler does NOT call `get_health_status()` (removed in S03).

---

### 6. Health schema fields — api_server.py (with offline_queue import)

```bash
grep -n 'sheets_ok\|latency_ms\|queue_pending' backend/api/api_server.py
grep -n 'get_offline_queue\|_OFFLINE_QUEUE_AVAILABLE' backend/api/api_server.py
grep -n 'get_sheets_client' backend/api/api_server.py
grep -n '503' backend/api/api_server.py
```
1. Run greps.
2. **Expected:**
   - `sheets_ok`, `latency_ms`, `queue_pending` all present in health handler.
   - `get_offline_queue` is imported inside a `try/except ImportError` block; `_OFFLINE_QUEUE_AVAILABLE` flag guards the queue status call.
   - `get_sheets_client()` is called **inside** the health handler (fresh per-request, not a stale module-level client).
   - `503` status code returned on Sheets failure path.

---

### 7. 503 on Sheets failure — dashboard_core.py

```bash
grep -n '503' backend/dashboard/dashboard_core.py
```
1. Run grep.
2. **Expected:** At least one match inside the `health_check` function returning 503 when `sheets_ok` is False or when an exception is caught.

---

### 8. 503 on Sheets failure — api_server.py

```bash
grep -n '503' backend/api/api_server.py
```
1. Run grep.
2. **Expected:** At least one match inside the `health_check` function returning 503 when the Sheets probe fails.

---

### 9. Module-level guard placement (not inside `__main__`)

```bash
grep -n '__main__\|WEB_CONCURRENCY guard\|_parse_worker_count' backend/dashboard/web_app.py
```
1. Run grep.
2. **Expected:** `_parse_worker_count` and the guard block appear **before** the line containing `if __name__ == '__main__':`. This confirms gunicorn triggers the guard on WSGI import, not only on direct execution.

---

### 10. verify-s03.sh full run

```bash
bash scripts/verify-s03.sh
```
1. Run script.
2. **Expected:** All 18 checks print `✓` and final line reads: `Results: 18 passed, 0 failed — S03 verification PASSED ✓`
3. **Expected:** Non-zero exit code if any check fails (script uses `exit 1` on failure).

---

## Edge Cases

### WEB_CONCURRENCY set to empty string (non-fatal)

```bash
grep -n '_parse_worker_count\|int(.*default\|try.*int\|except.*ValueError' backend/dashboard/web_app.py | head -10
```
1. Run grep.
2. **Expected:** A helper function (`_parse_worker_count`) uses try/except to convert the env var to int, with a fallback of `1` when the value is empty string or non-numeric.
3. **Significance:** PythonAnywhere may set `WEB_CONCURRENCY=` (empty) in some configs; the guard must not crash or false-positive on empty string.

---

### GUNICORN_WORKERS path (alternate env var name)

```bash
grep -n 'GUNICORN_WORKERS' backend/dashboard/web_app.py backend/dashboard/admin_dashboard.py
```
1. Run grep.
2. **Expected:** `GUNICORN_WORKERS` is read alongside `WEB_CONCURRENCY` in both files. Either variable being > 1 triggers the guard.
3. **Significance:** Some gunicorn configs use `--workers` CLI flag which sets `GUNICORN_WORKERS`, not `WEB_CONCURRENCY`.

---

### Health response when Sheets client is None (latency_ms sentinel)

```bash
grep -n 'db is None\|latency_ms.*0\|latency_ms = 0' backend/dashboard/dashboard_core.py backend/dashboard/admin_dashboard.py
```
1. Run grep.
2. **Expected:** Explicit `if db is None:` branch sets `latency_ms = 0` (not a computed value), signaling client-not-initialized rather than a fast network response.
3. **Significance:** `latency_ms: 0` is a sentinel value meaning "client was never initialized" (bad env vars or service account). Distinguishing this from `latency_ms: 3` (fast successful response) is important for operational diagnosis.

---

### offline_queue import failure in api_server.py is non-fatal

```bash
grep -n '_OFFLINE_QUEUE_AVAILABLE\|except ImportError' backend/api/api_server.py | head -10
```
1. Run grep.
2. **Expected:** `_OFFLINE_QUEUE_AVAILABLE = False` is set in the `except ImportError` branch; the health handler uses this flag to return `queue_pending: 0` if the module is unavailable rather than raising.
3. **Significance:** api_server.py should start cleanly even if offline_queue.py is missing from the deployment.

---

## Failure Signals

- `verify-s03.sh` reports any `✗` — a file was modified after S03 and broke a structural invariant
- `python -m py_compile` exits non-zero — syntax error introduced in one of the four files
- `grep sheets_ok backend/api/api_server.py` returns no matches — health handler was accidentally reverted to the stub
- Health endpoint returns `{"status":"ok","service":"BankongSeton API"}` — api_server.py was overwritten with the old stub
- Health endpoint returns 200 even when Sheets is down — 503 path is broken or the Sheets probe is not actually called
- `WEB_CONCURRENCY=2` import does not exit non-zero — guard is inside `__main__` block instead of module level
- `latency_ms` is missing from health JSON — field was renamed or dropped during a merge

## Requirements Proved By This UAT

- R016 — WEB_CONCURRENCY guard is at module level (not `__main__`), checks both env var names, uses safe int parse, and exits code 1 with human-readable message. Confirmed by greps in test cases 2, 3, 9, and edge case "WEB_CONCURRENCY empty string".
- R018 — All three health endpoints return `{status, sheets_ok, latency_ms, queue_pending, timestamp}` schema and have explicit 503 return on Sheets failure. Confirmed by greps in test cases 4–8 and verify-s03.sh 18/18.

## Not Proven By This UAT

- Live 503 runtime behavior: UAT confirms 503 code is present in the source but does not execute it against a real Sheets failure. Runtime 503 verification is covered by S04 unit tests that mock `db.worksheets()` raising an exception.
- WEB_CONCURRENCY runtime hard-fail: UAT confirms guard code is at module level but does not execute a live `WEB_CONCURRENCY=2 python -c "import web_app"` (requires full venv with all deps). S04 environment will validate this if the test suite imports these modules.
- `queue_pending` accuracy: UAT confirms the field is present and sourced from `get_queue_status()` / offline_queue, but does not verify the count is correct under load. Operational verification deferred to S05 / production deployment.

## Notes for Tester

- All UAT test cases here are script/grep-based and require no live Sheets credentials or running Flask server — safe to run in any environment.
- `verify-s03.sh` is the authoritative single-command check. Run it first. Only drill into individual test cases if a check fails and you need to diagnose which file/field is the problem.
- The `latency_ms: 0` sentinel convention (client None, not fast response) is important for ops. When documenting the health endpoint in S05 runbook, call this out explicitly.
- `admin_dashboard.py` health handler 503 path is verified by grep but is not a numbered check in verify-s03.sh — if you refactor admin_dashboard.py's health handler, manually confirm the 503 path is preserved.
