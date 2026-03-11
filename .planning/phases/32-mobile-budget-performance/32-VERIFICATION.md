---
phase: 32-mobile-budget-performance
verified: 2026-03-10T12:00:00Z
status: human_needed
score: 5/5 must-haves verified
re_verification:
  previous_status: gaps_found
  previous_score: 3/5
  gaps_closed:
    - "iOS URL double-prefix fixed: APIEndpoints.budgetSummary = \"/budget-summary\" (was \"/api/budget-summary\")"
    - "iOS BudgetSummaryResponse now decodes monthly_spend -> spent via CodingKeys — no longer returns 0.0"
    - "Android BudgetSummaryResponse now maps @SerializedName(\"monthly_spend\") -> spent — no longer returns 0.0"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Run iOS app on simulator, log in as student with purchase transactions this month, navigate to Budget screen"
    expected: "Non-zero PHP spend amount displayed (not 0.00); no 404 errors on /api/budget-summary in console"
    why_human: "Static analysis confirms wiring is correct; only a live round-trip can confirm network + decoding + UI binding all work together"
  - test: "Run Android app on emulator, log in, view Home screen budget card"
    expected: "Budget card shows non-zero PHP spend amount; no JSON decode errors in Logcat"
    why_human: "Same reason — requires live network + Gson deserialization + UI render to confirm"
  - test: "Android: open Transactions screen with 50+ items, scroll rapidly, trigger a data refresh"
    expected: "No full-list flash/flicker; only changed rows animate"
    why_human: "DiffUtil correctness is a visual/perceptual check that cannot be verified by static analysis"
---

# Phase 32: Mobile Budget Performance — Verification Report

**Phase Goal:** Budget spend calculation no longer requires loading 200 transactions on either mobile platform; a new backend endpoint serves pre-aggregated monthly spend; iOS DateFormatter is not re-allocated on every render.
**Verified:** 2026-03-10
**Status:** `human_needed`
**Re-verification:** Yes — after gap closure (Plan 32-04)

---

## Re-verification Summary

Previous verification (initial) found **3/5 truths verified** with two blocker gaps:
1. iOS URL double-prefix (`/api/api/budget-summary` → 404)
2. Response shape mismatch on both platforms (both clients decoded `spent` as 0.0)

Plan 32-04 closed all gaps. This re-verification confirms **5/5 truths verified**. All automated checks pass; three human tests remain to confirm the live end-to-end round-trips.

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Backend exposes `GET /api/budget-summary` returning pre-aggregated monthly spend | ✓ VERIFIED | `api_server.py` lines 770–831: route exists, uses `get_cached("transactions_all")`, filters `purchase`/`nfc purchase` case-insensitively, returns `{"monthly_spend": <float>}`, checks session with `_check_session()` |
| 2 | iOS `BudgetViewModel.load()` calls the summary endpoint instead of fetching all transactions | ✓ VERIFIED | `BudgetViewModel.swift`: `load()` uses `async let summaryResp = apiClient.fetchBudgetSummary()`; no `getTransactions` call anywhere in the file |
| 3 | iOS `DateFormatter` instances are static (not re-allocated per render) | ✓ VERIFIED | `ReceiptView.swift`: `static let timestampParser`, `static let dateDisplay`, `static let timeDisplay`. `BudgetViewModel.swift`: `private static let monthPrefixFormatter`. Zero inline `DateFormatter()` allocations remain in either file. |
| 4 | iOS client fetches aggregated spend from the correct URL and decodes the response | ✓ VERIFIED | `APIEndpoints.budgetSummary = "/budget-summary"` — correct relative to `baseURL` ending in `/api`. `BudgetSummaryResponse` has `case spent = "monthly_spend"` CodingKey. `BudgetViewModel` sets `self.spent = summary.spent`. |
| 5 | Android client fetches aggregated spend and correctly decodes the backend response | ✓ VERIFIED | `ApiClient.kt` `@GET("budget-summary")` (correct Retrofit path). `Models.kt` `@SerializedName("monthly_spend") val spent: Double`. `HomeActivity` passes `summaryResponse.body()?.spent` to `updateBudgetUI(spent: Double?)`. |

**Score: 5/5 truths verified**

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/api/api_server.py` (lines 770–831) | `GET /api/budget-summary` endpoint | ✓ VERIFIED | Route exists, `_check_session()` auth, `get_cached("transactions_all")`, PH-time month filter, returns `{"monthly_spend": float}` |
| `mobile/ios/.../BudgetViewModel.swift` | `async let` parallel fetch; `spent = summary.spent`; static `monthPrefixFormatter` | ✓ VERIFIED | `async let budgetResp` + `async let summaryResp` in parallel; `spent = summary.spent`; static formatter present |
| `mobile/ios/.../ReceiptView.swift` | Three static formatters; zero inline `DateFormatter()` allocations | ✓ VERIFIED | `timestampParser`, `dateDisplay`, `timeDisplay` all `private static let`; no inline allocations |
| `mobile/ios/.../APIEndpoints.swift` | `budgetSummary = "/budget-summary"` (no double `/api/` prefix) | ✓ VERIFIED | Value is `"/budget-summary"` — consistent with all other endpoints |
| `mobile/ios/.../APIClient.swift` | `fetchBudgetSummary()` + `BudgetSummaryResponse` with `case spent = "monthly_spend"` CodingKey | ✓ VERIFIED | Both confirmed present |
| `mobile/.../TransactionsAdapter.kt` | DiffUtil; no `notifyDataSetChanged()`; `adapterScope` cancelled on detach | ✓ VERIFIED | `DiffUtil.calculateDiff()` on `Dispatchers.Default`; `adapterScope = MainScope()`; cancelled in `onDetachedFromRecyclerView()` |
| `mobile/.../Models.kt` | `BudgetSummaryResponse(@SerializedName("monthly_spend") val spent: Double)` | ✓ VERIFIED | Exactly this — no extra unmapped fields |
| `mobile/.../ApiClient.kt` | `@GET("budget-summary") suspend fun fetchBudgetSummary(...)` | ✓ VERIFIED | In `BangkoApiService`; path `"budget-summary"` correct relative to `BASE_URL` ending `/api/` |
| `mobile/.../HomeActivity.kt` | `loadAndDisplayBudget()` calls `fetchBudgetSummary()`; `updateBudgetUI(Double?)` | ✓ VERIFIED | `summaryResponse.body()?.spent` extracted and passed to `updateBudgetUI(spent: Double?)` |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `BudgetViewModel.load()` | `/api/budget-summary` | `apiClient.fetchBudgetSummary()` → `APIEndpoints.budgetSummary` | ✓ WIRED | `baseURL + "/budget-summary"` = `https://juley2823.pythonanywhere.com/api/budget-summary` ✓ |
| `APIClient.BudgetSummaryResponse` | Backend JSON `{monthly_spend}` | `Codable` + `CodingKeys` (`case spent = "monthly_spend"`) | ✓ WIRED | `spent` will be populated correctly; `BudgetViewModel.spent = summary.spent` flows to UI |
| `HomeActivity.loadAndDisplayBudget()` | `/api/budget-summary` (Retrofit) | `ApiClient.apiService.fetchBudgetSummary("Bearer $token")` | ✓ WIRED | `@GET("budget-summary")` relative to `BASE_URL` ending `/api/` → correct absolute URL |
| `Models.BudgetSummaryResponse` | Backend JSON `{monthly_spend}` | Gson + `@SerializedName("monthly_spend")` | ✓ WIRED | `val spent: Double` correctly populated from `monthly_spend` JSON key |
| `TransactionsAdapter.setTransactions()` | `DiffUtil.calculateDiff()` | `adapterScope.launch { withContext(Dispatchers.Default) { … } }` | ✓ WIRED | Confirmed in adapter source |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| REQ-PERF-06 | 32-01-PLAN | Add backend `GET /api/budget-summary` pre-aggregation endpoint | ✓ SATISFIED | Route at `api_server.py:770–831`; caching + month filter + correct response shape confirmed |
| REQ-PERF-07 | 32-02-PLAN, 32-04-PLAN | iOS `BudgetViewModel`: replace transaction fetch with summary endpoint; URL and decoder correct | ✓ SATISFIED | `load()` calls `fetchBudgetSummary()`; URL is `"/budget-summary"`; CodingKey mapping confirmed |
| REQ-PERF-08 | 32-02-PLAN | iOS: eliminate `DateFormatter` re-allocation in `ReceiptView` and `BudgetViewModel` | ✓ SATISFIED | All inline allocations replaced with 4 static formatters across the two files |
| REQ-PERF-09 | 32-03-PLAN, 32-04-PLAN | Android `HomeActivity`: replace transaction fetch with summary endpoint; decoder correct | ✓ SATISFIED | `fetchBudgetSummary()` called in `loadAndDisplayBudget()`; `@SerializedName` mapping confirmed |
| REQ-PERF-10 | 32-03-PLAN | Android `TransactionsAdapter`: replace `notifyDataSetChanged()` with DiffUtil | ✓ SATISFIED | DiffUtil implemented; `notifyDataSetChanged()` absent from `setTransactions()` |

**Note on REQUIREMENTS.md:** REQ-PERF-07 and REQ-PERF-09 are both marked ✅ Complete (32-04) in `REQUIREMENTS.md`, consistent with Plan 32-04 being the gap-closure plan that fixed the runtime bugs for those two requirements.

---

## Anti-Patterns Found

None. All three blocker anti-patterns from the initial verification have been remediated:

| Previously Found | Severity | Resolution |
|-----------------|----------|------------|
| `APIEndpoints.swift`: `budgetSummary = "/api/budget-summary"` (double prefix → 404) | 🛑 Fixed | `"/budget-summary"` |
| `APIClient.swift → BudgetSummaryResponse`: no CodingKeys (→ `spent` always 0.0) | 🛑 Fixed | `case spent = "monthly_spend"` |
| `Models.kt → BudgetSummaryResponse`: no @SerializedName (→ `spent` always 0.0) | 🛑 Fixed | `@SerializedName("monthly_spend") val spent: Double` |

---

## Human Verification Required

### 1. iOS Budget Screen — End-to-End

**Test:** Run the iOS app on a simulator or device, log in as a student with known purchase transactions in the current month, navigate to the Budget screen.
**Expected:** Non-zero PHP spend amount displayed (not 0.00, not an error); Xcode console shows no 404 errors for `/api/budget-summary`.
**Why human:** Static analysis confirms all wiring is correct. Only a live device/simulator test can confirm the full round-trip (network, JWT auth, JSON decoding, SwiftUI `@Published` binding to the view).

### 2. Android Budget Screen — End-to-End

**Test:** Run the Android app on an emulator, log in, observe the budget card on the Home screen.
**Expected:** Budget card shows a non-zero PHP spend amount; Logcat shows no JSON decode exceptions for `BudgetSummaryResponse`.
**Why human:** Requires live network + Gson deserialization + UI render to confirm.

### 3. Android TransactionsAdapter — Smooth Scroll & No Flash

**Test:** Open the Transactions screen with 50+ items; scroll rapidly; trigger a data refresh.
**Expected:** No full-list flash/flicker; only changed rows animate.
**Why human:** DiffUtil correctness is a visual/perceptual check that cannot be verified by static analysis.

---

## Gaps Summary

No gaps remain. All five observable truths are verified and all five requirements are satisfied.

**Gap closure recap (Plan 32-04):**
- **iOS URL fix:** `budgetSummary = "/budget-summary"` — runtime URL now resolves correctly to `https://juley2823.pythonanywhere.com/api/budget-summary` (no more 404).
- **iOS response decoder fix:** `BudgetSummaryResponse` has `case spent = "monthly_spend"` CodingKey — `summary.spent` will correctly reflect backend's `monthly_spend`.
- **Android response decoder fix:** `BudgetSummaryResponse` has `@SerializedName("monthly_spend") val spent: Double` — `response.body()?.spent` will correctly reflect backend's `monthly_spend`.

Three human end-to-end tests are required to confirm live network + decode + UI render behaviour before this phase can be fully signed off.

---

_Verified: 2026-03-10_
_Verifier: Claude (gsd-verifier)_
_Re-verification: Yes — gaps from initial verification closed by Plan 32-04_
