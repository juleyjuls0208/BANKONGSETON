# S02: Cache Layer Wiring — Research

**Date:** 2026-03-15

## Summary

S02 owns **R015 — Cache Layer Coverage**. The cache implementation (`backend/cache.py`) is complete and solid — 254 lines, TTLCache with LRU eviction, thread-safe, `get_cached` / `set_cached` / `invalidate_pattern` / `get_cache_stats` all ready to use. The problem is adoption: `admin_dashboard.py` has 91 raw `get_all_records` calls and only 2 cached ones (via `cache.py`); `cashier_routes.py` has 17 raw worksheet calls and 0 cached; `api_server.py` has 46 raw calls and the handful of cache calls that do exist are inside unresolved merge conflict markers (so they don't run).

**Critical blocker discovered during research:** Two additional unresolved merge conflicts were missed by S01. `backend/api/api_server.py` has a large conflict block spanning lines 484–848 that contains all NFC endpoints plus the existing cache calls. `backend/dashboard/cashier/cashier_routes.py` has two conflict blocks (lines 427–474 and 484–497) inside `complete_sale()`. Both files are invalid Python as they stand. These conflicts must be resolved as the first step of S02 before any cache wiring can happen.

The wiring plan itself is straightforward: five hot endpoints in admin_dashboard.py, one in cashier_routes.py, and three in api_server.py get `get_cached` / `set_cached` wrapped around their `get_all_records()` calls. Mutations (`load_balance`, `void_transaction`, `complete_sale`, `process_cashier_transaction`) each get two `invalidate_pattern()` calls after a successful Sheets write. The `GET /api/cache/stats` endpoint is already wired — it calls the real `get_cache_stats()` today. No new cache logic needed anywhere.

## Recommendation

Resolve the two unexpected merge conflicts first (they gate everything else), then wire cache to each endpoint in a single focused pass per file. Keep balance-read calls in `complete_sale()` and `process_cashier_transaction()` un-cached — payment processing must read fresh data to prevent overdraft. Cache reads are for reporting and display endpoints only.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Cache with TTL + LRU | `backend/cache.py` — `TTLCache`, `get_cached`, `set_cached`, `invalidate_pattern` | Fully implemented, thread-safe, stats-equipped — zero new code needed |
| Cache statistics endpoint | `GET /api/cache/stats` in admin_dashboard.py line 462 | Already routes to real `get_cache_stats()` — nothing to add |
| Import path for cache in sub-modules | `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))` — pattern used throughout | cashier_routes.py and api_server.py both need `backend/` on sys.path to import cache.py |

## Existing Code and Patterns

- `backend/cache.py` — Complete cache implementation. Public API: `get_cached(key)`, `set_cached(key, value, ttl=None)`, `invalidate_cached(key)`, `invalidate_pattern(pattern)`, `get_cache_stats()`. Module-level singleton `_global_cache = TTLCache(default_ttl=30, max_size=200)`. The `invalidate_pattern(pattern)` does substring match across all keys — so `invalidate_pattern("money_accounts")` clears `money_accounts_all`, and `invalidate_pattern("transactions")` clears `transactions_all`. Thread-safe via `threading.RLock`.

- `backend/dashboard/admin_dashboard.py` line 29 — imports `get_cache, get_cache_stats, set_cached, get_cached, invalidate_pattern` from cache at module load. These are already available throughout the file. Also has a parallel `_sheets_cache` dict (line 111) with its own `get_cached_sheet_data()` helper — this is an old local cache that should not be mixed up with `cache.py` calls. Leave `_sheets_cache` alone; just add `cache.py` calls to the hot endpoints.

- `backend/dashboard/admin_dashboard.py` line 462 — `GET /api/cache/stats` is already wired to `get_cache_stats()`. Returns `{size, max_size, hits, misses, hit_rate, evictions, stale_hits}`. No changes needed here.

- `backend/api/api_server.py` — No import of `cache.py` at module level. Cache calls (`get_cached`, `set_cached`, `invalidate_cached`) appear in the `gsd/M001/S02` side of the large merge conflict (lines 490–848) but are undefined there because the conflict block was never resolved. Adding the import must happen when the conflict is resolved.

- `backend/dashboard/cashier/cashier_routes.py` — `get_products()` (line 188) calls `db.worksheet('Products').get_all_records()` with no cache. `complete_sale()` (line 265) does the same for `Money Accounts`. Both cashier_routes.py imports of admin_dashboard modules use inline `sys.path.insert` inside each function — follow the same pattern for cache import.

- `backend/api/api_server.py` `nfc_pay()` (inside merge conflict block, line 786) — calls `invalidate_cached("transactions_all")` after a successful transaction write. This is the existing pattern to follow for `process_cashier_transaction()`.

- `tests/test_fraud_api.py` — 33-test canonical mock pattern to follow for S04; not directly relevant to S02 but confirms test infra exists.

## Constraints

- **Two apps, two separate processes**: admin_dashboard.py (port 5000) and api_server.py (port 5001) each load `cache.py` into their own process. The module-level singleton means **cache invalidation in one app does not affect the other**. A cashier sale via the dashboard does NOT invalidate the API server's cache. This is by design (D014) — the 30s TTL handles staleness across process boundaries.

- **Balance reads in payment flows must NOT be cached**: `complete_sale()` and `process_cashier_transaction()` read Money Accounts to check the current balance before deducting. These reads must hit Sheets directly — a stale cached balance could allow overdraft. Only the reporting/display endpoints (student list, product list, transaction history display) should be cached.

- **Cache keys must be consistent across both apps**: Use `"products_all"`, `"users_all"`, `"money_accounts_all"`, `"transactions_all"` as the canonical key names. The existing NFC code in api_server.py already uses `"users_all"` and `"virtual_cards_all"` — maintain these.

- **cashier_routes.py imports cache via sys.path**: The file is at `backend/dashboard/cashier/cashier_routes.py`; to reach `backend/cache.py`, it needs `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))`. Do this at module level inside a try/except (same pattern as admin_dashboard.py line 28–47).

- **api_server.py is at `backend/api/api_server.py`**: To reach `backend/cache.py`, it needs `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))`.

- **PythonAnywhere quota**: 60 req/min per service account. At 5 hot endpoints × potentially 10–15 req/min each at lunch = up to 75 raw Sheets calls/min without cache. With 30s TTL, at most 2 Sheets calls/min per endpoint = 10 calls/min for all five hot endpoints. This is the whole point.

## Common Pitfalls

- **Caching the payment balance read**: Do NOT cache the Money Accounts read inside the payment deduction logic in `complete_sale()` or `process_cashier_transaction()`. Only cache reads for *display* purposes (student list page, product grid, transaction history display). The balance check before deduction must always read fresh from Sheets.

- **Wrong invalidate_pattern argument**: `invalidate_pattern("money_accounts")` clears keys containing the substring `"money_accounts"`. If you use `"money"` as the pattern it would also clear unrelated keys (unlikely but possible if a future key has "money" in it). Use the full canonical substring: `"money_accounts"`, `"transactions"`, `"products"`, `"users"`.

- **Merge conflict resolution order**: The conflict in api_server.py (lines 484–848) spans the entire NFC section. The correct resolution keeps: (a) the one-liner exception handler from HEAD (or either — they only differ in quote style), AND (b) all NFC endpoint code from gsd/M001/S02. Missing any NFC endpoint will break the virtual card payment flow.

- **cashier_routes.py conflict content**: The first conflict (lines 427–474) is between HEAD (simple purchase SMS only) and gsd/M001/S02 (purchase SMS + low-balance SMS). The correct resolution keeps both: first send low-balance SMS if applicable, then send purchase SMS. The second conflict (lines 484–497) is HEAD (FCM push to student) vs gsd/M001/S02 (empty — no FCM). Keep the HEAD version (FCM push) as it was implemented in M001/S05.

- **`invalidate_cached` vs `invalidate_pattern`**: cache.py exports both. `invalidate_cached(key)` removes one exact key. `invalidate_pattern(pattern)` removes all keys matching a substring. For mutation invalidation, prefer `invalidate_pattern` because the cache key for students list may accumulate with different argument fingerprints if the caching is ever parameterized. Using `invalidate_pattern("users")` is safer than hoping `invalidate_cached("users_all")` hits every key.

- **`get_cached()` returns None on miss, not raising**: The check pattern is always `val = get_cached(key); if val is None: val = fetch(); set_cached(key, val, ttl=30)`. Don't use `if not val` — an empty list `[]` is falsy and would cause an infinite re-fetch loop.

- **The `_sheets_cache` dict in admin_dashboard.py**: Leave it alone. It's used by `get_cached_sheet_data()` which is called in at least one place. Mixing two cache layers is messy but removing `_sheets_cache` is out of scope for S02.

## Open Risks

- **S01 missed two merge conflicts** — `backend/api/api_server.py` and `backend/dashboard/cashier/cashier_routes.py` both have unresolved conflict markers. Python raises `SyntaxError` on any import of these files. If any test or startup script imports them, it will fail. These must be fixed first in S02 before any cache wiring can be verified or tested.

- **api_server.py NFC code uses undefined names inside conflict block** — `nfc_service`, `_card_locks`, `_card_locks_lock`, `threading`, `uuid` are referenced inside the gsd/M001/S02 conflict block but their imports/definitions are not visible in the file before the conflict starts. These must be defined/imported somewhere. Check git history or the gsd/M001/S02 branch for the original module-level setup that was lost when the conflict was left unresolved. This is the highest-risk item in S02.

- **Cache key collisions between admin_dashboard.py and api_server.py** — both apps use `"users_all"` as the key for Users sheet data. Since they're separate processes with independent caches, this is not a collision risk. But it does mean a Sheets write from the API server (e.g., FCM token update) won't invalidate the admin dashboard's users cache. Acceptable per D014.

- **Analytics summary caching correctness** — `/api/analytics/summary` at line 494 accepts no query parameters, so a fixed key `"analytics_summary"` with 30s TTL is safe. But if future query parameters are added (date filter, etc.), the key must be parameterized. Flag this in the implementation comment.

- **`stats` endpoint (`/api/stats`) has `today_transactions` computed from Transactions Log** — caching the raw transactions list and then filtering locally works, but the `today` variable is computed inside the handler. As long as the cache TTL (30s) is short enough, this is fine — 30s stale count is acceptable for a dashboard stat.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Flask | (built-in) | n/a |
| gspread | (well-known) | n/a |
| Python threading/cache | (stdlib) | n/a |

No specialized external skills needed — this is pure Python wiring work.

## Sources

- `backend/cache.py` lines 1–255 — full cache implementation with all public functions
- `backend/dashboard/admin_dashboard.py` lines 29, 111, 153–186, 315–344, 462–476, 716–780, 880–1022, 1023–1075, 494–516, 2178–2265 — import, parallel cache, all hot endpoints and mutations
- `backend/dashboard/cashier/cashier_routes.py` lines 188–214, 265–512 — products endpoint and complete_sale with conflict markers
- `backend/api/api_server.py` lines 152–160, 243–309, 310–372, 484–848, 852–913, 970–1090 — hardcoded health, uncached profile/balance, merge conflict with NFC+cache, products, cashier transaction
- `backend/api/api_server.py` grep for `get_cached|set_cached|invalidate_cached` — confirms existing cache calls are inside the conflict block at lines 516, 519, 530, 531, 681, 684, 754, 757, 786, 796, 799
- `backend/dashboard/admin_dashboard.py` line 462 — `GET /api/cache/stats` confirmed wired to `get_cache_stats()` already
