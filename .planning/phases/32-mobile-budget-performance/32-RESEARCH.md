# Phase 32: Mobile Budget Performance - Research

**Researched:** 2026-03-10
**Domain:** iOS Swift performance, Android Kotlin/RecyclerView, Python Flask backend
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Backend
- New endpoint: `GET /api/budget-summary` → `{ "monthly_spend": 1234.56 }`
- Response value is current calendar month only, never null (always 0.0 if no transactions)
- Reuse existing `"transactions_all"` cache key (30-second TTL already in place)
- Filter cached transactions to current month server-side, sum the `amount` field
- No new cache key; no new cache TTL

#### iOS
- Extract `DateFormatter` to `private static let` on **both** `BudgetViewModel` and `ReceiptView`
- Add new `fetchBudgetSummary()` async method on `BudgetViewModel`
- Follow Phase 30 `.unauthorized` → `authManager.handleUnauthorized()` error pattern
- `BudgetViewModel.load()` must call `fetchBudgetSummary()` instead of filtering 200 transactions locally

#### Android
- DiffUtil with composite key: `timestamp + type + amount` for `areItemsTheSame()`
- `areContentsTheSame()` uses `data class` structural equality (`==`)
- `calculateDiff()` runs on `Dispatchers.Default`; result applied on main thread
- New `fetchBudgetSummary()` in `HomeActivity` replaces the transaction-fetch-based spend calculation
- Keep existing transaction list fetch if it serves other UI purposes

### Claude's Discretion
- Exact coroutine scope for Android `fetchBudgetSummary()` (lifecycleScope recommended)
- Whether to use `suspend fun` or callback style for Android API call (suspend recommended for consistency)
- Exact placement of `static let` formatters within each Swift file (top of class body)
- Naming of `BudgetSummaryResponse` data class fields (must match `@SerializedName("monthly_spend")`)

### Deferred Ideas (OUT OF SCOPE)
- Full budget analytics / multi-month history
- Push notifications for budget threshold
- Android transaction pagination / infinite scroll
- iOS transaction pagination beyond 200-item limit
- Any UI redesign or new screens
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REQ-PERF-06 | `GET /api/budget-summary` returns `{ "monthly_spend": <float> }` for current month | Backend cache pattern confirmed at lines 555–558 of `api_server.py`; `get_philippines_time()` available for month boundary |
| REQ-PERF-07 | iOS `DateFormatter` extracted to `private static let` on `BudgetViewModel` and `ReceiptView` | Bug confirmed: 1 allocation per `currentMonthPrefix()` call in `BudgetViewModel` (called twice per `load()`); 4 allocations per render in `ReceiptView` |
| REQ-PERF-08 | iOS `BudgetViewModel` calls `fetchBudgetSummary()` for monthly spend instead of local filtering | `load()` currently calls `getTransactions(limit: 200)` and filters locally; new method follows `getBudget()` pattern in `APIClient.swift` |
| REQ-PERF-09 | Android `TransactionsAdapter` uses DiffUtil instead of `notifyDataSetChanged()` | `setTransactions()` at line 17–21 confirmed using `notifyDataSetChanged()`; `Transaction` confirmed as `data class` |
| REQ-PERF-10 | Android `HomeActivity` calls `fetchBudgetSummary()` for monthly spend | `loadAndDisplayBudget()` confirmed at lines 223–253; `updateBudgetUI()` signature change required |
</phase_requirements>

---

## Summary

Phase 32 is a targeted performance improvement phase spanning backend, iOS, and Android. All three platforms have **well-understood, isolated bugs** — no architectural changes are needed. The work is surgical: fix a DateFormatter allocation regression on iOS, replace a full-list-scan with a dedicated API endpoint, and replace `notifyDataSetChanged()` with DiffUtil on Android.

The backend work is minimal: one new Flask route that reuses the existing cache and performs a server-side month filter. The iOS work has two independent sub-tasks (formatter extraction and new API call). The Android work also has two independent sub-tasks (DiffUtil and new API call). All five tasks are leaf-level changes with no cross-dependency.

All prerequisite phases are confirmed complete (Phase 28 cache infrastructure, Phase 29 Android P1, Phase 30 iOS P1). The codebase patterns are well-established and the changes closely mirror existing code.

**Primary recommendation:** Implement in this order — backend first (unblocks iOS/Android API testing), then iOS, then Android. Each task is independently verifiable.

---

## Standard Stack

### Core
| Library/Tool | Version | Purpose | Why Standard |
|---|---|---|---|
| Flask (Python) | existing | HTTP routing for backend endpoint | Already in use; no new dependency |
| Swift async/await | Swift 5.5+ / iOS 15+ | `fetchBudgetSummary()` async method | Already used in `APIClient.swift` and `BudgetViewModel` |
| Kotlin Coroutines | existing | `Dispatchers.Default` for DiffUtil calc | Already used in project |
| RecyclerView DiffUtil | AndroidX | Efficient list diff | Standard AndroidX; replaces `notifyDataSetChanged()` |
| Retrofit | existing | Android HTTP client | Already used in `BangkoApiService` |
| Gson / `@SerializedName` | existing | JSON deserialization | Already used for all Android models |

### Supporting
| Library | Purpose | When to Use |
|---|---|---|
| `get_philippines_time()` | Server-side current-month boundary | Already defined in `api_server.py`; use for month prefix filter |
| `DateFormatter` (`private static let`) | iOS date parsing/formatting | Replace ALL inline `DateFormatter()` allocations |
| `AsyncListDiffer` (alternative) | Alternative to `DiffUtil.calculateDiff()` | Not needed; manual `DiffUtil` is sufficient and consistent with project style |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|---|---|---|
| Reusing `"transactions_all"` cache | New `"budget_summary"` cache key | New key wastes memory and can desync; user locked this to reuse |
| `notifyDataSetChanged()` | `ListAdapter` (wraps DiffUtil) | `ListAdapter` requires larger refactor; DiffUtil directly is sufficient |
| Composite key DiffUtil | Server-assigned transaction ID | No server ID on `Transaction`; composite key is correct here |

**Installation:** No new dependencies required. All changes use existing libraries.

---

## Architecture Patterns

### Recommended Project Structure
No structural changes. All edits are within existing files:
```
backend/api/
└── api_server.py                          # Add /api/budget-summary route

mobile/ios/BankongSetonStudent/
├── ViewModels/BudgetViewModel.swift        # Static formatter + fetchBudgetSummary()
├── Views/Receipt/ReceiptView.swift         # Static formatters (4 allocations → 4 statics)
├── Core/Network/APIClient.swift            # Add fetchBudgetSummary() method
└── Core/Network/APIEndpoints.swift         # Add budgetSummary constant

mobile/student_app_v2/app/src/main/java/com/bankongseton/student/
├── TransactionsAdapter.kt                  # DiffUtil replaces notifyDataSetChanged()
├── HomeActivity.kt                         # fetchBudgetSummary() + updateBudgetUI() sig change
├── ApiClient.kt                            # New @GET("budget-summary") suspend fun
└── Models.kt                               # New BudgetSummaryResponse data class
```

### Pattern 1: Backend Route with Cache Reuse
**What:** New Flask route reads from `"transactions_all"` cache, filters to current month, sums amounts.
**When to use:** Any endpoint that can derive its value from an existing cached collection.

```python
# Source: api_server.py lines 555-558 (existing pattern)
@app.route('/api/budget-summary', methods=['GET'])
def get_budget_summary():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    student_id = validate_session(token)
    if not student_id:
        return jsonify({'error': 'Unauthorized'}), 401

    cached = get_cached("transactions_all")
    if cached is None:
        # Fallback: fetch from DB
        transactions = fetch_transactions_from_db(student_id)
        set_cached("transactions_all", transactions, ttl=30)
    else:
        transactions = cached

    # Filter to current calendar month (Philippines time)
    now = get_philippines_time()
    month_prefix = now.strftime('%Y-%m')
    monthly = [t for t in transactions if t.get('date', '').startswith(month_prefix)]
    monthly_spend = sum(float(t.get('amount', 0)) for t in monthly)

    return jsonify({'monthly_spend': round(monthly_spend, 2)})
```

**Important:** `"transactions_all"` is already filtered by `student_id` at cache population time (confirm this assumption in code — see Open Questions).

### Pattern 2: iOS `private static let` DateFormatter
**What:** Move `DateFormatter` creation out of computed properties into class-level static constants.
**When to use:** Any time a `DateFormatter` is used in a computed property, `ForEach`, or frequently-called method.

```swift
// ❌ Before (BudgetViewModel.swift lines 49-52) — allocates every call
private func currentMonthPrefix() -> String {
    let formatter = DateFormatter()
    formatter.dateFormat = "yyyy-MM"
    return formatter.string(from: Date())
}

// ✅ After — allocated once per process lifetime
private static let monthFormatter: DateFormatter = {
    let f = DateFormatter()
    f.dateFormat = "yyyy-MM"
    return f
}()

private func currentMonthPrefix() -> String {
    return Self.monthFormatter.string(from: Date())
}
```

```swift
// ❌ Before (ReceiptView.swift lines 13-21) — 2 allocations per render
var formattedDate: String {
    let parser = DateFormatter()
    parser.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
    let display = DateFormatter()
    display.dateFormat = "MMM d, yyyy"
    ...
}

// ✅ After — allocated once
private static let isoParser: DateFormatter = { ... }()
private static let dateDisplay: DateFormatter = { ... }()
private static let timeDisplay: DateFormatter = { ... }()
// etc.
```

### Pattern 3: iOS `fetchBudgetSummary()` (follows existing `getBudget()` pattern)
**What:** New async method on `BudgetViewModel` that calls the backend and handles `.unauthorized`.
**When to use:** Any new API fetch in `BudgetViewModel`.

```swift
// Source: follows getBudget() pattern in APIClient.swift lines 99-102
// In APIEndpoints.swift:
static let budgetSummary = "/budget-summary"

// In APIClient.swift:
func fetchBudgetSummary() async throws -> BudgetSummaryResponse {
    let request = APIRequest(path: APIEndpoints.budgetSummary, method: "GET")
    return try await perform(request)
}

// In BudgetViewModel.swift:
func fetchBudgetSummary() async {
    do {
        let summary = try await apiClient.fetchBudgetSummary()
        await MainActor.run { self.spent = summary.monthlySend }
    } catch APIError.unauthorized {
        authManager.handleUnauthorized()
    } catch {
        // handle gracefully
    }
}
```

### Pattern 4: Android DiffUtil with Composite Key
**What:** Replace `notifyDataSetChanged()` with `DiffUtil.calculateDiff()` on `Dispatchers.Default`.
**When to use:** Any `RecyclerView.Adapter` whose data changes via a full-list replacement.

```kotlin
// Source: Standard AndroidX DiffUtil pattern
class TransactionDiffCallback(
    private val oldList: List<Transaction>,
    private val newList: List<Transaction>
) : DiffUtil.Callback() {
    override fun getOldListSize() = oldList.size
    override fun getNewListSize() = newList.size

    override fun areItemsTheSame(oldItemPosition: Int, newItemPosition: Int): Boolean {
        val old = oldList[oldItemPosition]
        val new = newList[newItemPosition]
        // Composite key: no server-assigned ID
        return old.timestamp == new.timestamp &&
               old.type == new.type &&
               old.amount == new.amount
    }

    override fun areContentsTheSame(oldItemPosition: Int, newItemPosition: Int): Boolean {
        // data class == compares all fields
        return oldList[oldItemPosition] == newList[newItemPosition]
    }
}

// In TransactionsAdapter.kt — replaces setTransactions():
fun setTransactions(newTransactions: List<Transaction>) {
    val scope = CoroutineScope(Dispatchers.Default)
    scope.launch {
        val diffResult = DiffUtil.calculateDiff(
            TransactionDiffCallback(transactions, newTransactions)
        )
        withContext(Dispatchers.Main) {
            transactions = newTransactions
            diffResult.dispatchUpdatesTo(this@TransactionsAdapter)
        }
    }
}
```

**Note:** The coroutine scope for DiffUtil should be the adapter's own scope or passed in; do not leak. Use `lifecycleScope` from the calling Activity if cleaner.

### Pattern 5: Android `fetchBudgetSummary()` in `HomeActivity`
**What:** Suspend function call using `lifecycleScope`, replacing the Retrofit callback inside `loadAndDisplayBudget()`.

```kotlin
// In Models.kt:
data class BudgetSummaryResponse(
    @SerializedName("monthly_spend") val monthlySpend: Double
)

// In ApiClient.kt (BangkoApiService interface):
@GET("budget-summary")
suspend fun getBudgetSummary(
    @Header("Authorization") token: String
): Response<BudgetSummaryResponse>

// In HomeActivity.kt:
private fun fetchBudgetSummary() {
    lifecycleScope.launch {
        try {
            val token = "Bearer ${sessionManager.getToken()}"
            val response = apiService.getBudgetSummary(token)
            if (response.isSuccessful) {
                val spend = response.body()?.monthlySpend ?: 0.0
                updateBudgetUI(spend)  // signature changes to accept Double
            }
        } catch (e: Exception) {
            // handle error
        }
    }
}

// updateBudgetUI signature change:
private fun updateBudgetUI(spent: Double) { ... }
```

### Anti-Patterns to Avoid
- **Inline `DateFormatter` in computed properties:** Creates a new object on every property access. `DateFormatter` is expensive to initialize.
- **`notifyDataSetChanged()` for partial updates:** Redraws every visible item, causes flicker, and skips RecyclerView's item animation system.
- **New cache key for derived data:** Creates cache staleness risk when the source key is invalidated but the derived key is not.
- **Filtering transactions client-side after fetching 200:** Wastes bandwidth and CPU; server should aggregate.
- **Running DiffUtil on main thread:** `calculateDiff()` is O(N²) in worst case; must run on background thread.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| List diffing | Custom change detection / index comparison | `DiffUtil.Callback` (AndroidX) | Handles moves, inserts, deletes; battle-tested Myers diff algorithm |
| DateFormatter caching | Custom formatter pool or cache dict | `private static let` (Swift class property) | Swift class properties are initialized once; zero boilerplate |
| Month boundary calculation | Manual string slicing on timestamps | `get_philippines_time().strftime('%Y-%m')` | Already handles timezone; reuses project's established utility |
| JSON deserialization | Manual key parsing | `@SerializedName` + Gson (Android) / `Codable` (iOS) | Type-safe, handles missing keys, follows existing project pattern |

---

## Common Pitfalls

### Pitfall 1: Cache Populated Per-Student vs. Global
**What goes wrong:** The `"transactions_all"` cache may be keyed globally, but transactions belong to a specific student. If `get_cached("transactions_all")` returns another student's transactions, the budget summary will be wrong.
**Why it happens:** Cache key doesn't include `student_id`.
**How to avoid:** Verify actual cache population in `api_server.py`. If keyed globally, either add `student_id` to cache key or always filter by `student_id` before summing. (See Open Questions #1.)
**Warning signs:** Budget summary shows wrong amount; changes with login/logout cycle.

### Pitfall 2: DiffUtil Coroutine Scope Leak
**What goes wrong:** Using `CoroutineScope(Dispatchers.Default)` inside `setTransactions()` creates an unmanaged scope that leaks if the Activity is destroyed.
**Why it happens:** The coroutine is not tied to any lifecycle.
**How to avoid:** Pass `lifecycleScope` from `HomeActivity` into the adapter, or have `HomeActivity` call `calculateDiff` itself before calling `setTransactions(diffResult)`.
**Warning signs:** Memory leaks in LeakCanary; crash after back navigation.

### Pitfall 3: `areItemsTheSame` False Positives with Composite Key
**What goes wrong:** Two different transactions on the same timestamp with same type and amount are treated as "same item" — one gets silently dropped.
**Why it happens:** Composite key `timestamp + type + amount` is not guaranteed unique.
**How to avoid:** Accept this known limitation (matches user's locked decision). For the typical student transaction set, collisions are extremely unlikely. If collisions become a problem, request a server-assigned ID in a future phase.
**Warning signs:** Transaction count in UI doesn't match server count.

### Pitfall 4: iOS `MainActor` Missing on `@Published` Updates
**What goes wrong:** Setting `self.spent` from inside a `Task {}` without `MainActor.run {}` triggers a purple runtime warning (and potential crash on iOS 17+).
**Why it happens:** `@Published` properties on `ObservableObject` must be mutated on the main thread.
**How to avoid:** Always wrap `@Published` mutations in `await MainActor.run { }` or annotate the `ViewModel` with `@MainActor`.
**Warning signs:** Purple runtime warning: "Publishing changes from background threads is not allowed".

### Pitfall 5: `ReceiptView` Static Formatter Locale
**What goes wrong:** `DateFormatter` without explicit `locale` uses device locale. If the device is set to a non-Gregorian calendar, dates parse incorrectly.
**Why it happens:** Implicit locale inheritance.
**How to avoid:** Set `formatter.locale = Locale(identifier: "en_US_POSIX")` on all parsers that use ISO 8601 input. Display formatters may use device locale.
**Warning signs:** Date parsing returns `nil` on non-English devices.

---

## Code Examples

### Backend: Current Cache Pattern (api_server.py)
```python
# Source: api_server.py lines 555-558 — existing get_transactions endpoint
cached = get_cached("transactions_all")
if cached:
    transactions = cached
else:
    transactions = db_fetch_transactions(student_id)
    set_cached("transactions_all", transactions, ttl=30)
```

### iOS: Existing getBudget() Pattern (APIClient.swift ~line 99)
```swift
// Source: APIClient.swift — template for fetchBudgetSummary()
func getBudget() async throws -> BudgetResponse {
    let request = APIRequest(path: APIEndpoints.budget, method: "GET")
    return try await perform(request)
}
```

### iOS: Existing .unauthorized Handling (Phase 30 pattern)
```swift
// Source: BudgetViewModel.swift — error handling pattern
} catch APIError.unauthorized {
    authManager.handleUnauthorized()
}
```

### Android: Existing Retrofit Suspend Pattern (ApiClient.kt)
```kotlin
// Source: ApiClient.kt — template for getBudgetSummary()
@GET("transactions")
suspend fun getTransactions(
    @Header("Authorization") token: String,
    @Query("limit") limit: Int = 20
): Response<TransactionsResponse>
```

### Android: Transaction data class (Models.kt)
```kotlin
// Source: Models.kt — confirms structural equality works for DiffUtil
data class Transaction(
    val timestamp: String,
    val type: String,
    val amount: Double,
    // ... other fields
)
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|---|---|---|
| `notifyDataSetChanged()` | `DiffUtil` / `ListAdapter` | Smooth animations, no full redraw |
| Inline `DateFormatter` | `static let` / cached instance | 10–100× fewer allocations in hot paths |
| Client-side aggregation | Server-side aggregate endpoint | Reduced payload, reduced client CPU |
| Direct Retrofit callback in Activity | `lifecycleScope.launch` + suspend | Lifecycle-safe, no manual cancel needed |

**Deprecated/outdated:**
- `notifyDataSetChanged()`: Still works but deprecated in spirit; DiffUtil is the standard since AndroidX RecyclerView 1.0
- Inline `DateFormatter()`: Never correct in hot paths; Swift docs explicitly warn about `DateFormatter` being expensive to create

---

## Open Questions

1. **Is `"transactions_all"` cache keyed per-student or globally?**
   - What we know: The cache key string is `"transactions_all"` (literal, confirmed in `api_server.py`)
   - What's unclear: Whether `get_cached()` / `set_cached()` wrap the key with a student ID prefix internally, or whether the key is used as-is across all students
   - Recommendation: **Check `cache_utils.py` or wherever `get_cached`/`set_cached` are defined before implementing the backend route.** If the cache is global, the budget summary will need to filter by `student_id` after retrieval — or use a per-student key like `f"transactions_all_{student_id}"`.

2. **Does `HomeActivity.loadAndDisplayBudget()` also serve the transaction _list_ UI, or only the budget spend calculation?**
   - What we know: The method calls `getTransactions()` (limit=20) and uses the result for both spend calculation AND presumably populates `TransactionsAdapter`
   - What's unclear: Whether removing the transaction fetch from `loadAndDisplayBudget()` will break the displayed transaction list
   - Recommendation: **Read `loadAndDisplayBudget()` lines 223–283 in full.** If it feeds `TransactionsAdapter`, keep the `getTransactions()` call but remove the spend-calculation logic from it. The user constraint says "keep existing transaction list fetch if it serves other UI purposes."

3. **What is `update_budget_ui`'s current signature and all call sites?**
   - What we know: It currently accepts `List<Transaction>` and computes `spent` internally
   - What's unclear: Whether there are other call sites beyond `loadAndDisplayBudget()`
   - Recommendation: Grep for `updateBudgetUI` before changing the signature to avoid breaking other callers.

---

## Sources

### Primary (HIGH confidence)
- Direct source code reads:
  - `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift` — formatter bug confirmed lines 49–52
  - `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift` — 4 inline allocations confirmed lines 13–31
  - `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift` — fetch pattern confirmed
  - `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/TransactionsAdapter.kt` — `notifyDataSetChanged()` confirmed line 17–21
  - `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt` — `loadAndDisplayBudget()` confirmed lines 223–253
  - `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt` — `Transaction` as `data class` confirmed
  - `backend/api/api_server.py` — cache pattern confirmed lines 555–558
- `.planning/phases/32-mobile-budget-performance/32-CONTEXT.md` — locked decisions

### Secondary (MEDIUM confidence)
- AndroidX RecyclerView DiffUtil documentation (standard API, stable since 1.0)
- Swift `DateFormatter` performance characteristics (Apple developer docs — well-established guidance)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in the project, no new dependencies
- Architecture: HIGH — all patterns directly verified from source code
- Pitfalls: HIGH (Pitfall 1 & 2) / MEDIUM (Pitfall 3–5) — confirmed from code, some are general best-practice
- Open Questions: require code verification before implementation begins

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (stable codebase, no fast-moving dependencies)
