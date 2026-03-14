---
estimated_steps: 6
estimated_files: 2
---

# T03: Wire cache to cashier_routes.py and api_server.py

**Slice:** S02 — Cache Layer Wiring
**Milestone:** M002

## Description

Two remaining files need cache wiring. `cashier_routes.py` has zero cached calls; `api_server.py` display endpoints are uncached and `process_cashier_transaction` doesn't invalidate after writes (the NFC endpoints already have cache calls from the T01 conflict resolution).

**Critical constraint:** The balance-deduction reads in `complete_sale()` and `process_cashier_transaction()` must NOT be cached. These reads determine the current balance before deducting — a stale cached balance could allow overdraft. Only the Products read in `get_products()` (display/POS grid) is cached.

**Import path for cache in cashier_routes.py:** The file is at `backend/dashboard/cashier/cashier_routes.py`. To reach `backend/cache.py`, it needs two levels up: `os.path.join(os.path.dirname(__file__), '..', '..')`. Use a try/except ImportError with no-op fallbacks so the cashier app still starts even if cache import somehow fails.

**Import path for cache in api_server.py:** After T01, `from cache import get_cached, set_cached, invalidate_cached` is already at module level. `invalidate_pattern` also needs to be imported — add it to that import line.

## Steps

1. **cashier_routes.py — add cache import at module level.** Near the top of the file (after existing imports), add:
   ```python
   try:
       import sys as _sys
       _sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
       from cache import get_cached, set_cached, invalidate_pattern
   except ImportError:
       def get_cached(key): return None
       def set_cached(key, val, ttl=None): pass
       def invalidate_pattern(pat): pass
   ```

2. **cashier_routes.py — cache `get_products()`** (line ~188). Replace `records = products_sheet.get_all_records()` with the cache pattern using key `"products_all"`, TTL 30:
   ```python
   records = get_cached("products_all")
   if records is None:
       records = products_sheet.get_all_records()
       set_cached("products_all", records, ttl=30)
   ```

3. **cashier_routes.py — add cache invalidation to `complete_sale()`** (line ~265). After the successful Sheets writes (after the transaction append row and before the return jsonify), add:
   ```python
   invalidate_pattern("transactions")
   invalidate_pattern("money_accounts")
   ```
   Do NOT cache the `money_sheet.get_all_records()` call used for balance checking and deduction — that must always read fresh.

4. **api_server.py — extend cache import to include `invalidate_pattern`.** The T01 import line is `from cache import get_cached, set_cached, invalidate_cached` — add `invalidate_pattern` to it.

5. **api_server.py — cache `get_profile()`** (line ~243). The Users `get_all_records()` call is used only for profile display, not for payment processing. Wrap it with `"users_all"` TTL 30:
   ```python
   records = get_cached("users_all")
   if records is None:
       records = users_sheet.get_all_records()
       set_cached("users_all", records, ttl=30)
   ```

6. **api_server.py — cache `/api/products` (GET) endpoint** (line ~852 in the POST-conflict section). Wrap the `products_sheet.get_all_records()` call with `"products_all"` TTL 30.

7. **api_server.py — add cache invalidation to `process_cashier_transaction()`** (line ~972). After `trans_sheet.append_row(transaction_row)`, add:
   ```python
   invalidate_pattern("transactions")
   invalidate_pattern("money_accounts")
   ```
   Do NOT cache the `money_sheet.get_all_records()` call used for balance checking — that must always read fresh.

## Must-Haves

- [ ] `cashier_routes.py` imports `get_cached`, `set_cached`, `invalidate_pattern` at module level (with ImportError fallback)
- [ ] `get_products()` in `cashier_routes.py` uses `get_cached("products_all")` / `set_cached("products_all", ..., ttl=30)`
- [ ] `complete_sale()` in `cashier_routes.py` calls `invalidate_pattern("transactions")` and `invalidate_pattern("money_accounts")` after success
- [ ] `complete_sale()` Money Accounts balance-deduction read is NOT wrapped in `get_cached`
- [ ] `api_server.py` import includes `invalidate_pattern`
- [ ] `get_profile()` in `api_server.py` wraps Users `get_all_records()` with `"users_all"` TTL 30
- [ ] `/api/products` GET in `api_server.py` wraps Products `get_all_records()` with `"products_all"` TTL 30
- [ ] `process_cashier_transaction()` calls `invalidate_pattern("transactions")` and `invalidate_pattern("money_accounts")` after `trans_sheet.append_row()`
- [ ] `process_cashier_transaction()` Money Accounts balance-deduction read is NOT cached
- [ ] `python -m py_compile backend/dashboard/cashier/cashier_routes.py backend/api/api_server.py` exits 0

## Verification

- `python -m py_compile backend/dashboard/cashier/cashier_routes.py backend/api/api_server.py`
- `grep -n "get_cached\|set_cached\|invalidate_pattern" backend/dashboard/cashier/cashier_routes.py` — should show import + get_products + complete_sale hits
- `grep -n "get_cached\|set_cached\|invalidate_pattern" backend/api/api_server.py` — should show import + get_profile + /api/products + process_cashier_transaction + NFC endpoints (from T01)
- `grep -A5 "money_sheet.get_all_records" backend/dashboard/cashier/cashier_routes.py | grep -v "get_cached"` — balance read must not be inside a get_cached block

## Inputs

- `backend/dashboard/cashier/cashier_routes.py` — T01 resolved conflicts; `get_products()` at line ~188; `complete_sale()` at line ~265
- `backend/api/api_server.py` — T01 resolved conflicts and added module-level cache import; `get_profile()` at line ~243; `/api/products` GET endpoint at line ~852; `process_cashier_transaction()` at line ~972
- `backend/cache.py` — `invalidate_pattern(pattern)` does substring match

## Expected Output

- `backend/dashboard/cashier/cashier_routes.py` — cache import at module level; `get_products()` cached; `complete_sale()` invalidates after success; balance-deduction reads remain uncached
- `backend/api/api_server.py` — `get_profile()` and `/api/products` GET cached; `process_cashier_transaction()` invalidates after success; NFC endpoints retain their existing cache calls from T01

## Observability Impact

**Signals that change after T03:**
- `GET /api/cache/stats` — `hits` counter increments on second and subsequent requests to `GET /cashier/api/products` (cashier POS grid) and `GET /api/student/profile` and `GET /api/products` within their 30s TTL windows. `hit_rate` rises above 0.
- `misses` counter increments on first request to each of those endpoints (cold start) and on any request immediately after a `complete_sale` or `process_cashier_transaction` (invalidation wipes keys matching "transactions" and "money_accounts").

**How a future agent inspects this task's runtime effect:**
1. Call `GET /api/cache/stats` twice in quick succession for each newly cached endpoint — `hits` must be > 0 on the second call.
2. Call `POST /cashier/api/complete-sale` or `POST /api/cashier/transaction`, then `GET /api/cache/stats` — `misses` for "transactions"/"money_accounts" keys will increment, showing invalidation fired.
3. `grep -n "get_cached\|set_cached\|invalidate_pattern" backend/dashboard/cashier/cashier_routes.py backend/api/api_server.py` must show cache calls in all required functions.

**Failure visibility:**
- If cache import fails in cashier_routes.py: no-op fallbacks activate (ImportError caught), Flask still starts, products endpoint reads Sheets every time (no caching, no error).
- If cache import fails in api_server.py: existing no-op fallback block already handles it; `get_profile` and `/api/products` fall back to always reading Sheets.
- Money Accounts reads for balance checks are intentionally uncached — a stale-balance bug would appear as overdraft transactions succeeding with negative balance (testable by checking balance < 0 in Sheets after a sale with exact balance).

**Redaction constraints:** None — cache keys are non-sensitive sheet names ("products_all", "users_all", "transactions", "money_accounts").
