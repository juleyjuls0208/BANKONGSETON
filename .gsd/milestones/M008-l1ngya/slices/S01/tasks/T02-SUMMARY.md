---
id: T02
parent: S01
milestone: M008-l1ngya
provides:
  - Budget summary backend contract (`GET /api/budget-summary`) with PH-month spend computation from `Transactions Log` and malformed-row-tolerant diagnostics
  - iOS contract-marker regression coverage for `/student/budget` + `/budget-summary` endpoint/payload/retry wiring
key_files:
  - backend/api/api_server.py
  - tests/test_verify_m008_s01_budget_contract.py
  - tests/test_verify_m008_s01_ios_budget_contract.py
  - .gsd/milestones/M008-l1ngya/slices/S01/S01-PLAN.md
  - .gsd/DECISIONS.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - D101 — Classify spend rows using completed-status + spend-type rules (`TransactionType`/`Type`) and skip malformed timestamp/amount rows with warning logs
patterns_established:
  - Budget summary derivation uses `[month_start, next_month_start)` in PH timezone and warns on per-row parse failures instead of failing the entire response
observability_surfaces:
  - backend/api/api_server.py logs: `budget_summary_auth_error`, `budget_summary_student_guard_failed`, `budget_summary_malformed_row`, `budget_summary_unavailable`, `budget_summary_unexpected`
  - tests/test_verify_m008_s01_budget_contract.py (`test_budget_summary_skips_malformed_rows_and_keeps_response_retryable`)
  - tests/test_verify_m008_s01_ios_budget_contract.py
duration: 1h 25m
verification_result: passed
completed_at: 2026-03-24T08:33:19+08:00
blocker_discovered: false
---

# T02: Implement `/api/budget-summary` monthly spend computation and iOS contract guards

**Implemented `/api/budget-summary` PH-month spend contract with malformed-row-tolerant diagnostics, plus backend/iOS regression guards for endpoint/payload/retry compatibility.**

## What Happened

Activated task-relevant skills (`qodo-get-rules`, `senior-backend`, `api-design-reviewer`, `test`, `build-iphone-apps`, `swiftui`). Qodo rules could not be fetched in this environment because `~/.qodo/config.json` is missing.

Verified the pre-flight observability gap requirement was already satisfied in `S01-PLAN.md` (failure-path verification command present), then implemented `GET /api/budget-summary` in `backend/api/api_server.py`:
- session-authenticated (`_check_session`) with explicit `401`
- student/money-card guard reuse via `resolve_budget_student()` with explicit `404`
- PH timezone month-window helpers (`get_current_ph_month_bounds()`)
- spend classification guard (`is_completed_spend_record`) requiring:
  - `Status == Completed`
  - spend-like transaction type keywords from `TransactionType` or legacy `Type`
- defensive parsing for timestamp (`parse_transaction_timestamp`) and amount (`parse_budget_limit`)
- malformed rows are skipped (non-fatal) with structured warnings (`budget_summary_malformed_row ...`)
- explicit `503/500` envelopes with route-scoped diagnostics

Expanded backend contract tests in `tests/test_verify_m008_s01_budget_contract.py`:
- added fixture support for `Transactions Log` sheet
- added happy-path spend aggregation test for current PH month filtering and spend-only classification
- added malformed-row tolerance test that also asserts warning log emission (observability verification)
- added unauthorized/missing-card/unavailable failure-path assertions for `/api/budget-summary`

Created iOS contract-marker suite `tests/test_verify_m008_s01_ios_budget_contract.py` to enforce:
- endpoint constants remain `/student/budget` and `/budget-summary`
- API client still calls those endpoints and decodes `monthly_spend`
- budget view model keeps dual-segment load + retry channels
- budget view still exposes retry controls wired to retry actions

Recorded D101 in `.gsd/DECISIONS.md` and appended a non-obvious transaction-schema gotcha in `.gsd/KNOWLEDGE.md`.

Marked T02 complete in `.gsd/milestones/M008-l1ngya/slices/S01/S01-PLAN.md`.

## Verification

Task-level checks passed (`m008_s01_budget_contract`, `m008_s01_ios_budget_contract`).

Slice-level checks were also executed for this intermediate task:
- all Python verification suites passed
- `rtk proxy bash scripts/verify-m008-s01.sh` failed in this Windows executor because `/bin/bash` is unavailable (known environment constraint; T03 will also add that script)

Observability impact was directly verified by asserting malformed-row warning logs in backend contract tests.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m py_compile backend/api/api_server.py tests/test_verify_m008_s01_budget_contract.py tests/test_verify_m008_s01_ios_budget_contract.py` | 0 | ✅ pass | <0.1s |
| 2 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py` | 0 | ✅ pass | 1.87s |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py` | 0 | ✅ pass | 0.55s |
| 4 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "unauthorized or unavailable or malformed"` | 0 | ✅ pass | 2.08s |
| 5 | `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` | 0 | ✅ pass | 0.78s |
| 6 | `rtk proxy bash scripts/verify-m008-s01.sh` | 1 | ❌ fail | <1s |

## Diagnostics

- Backend summary-route diagnostics now available in `backend/api/api_server.py`:
  - `budget_summary_auth_error`
  - `budget_summary_student_guard_failed`
  - `budget_summary_malformed_row`
  - `budget_summary_unavailable`
  - `budget_summary_unexpected`
- Direct malformed-row observability assertion:
  - `tests/test_verify_m008_s01_budget_contract.py::test_budget_summary_skips_malformed_rows_and_keeps_response_retryable`
- iOS contract inspection surface:
  - `tests/test_verify_m008_s01_ios_budget_contract.py`

## Deviations

- Minor local adaptation: spend classification supports both `TransactionType` and legacy `Type` columns to match mixed transaction-row schemas found in existing writers.

## Known Issues

- `rtk proxy bash scripts/verify-m008-s01.sh` cannot execute in this Windows host because `/bin/bash` is unavailable (`execvpe(/bin/bash) failed`); additionally, this script is planned for T03.
- Qodo rules API could not be loaded in this environment due missing `~/.qodo/config.json`.

## Files Created/Modified

- `backend/api/api_server.py` — added `/api/budget-summary` route, PH month-boundary + timestamp parsing helpers, spend-row classification, and malformed-row diagnostics.
- `tests/test_verify_m008_s01_budget_contract.py` — expanded backend contract suite with summary success/failure/malformed observability assertions.
- `tests/test_verify_m008_s01_ios_budget_contract.py` — new iOS endpoint/payload/retry-marker contract test suite.
- `.gsd/milestones/M008-l1ngya/slices/S01/S01-PLAN.md` — marked T02 as completed (`[x]`).
- `.gsd/DECISIONS.md` — appended D101 budget-summary spend-classification decision.
- `.gsd/KNOWLEDGE.md` — added transaction-schema fallback/skip-and-log guidance for future agents.
