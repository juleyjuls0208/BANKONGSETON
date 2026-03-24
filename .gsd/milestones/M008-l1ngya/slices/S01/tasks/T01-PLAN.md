---
estimated_steps: 5
estimated_files: 3
skills_used:
  - qodo-get-rules
  - senior-backend
  - api-design-reviewer
  - test
  - best-practices
---

# T01: Implement Student-Budgets-backed `/api/student/budget` read/write contract

**Slice:** S01 — Budget Contract Restoration (Backend + iOS)
**Milestone:** M008-l1ngya

## Description

Implement the missing budget limit contract in the backend so iOS can reliably read and save monthly limits using a dedicated `Student Budgets` worksheet instead of implicit/stale fallbacks.

## Steps

1. Load repo coding constraints via `qodo-get-rules`, then inspect existing student-route auth/error patterns in `backend/api/api_server.py` to match contract style (`401/404/503/500`) and avoid introducing inconsistent semantics.
2. Add worksheet helper(s) in `backend/api/api_server.py` to get-or-create `Student Budgets` with canonical headers (`StudentID`, `MonthlyLimit`, `YearMonth`, `UpdatedAt`) and invalidate relevant caches after writes.
3. Implement `GET /api/student/budget` using active student session context, current PH month key, and deterministic payload keys (`monthly_limit`, optional month metadata if useful) without changing iOS endpoint names.
4. Implement `POST /api/student/budget` with numeric validation and month-scoped upsert (create new row when absent, update existing row when present) for the same student+month key.
5. Add initial tests in `tests/test_verify_m008_s01_budget_contract.py` covering auth rejection plus create/read/update flow for `/api/student/budget` using pre-import gspread mocking.

## Must-Haves

- [ ] `backend/api/api_server.py` exposes both `GET /api/student/budget` and `POST /api/student/budget`.
- [ ] `Student Budgets` sheet is ensured lazily with stable header shape.
- [ ] POST behavior is upsert-by-student-by-month (no uncontrolled duplicate growth for same month).
- [ ] Route responses preserve iOS field compatibility (`monthly_limit`) and explicit error statuses.
- [ ] New tests fail when auth/path/upsert contract regresses.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "student_budget"`
- `rtk proxy python -m py_compile backend/api/api_server.py`

## Observability Impact

- Signals added/changed: explicit budget contract error paths and route-level diagnostics for sheet create/read/write failures.
- How a future agent inspects this: run `tests/test_verify_m008_s01_budget_contract.py -k "student_budget"` and inspect route helpers in `backend/api/api_server.py`.
- Failure state exposed: invalid session, missing money-card binding, and sheets-unavailable states become deterministic status+JSON responses.

## Inputs

- `backend/api/api_server.py` — current API server with student auth/session patterns but no budget routes.
- `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift` — iOS path contract requiring `/student/budget`.
- `mobile/ios/BankongSetonStudent/Models/BudgetModels.swift` — iOS JSON key contract for `monthly_limit`.

## Expected Output

- `backend/api/api_server.py` — new Student Budgets helper(s) and `/api/student/budget` GET/POST route handlers.
- `tests/test_verify_m008_s01_budget_contract.py` — initial executable contract tests for budget read/write/auth behavior.
