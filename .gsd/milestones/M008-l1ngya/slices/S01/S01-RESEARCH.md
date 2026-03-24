# S01 Research — Budget Contract Restoration (Backend + iOS)

**Date:** 2026-03-24  
**Slice:** M008-l1ngya/S01  
**Status:** Ready for planning (with explicit infra blockers noted)

## Requirement Targeting (Active)

S01 directly owns:

- **R073 [integration]** — Budget limit and spend segments load from stable backend contract backed by `Student Budgets`.
- **R074 [failure-visibility]** — Budget load/save failures are explicit, retryable, and not silently masked.

## Summary

This is **targeted research** with **high integration risk** (backend contract gap + Sheets data coupling).

### Core finding

The iOS app is already wired to budget endpoints and explicit retry UX, but the backend API currently does **not** implement the required routes.

- iOS expects:
  - `GET /api/student/budget`
  - `POST /api/student/budget`
  - `GET /api/budget-summary`
- These are defined and used in:
  - `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift`
  - `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
  - `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift`
- Backend `backend/api/api_server.py` currently has **no** `/api/student/budget` or `/api/budget-summary` routes.

### R074 status reality

R074 is already substantially implemented on iOS UI/viewmodel side:

- Explicit load failure channel (`loadErrorMessage`) + Retry Load action
- Explicit save failure channel (`saveErrorMessage`, `pendingRetryLimit`) + Retry Save action
- Distinct loading/error/ready cards with accessibility IDs

So S01 risk is primarily backend contract + backend testability, not iOS UI rework.

## Key Findings for Planner

1. **Backend route gap is the blocker for R073**
   - `backend/api/api_server.py` has student profile/balance/transactions/lost-card routes, but no budget routes.

2. **No `Student Budgets` worksheet provisioning helper exists in API server**
   - There is a pattern for lazy sheet creation in other modules (`ensure_virtual_cards_sheet` in `backend/nfc_payments.py`), but nothing equivalent for `Student Budgets`.

3. **Good reusable backend primitives already exist**
   - Auth/session pattern: `active_sessions` checks for student endpoints
   - Sheets retry/cache helpers: `get_worksheet_with_retry`, `get_sheet_records_cached`
   - Defensive numeric parsing pattern already present in `get_transactions()` (`parse_numeric`)

4. **Transaction source for monthly spend is available**
   - `Transactions Log` is read in `get_transactions()` and contains `Timestamp`, `MoneyCardNumber`, `TransactionType`, `Amount`, `Status`.
   - This supports roadmap guidance to compute monthly spend from transaction source-of-truth.

5. **Test harness needs mocking-first strategy for API server imports**
   - `api_server.py` initializes `db = get_sheets_client()` at import time.
   - In this environment, import fails without credentials (`credentials.json` missing).
   - Tests must patch `gspread.service_account` (or equivalent) **before importing** `backend.api.api_server`.

## Recommendation

Deliver S01 in backend-first order, then contract verification, then optional iOS touch-up only if mismatch remains.

1. Implement backend budget contract (`GET/POST /api/student/budget`, `GET /api/budget-summary`) in `backend/api/api_server.py`.
2. Implement/ensure `Student Budgets` sheet shape and upsert semantics.
3. Compute monthly spend from `Transactions Log` for current PH month (as context recommends), with defensive parsing/filtering.
4. Add pytest contract tests with pre-import Sheets mocking.
5. Re-run existing iOS budget failure-contract tests to ensure R074 remains intact.

## Implementation Landscape

### Files to change (high confidence)

- `backend/api/api_server.py`
  - Add new routes and helper functions:
    - `GET /api/student/budget`
    - `POST /api/student/budget`
    - `GET /api/budget-summary`
    - helper to get/create `Student Budgets` worksheet
    - helper to resolve current student’s money card + monthly spend

### Files likely to add

- `tests/test_verify_m008_s01_budget_contract.py`
  - Contract/runtime tests for new backend endpoints using mocked Sheets

- `scripts/verify-m008-s01.sh`
  - One-command verifier following existing project pattern

### Files to keep as-is unless contract mismatch appears

- `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift`
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift`

Current iOS contract already matches roadmap endpoint names and response keys (`monthly_limit`, `monthly_spend`).

## Natural Seams (Task Decomposition)

### Seam A — Student Budgets persistence contract

Scope:
- Create/get `Student Budgets` sheet with canonical headers (at minimum):
  - `StudentID`, `MonthlyLimit`, `YearMonth`, `UpdatedAt`
  - (or equivalent, but must map to API keys `monthly_limit`, `year_month`)
- Implement per-student/per-month upsert on POST.

### Seam B — Budget API routes

Scope:
- `GET /api/student/budget` returns current month budget limit (nullable when unset)
- `POST /api/student/budget` stores/upserts current month budget
- Keep auth semantics aligned with existing student endpoints (session token in `active_sessions`).

### Seam C — Monthly spend summary

Scope:
- `GET /api/budget-summary` computes current month spend from `Transactions Log` for logged-in student’s money card
- Use defensive number parsing; avoid hard failure on malformed rows
- Exclude non-completed / non-spend rows based on clear rule set

### Seam D — Verification harness

Scope:
- Pytest contract tests for 2xx/4xx/5xx behavior and payload keys
- Verifier script that runs M008 S01 tests plus existing iOS budget failure contract guard

## Critical Constraints / Fragility

- **Import-time DB initialization in `api_server.py`** can break tests if mocks are applied too late.
- **Auth consistency risk**: some API-server routes use direct `token in active_sessions` while others use `_check_session()`. S01 should avoid introducing inconsistent auth behavior across budget routes unless explicitly decided.
- **Data normalization risk**: `Transactions Log` amount/timestamp strings may be inconsistent; parser must tolerate currency symbols/commas and malformed rows.
- **Month boundary correctness**: summary must use PH timezone (`Asia/Manila`) to match app/user expectations.
- **Route compatibility**: iOS expects exact paths and key names; do not rename endpoints or fields.

## Don’t Hand-Roll

Reuse project patterns already present:

- Sheets access/retry/cache helpers from `api_server.py`
- Defensive parse style from `get_transactions()`
- Error envelope/status style from existing student endpoints (`401`, `403`, `404`, `503`, `500`)
- Existing verifier + pytest structure from M007 scripts/tests

## What to Build/Prove First

1. **First proof (highest risk retirement):** backend routes exist and return expected JSON keys.
2. **Second proof:** `Student Budgets` upsert works for create + update within same month.
3. **Third proof:** `budget-summary` computes monthly spend from `Transactions Log` for correct student card.
4. **Fourth proof:** iOS failure/retry state contract remains present (R074 regression guard).

## Verification Strategy

### Minimal automated checks (expected)

- New backend contract tests:
  - valid session → 200 for GET/POST budget + GET summary
  - invalid session → 401
  - missing money card → 404/400 per chosen contract
  - Sheets failures → 503
  - payload keys:
    - budget: `monthly_limit`
    - summary: `monthly_spend`

- Existing iOS contract guard:
  - `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`

### Suggested commands

- `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`
- `rtk proxy sh scripts/verify-m008-s01.sh` (after script is added)

## Skill-Guided Rules Applied

From activated skills:

- **build-iphone-apps / swiftui**
  - “Prove, don’t promise” → planner should require executable verification artifacts, not prose confidence.
  - Small-step loop (`change → verify → next`) for backend + iOS contract safety.

- **api-design-reviewer**
  - Keep REST path stability and status code consistency.
  - Avoid accidental breaking-contract field/path changes.

- **test**
  - Match existing repo test conventions.
  - Mock external dependencies (Sheets) rather than live-calling in CI/harness.

- **senior-backend**
  - Contract-first endpoint design and defensive error handling at API boundary.

## Skills Discovered

Relevant installed skills already available and used for guidance:

- `build-iphone-apps`
- `swiftui`
- `senior-backend`
- `api-design-reviewer`
- `test`
- `best-practices`

Discovery attempts for additional skills:

- `rtk proxy npx skills find "Flask"` and `rtk proxy npm exec skills find "Flask"`
- **Blocked**: `npx`/`npm` unavailable in this environment (`program not found`)

No new skills were installed during this slice research.

## Blockers / Environment Notes

1. **Local skill discovery tooling unavailable** (`npx`/`npm` missing) — recorded above.
2. **Live API runtime checks blocked** in this scout environment due missing Sheets credentials at import time for `backend/api/api_server.py`.
   - Workaround for execution phase: use pre-import mocking of `gspread.service_account` in tests.

## Sources

- `.gsd/milestones/M008-l1ngya/M008-l1ngya-ROADMAP.md` (preloaded)
- `.gsd/milestones/M008-l1ngya/M008-l1ngya-CONTEXT.md` (preloaded)
- `.gsd/DECISIONS.md` (D094, D098 context)
- `.gsd/REQUIREMENTS.md` (R073, R074)
- `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift`
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
- `mobile/ios/BankongSetonStudent/Models/BudgetModels.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift`
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift`
- `backend/api/api_server.py`
- `backend/api/wsgi.py`
- `backend/nfc_payments.py` (sheet-ensure pattern)
- `backend/dashboard/templates/parent_dashboard.html` (existing `monthly_spend` consumer shape)
- `tests/conftest.py` (existing patching/test infra patterns)
- `tests/test_standalone_cashier_app.py` (pre-import mocking pattern)
- `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`
- `scripts/verify-m007-s04.sh`
- `scripts/verify-m007-s07.sh`
