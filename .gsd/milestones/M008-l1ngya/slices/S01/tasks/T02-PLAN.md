---
estimated_steps: 5
estimated_files: 4
skills_used:
  - qodo-get-rules
  - senior-backend
  - api-design-reviewer
  - test
  - build-iphone-apps
  - swiftui
---

# T02: Implement `/api/budget-summary` monthly spend computation and iOS contract guards

**Slice:** S01 — Budget Contract Restoration (Backend + iOS)
**Milestone:** M008-l1ngya

## Description

Close the second half of the budget contract by implementing spend-segment computation from transaction source data, then lock backend/iOS field-path compatibility with targeted contract tests.

## Steps

1. Extend `backend/api/api_server.py` with `GET /api/budget-summary` using the authenticated student’s linked money card and PH timezone month boundaries.
2. Compute `monthly_spend` from `Transactions Log` using defensive numeric parsing and non-fatal handling of malformed rows; include only rows that represent completed spend events per explicit rules.
3. Keep error semantics consistent with student endpoints (invalid/expired session, missing card mapping, sheets unavailable, unexpected exceptions) and add concise diagnostics without leaking secrets.
4. Expand `tests/test_verify_m008_s01_budget_contract.py` to cover budget-summary happy path, malformed-row tolerance, and failure-path statuses.
5. Add `tests/test_verify_m008_s01_ios_budget_contract.py` asserting iOS still targets `/student/budget` + `/budget-summary`, decodes `monthly_spend`, and keeps retryable budget failure channels wired in viewmodel/view markers.

## Must-Haves

- [ ] `/api/budget-summary` returns `monthly_spend` computed from current PH month transaction data.
- [ ] Malformed transaction rows do not hard-fail summary computation.
- [ ] Error statuses/messages remain explicit and contract-stable for client handling.
- [ ] Backend contract tests cover both success and failure paths for summary.
- [ ] iOS contract-marker tests enforce endpoint + payload-key compatibility and retry visibility hooks.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py`

## Observability Impact

- Signals added/changed: summary-route warnings for skipped malformed rows and explicit failure responses for integration diagnosis.
- How a future agent inspects this: run new backend/iOS contract test files and inspect `budget-summary` logic in `backend/api/api_server.py`.
- Failure state exposed: spend-segment contract drift now appears as deterministic test failures plus explicit API error payloads.

## Inputs

- `backend/api/api_server.py` — T01 budget route foundation and existing transactions parsing patterns.
- `tests/test_verify_m008_s01_budget_contract.py` — initial budget route tests to extend with summary coverage.
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift` — iOS decoder contract for `monthly_spend`.
- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift` — retryable failure-channel contract to keep enforced.

## Expected Output

- `backend/api/api_server.py` — `/api/budget-summary` implementation with defensive month-filtered spend computation.
- `tests/test_verify_m008_s01_budget_contract.py` — expanded backend contract tests including summary/failure-path assertions.
- `tests/test_verify_m008_s01_ios_budget_contract.py` — iOS endpoint/payload/retry-marker contract assertions.
