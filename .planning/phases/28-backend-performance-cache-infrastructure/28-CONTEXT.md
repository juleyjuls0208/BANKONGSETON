# Phase 28: Backend Performance — Cache Infrastructure - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Reduce Google Sheets API call volume on the NFC payment path and cashier transaction path by applying TTL caching to currently-uncached sheet reads. Target: NFC pay path drops from 7–9 sequential Sheets API calls to ≤3; cashier transaction reads the Users sheet once (not thrice); per-user transaction query no longer does an all-users fetch + Python filter on every request.

Does NOT include: caching Money Accounts (balance) reads — these must stay fresh for correctness.

</domain>

<decisions>
## Implementation Decisions

### VirtualCards Cache

- **TTL:** 30s — same as `users_all`, consistent with established pattern
- **Key:** `"virtual_cards_all"` — single flat key for the entire sheet (same pattern as `"users_all"`)
- **Invalidation:** Yes — call `invalidate_cached("virtual_cards_all")` after `nfc_register()` writes a new card
- **Location:** Cache at the call-site in `api_server.py` (before/after calling `nfc_payments.get_virtual_card_by_token()`). Keeps `nfc_payments.py` free of cache dependencies.

### Money Accounts (Balance) Reads

- **No caching** — balance must always be read fresh; stale balance could cause incorrect low-balance rejections or wrong deductions
- **Deduplication within request:** NFC pay currently reads Money Accounts multiple times in one request. Fetch once at the start of `nfc_pay()`, reuse the result for both the balance check and the row update. No cache risk — just eliminates redundant within-request API calls.

### Per-User Transaction Query

- **Approach:** Cache the full transactions sheet under key `"transactions_all"` with 30s TTL. First request per TTL window pays the API cost; all subsequent requests hit cache. Python-side filter on the cached result.
- **Invalidation:** Yes — call `invalidate_cached("transactions_all")` after `append_row()` in the NFC pay handler and any other location that writes a transaction row.
- Satisfies REQ-PERF-04 intent: no all-users-fetch + Python filter on every API call.

### Cashier Users-Sheet Deduplication

- **Approach:** Import `get_cached` / `set_cached` from `backend/cache.py` into `cashier_routes.py`. Reuse the existing `"users_all"` key and 30s TTL — same key already populated by `api_server.py`.
- **Shared instance:** `cache.py` exports a singleton `_global_cache`; both modules share the same in-process cache, so a warm `"users_all"` from an API request is immediately available in `cashier_routes.py` without an extra fetch.
- No new cache key needed; no separate TTL to maintain.

### Claude's Discretion

- Exact placement of `invalidate_cached` calls within `nfc_pay()` (before vs. after response construction)
- Whether to extract the within-request Money Accounts deduplication into a local variable or inline it
- Any minor refactoring needed to thread the single Money Accounts fetch result through the NFC pay handler

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `backend/cache.py` — `TTLCache` class, `get_cached(key)`, `set_cached(key, value, ttl)`, `invalidate_cached(key)` convenience functions; `_global_cache` singleton with 30s default TTL. Ready to use — no changes needed to cache.py itself.
- `backend/api/api_server.py` — Already imports and uses `get_cached`/`set_cached` for `"users_all"` (30s TTL) in ~14 places. The invalidation pattern (`invalidate_cached` after writes) is already established in `report_lost_card` and `nfc_register`.

### Established Patterns

- Flat string cache keys (`"users_all"`, `"virtual_cards_all"`, `"transactions_all"`)
- 30s TTL uniform across all sheet caches
- `invalidate_cached(key)` called immediately after any write that mutates cached data
- Cache wrapping is done at the call-site in `api_server.py`, not inside service modules

### Integration Points

- `backend/api/api_server.py` → `nfc_pay()` (line ~1025): wrap `get_virtual_card_by_token()` call with `"virtual_cards_all"` cache; deduplicate Money Accounts reads; add `invalidate_cached("transactions_all")` after `append_row()`
- `backend/api/api_server.py` → `get_transactions()` (line ~485): wrap `trans_sheet.get_all_records()` with `"transactions_all"` cache
- `backend/api/api_server.py` → `nfc_register()`: add `invalidate_cached("virtual_cards_all")` after writing new VirtualCard
- `backend/dashboard/cashier/cashier_routes.py` → cashier transaction handler (lines ~442, ~499): import `get_cached`/`set_cached` from `cache.py`; replace two independent `db.worksheet("Users").get_all_records()` calls with `"users_all"` cache reads

</code_context>

<specifics>
## Specific Ideas

- The `"users_all"` cache key is shared between `api_server.py` and `cashier_routes.py` — this is intentional. A warm cache from any API request benefits cashier reads automatically.
- Money Accounts deduplication is a within-request optimization only (no TTL cache). The single fetched result should be stored in a local variable at the top of `nfc_pay()` and passed to wherever balance check and row lookup currently re-fetch it.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 28-backend-performance-cache-infrastructure*
*Context gathered: 2026-03-09*
