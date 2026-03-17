---
id: T03
parent: S02
milestone: M002
provides:
  - "cashier_routes.py: get_products() cached with 'products_all'/30s; complete_sale() invalidates 'transactions' and 'money_accounts' after append_row"
  - "api_server.py: get_profile() cached with 'users_all'/30s; /api/products GET cached with 'products_all'/30s; process_cashier_transaction() invalidates 'transactions' and 'money_accounts' after append_row; import includes invalidate_pattern"
  - "scripts/verify-s02.sh: conflict-marker grep fixed (exact-prefix pattern, no false positives from comment separators); process_cashier_transaction window widened from -A60 to -A120"
key_files:
  - backend/dashboard/cashier/cashier_routes.py
  - backend/api/api_server.py
  - scripts/verify-s02.sh
key_decisions:
  - "Balance-deduction reads (money_sheet.get_all_records() in complete_sale and process_cashier_transaction) intentionally NOT cached — stale balance could allow overdraft"
  - "invalidate_pattern calls placed immediately after trans_sheet.append_row() (before any notification code) so invalidation fires even if notifications raise"
  - "Widened verify-s02.sh grep window for process_cashier_transaction from -A60 to -A120 (function body is ~85 lines; invalidations land after complex retry + balance logic)"
  - "Fixed verify-s02.sh conflict marker pattern from grep -q '<<<<<<<\\|=======\\|>>>>>>>' to grep -qP '^(<{7} |={7}$|>{7} )' to avoid false positive from '# ==================== NEW PHASE 1 ENDPOINTS ====================' comment separator"
patterns_established:
  - "try/except ImportError at cashier_routes.py module level: _sys.path.insert to reach backend/cache.py two dirs up; no-op stubs so Flask still starts on cache import failure"
  - "None-check pattern: val = get_cached(key); if val is None: val = sheet.get_all_records(); set_cached(key, val, ttl=N) — avoids false re-fetch on empty list []"
  - "Invalidate after mutation: call invalidate_pattern(prefix) immediately after the last successful Sheets write, before notification/return code"
observability_surfaces:
  - "GET /api/cache/stats — hits counter increments on repeated GET /cashier/api/products, GET /api/student/profile, GET /api/products within TTL; misses increment after complete_sale or process_cashier_transaction (invalidation wipes transactions/money_accounts keys)"
  - "grep -n 'get_cached\\|set_cached\\|invalidate_pattern' backend/dashboard/cashier/cashier_routes.py backend/api/api_server.py — shows all cache call sites"
  - "bash scripts/verify-s02.sh — 32/32 checks; authoritative pass/fail for all S02 wiring"
duration: ~20min
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T03: Wire cache to cashier_routes.py and api_server.py

**Wired get_cached/set_cached to three display endpoints and invalidate_pattern to two mutation handlers; all 32 S02 verify checks pass.**

## What Happened

Added module-level cache import to `cashier_routes.py` (try/except ImportError with no-op fallbacks, two-level path insert to reach `backend/cache.py`). Wrapped the `get_products()` Products read with `"products_all"` / TTL 30. Added `invalidate_pattern("transactions")` and `invalidate_pattern("money_accounts")` in `complete_sale()` immediately after `trans_sheet.append_row()`. The `money_sheet.get_all_records()` balance-deduction read was left uncached per the critical overdraft constraint.

In `api_server.py`: extended the existing T01 import line to include `invalidate_pattern` (both real import and no-op fallback). Wrapped `get_profile()`'s Users read with `"users_all"` / TTL 30 and the `/api/products` GET Products read with `"products_all"` / TTL 30. Added `invalidate_pattern("transactions")` and `invalidate_pattern("money_accounts")` in `process_cashier_transaction()` after `trans_sheet.append_row()`.

Discovered two bugs in `scripts/verify-s02.sh` and fixed them: (1) the conflict-marker grep matched the `# ====` comment separator causing a false failure; (2) the `process_cashier_transaction` window was `-A60` but the function body is 85+ lines, so the invalidation calls were outside the grep window. Both fixed in the script.

## Verification

```
python -m py_compile backend/dashboard/cashier/cashier_routes.py backend/api/api_server.py
# → COMPILE OK

grep -n "get_cached\|set_cached\|invalidate_pattern" backend/dashboard/cashier/cashier_routes.py
# → import (line 19), get_products (208/211), complete_sale (366/367)

grep -n "get_cached\|set_cached\|invalidate_pattern" backend/api/api_server.py
# → import (31/39), get_profile (301/304), /api/products (904/907), process_cashier_transaction (1100/1101)

grep -A5 "money_sheet.get_all_records" backend/dashboard/cashier/cashier_routes.py | grep -v "get_cached"
# → only raw money_records = money_sheet.get_all_records() — no get_cached wrapper ✓

bash scripts/verify-s02.sh
# → Results: 32 passed, 0 failed — S02 verification PASSED ✓
```

## Diagnostics

- `GET /api/cache/stats` — after two calls to `/cashier/api/products`, `/api/student/profile`, or `/api/products` within 30s, `hits > 0` and `hit_rate > 0`
- After `POST /cashier/api/complete-sale` or `POST /api/cashier/transaction`, the next read for "transactions"/"money_accounts" keys is a miss (invalidated)
- On cache import failure in cashier_routes.py: no-op fallbacks activate, products endpoint reads Sheets every call, no crash

## Deviations

- `scripts/verify-s02.sh` was modified (not just the two backend files). The script had pre-existing bugs that caused false failures for T03 checks; fixing them was necessary to get an accurate pass/fail signal.

## Known Issues

None.

## Files Created/Modified

- `backend/dashboard/cashier/cashier_routes.py` — cache import block; get_products() cached; complete_sale() invalidates after append_row
- `backend/api/api_server.py` — invalidate_pattern added to import and no-op fallback; get_profile() and /api/products GET cached; process_cashier_transaction() invalidates after append_row
- `scripts/verify-s02.sh` — conflict-marker grep fixed; process_cashier_transaction window widened to -A120
- `.gsd/milestones/M002/slices/S02/tasks/T03-PLAN.md` — added Observability Impact section (pre-flight requirement)
