---
phase: 29-android-security-p1-bugs
plan: "02"
subsystem: mobile
tags: [android, recyclerview, kotlin, viewholder, budget]

# Dependency graph
requires: []
provides:
  - ViewHolder isClickable reset fix — recycled Purchase rows are now tappable
  - Budget spend filter — updateBudgetUI() sums only Purchase + NFC Purchase transactions
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Always reset ViewHolder state at top of bind() before conditional branches"
    - "Use exact string equality for server-defined transaction type values (not ignoreCase)"

key-files:
  created: []
  modified:
    - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/TransactionsAdapter.kt
    - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt

key-decisions:
  - "Add isClickable = true as first line of bind(), before isPurchase branch — only the recycling path is broken; the false guard in the else-branch is still needed for current render"
  - "Use exact == equality (not ignoreCase) for type filter in updateBudgetUI() — server always sends exact strings; case-insensitive match could accidentally include future types containing 'purchase'"

requirements-completed:
  - REQ-BUG-MOB-06
  - REQ-BUG-MOB-07

# Metrics
duration: 3min
completed: 2026-03-09
---

# Phase 29 Plan 02: Android P1 Bug Fixes — ViewHolder Reuse & Budget Inflation Summary

**Fixed two P1 Android bugs: recycled non-purchase ViewHolder rows permanently blocking tap navigation, and budget card inflating spend totals by including Top-Up credits**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-09T13:00:00Z
- **Completed:** 2026-03-09T13:03:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `TransactionsAdapter.kt`: Added `itemView.isClickable = true` as first line of `bind()` — recycled ViewHolders that previously had `isClickable = false` are now reset before the `isPurchase` branch, ensuring tapped Purchase rows always navigate to ReceiptActivity
- `HomeActivity.kt`: Added `.filter { it.type == "Purchase" || it.type == "NFC Purchase" }` before `.sumOf { it.amount }` in `updateBudgetUI()` — Top-Up and other credit transactions no longer inflate the monthly spend total
- Both fixes use the minimum required change with no side effects on other logic

## Task Commits

Each task was committed atomically:

1. **Task 1: Reset isClickable at top of bind() (REQ-BUG-MOB-07)** - `161b5fd` (fix)
2. **Task 2: Filter to purchase-only in updateBudgetUI() (REQ-BUG-MOB-06)** - `8c7d7d0` (fix)

**Plan metadata:** _(docs commit — see below)_

## Files Created/Modified

- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/TransactionsAdapter.kt` — Added `itemView.isClickable = true` as first line of `bind()`
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt` — Added type filter before `.sumOf` in `updateBudgetUI()`

## Decisions Made

- Reset `isClickable = true` at top of `bind()`, not inside the `if (isPurchase)` branch — the RecyclerView recycling path means any prior `isClickable = false` state persists across reuse; unconditional reset at top is the correct fix
- Preserved `itemView.isClickable = false` in the else-branch — still required for the current (non-recycled) non-purchase row render
- Used `==` (not `ignoreCase = true`) for type filter — server always sends exact-case strings; case-insensitive match risks accidentally including future transaction types

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02 complete; Plan 01 (NfcManager plaintext PIN fix, REQ-BUG-MOB-05) still pending in this phase
- Both changes are isolated to TransactionsAdapter.kt and HomeActivity.kt — no dependencies on Plan 01
- NfcManager.kt was not touched by Plan 02 (verified: grep for putString(KEY_NFC_PIN) still shows original line, confirming no regression)

---
*Phase: 29-android-security-p1-bugs*
*Completed: 2026-03-09*
