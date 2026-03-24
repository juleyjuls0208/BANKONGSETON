# S01 Summary — Budget Contract Restoration (Backend + iOS)

## Slice Verdict

**Status:** ✅ Complete  
**Milestone:** M008-l1ngya  
**Slice:** S01 (high risk)  
**Proof level achieved:** Integration-level automated contract proof (no manual iOS device gate required for this slice)

This slice restored the broken budget API boundary by shipping a dedicated backend contract for monthly limit + monthly spend, preserving iOS payload/path compatibility, and retaining explicit retryable failure UX channels.

---

## What S01 Delivered

### 1) Backend monthly budget contract is now real and persistent

Implemented in `backend/api/api_server.py`:

- `GET /api/student/budget`
- `POST /api/student/budget`

Behavior now includes:

- Session auth envelope (`401` on invalid/expired token)
- Student + card binding guard (`404` when student has no money card)
- Dedicated `Student Budgets` worksheet
- Lazy worksheet creation + canonical header repair (`StudentID`, `MonthlyLimit`, `YearMonth`, `UpdatedAt`)
- PH-month scoped upsert (student + month key) to avoid duplicate rows
- Explicit service/unexpected envelopes (`503`/`500`)
- Cache invalidation for budget-sheet reads after writes

### 2) Backend monthly spend contract for budget segment

Implemented in `backend/api/api_server.py`:

- `GET /api/budget-summary`

Behavior now includes:

- Session auth + student/card guard (`401`/`404`)
- PH month window: `[month_start, next_month_start)`
- Spend source: `Transactions Log`
- Spend classification:
  - `Status == Completed`
  - transaction type from `TransactionType` or fallback `Type`
  - spend keywords only (`purchase`, `spend`, `debit`, `payment`)
- Malformed timestamp/amount rows are skipped (not fatal) with warning logs
- Output contract includes `monthly_spend` (+ `year_month`)
- Explicit unavailability/unexpected envelopes (`503`/`500`)

### 3) iOS contract compatibility kept stable

Confirmed against:

- `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift`
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift`

Preserved:

- Endpoint constants: `/student/budget`, `/budget-summary`
- `monthly_spend` decode key in API client
- Parallel segment loading (`budget` + `summary`)
- Explicit retry channels/actions:
  - `loadErrorMessage`
  - `saveErrorMessage`
  - `retryLoad(...)`
  - `retryLastSave(...)`
  - retry controls in BudgetView (`budget-retry-load-button`, `budget-retry-save-button`)

### 4) One-command closure verifier for this slice

Added:

- `scripts/verify-m008-s01.sh`

Verifier phases:

- `preflight`
- `backend-contract`
- `ios-contract`
- `retry-visibility-regression`
- `static-contract`

It fails fast with phase-scoped guidance and validates both pytest suites and high-risk static markers.

---

## Verification Evidence (Executed in this closure pass)

All slice-plan verification checks were executed.

| Command | Result |
|---|---|
| `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py` | ✅ pass |
| `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "unauthorized or unavailable or malformed"` | ✅ pass |
| `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py` | ✅ pass |
| `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` | ✅ pass |
| `rtk proxy bash scripts/verify-m008-s01.sh` | ⚠️ host-shell failure (`/bin/bash` unresolved in this Windows relay) |
| `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s01.sh` | ✅ pass (all verifier phases green) |

Additional observability check executed:

- `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "malformed_row"` ✅ pass

---

## Observability / Diagnostics Confirmed

Runtime diagnostic surfaces are in place and test-verified:

- Budget route logs:
  - `budget_route_auth_error`
  - `budget_route_student_guard_failed`
  - `budget_route_malformed_limit`
  - `budget_route_unavailable`
  - `budget_route_unexpected`
- Budget summary logs:
  - `budget_summary_auth_error`
  - `budget_summary_student_guard_failed`
  - `budget_summary_malformed_row`
  - `budget_summary_unavailable`
  - `budget_summary_unexpected`
- Verifier emits phase-level status + guidance for triage.

---

## Requirement Status Changes

Updated in `.gsd/REQUIREMENTS.md`:

- **R073** → `validated`
- **R074** → `validated`

Validation entries now point to the exact contract and retry-visibility proof commands.

---

## Decisions Captured

Confirmed present:

- **D100** — Student Budgets sheet + student/month upsert contract for `/api/student/budget`
- **D101** — `/api/budget-summary` spend classification and malformed-row skip+warn behavior

Newly appended:

- **D102** — S01 closure verifier uses phased checks + focused static literals for rapid fault localization

---

## Knowledge Added/Carried Forward

Useful non-obvious patterns now codified in `.gsd/KNOWLEDGE.md` for future slices:

- Student-budget sheet tests must patch `get_sheets_client` in addition to pre-import `gspread.service_account` when simulating `WorksheetNotFound`.
- Budget summary must handle mixed transaction schema (`TransactionType` and legacy `Type`) and skip malformed rows with warning logs.
- Windows shell workaround for `.sh` verifiers: run via explicit Git Bash path when `rtk proxy bash` resolves to missing `/bin/bash`.

---

## Handoff to Next Slices

### What downstream slices can now rely on

- A stable backend contract exists for budget limit + spend segments:
  - `GET/POST /api/student/budget`
  - `GET /api/budget-summary`
- iOS budget networking contract remains aligned with backend paths/payloads.
- Retryable budget failure UX is preserved and regression-guarded.
- A deterministic slice verifier exists (`scripts/verify-m008-s01.sh`).

### What this slice intentionally did not cover

- Native tab rollback / shell replacement (S02)
- Home credit-card hero refresh (S03)
- Transactions filter-only + appearance controls (S04)
- Cross-surface speed-first polish (S05)
- Final human on-device acceptance gate (S06)

S01 removes the budget API reliability blocker so the remaining UX rollback/minimalism slices can proceed without hidden budget data ambiguity.
