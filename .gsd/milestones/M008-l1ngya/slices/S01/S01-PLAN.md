# S01: Budget Contract Restoration (Backend + iOS)

**Goal:** Restore reliable budget loading for iOS by implementing the missing backend budget contract (`/api/student/budget`, `/api/budget-summary`) on top of a dedicated `Student Budgets` sheet and preserving explicit retryable failure UX.
**Demo:** A logged-in student can load monthly budget limit + monthly spend, save/update the current-month limit, and when backend reads/writes fail the app surfaces explicit retry paths instead of silent fallback.

## Must-Haves

- Directly satisfy **R073** by implementing `GET /api/student/budget` and `POST /api/student/budget` in `backend/api/api_server.py` with session auth and `Student Budgets` upsert semantics keyed by student + month.
- Directly satisfy **R073** by implementing `GET /api/budget-summary` that returns `monthly_spend` from `Transactions Log` for the authenticated student’s money card using PH month boundaries.
- Directly satisfy **R073** by preserving iOS contract compatibility (`monthly_limit`, `monthly_spend`, endpoint paths) with `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift` and `APIClient.swift`.
- Support **R074** by proving budget failure visibility remains explicit/retryable on iOS (no silent masking) via regression checks tied to existing budget view-model contracts.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "unauthorized or unavailable or malformed"`
- `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`
- `rtk proxy bash scripts/verify-m008-s01.sh`

## Observability / Diagnostics

- Runtime signals: budget-route logs for auth errors, worksheet failures, malformed transaction rows skipped during spend computation, and explicit HTTP status envelopes (`401/404/503/500`).
- Inspection surfaces: `tests/test_verify_m008_s01_budget_contract.py`, `tests/test_verify_m008_s01_ios_budget_contract.py`, `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`, and `scripts/verify-m008-s01.sh` phase output.
- Failure visibility: route-level JSON errors + iOS retry-state contract markers (`loadErrorMessage`, `saveErrorMessage`, retry actions) remain test-enforced.
- Redaction constraints: never log bearer tokens, JWTs, or full student PII in new diagnostics/verifier output.

## Integration Closure

- Upstream surfaces consumed: `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift`, `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`, `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift`, and existing Sheets-backed student/transactions helpers in `backend/api/api_server.py`.
- New wiring introduced in this slice: authenticated student budget contract routes + `Student Budgets` persistence helper + monthly summary contract + one-command verifier spanning backend and iOS contract guards.
- What remains before the milestone is truly usable end-to-end: S02–S06 UX rollback/minimalist composition and final manual on-device acceptance gate.

## Tasks

- [x] **T01: Implement Student-Budgets-backed `/api/student/budget` read/write contract** `est:1h 40m`
  - Why: R073 cannot be met until the missing backend budget limit contract exists with reliable per-student/per-month persistence.
  - Files: `backend/api/api_server.py`, `tests/test_verify_m008_s01_budget_contract.py`, `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift`
  - Do: Add session-authenticated budget helpers/routes in `api_server.py`, including `Student Budgets` worksheet ensure/create, canonical headers, month-keyed lookup, and POST upsert behavior; add initial contract tests for auth + create/update/read path compatibility with iOS endpoint names.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "student_budget"`
  - Done when: `GET/POST /api/student/budget` return stable `monthly_limit` contract fields for valid sessions, reject invalid sessions, and persist month-scoped limit updates without duplicate-row ambiguity.

- [x] **T02: Implement `/api/budget-summary` monthly spend computation and iOS contract guards** `est:1h 30m`
  - Why: R073 requires reliable spend segment loading, and this is the current ambiguity causing iOS budget segment failures.
  - Files: `backend/api/api_server.py`, `tests/test_verify_m008_s01_budget_contract.py`, `tests/test_verify_m008_s01_ios_budget_contract.py`, `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
  - Do: Add `/api/budget-summary` route that computes current PH-month spend from `Transactions Log` for the authenticated student’s money card with defensive parsing/filtering and explicit 401/404/503 semantics; extend backend tests for happy/failure paths; add iOS contract-marker tests for endpoint path constants and `monthly_spend` decoding.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py && rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py`
  - Done when: budget summary returns deterministic `monthly_spend` for current month data, malformed rows are non-fatal, and iOS-side contract markers remain aligned with backend payload/route names.

- [x] **T03: Ship S01 verifier tying backend contract proof to iOS retry-visibility regression checks** `est:55m`
  - Why: Slice closure needs one deterministic command that proves both backend budget contract reliability and R074-visible retry behavior are intact.
  - Files: `scripts/verify-m008-s01.sh`, `tests/test_verify_m008_s01_budget_contract.py`, `tests/test_verify_m008_s01_ios_budget_contract.py`, `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`
  - Do: Create `verify-m008-s01.sh` with preflight guards and phased execution for backend contract tests + iOS contract tests + existing budget failure-visibility regression suite; emit clear per-phase guidance on failures and enforce RTK-prefixed commands.
  - Verify: `rtk proxy bash scripts/verify-m008-s01.sh`
  - Done when: one command passes on green state, fails fast with actionable diagnostics on regressions, and serves as the objective stopping condition for S01 completion.

## Files Likely Touched

- `backend/api/api_server.py`
- `tests/test_verify_m008_s01_budget_contract.py`
- `tests/test_verify_m008_s01_ios_budget_contract.py`
- `scripts/verify-m008-s01.sh`
- `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift`
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
