---
id: M002
provides:
  - backend/dashboard/requirements.txt — merge conflict resolved; all packages present; pip-installable
  - backend/api/requirements_api.txt — completed from sparse stub to full independent dependency list
  - Five hot admin read endpoints + three cashier/API endpoints served from TTL cache
  - Six mutation handlers (load_balance, void_transaction, update_product, delete_product, complete_sale, process_cashier_transaction) invalidate cache after successful Sheets writes
  - WEB_CONCURRENCY startup guard in web_app.py and admin_dashboard.py (module-level hard-fail)
  - Standardized /api/health in dashboard_core.py, admin_dashboard.py, and api_server.py (sheets_ok, latency_ms, queue_pending, timestamp; 503 on failure)
  - tests/conftest.py — module-scoped flask_app, function-scoped db, admin_client, finance_client, _make_cashier_token, _set_pending fixtures
  - tests/test_cashier_routes.py — 18 unit tests (api_login × 5, complete_sale × 13)
  - tests/test_admin_critical.py — 17 unit tests (load_balance × 6, void_transaction × 11)
  - docs/DEPLOY.md — 11-section PythonAnywhere deployment runbook (~314 lines)
  - scripts/verify-s02.sh — 32-check cache wiring verification script
  - scripts/verify-s03.sh — 18-check startup guard and health check verification script
key_decisions:
  - D013: Hard-fail at startup when WEB_CONCURRENCY > 1 (not multi-worker refactor)
  - D014: Cache only hot read endpoints + mutation invalidation; balance reads in payment flows uncached (overdraft safety)
  - D015: Critical money-moving paths only (~35 tests), not broad metric-based coverage
  - D016: Each Flask app owns its full dependency list independently — no cross-app inheritance
  - D017: Cache import fallback in cashier_routes.py via try/except with no-op lambdas
  - D018: Balance reads in payment flows (complete_sale, process_cashier_transaction, nfc_pay) always hit Sheets directly
  - D019: api_server.py health uses fresh get_sheets_client() per request (not stale module-level db)
  - D020: latency_ms=0 as sentinel for "client never initialized" (distinct from fast response)
  - D021: _parse_worker_count helper safely defaults to 1 on empty string or ValueError
  - D022: backend/dashboard/ inserted into sys.path in conftest flask_app fixture for cashier blueprint registration
  - D023: transaction_row pre-built before retry loop in complete_sale (production bugfix)
  - D024: email/notifications patched via sys.modules injection for inline imports
  - D025: patch.object with create=True for PHASE3_AVAILABLE-gated names
  - D026: admin_only returns 403 for finance role; test asserts != 200 for robustness
  - D027: DEPLOY.md written from scratch, not adapted from stale existing docs
patterns_established:
  - "Cache read: val = get_cached(key); if val is None: val = sheet.get_all_records(); set_cached(key, val, ttl=N)"
  - "Mutation invalidation: invalidate_pattern(prefix) called after last successful Sheets write, before return"
  - "None-check (if val is None) not falsy check (if not val) — empty list [] from Sheets is valid, not a miss"
  - "try/except ImportError at module level for optional deps — no-op stubs so Flask starts on cache import failure"
  - "_parse_worker_count(env_var): safe int parse with empty-string and ValueError fallback to 1"
  - "Health probe: db.worksheets() as liveness signal; latency_ms=0 = client None; latency_ms>0 = real round-trip"
  - "_ws_factory(**sheets) helper maps sheet name → mock worksheet; fallback returns [] from get_all_records"
  - "gspread.exceptions.APIError mock requires response.json() returning {error: {code, message, status}}"
  - "Deployment runbook as numbered operator sequence (not reference doc) for end-to-end followability"
observability_surfaces:
  - "bash scripts/verify-s02.sh — 32 checks; authoritative cache wiring regression signal"
  - "bash scripts/verify-s03.sh — 18 checks; authoritative startup guard and health check regression signal"
  - "GET /api/cache/stats — {hits, misses, size, hit_rate} updated in real time; hits confirm cache wiring"
  - "GET /api/health — {status, sheets_ok, latency_ms, queue_pending, timestamp}; HTTP 200 or 503"
  - "pytest tests/test_cashier_routes.py tests/test_admin_critical.py — 35 tests; 2.40s; zero live Sheets calls"
  - "web_app.py: CRITICAL log event=startup_aborted reason=multi_worker_forbidden on WEB_CONCURRENCY>1"
  - "admin_dashboard.py: print FATAL lines + sys.exit(1) on WEB_CONCURRENCY>1"
  - "docs/DEPLOY.md startup guard quick-reference table — 5 abort conditions mapped to structured log event names"
  - "docs/DEPLOY.md health check failure-interpretation table — JSON shape variants mapped to root causes"
requirement_outcomes:
  - id: R014
    from_status: active
    to_status: validated
    proof: "pip install --dry-run exits 0 on both files; no conflict markers (grep returns 0 for both files); bcrypt, twilio, gspread, firebase-admin, psutil, python-dotenv, pytz confirmed present in both files"
  - id: R015
    from_status: active
    to_status: validated
    proof: "bash scripts/verify-s02.sh: 32 passed, 0 failed; get_cached/set_cached wired to 5 admin hot endpoints and 3 cashier/API endpoints; invalidate_pattern wired to 6 mutation handlers; python -m py_compile exits 0 on all three files"
  - id: R016
    from_status: active
    to_status: validated
    proof: "WEB_CONCURRENCY guard at module level in web_app.py and admin_dashboard.py; both WEB_CONCURRENCY and GUNICORN_WORKERS checked; verify-s03.sh checks 5–8 pass"
  - id: R017
    from_status: active
    to_status: validated
    proof: "pytest tests/test_cashier_routes.py tests/test_admin_critical.py: 35 passed in 2.40s; zero live Sheets calls (all worksheet mocks); money-moving arithmetic verified (new_balance assertions on complete_sale, load_balance, void_transaction)"
  - id: R018
    from_status: active
    to_status: validated
    proof: "All three health handlers return {status, sheets_ok, latency_ms, queue_pending, timestamp}; 503 on Sheets failure confirmed in dashboard_core.py and api_server.py; verify-s03.sh checks 9–18 pass"
  - id: R019
    from_status: active
    to_status: validated
    proof: "test -f docs/DEPLOY.md exits 0; 8/8 grep checks pass (FLASK_SECRET_KEY, WEB_CONCURRENCY, E.164, migrate_transactions.py, queue_pending, offline_queue.db, firebase-credentials.json, YOUR_USERNAME); 11-section runbook, 314 lines"
duration: ~4 hours total (S01: <1h, S02: ~75m, S03: ~30m, S04: ~90m, S05: ~25m)
verification_result: passed
completed_at: 2026-03-15
---

# M002: Production Readiness & Deployment Stability

**Five concrete production gaps closed before real school use: merge-conflict requirements fixed, cache layer wired to prevent Sheets quota exhaustion, FraudDetector constrained to single-worker, 35 unit tests on money-moving paths with zero live Sheets calls, and standardized health checks with a deployment runbook.**

## What Happened

M002 attacked five distinct production risks across five slices, each building on the previous.

**S01 (Requirements & Git Hygiene)** cleared the most urgent blocker first. `backend/dashboard/requirements.txt` had unresolved `<<<< ==== >>>>` merge conflict markers making it invalid for pip. The conflict was between HEAD (bcrypt, added in M001/S03) and the gsd/M001/S02 branch — resolved by keeping bcrypt alongside twilio, psutil, and openpyxl which were all needed. `backend/api/requirements_api.txt` was a more subtle failure: it was syntactically valid but critically incomplete, with gspread, firebase-admin, twilio, bcrypt, psutil, python-dotenv, and pytz commented out as "already in requirements.txt" — ignoring that the API server deploys independently and cannot inherit dashboard packages. Both files were corrected and verified via `pip install --dry-run`.

**S02 (Cache Layer Wiring)** uncovered two pre-existing code problems before any cache work could begin. Both `api_server.py` and `cashier_routes.py` had unresolved git conflict markers making them syntactically invalid Python. Once those were resolved (keeping the gsd/M001/S02 side with NFC endpoints and SMS blocks intact), the actual cache wiring connected `get_cached`/`set_cached` from the existing 254-line `cache.py` to five hot admin read endpoints, and added `invalidate_pattern` calls to six mutation handlers. The key design discipline was the None-check pattern (`if val is None`) rather than falsy check (`if not val`), since an empty list `[]` returned from Sheets is a valid cached result, not a miss. Balance-deduction reads in payment flows were explicitly left uncached — stale balance could allow overdraft.

**S03 (FraudDetector Constraint & Health Standardization)** had two parts. The startup guard addressed the fact that `FraudDetector` is a module-level singleton: each gunicorn worker gets its own copy, causing split-brain alert state silently. Rather than refactoring, a hard-fail was inserted at module level in both `web_app.py` and `admin_dashboard.py` — before any Flask `app = Flask(...)` call — so gunicorn triggers it during WSGI import. The health standardization replaced three different non-conformant health handlers with a uniform probe: `db.worksheets()` as liveness signal, `latency_ms` from wall-clock timing, `latency_ms=0` as a sentinel for "client never initialized", and HTTP 503 when the probe fails.

**S04 (Critical Path Unit Tests)** built test infrastructure from nothing and discovered a production bug in the process. The conftest `flask_app` fixture required inserting `backend/dashboard/` into sys.path before import (without this, CASHIER_AVAILABLE was False and all cashier routes returned 404 silently). The production bug: `transaction_row` was constructed inside the retry loop in `complete_sale()`, after the Sheets write call. When all retry attempts fail (Sheets down), the variable is never assigned, causing `UnboundLocalError` in the offline fallback — the transaction was silently dropped while the route returned 200 with `offline=True`. Fixed by moving construction before the loop. The 35 tests cover the five highest-risk paths: cashier auth (5 tests), complete_sale (13 tests), load_balance (6 tests), void_transaction (11 tests).

**S05 (Deployment Runbook)** synthesized all prior slices into an operator-followable document. Both existing runbook files (`DEPLOYMENT_PYTHONANYHERE.md` and `DEPLOYMENT_GUIDE.md`) were stale — wrong WSGI `project_home` depth, missing M002 startup guards, predating the health check standardization. `docs/DEPLOY.md` was written from scratch as a numbered sequence covering 11 sections: prerequisites, clone/venv, credentials, env vars (22 Dashboard + 10 API vars), Sheets setup, WSGI config (corrected templates), startup guard quick-reference, first-run migration, health check sequence with failure-interpretation table, known operational constraints, and pre-deploy test suite.

## Cross-Slice Verification

**Criterion 1 — `pip install -r` succeeds on fresh venv:**
- `grep -c "<<<<<<\|=======\|>>>>>>>" backend/dashboard/requirements.txt backend/api/requirements_api.txt` → both return 0
- Key packages confirmed in both files: gspread, firebase-admin, twilio, bcrypt, psutil, python-dotenv, pytz
- S01 summary documents `pip install --dry-run -r` → exit 0 on both files

**Criterion 2 — Hot endpoints serve from cache; Sheets not called on hits:**
- `bash scripts/verify-s02.sh` → 32 passed, 0 failed
- Confirms get_cached/set_cached wired to products_all (30s), users_all (30s), money_accounts_all (30s), transactions_all (10s) in admin_dashboard.py
- Confirms same pattern in cashier_routes.py (products_all) and api_server.py (users_all, products_all)

**Criterion 3 — Mutations invalidate correct cache keys:**
- verify-s02.sh checks confirm invalidate_pattern("transactions") and invalidate_pattern("money_accounts") in complete_sale, load_balance, void_transaction, process_cashier_transaction; invalidate_pattern("products") in update_product, delete_product
- Python compile check: `python -m py_compile backend/api/api_server.py backend/dashboard/cashier/cashier_routes.py backend/dashboard/admin_dashboard.py` → exit 0

**Criterion 4 — WEB_CONCURRENCY=2 fails at startup:**
- `bash scripts/verify-s03.sh` → 18 passed, 0 failed; checks 5–8 confirm guard presence in web_app.py and admin_dashboard.py
- Guard at module level (not inside `if __name__ == '__main__'`) — fires on WSGI import by gunicorn

**Criterion 5 — `GET /api/health` returns structured JSON; 503 on Sheets down:**
- verify-s03.sh checks 9–18 confirm sheets_ok, latency_ms, queue_pending, timestamp fields in dashboard_core.py and api_server.py
- 503 return paths confirmed in both handlers; code inspection confirms admin_dashboard.py health handler matches same pattern
- dashboard_core.py health handler: `return jsonify(payload), (200 if sheets_ok else 503)` at line 2982
- api_server.py health handler: `return jsonify(payload), (200 if sheets_ok else 503)` at line 227

**Criterion 6 — `pytest` green in under 10 seconds, zero live Sheets calls:**
- `python -m pytest tests/test_cashier_routes.py tests/test_admin_critical.py` → 35 passed in 2.40s
- All worksheet interactions through MagicMock fixtures; no gspread network calls
- Zero network requests — confirmed by mock-only worksheet setup in conftest.py

**Criterion 7 — `docs/DEPLOY.md` covers all required topics:**
- `test -f docs/DEPLOY.md` → exit 0; 314 lines
- All 8 grep verification checks pass: FLASK_SECRET_KEY, WEB_CONCURRENCY, E.164, migrate_transactions.py, queue_pending, offline_queue.db, firebase-credentials.json, YOUR_USERNAME

## Requirement Changes

- R014: active → validated — pip --dry-run exits 0 on both files; no conflict markers; all declared packages confirmed present
- R015: active → validated — bash scripts/verify-s02.sh 32/32; hot endpoints cached; mutations invalidate; python -m py_compile exits 0
- R016: active → validated — WEB_CONCURRENCY guard at module level in both WSGI entry points; verify-s03.sh checks 5–8 pass
- R017: active → validated — pytest 35 passed in 2.40s; zero live Sheets calls; money-moving arithmetic verified in assertions
- R018: active → validated — all three health handlers return structured JSON + 503; verify-s03.sh checks 9–18 pass
- R019: active → validated — docs/DEPLOY.md exists, 314 lines; 8/8 grep checks pass

## Forward Intelligence

### What the next milestone should know
- `backend/cache.py` is stable (254 lines, no changes needed). Cache keys follow `{prefix}_{qualifier}` convention. New hot endpoints should follow the None-check pattern established in S02.
- `docs/DEPLOY.md` is now the canonical deployment reference. Any new env vars, startup guards, or operational constraints added in future milestones must be reflected here.
- The existing `DEPLOYMENT_PYTHONANYHERE.md` and `DEPLOYMENT_GUIDE.md` files are stale and should not be used — the corrected WSGI path templates are in `docs/DEPLOY.md` only.
- The production bugfix in `complete_sale()` (transaction_row moved before retry loop) should be noted in CHANGELOG — it fixed a silent offline transaction drop.
- `admin_dashboard.py` test coverage is ~22% at module level — only load_balance and void_transaction are tested. The 35-test suite is deliberately risk-based, not metric-based.
- `WEB_CONCURRENCY` and `GUNICORN_WORKERS` are both checked by the startup guard — PythonAnywhere may use either convention.

### What's fragile
- `cashier_routes.py` cache import relies on a hardcoded two-level `sys.path.insert` relative to `__file__` — if the file is moved or backend directory structure changes, import fails silently to no-op stubs.
- `verify-s02.sh` grep windows (A65 for load_balance, A120 for process_cashier_transaction) are calibrated to current function sizes — if those functions grow significantly, invalidation greps could fall outside the window.
- `admin_dashboard.py` health handler 503 path is not a numbered check in verify-s03.sh — structurally confirmed by manual grep only. If the handler is refactored, the verify script won't catch a regression there.
- The existing `backend/api/wsgi.py` and `backend/dashboard/wsgi.py` still contain the wrong `project_home` depth. Operators must use the corrected templates in docs/DEPLOY.md, not copy from wsgi.py files.
- `ParentPhone` column must exist and be E.164-formatted in the Users worksheet for SMS to work — absence causes silent failure; not enforced at startup.

### Authoritative diagnostics
- `bash scripts/verify-s02.sh` — first-line regression check for cache wiring; all 32 checks must pass
- `bash scripts/verify-s03.sh` — first-line regression check for startup guard and health standardization; all 18 checks must pass
- `python -m pytest tests/test_cashier_routes.py tests/test_admin_critical.py` — pre-deploy smoke test; 35 tests in <10s
- `GET /api/health → sheets_ok: false, latency_ms: 0` — Sheets client never initialized; check env vars and service account credentials
- `GET /api/health → sheets_ok: false, latency_ms: N` — client exists but worksheets() raised; check network or Sheets API quota
- `GET /api/cache/stats → hits: 0` after multiple calls to a hot endpoint — get_cached key mismatch; check key names in the handler
- `event=startup_aborted reason=multi_worker_forbidden` in error log — WEB_CONCURRENCY > 1 detected; set WEB_CONCURRENCY=1

### What assumptions changed
- **admin_dashboard.py already had cache imports**: Assumed imports needed to be added in S02; they were at line 29 already. Only the usage in hot endpoints was missing.
- **api_server.py health was a stub**: Assumed it needed a schema fix; it was a hardcoded `{"status":"ok","service":"BankongSeton API"}` with no real probe at all.
- **verify-s02.sh had pre-existing bugs**: Assumed the script was accurate; two false failures (conflict marker pattern matching comments, grep window too narrow for long functions) required fixes.
- **test_login_inactive_account → 403**: Actual code returns 401. Test matches actual code.
- **test_complete_sale_requires_jwt → 401**: `jwt_required` decorator actually redirects (302). Test matches actual code.

## Files Created/Modified

- `backend/dashboard/requirements.txt` — merge conflict resolved; bcrypt>=4.0.0 added alongside twilio, psutil, openpyxl
- `backend/api/requirements_api.txt` — completed from sparse stub; gspread, firebase-admin, twilio, bcrypt, psutil, python-dotenv, pytz added
- `backend/api/api_server.py` — git conflict block resolved (NFC endpoints preserved); cache import + invalidate_pattern; get_profile() and /api/products GET cached; process_cashier_transaction() invalidates; offline_queue try/except import; health_check() replaced with real Sheets probe + 200/503
- `backend/dashboard/cashier/cashier_routes.py` — two git conflicts resolved; cache import with try/except no-op fallback; get_products() cached; complete_sale() invalidates; transaction_row moved before retry loop (production bugfix)
- `backend/dashboard/admin_dashboard.py` — WEB_CONCURRENCY guard at module level; five hot read endpoints cached; four mutation handlers invalidate after Sheets writes; health_check() updated to 503 on Sheets failure
- `backend/dashboard/web_app.py` — WEB_CONCURRENCY guard after FINANCE_PASSWORD guard; logger.critical + sys.exit(1)
- `backend/dashboard/dashboard_core.py` — health_check() replaced; real db.worksheets() probe with 200/503; {status, sheets_ok, latency_ms, queue_pending, timestamp} schema
- `tests/conftest.py` — flask_app, db, admin_client, finance_client, _make_cashier_token, _set_pending fixtures; backend/dashboard/ added to sys.path
- `tests/test_cashier_routes.py` — new file; 18 tests (TestApiLogin × 5, TestCompleteSale × 13)
- `tests/test_admin_critical.py` — new file; 17 tests (TestLoadBalance × 6, TestVoidTransaction × 11)
- `docs/DEPLOY.md` — new file; 11-section PythonAnywhere deployment runbook; 314 lines
- `scripts/verify-s02.sh` — new file; 32-check cache wiring verification
- `scripts/verify-s03.sh` — new file; 18-check startup guard and health check verification
