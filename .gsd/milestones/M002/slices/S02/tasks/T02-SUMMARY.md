---
id: T02
parent: S02
milestone: M002
provides:
  - "Five hot read endpoints in admin_dashboard.py served from TTL cache (products_all/30s, users_all/30s, money_accounts_all/30s, transactions_all/10s)"
  - "Four mutation handlers in admin_dashboard.py invalidate relevant cache keys after successful Sheets writes"
key_files:
  - backend/dashboard/admin_dashboard.py
  - scripts/verify-s02.sh
key_decisions:
  - "Cache raw get_all_records() result (not the shaped list) in get_products_list() — keeps key shape consistent across endpoints that also read Products"
  - "Invalidate after the LAST successful Sheets write in load_balance() (after LastUpdated update_cell), not after the first"
  - "verify-s02.sh A60 window was too tight for load_balance (61-line function body) — bumped to A65 for those two checks"
patterns_established:
  - "None-check pattern: val = get_cached(key); if val is None: val = sheet.get_all_records(); set_cached(key, val, ttl=N) — avoids false re-fetch on empty list []"
  - "Invalidate after mutation: call invalidate_pattern(prefix) immediately after the last successful Sheets write, before the return"
observability_surfaces:
  - "GET /api/cache/stats — hits counter increments on second and subsequent calls within TTL window; Sheets API call rate drops to at most 1/30s per key"
  - "python -m py_compile backend/dashboard/admin_dashboard.py — must exit 0"
  - "bash scripts/verify-s02.sh — T02 section: 11/11 checks pass"
duration: ~30m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Wire cache to admin_dashboard.py hot endpoints and mutations

**Wired `get_cached`/`set_cached` to five hot read endpoints and `invalidate_pattern` to four mutation handlers in `admin_dashboard.py`; file compiles cleanly and all 11 T02 verify-s02.sh checks pass.**

## What Happened

`admin_dashboard.py` already imported `get_cached`, `set_cached`, and `invalidate_pattern` at line 29 but used none of them in the hot endpoints. Applied the canonical cache pattern to each of the five hottest read endpoints:

- **`get_products_list()`** — caches raw `products_sheet.get_all_records()` as `"products_all"` TTL 30s
- **`get_students()`** — caches Users as `"users_all"` TTL 30s and Money Accounts as `"money_accounts_all"` TTL 30s
- **`analytics_summary()`** — caches Transactions Log as `"transactions_all"` TTL 10s and Money Accounts as `"money_accounts_all"` TTL 30s
- **`get_recent_transactions()`** — caches Transactions as `"transactions_all"` TTL 10s and Users as `"users_all"` TTL 30s
- **`get_stats()`** — caches Users as `"users_all"` TTL 30s and Transactions as `"transactions_all"` TTL 10s

All cache reads use `if val is None:` (not `if not val:`) to handle empty lists correctly.

Added `invalidate_pattern` calls to all four mutation handlers:
- **`load_balance()`** — `invalidate_pattern("money_accounts")` + `invalidate_pattern("transactions")` after `money_sheet.update_cell(row_index, update_col, timestamp)` (the last Sheets write)
- **`void_transaction()`** — `invalidate_pattern("transactions")` + `invalidate_pattern("money_accounts")` after `txn_sheet.append_row([...])`
- **`update_product()`** — `invalidate_pattern("products")` in both the update and append branches
- **`delete_product()`** — `invalidate_pattern("products")` after the `update_cell` deactivation write

Also bumped `verify-s02.sh` `-A60` to `-A65` for the two `load_balance` invalidation checks — the function body spans 61 lines, placing the second invalidation one line outside the original window.

## Verification

```
python -m py_compile backend/dashboard/admin_dashboard.py  # Exit: 0

# Cache reads present
grep -A15 "def get_products_list" ... | grep -E "get_cached|set_cached"   # ✓ both
grep -A20 "def get_students"      ... | grep -E "get_cached|set_cached"   # ✓ both
grep -A20 "def analytics_summary" ... | grep -E "get_cached|set_cached"   # ✓ both
grep -A30 "def get_recent_transactions" ... | grep -E "get_cached|set_cached" # ✓ both
grep -A20 "def get_stats"         ... | grep -E "get_cached|set_cached"   # ✓ both

# Mutation invalidations present
grep -B2 -A2 "invalidate_pattern" backend/dashboard/admin_dashboard.py
# → load_balance: money_accounts + transactions ✓
# → void_transaction: transactions + money_accounts ✓
# → update_product: products (both branches) ✓
# → delete_product: products ✓

# No falsy cache checks
grep "if not val\|if not records\|if not transactions\|if not users\|if not students\|if not accounts\|if not money_accounts" admin_dashboard.py
# → empty ✓

bash scripts/verify-s02.sh  # T02 section: 11/11 pass; T03 section: 9 expected failures (not yet done)

python -c "import sys; sys.path.insert(0,'backend'); from cache import get_cached, set_cached, invalidate_pattern; print('cache import OK')"
# → cache import OK ✓
```

## Diagnostics

- `GET /api/cache/stats` — `hits` counter will increment on second and subsequent calls to any of the five hot endpoints within the TTL window; Sheets API rate drops from up to 10/request to at most 1/30s
- Cache miss path: `get_cached(key)` returns `None` → falls through to `sheet.get_all_records()` → logger records the Sheets call → `set_cached(key, result, ttl=N)` stores it
- Cache hit path: `get_cached(key)` returns the list → `get_all_records()` is skipped entirely
- Invalidation check: after `load_balance`, `void_transaction`, `update_product`, or `delete_product`, the next read for the affected key will miss and re-fetch fresh data

## Deviations

- **verify-s02.sh A60→A65 for load_balance**: `load_balance()` body spans 61 lines before the invalidation calls; the original `-A60` window captured only the first invalidation. Bumped to `-A65` to fit both — this is a script accuracy fix, not a code change.
- **Cache key for products in get_products_list**: task plan noted caching "raw records" (not shaped list) for key-shape consistency across endpoints — implemented as specified.

## Known Issues

None. All T02 must-haves verified. T03 (cashier_routes.py and api_server.py wiring) is the next task and its verify checks are expected to fail until executed.

## Files Created/Modified

- `backend/dashboard/admin_dashboard.py` — five hot read endpoints now use get_cached/set_cached; four mutation handlers now call invalidate_pattern
- `scripts/verify-s02.sh` — bumped A60→A65 for load_balance invalidation checks (function body is 61 lines)
