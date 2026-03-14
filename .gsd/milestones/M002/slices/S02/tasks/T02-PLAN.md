---
estimated_steps: 6
estimated_files: 1
---

# T02: Wire cache to admin_dashboard.py hot endpoints and mutations

**Slice:** S02 — Cache Layer Wiring
**Milestone:** M002

## Description

`admin_dashboard.py` already imports the cache module at line 29 (`from cache import get_cache, get_cache_stats, set_cached, get_cached, invalidate_pattern`). The problem is adoption: 91 raw `get_all_records()` calls exist, only 2 use cache. This task wires `get_cached`/`set_cached` to the five hottest read endpoints and adds `invalidate_pattern` calls to the four mutation handlers.

**Cache pattern** (identical for every read endpoint):
```python
val = get_cached("key")
if val is None:
    val = sheet.get_all_records()
    set_cached("key", val, ttl=N)
```
Use `None`-check (not `not val`) — an empty list `[]` is falsy and would cause an infinite re-fetch.

**Canonical keys and TTLs:**
- `"products_all"` — TTL 30s
- `"users_all"` — TTL 30s
- `"money_accounts_all"` — TTL 30s
- `"analytics_summary"` — TTL 30s
- `"transactions_all"` — TTL 10s (transaction data is more time-sensitive)

**Important: do not cache the `_sheets_cache` / `get_cached_sheet_data()` reads** — they use a separate parallel cache dict; leave those untouched.

## Steps

1. **Cache `get_products_list()`** (line ~315). Replace the `products_sheet.get_all_records()` call with the cache pattern using key `"products_all"`, TTL 30. The `products` list built from `records` is the value to cache — not the raw records but the already-shaped list.

   Actually: cache the raw `records` from `get_all_records()` and build the products list from them. This keeps the cache key shape consistent with other endpoints that also read Products.

2. **Cache `get_students()`** (line ~750). Cache the Users `get_all_records()` with `"users_all"` TTL 30. Cache the Money Accounts `get_all_records()` with `"money_accounts_all"` TTL 30.

3. **Cache `analytics_summary()`** (line ~494). Cache the Transactions `get_all_records()` with `"transactions_all"` TTL 10. Cache the Money Accounts `get_all_records()` with `"money_accounts_all"` TTL 30.

4. **Cache `get_recent_transactions()`** (line ~1023). Cache the Transactions `get_all_records()` with `"transactions_all"` TTL 10. Cache the Users `get_all_records()` with `"users_all"` TTL 30.

5. **Cache `get_stats()`** (line ~716). Cache the Users `get_all_records()` with `"users_all"` TTL 30. Cache the Transactions `get_all_records()` with `"transactions_all"` TTL 10.

6. **Add `invalidate_pattern` to mutation handlers.** In `load_balance()` (line ~882): after `money_sheet.update_cell(row_index, update_col, timestamp)` (the last successful Sheets write), add `invalidate_pattern("money_accounts")` and `invalidate_pattern("transactions")`. In `void_transaction()` (line ~2181): after `txn_sheet.append_row([...])` (the void record append), add `invalidate_pattern("transactions")` and `invalidate_pattern("money_accounts")`. In `update_product()` (line ~345): after the `products_sheet.update(...)` or `products_sheet.append_row(...)`, add `invalidate_pattern("products")`. In `delete_product()` (line ~394): after the deactivation write, add `invalidate_pattern("products")`.

## Must-Haves

- [ ] `get_products_list()` uses `get_cached("products_all")` / `set_cached("products_all", ..., ttl=30)`
- [ ] `get_students()` uses `get_cached("users_all")` and `get_cached("money_accounts_all")` (both TTL 30)
- [ ] `analytics_summary()` uses `get_cached("transactions_all")` (TTL 10) and `get_cached("money_accounts_all")` (TTL 30)
- [ ] `get_recent_transactions()` uses `get_cached("transactions_all")` (TTL 10) and `get_cached("users_all")` (TTL 30)
- [ ] `get_stats()` uses `get_cached("users_all")` (TTL 30) and `get_cached("transactions_all")` (TTL 10)
- [ ] `load_balance()` calls `invalidate_pattern("money_accounts")` and `invalidate_pattern("transactions")` after successful write
- [ ] `void_transaction()` calls `invalidate_pattern("transactions")` and `invalidate_pattern("money_accounts")` after successful append
- [ ] `update_product()` calls `invalidate_pattern("products")` after write
- [ ] `delete_product()` calls `invalidate_pattern("products")` after write
- [ ] None of the cached reads use `if not val` (must use `if val is None`)
- [ ] `python -m py_compile backend/dashboard/admin_dashboard.py` exits 0

## Verification

- `python -m py_compile backend/dashboard/admin_dashboard.py`
- `grep -A10 "def get_products_list" backend/dashboard/admin_dashboard.py | grep -E "get_cached|set_cached"`
- `grep -A10 "def analytics_summary" backend/dashboard/admin_dashboard.py | grep -E "get_cached|set_cached"`
- `grep -A25 "def get_recent_transactions" backend/dashboard/admin_dashboard.py | grep -E "get_cached|set_cached"`
- `grep -A10 "def get_stats" backend/dashboard/admin_dashboard.py | grep -E "get_cached|set_cached"`
- `grep -B2 -A5 "invalidate_pattern" backend/dashboard/admin_dashboard.py` — should show hits in load_balance, void_transaction, update_product, delete_product

## Observability Impact

- Signals added/changed: `GET /api/cache/stats` hit counter now increments on repeated calls to the five hot endpoints; Sheets API calls drop from up to 10/request to at most 2/min per endpoint
- How a future agent inspects this: `curl http://localhost:5000/api/cache/stats` before and after repeated reads — `hits` count rises on second and subsequent calls within TTL window
- Failure state exposed: a stale `None` from an empty sheet would trigger re-fetch every time (acceptable — empty list [] is stored correctly with the `is None` check)

## Inputs

- `backend/dashboard/admin_dashboard.py` — line 29 already imports `get_cached`, `set_cached`, `invalidate_pattern`; endpoints at lines 315 (get_products_list), 494 (analytics_summary), 716 (get_stats), 748 (get_students), 882 (load_balance), 1023 (get_recent_transactions), 2178 (void_transaction), 345 (update_product), 394 (delete_product)
- `backend/cache.py` — TTL cache singleton; `invalidate_pattern(pattern)` does substring match across all keys

## Expected Output

- `backend/dashboard/admin_dashboard.py` — all five hot endpoints guarded with cache read/write; four mutation handlers invalidate relevant keys; file compiles cleanly
