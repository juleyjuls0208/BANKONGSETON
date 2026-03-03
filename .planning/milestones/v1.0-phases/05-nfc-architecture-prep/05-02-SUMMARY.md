---
phase: 05-nfc-architecture-prep
plan: "02"
subsystem: api
tags: [flask, nfc, jwt, cors, gspread, virtual-card]

# Dependency graph
requires:
  - phase: 05-nfc-architecture-prep
    provides: NFCService with register_virtual_card and get_virtual_card_by_tokens methods (nfc_payments.py)
provides:
  - POST /api/nfc/register endpoint (active_sessions auth, returns virtual_card_token + device_token)
  - POST /api/nfc/pay endpoint (dual auth: cashier JWT + X-Device-Token, debits balance, logs NFC Purchase)
  - CORS allow_headers updated to include X-Device-Token for Android preflight
affects:
  - 05-03-integration-guide
  - android-nfc-client
  - any client making NFC payment requests

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dual-auth pattern: @require_auth JWT decorator + X-Device-Token header check inside handler"
    - "active_sessions auth for student-facing NFC register (matches all /api/student/* endpoints)"
    - "NFC Purchase TransactionType distinct from Purchase for transaction history filtering"

key-files:
  created: []
  modified:
    - backend/api/api_server.py

key-decisions:
  - "Used active_sessions (not @require_auth) for nfc_register — consistent with all student endpoints (not JWT-based)"
  - "X-Device-Token checked inside nfc_pay handler (after JWT decorator), not as a separate middleware"
  - "TransactionType='NFC Purchase' distinct from 'Purchase' so Android can distinguish NFC from RFID transactions"
  - "Balance column found dynamically via header_row.index('Balance') with fallback to column C (index 3)"
  - "nfc_service = NFCService() instantiated at module level for shared use by both NFC routes"

patterns-established:
  - "Dual-auth pattern: @require_auth for JWT + manual header check for secondary token inside handler"
  - "CORS allow_headers must include any custom headers (X-Device-Token) to pass Android preflight"

requirements-completed:
  - NFC-01
  - NFC-03
  - NFC-04

# Metrics
duration: 3min
completed: 2026-02-28
---

# Phase 5 Plan 02: NFC Flask API Endpoints Summary

**Two NFC endpoints wired into Flask: POST /api/nfc/register with active_sessions auth and POST /api/nfc/pay with dual JWT + X-Device-Token auth, plus CORS updated for Android preflight**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-28T11:17:40Z
- **Completed:** 2026-02-28T11:20:57Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Added `POST /api/nfc/register` using `active_sessions` auth (matches all student endpoints) — returns `virtual_card_token`, `device_token`, `money_card` on success; 401/403/503 for error cases
- Added `POST /api/nfc/pay` with dual authentication: `@require_auth(roles=['admin','cashier'])` for JWT validation + `X-Device-Token` header check inside handler; calls `NFCService.get_virtual_card_by_tokens()`, debits Money Accounts balance, appends `NFC Purchase` row to Transactions Log
- Updated Flask-CORS `allow_headers` to include `X-Device-Token` so Android preflight OPTIONS requests are not blocked

## Task Commits

Each task was committed atomically:

1. **Task 1: Add /api/nfc/register + update CORS** - `9a58191` (feat)
   *(Task 2 also included — both tasks were applied to the same file in one session)*

**Plan metadata:** *(pending — will be docs commit)*

## Files Created/Modified

- `backend/api/api_server.py` — CORS updated, NFCService imported, nfc_register and nfc_pay routes added (~160 lines added)

## Decisions Made

- Used `active_sessions` dict check (not `@require_auth`) for `/api/nfc/register` — students use session tokens not JWT; critical correctness requirement per plan Pitfall 1
- `@require_auth(roles=['admin','cashier'])` on `/api/nfc/pay` — cashier POS device calls this, not the student app
- `X-Device-Token` validated inside the handler body (not as decorator) after JWT is already verified — clean separation of auth layers
- `TransactionType='NFC Purchase'` chosen over `'Purchase'` so Android transaction history can distinguish NFC from RFID tap payments
- `nfc_service = NFCService()` instantiated at module-level (not per-request) for efficiency — stateless service, safe to share

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan verification script checked wrong position for `@require_auth`**
- **Found during:** Task 2 verification
- **Issue:** The plan's verification script checked `src[nfc_pay_pos-300:nfc_pay_pos]` (before the route string), but `@require_auth` is on the line *after* `@app.route(...)`, so it appears *after* `'/api/nfc/pay'` in the source string
- **Fix:** Identified the correct structure — decorator is immediately after `@app.route(...)`, confirmed using `src[app_route_pos:app_route_pos+200]`. The code is correct; the script had a logic flaw.
- **Files modified:** None (script-only check issue, not a code bug)
- **Verification:** Confirmed `@require_auth(roles=['admin', 'cashier'])` is on the line directly after `@app.route('/api/nfc/pay', methods=['POST'])` — matches all other protected routes in the file
- **Committed in:** 9a58191 (Task 1/2 commit)

**2. [Rule 1 - Bug] Plan verification `handler_block` window too small (2000 chars) to cover full `nfc_pay` function**
- **Found during:** Task 2 verification
- **Issue:** The `NFC Purchase` string is 3799 chars from the start of the handler block; the plan's script used `nfc_pay_start + 2000`
- **Fix:** Expanded check window to 5000 chars — covers the full function body including transaction logging section
- **Files modified:** None (check-only issue)
- **Verification:** `'NFC Purchase' in handler_block` passes with 5000 char window
- **Committed in:** 9a58191 (Task 1/2 commit)

---

**Total deviations:** 2 auto-identified (both script/verification logic issues, not code bugs)
**Impact on plan:** Zero code scope creep. Both issues were in the plan's own verification scripts, not in the implementation. Actual endpoint code is exactly as specified.

## Issues Encountered

None — import check and route registration both passed cleanly.

## User Setup Required

None - no external service configuration required. NFC endpoints use existing Google Sheets credentials.

## Next Phase Readiness

- Both NFC endpoints implemented and verified with correct auth patterns
- CORS updated — Android clients can make NFC register/pay requests without preflight errors
- NFCService (Plan 01) is wired into Flask (Plan 02) — ready for Plan 03 integration guide
- All 3 requirements satisfied: NFC-01 (register + pay API contract), NFC-03 (transaction logging), NFC-04 (CORS + X-Device-Token)

---
*Phase: 05-nfc-architecture-prep*
*Completed: 2026-02-28*
