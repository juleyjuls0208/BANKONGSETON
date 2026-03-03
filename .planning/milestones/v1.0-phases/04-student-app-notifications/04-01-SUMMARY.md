---
phase: 04-student-app-notifications
plan: 01
subsystem: api
tags: [flask, gspread, fcm, pagination, transactions, google-sheets]

requires:
  - phase: 03-product-management
    provides: api_server.py foundation with active_sessions auth pattern

provides:
  - "FCM token endpoint that accepts real student session tokens (not JWT)"
  - "Offset pagination on GET /api/student/transactions with has_more flag"
  - "balance_before field on each transaction in response"
  - "8-column cashier transaction log with BalanceBefore at column 5"
  - "FCMToken column guaranteed present in live Users Google Sheet"

affects: [android-app, student-app, notifications]

tech-stack:
  added: []
  patterns:
    - "Session-based auth via active_sessions dict (not JWT decode) for student endpoints"
    - "update_cell(row, col, val) for gspread cell writes (avoids chr(64+col) column-letter bug)"

key-files:
  created: []
  modified:
    - backend/api/api_server.py
    - backend/migrate_transactions.py  # already had migrate_users_schema(); executed against live sheet

key-decisions:
  - "Use active_sessions auth (not JWT) for register_fcm_token — consistent with all other student endpoints"
  - "Replace chr(64+fcm_col_idx) column-letter conversion with update_cell() — avoids off-by-one for columns > Z"
  - "Insert BalanceBefore at transaction_row index 4 (before BalanceAfter) — matches Transactions Log sheet column spec"
  - "get_transactions uses record.get('BalanceBefore', 0) with fallback — backward-compatible with pre-migration rows"

patterns-established:
  - "Student endpoints always use active_sessions auth, never JWT require_auth decorator"
  - "Pagination pattern: offset + limit slice, return has_more = (offset+limit) < total"

requirements-completed: [APP-02, APP-03, APP-04, APP-05, NOTF-01]

duration: 2min
completed: 2026-02-26
---

# Phase 4 Plan 01: Backend API Fixes Summary

**Fixed 4 blocking backend bugs: FCM 401 auth mismatch, missing offset pagination, missing balance_before field in transactions, and 7-column cashier log missing BalanceBefore**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-26T14:18:20Z
- **Completed:** 2026-02-26T14:20:16Z
- **Tasks:** 3
- **Files modified:** 1 (api_server.py) + migration executed on live sheet

## Accomplishments

- FCM token endpoint now uses session-based auth — students can register FCM tokens without 401
- GET /api/student/transactions accepts `limit` + `offset` params and returns `has_more` + `total` for infinite scroll
- Transaction response now includes `balance_before` per transaction (needed for receipt screen)
- Cashier transaction log expanded to 8 columns with `BalanceBefore` at column 5 before `BalanceAfter`
- FCMToken column confirmed present in live Users Google Sheet (migrate_users_schema() executed)

## Task Commits

Each task was committed atomically:

1. **Task 1: migrate_users_schema()** — no file changes needed (function pre-existed and was correct); executed against live sheet
2. **Task 2: FCM auth fix + offset pagination** — `e9f9e85` (fix)
3. **Task 3: balance_before in response + cashier log** — `c9dc5b3` (feat)

**Plan metadata:** `087b933` (docs: complete plan)

## Files Created/Modified

- `backend/api/api_server.py` — 4 fixes applied:
  1. `register_fcm_token`: removed `@require_auth(roles=['student'])`, added session-based auth reading `active_sessions[token]['student_id']`
  2. `register_fcm_token`: replaced `chr(64+fcm_col_idx)` + `update()` with `update_cell(user_row, fcm_col_idx, fcm_token)`
  3. `get_transactions`: added `offset` param, slices `transactions[offset:offset+limit]`, returns `has_more` + `total`
  4. `get_transactions`: added `balance_before` field from `record.get('BalanceBefore', 0)`
  5. `process_cashier_transaction`: expanded `transaction_row` from 7 to 8 columns, inserting `current_balance` at index 4

## Decisions Made

- Used `active_sessions` dict for FCM auth — consistent with all other student endpoints (`get_profile`, `get_balance`, `get_transactions`)
- Used `update_cell(row, col, val)` instead of column-letter conversion — avoids `chr(64+col)` bug for columns > Z (which would produce wrong letters)
- Inserted `BalanceBefore` at column 5 (before `BalanceAfter`) — matches the Transactions Log sheet's intended column schema

## Deviations from Plan

None - plan executed exactly as written. All four fixes applied as specified. `migrate_users_schema()` was already correct and complete in migrate_transactions.py (pre-existing from an earlier phase).

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. The FCMToken column migration was run automatically and confirmed successful.

## Next Phase Readiness

- All 4 blocking bugs resolved — APP-02 through APP-05 and NOTF-01 can now be implemented
- Android app can call `POST /api/users/fcm-token` with student session tokens successfully
- Infinite scroll on transaction history is unblocked
- Receipt screen can show balance_before on all new transactions (old rows fall back to 0.0)
- Cashier POS will log BalanceBefore on every new Purchase transaction going forward

---
*Phase: 04-student-app-notifications*
*Completed: 2026-02-26*

## Self-Check: PASSED

- ✅ `backend/api/api_server.py` — exists on disk
- ✅ `04-01-SUMMARY.md` — exists on disk
- ✅ commit `e9f9e85` — confirmed in git log (Task 2: FCM auth + offset pagination)
- ✅ commit `c9dc5b3` — confirmed in git log (Task 3: balance_before)
- ✅ commit `087b933` — confirmed in git log (docs: plan metadata)
