---
phase: 32-mobile-budget-performance
plan: 04
subsystem: mobile

tags: [ios, android, swift, kotlin, budget, api, json-decoding, codingkeys, serializedname, gson]

# Dependency graph
requires:
  - phase: 32-mobile-budget-performance
    provides: budget summary API endpoint at /api/budget-summary returning {monthly_spend}

provides:
  - iOS APIEndpoints.budgetSummary corrected to /budget-summary (no double /api prefix)
  - iOS BudgetSummaryResponse with CodingKeys mapping monthly_spend → spent
  - Android BudgetSummaryResponse with @SerializedName("monthly_spend") on spent field

affects: [32-mobile-budget-performance]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "iOS: CodingKeys enum for snake_case → camelCase JSON field mapping"
    - "Android: @SerializedName annotation for Gson JSON field mapping"

key-files:
  created: []
  modified:
    - mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift
    - mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift
    - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt

key-decisions:
  - "iOS commit made from mobile/ios nested git repo (not parent repo) — mobile/ios/ is an untracked subdir in parent git"
  - "Android BudgetSummaryResponse stripped to single field (spent) — backend only returns monthly_spend; extra fields (limit, percent, currency) were dead weight"
  - "iOS BudgetSummaryResponse stripped to single field (spent) — same rationale"

patterns-established:
  - "iOS JSON mapping: CodingKeys enum inside Decodable struct for any snake_case backend field"
  - "Android JSON mapping: @SerializedName annotation on Gson data class field"

requirements-completed: [REQ-PERF-07, REQ-PERF-09]

# Metrics
duration: 8min
completed: 2026-03-10
---

# Phase 32 Plan 04: Budget Fix Runtime Bugs Summary

**Fixed iOS double `/api` URL prefix and both iOS + Android `monthly_spend` JSON decoding so budget screens display real spend instead of 0.0**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-10T~08:00Z (continuation from prior session)
- **Completed:** 2026-03-10
- **Tasks:** 3 (2 auto + 1 checkpoint:human-verify, auto-approved in yolo mode)
- **Files modified:** 3

## Accomplishments

- Fixed iOS URL double-prefix bug: `budgetSummary = "/api/budget-summary"` → `"/budget-summary"` (baseURL already includes `/api`; prior path caused 404 on every budget request)
- Fixed iOS response decoding: `BudgetSummaryResponse` now has `CodingKeys` mapping `monthly_spend` → `spent`; unused fields removed
- Fixed Android response decoding: `BudgetSummaryResponse` now has `@SerializedName("monthly_spend") val spent: Double`; unused fields removed

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix iOS budget URL prefix and response decoding** - `448264b` (fix) — committed from `mobile/ios` nested git repo
2. **Task 2: Fix Android BudgetSummaryResponse monthly_spend mapping** - `de918c1` (fix) — committed from parent repo
3. **Task 3: Verification checkpoint (auto-approved)** — no code commit (grep verification only)

**Plan metadata:** _(see final metadata commit below)_

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift` — Changed `budgetSummary` path from `"/api/budget-summary"` to `"/budget-summary"`
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift` — Replaced `BudgetSummaryResponse` struct: added `CodingKeys` enum mapping `monthly_spend → spent`, removed unused `limit/percent/currency` fields
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt` — Replaced `BudgetSummaryResponse` data class: added `@SerializedName("monthly_spend")` on `spent`, removed unused `limit/percent/currency` fields

## Decisions Made

- iOS commit made from `mobile/ios` git repo (not parent repo) — `mobile/ios/` is an untracked subdirectory in the parent project's git; staging iOS files from parent git silently no-ops
- Both response structs stripped to single field (`spent`) — backend only returns `monthly_spend`; extra fields were dead code that could confuse future readers
- `SerializedName` import was already present in `Models.kt` line 3 — no import changes needed

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Task 1 iOS commit originally attempted from parent repo in prior session — failed silently (nothing staged) because `mobile/ios/` is an untracked nested git repo. Resolved by committing from within `mobile/ios/` directory. Documented in key-decisions.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- REQ-PERF-07 (iOS budget wiring) and REQ-PERF-09 (Android budget wiring) both satisfied
- Budget screens on both platforms will now decode `monthly_spend` correctly and iOS will hit the correct URL
- Phase 32 can continue with remaining plans (budget limit set/read, etc.)

---
*Phase: 32-mobile-budget-performance*
*Completed: 2026-03-10*
