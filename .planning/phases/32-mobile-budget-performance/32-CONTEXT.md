# Phase 32: Mobile Budget Performance - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Add `GET /api/budget-summary` backend endpoint returning pre-aggregated monthly spend.
Switch iOS `BudgetViewModel` and Android `HomeActivity` from fetching 200 transactions to calling the new endpoint.
Cache the iOS `DateFormatter` in `BudgetViewModel` and `ReceiptView` as static properties.
Replace `notifyDataSetChanged()` in Android `TransactionsAdapter` with DiffUtil.

Requirements: REQ-PERF-06 through REQ-PERF-10.
Depends on: Phase 28 (cache infrastructure), Phase 29 (Android P1 bugs), Phase 30 (iOS P1 bugs).

</domain>

<decisions>
## Implementation Decisions

### Budget summary endpoint shape
- Route: `GET /api/budget-summary` (student-authenticated)
- Always computes current calendar month — no month parameter
- Response: `{ "monthly_spend": 1234.56 }` (snake_case, matches existing API convention)
- Zero transactions → return `{ "monthly_spend": 0.0 }` (valid, never null or 404)

### Cache strategy
- Reuse the Phase 28 `"transactions_all"` cache key (30s TTL) — no new cache key
- On cache hit: filter cached transactions to current month, sum amounts
- On cache miss: fetch all transactions from DB, write to `"transactions_all"`, then compute spend
- Invalidation: follow Phase 28 pattern — call `invalidate_cached("transactions_all")` whenever a transaction is written (existing write paths already do this)
- Mobile refresh: fetch on screen load only — no polling, no auto-refresh

### iOS: DateFormatter caching
- `BudgetViewModel.currentMonthPrefix()`: extract inline `DateFormatter` to `private static let` on `BudgetViewModel`
- `ReceiptView`: extract inline `DateFormatter` to `private static let` on `ReceiptView` (or its ViewModel)
- Keep exact same formatter configuration as the current inline version — no behavior change, just static

### iOS: BudgetViewModel fetch refactor
- Add a new `fetchBudgetSummary()` async method on `BudgetViewModel`
- Calls the new `GET /api/budget-summary` endpoint instead of `getTransactions(limit: 200)`
- Follow the Phase 30 `async let` parallel fetch pattern where applicable
- Follow the Phase 30 `.unauthorized` → `authManager.handleUnauthorized()` error handling pattern

### Android: DiffUtil identity
- `areItemsTheSame()`: composite key of `timestamp + type + amount`
- `areContentsTheSame()`: use `data class` structural equality (`==`) across all fields
- `DiffUtil.calculateDiff()` runs on a background thread via Kotlin coroutines (`Dispatchers.Default`), results applied on main thread
- Replace `notifyDataSetChanged()` in `setTransactions()` with DiffUtil dispatch

### Android: HomeActivity budget fetch refactor
- Add a new `fetchBudgetSummary()` call to `GET /api/budget-summary` in `HomeActivity`
- Use the result to update the budget/spend UI instead of computing from 200 transactions
- Keep the existing transaction list fetch if it serves other UI purposes; only swap where spend is sourced

### Claude's Discretion
- Exact coroutine scope and lifecycle handling for DiffUtil background dispatch in `TransactionsAdapter`
- Whether to introduce a `TransactionDiffCallback` inner class or companion object
- Exact property name for the static `DateFormatter` instances
- Error state / loading state UI for the new budget-summary call on both platforms

</decisions>

<specifics>
## Specific Ideas

- Backend endpoint follows exact same JSON casing convention as existing `/api/student/budget` (snake_case)
- DiffUtil composite key mirrors the fact that the API has no server-assigned transaction ID — this is a known model constraint, not a bug to fix in this phase

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `get_cached` / `set_cached` / `invalidate_cached` (backend): ready-to-use — wrap budget-summary computation identically to the Phase 28 transaction cache
- `appendTransactions()` in `TransactionsAdapter`: already uses `notifyItemRangeInserted` — DiffUtil only needs to replace `setTransactions()`
- Phase 30 `async let` parallel pattern in iOS ViewModels: apply to `fetchBudgetSummary()` if called alongside other fetches

### Established Patterns
- Phase 28: flat string cache keys, 30s TTL, invalidation after writes — budget-summary inherits this exactly
- Phase 30: `.unauthorized` error → `authManager.handleUnauthorized()` — iOS budget fetch must follow this
- Existing `/api/student/budget` GET/POST routes: budget-summary is a new sibling route, not a modification of these

### Integration Points
- `backend/api/api_server.py`: add `GET /api/budget-summary` route alongside existing `/api/student/budget` routes
- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift`: new method + static formatter
- `mobile/ios/BankongSetonStudent/Views/Budget/ReceiptView.swift` (or its ViewModel): static formatter
- `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift`: add budget-summary endpoint constant
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`: add `fetchBudgetSummary()` implementation
- `mobile/student_app_v2/.../TransactionsAdapter.kt`: replace `notifyDataSetChanged()` with DiffUtil
- `mobile/student_app_v2/.../HomeActivity.kt`: add budget-summary fetch, stop using transaction list for spend
- `mobile/student_app_v2/.../ApiClient.kt` (Retrofit): add budget-summary endpoint

</code_context>

<deferred>
## Deferred Ideas

- Adding a `month` parameter to budget-summary for historical spend — out of scope, always current month in this phase
- Adding a server-assigned ID to `Transaction` model — out of scope; DiffUtil composite key is the Phase 32 solution
- Polling or push-based budget refresh — out of scope; screen-load fetch only

</deferred>

---

*Phase: 32-mobile-budget-performance*
*Context gathered: 2026-03-10*
