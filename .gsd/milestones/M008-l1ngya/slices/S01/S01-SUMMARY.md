---
id: S01
parent: M008-l1ngya
milestone: M008-l1ngya
provides:
  - Stable backend budget contract: `GET /api/student/budget`, `POST /api/student/budget`, `GET /api/budget-summary`.
  - Dedicated `Student Budgets` persistence shape (`student_id`, `monthly_limit`, `year_month`, `updated_at`) with deterministic month-scoped upsert semantics.
  - iOS-compatible budget payload/path continuity (`monthly_limit`, `monthly_spend`) with explicit retry-visible failure channels.
  - Deterministic S01 closure verifier script for downstream integration gating.
requires:
  []
affects:
  - S05
  - S06
key_files:
  - backend/api/api_server.py
  - tests/test_verify_m008_s01_budget_contract.py
  - tests/test_verify_m008_s01_ios_budget_contract.py
  - tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py
  - tests/conftest.py
  - scripts/verify-m008-s01.sh
  - mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift
  - mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift
  - mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift
  - mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift
key_decisions:
  - Use dedicated `Student Budgets` worksheet with canonical headers and student+PH-month upsert semantics for `/api/student/budget`.
  - Compute `monthly_spend` from current PH-month `Transactions Log` rows with `TransactionType`/`Type` fallback and malformed-row skip+warn behavior.
  - Keep closure verification as a phased one-command gate (`scripts/verify-m008-s01.sh`) with phase-scoped diagnostics and high-risk static marker assertions.
  - Preserve canonical `.sh` verifier flow and execute via explicit Git Bash path on Windows when `/bin/bash` is unavailable (recorded as D103).
patterns_established:
  - Contract-first API restoration with explicit auth/not-found/unavailable/unexpected envelopes rather than silent fallback.
  - Monthly spend aggregation resilient to mixed sheet schemas and malformed rows through defensive parsing + warning logs.
  - Cross-platform verifier parity pattern: keep shell verifier canonical for CI/Linux while using explicit Git Bash invocation in Windows harnesses.
  - Pytest wrapper compatibility pattern: normalize one layer of quoted `-k` selectors in repo test configuration hooks.
observability_surfaces:
  - tests/test_verify_m008_s01_budget_contract.py (auth/unavailable/malformed/failure envelope coverage)
  - tests/test_verify_m008_s01_ios_budget_contract.py (iOS endpoint/payload/marker contract guards)
  - tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py (retry-visibility regression checks)
  - scripts/verify-m008-s01.sh phased output: preflight, backend-contract, ios-contract, retry-visibility-regression, static-contract
drill_down_paths:
  - .gsd/milestones/M008-l1ngya/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M008-l1ngya/slices/S01/tasks/T02-SUMMARY.md
  - .gsd/milestones/M008-l1ngya/slices/S01/tasks/T03-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-03-25T11:28:59.078Z
blocker_discovered: false
---

# S01: Budget Contract Restoration (Backend + iOS)

**Restored budget reliability by validating a Student-Budgets-backed backend contract and preserving iOS retry-visible budget loading/saving behavior with deterministic verifier coverage.**

## What Happened

S01 closed the budget reliability gap at the API/data boundary. The slice now provides authenticated `GET /api/student/budget`, `POST /api/student/budget`, and `GET /api/budget-summary` contracts backed by a dedicated `Student Budgets` worksheet and PH-month spend aggregation from `Transactions Log`. Across T01–T03, implementation and contract coverage were verified end-to-end: student/month upsert semantics, stable `monthly_limit` + `monthly_spend` payload fields, explicit 401/404/503/500 envelopes, malformed-row skip-with-warning behavior, and iOS endpoint/decoder/retry marker alignment. The slice also shipped/validated a phased one-command verifier (`scripts/verify-m008-s01.sh`) that localizes failures by phase (preflight/backend/ios/retry/static). During closeout in this Windows harness, canonical `rtk proxy bash ...` remained blocked by missing `/bin/bash`; the same verifier passed through explicit Git Bash invocation, and this execution-path decision was recorded for future agents.

## Verification

Executed all slice-plan verification checks and confirmed green status: `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py`; `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "unauthorized or unavailable or malformed"`; `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py`; `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`; `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s01.sh` (all verifier phases passed). Observability/diagnostic surfaces were confirmed via route-level contract/failure tests plus phased verifier output (including static marker checks and retry-visibility regression suite).

## Requirements Advanced

- R073 — Implemented and verified budget limit + spend loading via dedicated backend routes and Student Budgets persistence with iOS contract parity.
- R074 — Maintained explicit load/save failure channels and retry actions in iOS budget flow, guarded by regression and static contract checks.

## Requirements Validated

- R073 — `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py`; `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py`; `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s01.sh` (all phases pass).
- R074 — `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`; `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "unauthorized or unavailable or malformed"`; retry/static phases in `scripts/verify-m008-s01.sh` pass via Git Bash invocation.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

No major backend/iOS feature rewrites were required during closeout because core S01 implementation was already present; work focused on verification hardening and host-shell execution adaptation. In this harness, `rtk proxy bash scripts/verify-m008-s01.sh` still fails before script startup due missing `/bin/bash`, so explicit Git Bash invocation was used for equivalent verification.

## Known Limitations

Windows hosts without `/bin/bash` cannot run `rtk proxy bash scripts/verify-m008-s01.sh` directly; use `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s01.sh` for parity. Final device-level UX acceptance remains scoped to S06.

## Follow-ups

S05/S06 should keep using the S01 verifier as a prerequisite for integrated acceptance and use explicit Git Bash invocation on Windows executors. S06 manual acceptance should include budget load/save failure-injection checks to confirm user-visible retry behavior remains intact in the final UX.

## Files Created/Modified

- `backend/api/api_server.py` — Added/restored Student Budgets helpers plus `/api/student/budget` and `/api/budget-summary` contract behavior with explicit status envelopes and PH-month spend aggregation.
- `tests/test_verify_m008_s01_budget_contract.py` — Added/maintained backend contract coverage for auth, upsert semantics, unavailable/error envelopes, and malformed-row handling.
- `tests/test_verify_m008_s01_ios_budget_contract.py` — Added/maintained iOS contract marker checks for budget endpoints and payload field compatibility.
- `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` — Retained retry-visibility regression checks used as S01 guardrail evidence.
- `tests/conftest.py` — Normalized one layer of quoted pytest `-k` selectors for wrapper compatibility without changing test intent.
- `scripts/verify-m008-s01.sh` — Implemented/validated phased S01 verifier with preflight checks, actionable failure guidance, and high-risk static contract assertions.
- `.gsd/KNOWLEDGE.md` — Recorded non-obvious verification patterns for Windows shell execution and quoted pytest selector handling.
- `.gsd/DECISIONS.md` — Recorded closeout decision D103 for Windows `.sh` verifier execution fallback via explicit Git Bash path.
