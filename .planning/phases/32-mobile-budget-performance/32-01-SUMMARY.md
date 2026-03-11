# Phase 32-01 Summary — Backend Budget Summary Endpoint

## What Was Done

Added `GET /api/budget-summary` endpoint to `backend/api/api_server.py`.

## Files Modified

| File | Change |
|------|--------|
| `backend/api/api_server.py` | Inserted new route before `report_lost_card()` at ~line 770 |

## Implementation Details

The route was inserted immediately before the `report_lost_card` route to maintain logical grouping. It follows the established `_check_session(token)` authentication pattern used throughout the file (not the decorator pattern shown in the plan, which does not exist in the actual codebase).

**Route behaviour:**
- Authenticates via `Authorization: Bearer <token>` header using `_check_session()`
- Looks up the student by token in the `"Users"` worksheet (not `"Students"` — matches actual sheet name)
- Reads the student's `monthly_limit` from the budget data
- Computes `spent` by summing all current-month `Purchase` and `NFC Purchase` transactions
- Returns JSON: `{ spent, limit, percent, currency }`

## Deviations from Plan

| Plan said | Actual code uses | Reason |
|-----------|-----------------|--------|
| `@require_auth(roles=["student"])` decorator | `_check_session(token)` manual pattern | Decorator doesn't exist in codebase |
| `get_worksheet_with_retry("Students")` | `get_worksheet_with_retry("Users")` | Actual sheet is named "Users" |

## Outcome

✅ Backend now exposes a single `/api/budget-summary` endpoint that pre-computes spent/percent server-side, eliminating the need for clients to download and filter 200 transactions.
