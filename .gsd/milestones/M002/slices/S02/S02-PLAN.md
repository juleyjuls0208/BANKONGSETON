# S02: Cache Layer Wiring

**Goal:** Hot endpoints serve from cache; mutations invalidate correctly; `GET /api/cache/stats` shows hits during repeated requests.
**Demo:** After repeated calls to the five hot admin endpoints and the cashier products endpoint, `cache_stats.hits > 0` and `cache_stats.hit_rate > 0`; after a `complete_sale`, `load_balance`, or `void_transaction`, the subsequent read fetches fresh data (no stale cache hit on the mutated key).

## Must-Haves

- Both `backend/api/api_server.py` and `backend/dashboard/cashier/cashier_routes.py` are valid Python — no conflict markers, no SyntaxError
- `get_products_list()`, `get_students()`, `analytics_summary()`, `get_recent_transactions()`, `get_stats()` in `admin_dashboard.py` use `get_cached`/`set_cached` with correct keys and TTLs
- `get_products()` in `cashier_routes.py` uses `get_cached`/`set_cached` with key `"products_all"`
- `get_profile()` and the `/api/products` endpoint in `api_server.py` use `get_cached`/`set_cached`
- `load_balance()`, `void_transaction()`, `update_product()`, `delete_product()` in `admin_dashboard.py` each call `invalidate_pattern` after a successful Sheets write
- `complete_sale()` in `cashier_routes.py` calls `invalidate_pattern` after success
- `process_cashier_transaction()` in `api_server.py` calls `invalidate_pattern` after success
- Balance reads inside payment deduction logic (`complete_sale`, `process_cashier_transaction`, `nfc_pay`) are NOT cached
- `GET /api/cache/stats` returns `{hits, misses, hit_rate, ...}` — already wired, must remain functional

## Proof Level

- This slice proves: integration (cache wiring is real code, not stubs; stats endpoint reflects actual hits)
- Real runtime required: no — syntax + grep verification is sufficient; runtime cache stats available when app runs
- Human/UAT required: no

## Verification

- `python -m py_compile backend/api/api_server.py backend/dashboard/cashier/cashier_routes.py backend/dashboard/admin_dashboard.py` — all exit 0
- `grep -n "<<<<<<\|=======\|>>>>>>>" backend/api/api_server.py backend/dashboard/cashier/cashier_routes.py` — empty
- `bash scripts/verify-s02.sh` — asserts `set_cached` and `invalidate_pattern` appear in each required function
- **Failure-path check:** `python -c "import sys; sys.path.insert(0,'backend'); from cache import get_cached, set_cached, invalidate_cached; print('cache import OK')"` — must print `cache import OK`; on ImportError, Flask startup will fail with the same error (surfaced immediately on startup via the try/except fallback in api_server.py)

## Observability / Diagnostics

- Runtime signals: `GET /api/cache/stats` on admin_dashboard returns `{hits, misses, size, hit_rate, evictions, stale_hits}`; hits increment on cache hits
- Inspection surfaces: cache stats endpoint at `/api/cache/stats`; `logger` lines emit on Sheets calls that hit cache misses
- Failure visibility: on cache miss, `get_cached(key)` returns `None` and execution falls through to the Sheets call — no silent failure; on import error for `cache.py`, Flask startup fails with ImportError
- Redaction constraints: none — cache keys are non-sensitive sheet names

## Integration Closure

- Upstream surfaces consumed: `backend/cache.py` (singleton `get_cached`, `set_cached`, `invalidate_pattern`, `get_cache_stats`); `backend/nfc_payments.py` (NFCService, ensure_virtual_cards_sheet)
- New wiring introduced: cache import added to `cashier_routes.py` and `api_server.py` (module-level); NFC module-level setup (nfc_service, _card_locks) added to `api_server.py` HEAD
- What remains before the milestone is truly usable end-to-end: S03 (health check), S04 (unit tests), S05 (deploy runbook)

## Tasks

- [x] **T01: Resolve merge conflicts in api_server.py and cashier_routes.py** `est:45m`
  - Why: Both files are syntactically invalid Python — no other task can proceed until they compile
  - Files: `backend/api/api_server.py`, `backend/dashboard/cashier/cashier_routes.py`
  - Do: For `api_server.py` — add missing module-level setup (threading, uuid, time, sys.path, NFC imports, cache imports, nfc_service, sms_notifier, _card_locks, _card_locks_lock) that exists in gsd/M001/S02 but not in HEAD; then resolve the one conflict block (lines 484–848) by keeping the gsd/M001/S02 side in full (all NFC endpoints with their existing cache calls). For `cashier_routes.py` — resolve first conflict (lines 427–474) by keeping the gsd/M001/S02 version (low-balance SMS + purchase SMS); resolve second conflict (lines 484–497) by keeping HEAD (FCM push to student).
  - Verify: `python -m py_compile backend/api/api_server.py backend/dashboard/cashier/cashier_routes.py` exits 0; `grep -rn "<<<<<<" backend/api/api_server.py backend/dashboard/cashier/cashier_routes.py` returns empty
  - Done when: Both files are valid Python; no conflict markers in either file; NFC endpoints are present and functional in api_server.py; low-balance SMS and FCM push are both present in cashier_routes.py

- [x] **T02: Wire cache to admin_dashboard.py hot endpoints and mutations** `est:45m`
  - Why: admin_dashboard.py drives the lunch-rush quota exhaustion — 91 raw Sheets calls, 2 cached; closing this gap is the primary goal of S02
  - Files: `backend/dashboard/admin_dashboard.py`
  - Do: Wrap `get_products_list()` with `get_cached("products_all")` / `set_cached("products_all", products, ttl=30)`. Wrap `get_students()` Users read with `"users_all"` (TTL 30) and Money Accounts read with `"money_accounts_all"` (TTL 30). Wrap `analytics_summary()` with `"analytics_summary"` (TTL 30). Wrap `get_recent_transactions()` Transactions read with `"transactions_all"` (TTL 10); wrap Users read inside it with `"users_all"` (TTL 30). Wrap `get_stats()` Users read with `"users_all"` and Transactions read with `"transactions_all"`. After the successful Sheets write in `load_balance()`: call `invalidate_pattern("money_accounts")` and `invalidate_pattern("transactions")`. After the successful append in `void_transaction()`: call `invalidate_pattern("transactions")` and `invalidate_pattern("money_accounts")`. After writes in `update_product()` and `delete_product()`: call `invalidate_pattern("products")`. Pattern for all reads: `val = get_cached(key); if val is None: val = sheet.get_all_records(); set_cached(key, val, ttl=N)`.
  - Verify: `python -m py_compile backend/dashboard/admin_dashboard.py`; `grep -A5 "def get_products_list" backend/dashboard/admin_dashboard.py | grep set_cached`; same for get_students, analytics_summary, get_recent_transactions, get_stats; `grep -A20 "def load_balance" backend/dashboard/admin_dashboard.py | grep invalidate_pattern`; same for void_transaction, update_product, delete_product
  - Done when: All 5 hot endpoints have `get_cached` / `set_cached` guards; all 4 mutation handlers call `invalidate_pattern` after successful Sheets writes; file compiles without error

- [x] **T03: Wire cache to cashier_routes.py and api_server.py** `est:30m`
  - Why: cashier_routes.py has 0 cached calls; api_server.py display endpoints are uncached; process_cashier_transaction doesn't invalidate after writes
  - Files: `backend/dashboard/cashier/cashier_routes.py`, `backend/api/api_server.py`
  - Do: In `cashier_routes.py` — add cache import at module level: `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))` then `from cache import get_cached, set_cached, invalidate_pattern` (inside a try/except ImportError that sets them to no-op lambdas as fallback). Wrap `get_products()` with `"products_all"` (TTL 30). In `complete_sale()`, after the successful Sheets writes but before the return, add `invalidate_pattern("transactions")` and `invalidate_pattern("money_accounts")`. Do NOT cache the Money Accounts balance read used for deduction. In `api_server.py` — cache imports were added in T01; wrap `get_profile()` Users read with `"users_all"` (TTL 30). Wrap the `/api/products` (GET) endpoint's Products read with `"products_all"` (TTL 30). In `process_cashier_transaction()`, after `trans_sheet.append_row(...)`, add `invalidate_pattern("transactions")` and `invalidate_pattern("money_accounts")`. Do NOT cache the `money_sheet.get_all_records()` call used for balance deduction.
  - Verify: `python -m py_compile backend/dashboard/cashier/cashier_routes.py backend/api/api_server.py`; `grep -n "set_cached\|invalidate_pattern" backend/dashboard/cashier/cashier_routes.py`; `grep -n "set_cached\|invalidate_pattern" backend/api/api_server.py`
  - Done when: cashier_routes.py imports cache and wraps get_products; complete_sale invalidates after success; api_server.py get_profile and /api/products use cache; process_cashier_transaction invalidates after success; balance-deduction reads are NOT cached

## Files Likely Touched

- `backend/api/api_server.py`
- `backend/dashboard/cashier/cashier_routes.py`
- `backend/dashboard/admin_dashboard.py`
- `scripts/verify-s02.sh` (new — verification script)
