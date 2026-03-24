---
id: T01
parent: S01
milestone: M008-l1ngya
provides:
  - Student-budget backend contract (`GET/POST /api/student/budget`) with dedicated `Student Budgets` sheet persistence and month-scoped upsert behavior
key_files:
  - backend/api/api_server.py
  - tests/test_verify_m008_s01_budget_contract.py
  - .gsd/milestones/M008-l1ngya/slices/S01/S01-PLAN.md
  - .gsd/KNOWLEDGE.md
  - .gsd/DECISIONS.md
key_decisions:
  - D100 — Use lazy-created `Student Budgets` sheet with canonical headers and student+month upsert key for `/api/student/budget`
patterns_established:
  - Pre-import `gspread.service_account` mocking + post-import `get_sheets_client` patch when testing worksheet-missing retry paths
observability_surfaces:
  - budget-route structured logs (`budget_route_auth_error`, `budget_route_student_guard_failed`, `budget_route_unavailable`, `budget_route_malformed_limit`)
  - tests/test_verify_m008_s01_budget_contract.py
  - .gsd/milestones/M008-l1ngya/slices/S01/S01-PLAN.md verification section
duration: 1h 55m
verification_result: passed
completed_at: 2026-03-24T09:55:00+08:00
blocker_discovered: false
---

# T01: Implement Student-Budgets-backed `/api/student/budget` read/write contract

**Added `/api/student/budget` GET/POST with Student-Budgets month upsert semantics and contract tests for auth/create/update/failure paths.**

## What Happened

Loaded task-relevant skills (qodo-get-rules, backend/API/test best-practice guidance), but Qodo API rules could not be fetched because `~/.qodo/config.json` is missing in this environment.

Applied the required pre-flight fix by updating `.gsd/milestones/M008-l1ngya/slices/S01/S01-PLAN.md` to include an explicit failure-path verification command (`-k "unauthorized or unavailable or malformed"`).

Implemented backend budget contract in `backend/api/api_server.py`:
- Added Student Budgets constants and helpers:
  - `STUDENT_BUDGETS_SHEET_NAME`
  - `STUDENT_BUDGETS_HEADERS`
  - `get_current_ph_year_month()`
  - `invalidate_student_budgets_cache()`
  - `ensure_student_budgets_sheet()` (lazy create + canonical header repair)
  - `resolve_budget_student()` (student exists + money-card binding guard)
  - `parse_budget_limit()`
- Added `GET /api/student/budget`:
  - session auth (`401`)
  - student/money-card guard (`404`)
  - current PH month lookup from `Student Budgets`
  - contract payload includes `monthly_limit` (+ `year_month` metadata)
  - explicit unavailable/unexpected handling (`503/500`)
- Added `POST /api/student/budget`:
  - session auth (`401`)
  - student/money-card guard (`404`)
  - numeric validation of `monthly_limit` (`400`)
  - month-scoped upsert by `(StudentID, YearMonth)` (update existing row, append when absent)
  - cache invalidation after writes
  - explicit unavailable/unexpected handling (`503/500`)

Created `tests/test_verify_m008_s01_budget_contract.py` with pre-import gspread mocking and contract coverage:
- unauthorized GET/POST returns `401`
- create/read/update flow enforces one row per student-month (upsert, no duplicate growth)
- sheets-unavailable path returns `503`
- malformed stored limit is non-fatal and returns `monthly_limit: null`
- missing money-card binding returns `404`

Recorded one new decision (D100) and one non-obvious testing gotcha in `.gsd/KNOWLEDGE.md`.

Marked T01 done in `.gsd/milestones/M008-l1ngya/slices/S01/S01-PLAN.md`.

## Verification

Task-level verification passed for the T01 contract bar (`student_budget` tests + backend compile).

Slice-level verification was also executed as requested; expected partial status on this intermediate task:
- backend budget contract suite passes
- M007 lost-card regression suite passes
- M008 iOS contract suite is not present yet (T02/T03 scope)
- `scripts/verify-m008-s01.sh` cannot execute in this Windows host via `rtk proxy bash` because `/bin/bash` is unavailable

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "student_budget"` | 0 | ✅ pass | 1.41s |
| 2 | `rtk proxy python -m py_compile backend/api/api_server.py` | 0 | ✅ pass | ~0.01s |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "unauthorized or unavailable or malformed"` | 0 | ✅ pass | 1.37s |
| 4 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py` | 0 | ✅ pass | 1.42s |
| 5 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py` | 4 | ❌ fail | 0.01s |
| 6 | `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` | 0 | ✅ pass | 0.63s |
| 7 | `rtk proxy bash scripts/verify-m008-s01.sh` | 1 | ❌ fail | <1s |

## Diagnostics

Inspection/diagnostic surfaces now available for this task:
- Route diagnostics in `backend/api/api_server.py`:
  - `budget_route_auth_error`
  - `budget_route_student_guard_failed`
  - `budget_route_unavailable`
  - `budget_route_unexpected`
  - `budget_route_malformed_limit`
- Contract regression suite:
  - `tests/test_verify_m008_s01_budget_contract.py`
- Slice-level verification now includes explicit failure-path check command in:
  - `.gsd/milestones/M008-l1ngya/slices/S01/S01-PLAN.md`

## Deviations

- Added a pre-flight plan correction before coding (required by prompt): explicit failure-path verification command in S01 plan.
- Added two extra backend contract checks beyond minimum step text (`missing money card` + `malformed stored limit`) to strengthen deterministic failure observability.

## Known Issues

- `tests/test_verify_m008_s01_ios_budget_contract.py` does not exist yet (expected for later tasks in this slice).
- `rtk proxy bash scripts/verify-m008-s01.sh` currently fails on this Windows executor because `/bin/bash` is unavailable via WSL relay.
- Qodo rules API could not be loaded in this environment due missing `~/.qodo/config.json`.

## Files Created/Modified

- `backend/api/api_server.py` — added Student Budgets helpers and `GET/POST /api/student/budget` contract routes with explicit error semantics/logging.
- `tests/test_verify_m008_s01_budget_contract.py` — new contract tests for auth, create/read/update upsert, and failure paths.
- `.gsd/milestones/M008-l1ngya/slices/S01/S01-PLAN.md` — added failure-path verification command and marked T01 as completed.
- `.gsd/KNOWLEDGE.md` — added retry/mocking gotcha for worksheet-not-found test setups.
- `.gsd/DECISIONS.md` — appended D100 decision for Student Budgets persistence contract.
