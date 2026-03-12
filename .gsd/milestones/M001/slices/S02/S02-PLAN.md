# S02: SMS Notifications & Transaction Filter

**Goal:** Fix confirmed bugs and add missing wiring for Twilio SMS notifications (purchase + low-balance) and complete transaction filter UI migration.

**Demo:** 
1. Admin filters transactions by date range, student ID/name, or type on the Transactions page
2. After a cashier purchase, parent receives both purchase SMS AND low-balance SMS if balance < threshold
3. NFC payment triggers correct low-balance SMS with proper parameters

## Must-Haves

- [ ] `api_server.py` low-balance SMS call uses correct kwargs (`to_number`, `student_name`, `balance`) instead of buggy `phone_number`, `new_balance`
- [ ] `cashier_routes.py` checks `new_balance < LOW_BALANCE_THRESHOLD` after purchase and sends low-balance SMS if true
- [ ] `transactions.html` migrated to `{% extends "base.html" %}` with shared nav (removing inline sidebar)
- [ ] `tests/test_s02_sms_filter.py`: TwilioSMSNotifier tests (enabled gate, all 3 send methods), filtered endpoint contract tests

## Proof Level

- This slice proves: **integration**
- Real runtime required: **yes** (for SMS delivery verification with mocks)
- Human/UAT required: **no** (functional via test assertions and API contract checks)

## Verification

- `bash -c "python -m pytest tests/test_s02_sms_filter.py -v"` — all 15+ tests pass
- Unit tests verify TwilioSMSNotifier.enabled gate logic (disabled when env vars missing, enabled when present)
- Contract assertions confirm GET /api/transactions/filtered returns correct paginated results with filters applied

## Observability / Diagnostics

- Runtime signals: SMS send attempts logged via logger.warning() in except blocks; Twilio client lazy-init errors visible on first call
- Inspection surfaces: `backend/logs/sms_errors.log` for failed sends, Google Sheets "Scheduler Log" for batch email runs
- Failure visibility: TypeError from kwarg mismatch now fixed with proper kwargs; phone column fallback prevents empty string issues

## Integration Closure

- Upstream surfaces consumed: TwilioSMSNotifier class (notifications.py), existing transaction filter backend endpoint
- New wiring introduced in this slice: SMS low-balance check after cashier purchase, template migration to base.html
- What remains before the milestone is truly usable end-to-end: T02 verification tests provide coverage; S03-S06 remain for other features

## Tasks

- [x] **T01: Fix Twilio kwarg bug and wire low-balance SMS in cashier flow** `est:45m` ✅
  - Why: api_server.py silently fails on NFC low-balance SMS due to wrong kwargs; cashier purchases don't send low-balance alert after purchase SMS
  - Files: `backend/api/api_server.py`, `backend/dashboard/cashier/cashier_routes.py`
  - Do: 
    1. In api_server.py line ~1217-1222, rename kwargs from `phone_number=` → `to_number=`, `new_balance=` → `balance=`, add missing `student_name=`, `threshold=` params
    2. In cashier_routes.py complete_sale() after purchase SMS call (~369-392), check if new_balance < LOW_BALANCE_THRESHOLD and send low-balance SMS if true using same pattern as admin_dashboard.py load_balance()
    3. Add defensive phone column fallback in both files: `str(u.get('ParentPhone') or u.get('PhoneNumber', '')).strip()` to handle sheet inconsistency
  - Verify: Run unit tests from T02; manual check with curl that /api/transactions/nfc-payment sends SMS without TypeError (requires mocking Twilio)
  - Done when: kwargs corrected in api_server.py, low-balance SMS added to cashier flow, phone fallback implemented

- [x] **T02: Migrate transactions.html to base.html template** `est:45m` ✅ VERIFIED
  - Why: Standalone transactions.html has duplicate sidebar missing Fraud Alerts nav and live badge; needs consistency with other admin pages
  - Files: `backend/dashboard/templates/transactions.html`, `backend/dashboard/admin_dashboard.py` (route params)
  - Do: 
    1. Remove inline `<style>` block from transactions.html (use base.css instead), remove duplicate sidebar markup, keep only filter bar and results table
    2. Add `{% extends "base.html" %}` at top; in body pass `active_page='transactions'` and `role=session.get('role')`
    3. Keep existing filter bar HTML (From Date, To Date, Student search input, Type dropdown, Filter/Clear buttons) — ensure it renders correctly without inline CSS
    4. Update JS fetch calls if needed to match base.html structure; verify Fraud Alerts nav item and badge now visible on transactions page
  - Verify: Navigate /transactions in browser, confirm sidebar matches other admin pages (no duplicate), Fraud Alerts link present with live badge, filter bar functional at top of content area
  - Done when: Page renders without errors using base template, no duplicate sidebar, shared nav items including Fraud Alerts visible
  
## Task T02 Status

**VERIFIED COMPLETE:** transactions.html already uses `{% extends "base.html" %}` (line 1), has no inline CSS or duplicate sidebar markup. All task requirements satisfied by existing implementation - verification confirmed in `.gsd/milestones/M001/slices/S02/tasks/T02-SUMMARY.md`.

- [x] **T03: Write verification tests for SMS and transaction filter** `est:60m`
  - Why: No test coverage exists for TwilioSMSNotifier or filtered endpoint; need unit + contract tests to prevent regressions
  - Files: `tests/test_s02_sms_filter.py` (new file)
  - Do: 
    1. Mock Twilio client and import get_sms_notifier(); write tests for enabled gate (env vars missing → False, present → True), test all three send methods with correct param names and mock.assert_called_once()
    2. Write contract tests for GET /api/transactions/filtered: each filter param individually (date_from, date_to, student_id, txn_type) + combination test; assert returned JSON structure matches expected schema with count, transactions array, filters_applied object
    3. Add TwilioSMSNotifier unit tests in a separate class or section for clarity
  - Verify: `python -m pytest tests/test_s02_sms_filter.py -v` shows all tests pass (mocked Twilio calls verified)
  - Done when: All 15+ tests written and passing, covering SMS gate logic and filter endpoint contract

## Files Likely Touched

- `backend/api/api_server.py` — fix kwarg names in low-balance SMS call
- `backend/dashboard/cashier/cashier_routes.py` — add low-balance SMS check after purchase
- `backend/dashboard/templates/transactions.html` — migrate to base template, remove inline sidebar/CSS
- `tests/test_s02_sms_filter.py` — new test file
