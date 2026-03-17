# S02: Cache Layer Wiring — UAT

**Milestone:** M002
**Written:** 2026-03-15

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: The slice plan explicitly states "Real runtime required: no — syntax + grep verification is sufficient; runtime cache stats available when app runs." The 32-check verify-s02.sh script is the authoritative proof; GET /api/cache/stats runtime signals are bonus confirmation, not required for slice completion.

## Preconditions

- `pip install -r backend/dashboard/requirements.txt` and `pip install -r backend/api/requirements_api.txt` both succeed (S01 complete)
- Python available in PATH (any 3.x)
- Working directory is project root (`/c/Users/admin/Desktop/projects/BANKONGSETON`)
- `backend/cache.py` is present (it was not modified in S02; verify with `ls backend/cache.py`)

## Smoke Test

```bash
bash scripts/verify-s02.sh
```
Expected: `Results: 32 passed, 0 failed — S02 verification PASSED ✓`

This single command is the definitive smoke test. If it passes, the slice is verified.

## Test Cases

### 1. All three files compile without syntax errors

```bash
python -m py_compile backend/api/api_server.py backend/dashboard/cashier/cashier_routes.py backend/dashboard/admin_dashboard.py
echo "Exit: $?"
```

**Expected:** Exit code 0, no output, `echo` prints `Exit: 0`

### 2. No git conflict markers remain in any file

```bash
grep -n "^<<<<<<< \|^=======$\|^>>>>>>> " backend/api/api_server.py backend/dashboard/cashier/cashier_routes.py
echo "Lines found: $?"
```

**Expected:** Empty output (grep finds nothing), exit code 1 (no match = exit 1 for grep, which means zero conflict lines found)

### 3. Cache module is importable from project root

```bash
python -c "import sys; sys.path.insert(0,'backend'); from cache import get_cached, set_cached, invalidate_cached; print('cache import OK')"
```

**Expected:** Prints `cache import OK` with exit 0. An ImportError here means Flask startup will fail with the same error.

### 4. admin_dashboard.py hot endpoints are cached

```bash
grep -A15 "def get_products_list" backend/dashboard/admin_dashboard.py | grep -E "get_cached|set_cached"
grep -A20 "def get_students" backend/dashboard/admin_dashboard.py | grep -E "get_cached|set_cached"
grep -A30 "def analytics_summary" backend/dashboard/admin_dashboard.py | grep -E "get_cached|set_cached"
grep -A30 "def get_recent_transactions" backend/dashboard/admin_dashboard.py | grep -E "get_cached|set_cached"
grep -A20 "def get_stats" backend/dashboard/admin_dashboard.py | grep -E "get_cached|set_cached"
```

**Expected:** Each command returns at least one matching line containing `get_cached` and at least one containing `set_cached`. Any empty result means that endpoint is uncached and will hit Sheets every request.

### 5. admin_dashboard.py mutations invalidate cache after writes

```bash
grep -A65 "def load_balance" backend/dashboard/admin_dashboard.py | grep "invalidate_pattern"
grep -A30 "def void_transaction" backend/dashboard/admin_dashboard.py | grep "invalidate_pattern"
grep -A30 "def update_product" backend/dashboard/admin_dashboard.py | grep "invalidate_pattern"
grep -A20 "def delete_product" backend/dashboard/admin_dashboard.py | grep "invalidate_pattern"
```

**Expected:** Each command returns at least one `invalidate_pattern(...)` line. Missing lines mean stale cache will persist after mutations — the primary correctness risk of this slice.

### 6. cashier_routes.py has cache import and wires get_products + complete_sale

```bash
grep -n "get_cached\|set_cached\|invalidate_pattern" backend/dashboard/cashier/cashier_routes.py
```

**Expected:** At least 6 lines — the import line, `get_cached` in `get_products`, `set_cached` in `get_products`, and two `invalidate_pattern` calls in `complete_sale`. Fewer than 6 means the wiring is incomplete.

### 7. api_server.py caches get_profile and /api/products; invalidates in process_cashier_transaction

```bash
grep -n "get_cached\|set_cached\|invalidate_pattern" backend/api/api_server.py
```

**Expected:** At least 8 lines — import (real + no-op fallback), `get_cached`/`set_cached` in `get_profile`, `get_cached`/`set_cached` in the `/api/products` GET handler, and two `invalidate_pattern` calls in `process_cashier_transaction`.

### 8. NFC endpoints survived the conflict resolution (T01 correctness check)

```bash
grep -n "def nfc_register\|def nfc_status\|def nfc_pay" backend/api/api_server.py
```

**Expected:** Three matching lines with line numbers. These endpoints were at risk of being dropped during conflict resolution.

### 9. Both SMS types and FCM push intact in cashier_routes.py (T01 correctness check)

```bash
grep -n "send_low_balance_sms\|send_purchase_sms\|send_purchase_push" backend/dashboard/cashier/cashier_routes.py
```

**Expected:** At least three matching lines (one per notification type). Missing any means the conflict resolution dropped a notification path.

### 10. Balance-deduction reads are NOT cached (overdraft safety)

```bash
grep -A5 "money_sheet.get_all_records" backend/dashboard/cashier/cashier_routes.py | grep -v "get_cached"
grep -A5 "money_sheet.get_all_records" backend/api/api_server.py | grep -v "get_cached"
```

**Expected:** The raw `money_records = money_sheet.get_all_records()` lines appear without a `get_cached` wrapper. If these reads were cached, a stale balance could allow a student to overdraft.

## Edge Cases

### False positive from comment separators in conflict-marker check

```bash
grep -n "^<<<<<<< \|^=======$\|^>>>>>>> " backend/api/api_server.py | grep -v "^#"
```

**Expected:** Empty. The `# ==================== NEW PHASE 1 ENDPOINTS ====================` comment separator previously triggered a false positive with a naive `=======` substring grep; the exact-prefix pattern fixes this.

### Cache fallback path in cashier_routes.py — import failure degrades gracefully

```bash
python -c "
import sys, os
# Simulate import failure by inserting a dummy cache module
import types
fake_cache = types.ModuleType('cache')
# Don't insert it — just verify the try/except block exists in source
src = open('backend/dashboard/cashier/cashier_routes.py').read()
assert 'except ImportError' in src, 'No ImportError fallback found'
assert 'get_cached = lambda' in src or 'def get_cached' in src, 'No no-op fallback for get_cached'
print('Fallback block confirmed')
"
```

**Expected:** Prints `Fallback block confirmed`. If this fails, a cache import error would crash the cashier POS.

### None-check correctness — empty list is a valid cache hit

```bash
grep "if not val\|if not records\|if not transactions\|if not users\|if not students\|if not accounts\|if not money_accounts" backend/dashboard/admin_dashboard.py
```

**Expected:** Empty output. Any `if not val:` style check would treat an empty Sheets result as a cache miss and re-fetch on every call — the bug this pattern prevents.

### Full 32-check suite with zero failures

```bash
bash scripts/verify-s02.sh 2>&1 | tail -5
```

**Expected:**
```
========================================
Results: 32 passed, 0 failed
S02 verification PASSED ✓
```

## Failure Signals

- `verify-s02.sh` reports any failed check → specific check name identifies which file/function/pattern is missing
- `python -m py_compile` prints a SyntaxError → the conflict resolution or edit introduced broken syntax
- `grep "get_cached\|set_cached" backend/dashboard/admin_dashboard.py` returns no lines for a hot endpoint → that endpoint is uncached and will exhaust Sheets quota during lunch rush
- `grep "invalidate_pattern" backend/dashboard/admin_dashboard.py` returns no lines for a mutation handler → stale data will be served after that mutation
- `grep "send_low_balance_sms\|send_purchase_sms" backend/dashboard/cashier/cashier_routes.py` returns empty → SMS notifications were dropped during conflict resolution
- `grep "def nfc_register\|def nfc_status\|def nfc_pay" backend/api/api_server.py` returns empty → NFC endpoints were dropped during conflict resolution
- Cache import command returns ImportError → Flask will fail to start; `backend/cache.py` may be missing or path insert is wrong

## Requirements Proved By This UAT

- R015 (Cache Layer Coverage) — all six hot endpoints use get_cached/set_cached with TTLs; all six mutation paths call invalidate_pattern after writes; balance-deduction reads are explicitly uncached; 32/32 verify checks confirm wiring in code

## Not Proven By This UAT

- Actual Sheets quota reduction at runtime — proving hits > 0 at runtime requires the Flask app to be running with a real Sheets connection; artifact-driven verification is sufficient per slice plan
- Cache TTL adequacy under real lunch-rush load — 30s and 10s TTLs were chosen as reasonable defaults; no load testing was done
- Correctness of cache key eviction and TTL expiry — these are properties of `backend/cache.py` which was not modified in S02; their correctness is an upstream dependency
- NFC endpoint correctness beyond syntax validity — functional testing of nfc_register, nfc_status, nfc_pay requires a real NFC client and Sheets connection (out of scope for S02)

## Notes for Tester

- Run `bash scripts/verify-s02.sh` first — it is the single authoritative signal. If it passes 32/32, the slice is done. Manual grep checks above are for diagnosis only.
- The `=======` in `# ==================== NEW PHASE 1 ENDPOINTS ====================` will NOT match the conflict-marker grep (uses `^=======$` exact-line pattern) — this is intentional and correct.
- If testing the running app: call any hot endpoint twice in quick succession and then `GET /api/cache/stats`; `hits` should be > 0. This is bonus validation, not required for slice acceptance.
- The balance-deduction read intentionally hits Sheets on every payment — do not "fix" this as a performance improvement without understanding the overdraft risk (D018 in DECISIONS.md).
