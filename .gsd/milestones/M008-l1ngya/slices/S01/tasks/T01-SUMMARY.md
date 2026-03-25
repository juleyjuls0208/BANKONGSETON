---
id: T01
parent: S01
milestone: M008-l1ngya
key_files:
  - backend/api/api_server.py
  - tests/test_verify_m008_s01_budget_contract.py
  - tests/test_verify_m008_s01_ios_budget_contract.py
  - scripts/verify-m008-s01.sh
  - mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift
key_decisions:
  - Did not rewrite already-compliant backend contract code; treated existing implementation as source of truth and validated it against T01/slice verification bars.
  - Recorded shell execution portability explicitly: used `rtk proxy sh` as a host-level fallback to execute the same verifier phases when `rtk proxy bash` was unavailable.
duration: ""
verification_result: mixed
completed_at: 2026-03-25T11:06:12.529Z
blocker_discovered: false
---

# T01: Validate and finalize the Student Budgets-backed /api/student/budget read/write contract with full backend+iOS verification evidence.

**Validate and finalize the Student Budgets-backed /api/student/budget read/write contract with full backend+iOS verification evidence.**

## What Happened

Activated the required skills (api-design-reviewer, best-practices, qodo-get-rules, senior-backend, test), then inspected the local task/slice plans and the current backend/iOS contract files before making changes. Local reality check showed the planned T01 deliverables were already implemented in this worktree: `backend/api/api_server.py` already contains `Student Budgets` helpers (`ensure_student_budgets_sheet`, canonical headers, cache invalidation), `GET /api/student/budget`, and `POST /api/student/budget` month-scoped upsert handlers with explicit `401/404/503/500` envelopes and route-level diagnostics; `tests/test_verify_m008_s01_budget_contract.py` already includes pre-import gspread-mocked auth rejection + create/read/update upsert contract coverage. Instead of rewriting already-correct behavior, execution focused on strict verification against the task and slice bars, including observability/failure-path checks and iOS contract continuity tests. All Python/pytest verification checks passed. The only failing command was environment-specific (`rtk proxy bash scripts/verify-m008-s01.sh`) due missing `/bin/bash` on this Windows host; the same verifier was then run via `rtk proxy sh scripts/verify-m008-s01.sh` and passed end-to-end (backend contract, iOS contract, retry-visibility regression, static markers). No code changes were required because the implementation contract was already satisfied and verified.

## Verification

Ran task-level checks: (1) `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "student_budget"` (pass) to validate `/api/student/budget` auth + create/read/update upsert flow; (2) `rtk proxy python -m py_compile backend/api/api_server.py` (pass) for syntax integrity. Ran full slice verification suite: full backend contract file, unauthorized/unavailable/malformed subset, iOS budget contract markers, M007 retry/lost-card regression suite, and the one-command verifier script. Observability requirements were exercised through the contract tests that assert deterministic status envelopes and malformed-row handling/log-path behavior. Shell portability issue was verified as environmental: `rtk proxy bash ...` failed from missing `/bin/bash`, while equivalent `rtk proxy sh scripts/verify-m008-s01.sh` passed all verifier phases.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "student_budget"` | 0 | ✅ pass | 1680ms |
| 2 | `rtk proxy python -m py_compile backend/api/api_server.py` | 0 | ✅ pass | 120ms |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py` | 0 | ✅ pass | 1740ms |
| 4 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "unauthorized or unavailable or malformed"` | 0 | ✅ pass | 1590ms |
| 5 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py` | 0 | ✅ pass | 700ms |
| 6 | `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` | 0 | ✅ pass | 600ms |
| 7 | `rtk proxy bash scripts/verify-m008-s01.sh` | 1 | ❌ fail | 140ms |
| 8 | `rtk proxy sh scripts/verify-m008-s01.sh` | 0 | ✅ pass | 3900ms |


## Deviations

Task plan expected implementation edits; local code already contained the required T01 backend routes/helpers/tests, so no additional source edits were necessary. Also, slice command `rtk proxy bash scripts/verify-m008-s01.sh` could not execute on this host due missing `/bin/bash`; executed equivalent verifier via `rtk proxy sh scripts/verify-m008-s01.sh` to complete the same gate logic.

## Known Issues

Environment-only issue: `rtk proxy bash ...` fails on this Windows runner when `/bin/bash` is unavailable. Product/backend/iOS contract behavior is green under direct pytest checks and `rtk proxy sh scripts/verify-m008-s01.sh`.

## Files Created/Modified

- `backend/api/api_server.py`
- `tests/test_verify_m008_s01_budget_contract.py`
- `tests/test_verify_m008_s01_ios_budget_contract.py`
- `scripts/verify-m008-s01.sh`
- `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift`
