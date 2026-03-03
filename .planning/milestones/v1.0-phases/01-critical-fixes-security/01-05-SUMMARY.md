---
phase: "01"
plan: "05"
subsystem: "error-handling, transaction-safety"
tags: ["bug-fix", "security", "sheets-api", "error-handling", "transactions", "atomicity"]
dependency-graph:
  requires: ["01-01", "01-02", "01-03", "01-04"]
  provides: ["graceful-error-handling", "transaction-atomicity"]
  affects: ["backend/api/api_server.py", "backend/dashboard/admin_dashboard.py", "backend/dashboard/cashier/cashier_routes.py"]
tech-stack:
  added: ["gspread exception hierarchy", "logging.getLogger"]
  patterns: ["two-tier exception handling", "retry-with-backoff", "rollback-on-failure"]
key-files:
  created: []
  modified:
    - "backend/api/api_server.py"
    - "backend/dashboard/admin_dashboard.py"
    - "backend/dashboard/cashier/cashier_routes.py"
decisions:
  - "Serial/Arduino routes use ConnectionError/TimeoutError only (no gspread exceptions — they don't touch Sheets)"
  - "register_student and report_lost_card also sanitize socketio.emit messages (were previously emitting str(e))"
  - "timestamp set before retry loop to ensure consistent transaction timestamp across retry attempts"
  - "Both tasks included in single commit 433299c as cashier_routes.py was staged together"
metrics:
  duration: "~65 minutes (resumed from partial state)"
  completed: "2026-02-26T09:07:53Z"
  tasks: 2
  files: 3
requirements: ["BUG-03", "BUG-05"]
---

# Phase 01 Plan 05: Graceful Error Handling and Transaction Atomicity Summary

**One-liner:** Replaced all 38 bare `str(e)` 500 responses with two-tier gspread/network vs. unexpected error handling, and added 3-attempt retry with exponential backoff and rollback to `complete_sale()`.

## What Was Done

### Task 1 — BUG-03: Graceful Two-Tier Error Handling

Replaced every bare `except Exception as e: return jsonify({'error': str(e)}), 500` with a two-tier catch pattern across all three backend files:

```python
except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
    logger.error(f"Google Sheets unavailable in [route]: {e}")
    return jsonify({'error': 'Service unavailable, please try again'}), 503
except Exception as e:
    logger.error(f"Unexpected error in [route]: {e}", exc_info=True)
    return jsonify({'error': 'An unexpected error occurred'}), 500
```

**Files fixed:**
- `backend/api/api_server.py` — 9 routes (fixed earlier in session)
- `backend/dashboard/admin_dashboard.py` — 25 routes (all remaining instances)
- `backend/dashboard/cashier/cashier_routes.py` — 4 routes + added `import gspread`, `import logging`, `logger = logging.getLogger(__name__)`, `import time`

**Special cases handled:**
- `health_check`: returns `{'status': 'error', 'message': ...}` shape (not `{'error': ...}`) to match its expected response contract
- `register_student` and `report_lost_card`: also sanitized the `socketio.emit('card_error', ...)` messages to use generic text instead of `str(e)`
- Serial/Arduino routes (`get_serial_ports`, `connect_serial`, `disconnect_serial`): use `ConnectionError/TimeoutError` only (no gspread)

**Total bare `str(e)` eliminated:** 38 across 3 files (9 + 25 + 4)

### Task 2 — BUG-05: Transaction Atomicity with Retry and Rollback

Replaced the balance-deduction + transaction-log section in `complete_sale()` with retry-then-abort logic:

```python
MAX_RETRIES = 3
timestamp = get_philippines_time().strftime('%Y-%m-%d %H:%M:%S')
balance_deducted = False
last_error = None

for attempt in range(1, MAX_RETRIES + 1):
    try:
        if not balance_deducted:
            money_sheet.update_cell(account_row, 3, new_balance)
            balance_deducted = True
        # ... log transaction ...
        break
    except (gspread.exceptions.APIError, ConnectionError, TimeoutError) as e:
        if attempt < MAX_RETRIES:
            time.sleep(2 ** attempt)  # 2s, 4s
        else:
            if balance_deducted:
                money_sheet.update_cell(account_row, 3, current_balance)  # rollback
            return jsonify({'error': 'Service unavailable, please try again'}), 503
```

**Key design decisions:**
- Two-phase: deduct balance (step 1) then log transaction (step 2) — balance step only runs once across retries
- Exponential backoff: 2s then 4s between attempts
- Rollback on exhaustion: if balance was deducted but transaction logging failed all 3 attempts, restores original balance
- CRITICAL path: rollback failure logged with full context for manual recovery
- `timestamp` set before loop so retry attempts all log the same transaction time

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing sanitization] socketio.emit also leaked str(e)**
- **Found during:** Task 1 — register_student, report_lost_card
- **Issue:** `socketio.emit('card_error', {'message': str(e)})` was also leaking exception details to clients via WebSocket
- **Fix:** Replaced with generic messages (`'Service unavailable, please try again'` / `'An unexpected error occurred'`)
- **Files modified:** `backend/dashboard/admin_dashboard.py`

**2. [Rule 3 - Blocking] cashier_routes.py lacked gspread import for exception matching**
- **Found during:** Task 1 — cashier_routes.py
- **Issue:** File uses `get_sheets_client()` from admin_dashboard but never imports gspread directly; needed for `gspread.exceptions.*` in catch blocks
- **Fix:** Added `import gspread` at top of file
- **Files modified:** `backend/dashboard/cashier/cashier_routes.py`

**3. [Rule 1 - Bug] timestamp possibly unbound after retry loop refactor**
- **Found during:** Task 2
- **Issue:** Moving timestamp creation inside the loop caused LSP "possibly unbound" warning on the return statement
- **Fix:** Moved `timestamp = get_philippines_time().strftime(...)` to before the retry loop
- **Files modified:** `backend/dashboard/cashier/cashier_routes.py`

### Out of Scope (Deferred)

`backend/dashboard/web_app_complete.py` contains 6 additional bare `str(e)` 500 responses — this file was not in the plan scope (it appears to be a legacy/alternate version of the dashboard). Logged for future cleanup.

## Commits

| Hash | Description |
|------|-------------|
| `433299c` | fix(01-05): replace bare str(e) error responses with graceful Sheets error handling + transaction atomicity (both tasks) |

## Self-Check

- [x] `backend/api/api_server.py` — 0 bare `str(e)` remain (verified)
- [x] `backend/dashboard/admin_dashboard.py` — 0 bare `str(e)` remain (verified)
- [x] `backend/dashboard/cashier/cashier_routes.py` — 0 bare `str(e)` remain (verified)
- [x] `MAX_RETRIES = 3` present in complete_sale (verified)
- [x] Rollback logic present (verified)
- [x] Commit `433299c` exists (verified)
