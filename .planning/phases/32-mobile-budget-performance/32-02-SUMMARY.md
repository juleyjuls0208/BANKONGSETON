# Phase 32-02 Summary — iOS Budget Performance

## What Was Done

Three tasks completed across four iOS source files to eliminate redundant `DateFormatter` allocations and replace the 200-transaction download with the new `/api/budget-summary` endpoint.

## Files Modified

| File | Change |
|------|--------|
| `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift` | Static `monthPrefixFormatter`; rewrote `load()` to use `fetchBudgetSummary()` |
| `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift` | 3 static formatters replacing 4 inline allocations |
| `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift` | Added `budgetSummary = "/api/budget-summary"` |
| `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift` | Added `BudgetSummaryResponse` struct + `fetchBudgetSummary()` method |

## Task-by-Task Details

### Task 1 — Static DateFormatters

**BudgetViewModel.swift:** Replaced inline `DateFormatter()` in `currentMonthPrefix()` with a `private static let monthPrefixFormatter` computed once at class load. `currentMonthPrefix()` now calls the static instance.

**ReceiptView.swift:** Replaced 4 inline `DateFormatter` allocations (2 in `formattedDate`, 2 in `formattedTime`) with 3 static formatters: `timestampParser` (`"yyyy-MM-dd HH:mm:ss"`), `dateDisplay` (`"MMM d, yyyy"`), `timeDisplay` (`"h:mm a"`). The display format strings are preserved exactly — no functional change, only allocation eliminated.

### Task 2 — Network Layer

`APIEndpoints.swift`: Added `static let budgetSummary = "/api/budget-summary"`.

`APIClient.swift`: Added `fetchBudgetSummary() async throws -> BudgetSummaryResponse` following the existing `async throws -> T` pattern via `perform<T>()`. Added `BudgetSummaryResponse: Decodable` struct with `spent`, `limit`, `percent`, `currency` fields after the closing brace.

### Task 3 — BudgetViewModel.load() Rewrite

Replaced the old `load()` body that called `getTransactions(limit: 200, offset: 0)` and filtered client-side with:

```swift
async let budgetResp = apiClient.getBudget()
async let summaryResp = apiClient.fetchBudgetSummary()
let (budget, summary) = try await (budgetResp, summaryResp)
limit = budget.monthlyLimit
spent = summary.spent
```

Both calls fire concurrently via `async let`. Transaction downloading and client-side filtering removed entirely. `checkAlerts()` call preserved.

## Deviations from Plan

| Plan said | Actual implementation | Reason |
|-----------|----------------------|--------|
| `Result<BudgetSummaryResponse, APIError>` return type | `async throws -> BudgetSummaryResponse` | Matches APIClient's actual `async throws` pattern |
| `switch result { case .success: ... }` in load() | `try await (budgetResp, summaryResp)` with catch | Matches actual BudgetViewModel error handling style |
| `monthlySpend` property name | `spent` property name | Matches actual BudgetViewModel properties |

## Outcome

✅ `DateFormatter` objects in `BudgetViewModel` and `ReceiptView` are now allocated once (static), not per-call.  
✅ Budget screen no longer downloads 200 transactions — `load()` makes 2 concurrent lightweight API calls.  
✅ `spent` value is authoritative from the server, consistent with Android.
