---
id: T03
parent: S01
milestone: M008-l1ngya
provides:
  - One-command S01 closure verifier (`scripts/verify-m008-s01.sh`) that phases backend budget contract, iOS contract, and retry-visibility regression checks
  - Phase-localized failure guidance and high-risk static marker assertions for budget endpoint constants and retry controls
key_files:
  - scripts/verify-m008-s01.sh
  - .gsd/milestones/M008-l1ngya/slices/S01/S01-PLAN.md
  - tests/test_verify_m008_s01_budget_contract.py
  - tests/test_verify_m008_s01_ios_budget_contract.py
  - tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py
key_decisions:
  - Reuse M007 verifier conventions (preflight + phased `phase=... status=... guidance=...`) and keep static checks narrowly focused on high-risk budget endpoint/retry literals
patterns_established:
  - For cross-surface closure scripts, pair pytest phases with small literal assertions to improve immediate diagnosis without replacing contract tests
observability_surfaces:
  - `scripts/verify-m008-s01.sh` phase output: `phase=preflight|backend-contract|ios-contract|retry-visibility-regression|static-contract`
  - Phase-scoped guidance lines emitted on any failure (`guidance=...`)
  - Existing contract suites: `tests/test_verify_m008_s01_budget_contract.py`, `tests/test_verify_m008_s01_ios_budget_contract.py`, `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`
duration: 42m
verification_result: passed
completed_at: 2026-03-24T08:37:23+08:00
blocker_discovered: false
---

# T03: Ship S01 verifier tying backend contract proof to iOS retry-visibility regression checks

**Added `scripts/verify-m008-s01.sh` as a phased S01 closure gate that proves backend budget contracts, iOS contract markers, and R074 retry-visibility continuity in one run.**

## What Happened

Activated the task-plan skills (`test`, `best-practices`, `build-iphone-apps`, `swiftui`) and reviewed existing verifier patterns (`scripts/verify-m007-s04.sh`) before implementation.

Implemented `scripts/verify-m008-s01.sh` with:
- preflight file guards,
- explicit phases for backend contract, iOS contract, and retry-visibility regression,
- fail-fast phase guidance with actionable next steps,
- RTK-prefixed execution commands,
- concise static assertions for high-risk literals:
  - `APIEndpoints.budget` and `APIEndpoints.budgetSummary` path constants,
  - budget retry button identifiers,
  - retry action wiring (`retryLoad`, `retryLastSave`),
  - retry/failure channels (`loadErrorMessage`, `saveErrorMessage`).

Set executable bit on the new verifier and marked T03 done in `.gsd/milestones/M008-l1ngya/slices/S01/S01-PLAN.md`.

## Verification

Ran all task-level and slice-level verification commands for S01; Python contract suites are green, and verifier behavior was directly validated through phase output.

Host note: `rtk proxy bash ...` remains unavailable in this Windows executor due missing `/bin/bash`; to verify the script behavior end-to-end, `rtk proxy sh scripts/verify-m008-s01.sh` was also executed and passed.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py` | 0 | ✅ pass | 1.57s |
| 2 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "unauthorized or unavailable or malformed"` | 0 | ✅ pass | 1.46s |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py` | 0 | ✅ pass | 0.61s |
| 4 | `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` | 0 | ✅ pass | 0.54s |
| 5 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py tests/test_verify_m008_s01_ios_budget_contract.py tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` | 0 | ✅ pass | 1.66s |
| 6 | `rtk proxy bash scripts/verify-m008-s01.sh` | 1 | ❌ fail | <1s |
| 7 | `rtk proxy sh scripts/verify-m008-s01.sh` | 0 | ✅ pass | ~3s |

## Diagnostics

Primary inspection surface added by this task:
- `scripts/verify-m008-s01.sh`
  - emits phased runtime lines (`phase=... status=running/passed/failed`),
  - emits actionable `guidance=...` lines on any phase failure,
  - disambiguates backend-contract vs iOS-contract vs retry-visibility regression failures.

To inspect quickly, run:
- expected slice command: `rtk proxy bash scripts/verify-m008-s01.sh`
- current host-compatible fallback: `rtk proxy sh scripts/verify-m008-s01.sh`

## Deviations

- Environment-adapted execution for observability verification: in addition to the required `rtk proxy bash ...` invocation (which fails on this host), ran `rtk proxy sh scripts/verify-m008-s01.sh` to verify all verifier phases and static assertions end-to-end.

## Known Issues

- `rtk proxy bash scripts/verify-m008-s01.sh` fails in this Windows host (`execvpe(/bin/bash) failed: No such file or directory`) because `/bin/bash` is unavailable in the relay environment.

## Files Created/Modified

- `scripts/verify-m008-s01.sh` — new phased S01 verifier with preflight checks, contract test phases, static marker assertions, and phase-specific guidance.
- `.gsd/milestones/M008-l1ngya/slices/S01/S01-PLAN.md` — marked T03 as completed (`[x]`).
- `.gsd/milestones/M008-l1ngya/slices/S01/tasks/T03-SUMMARY.md` — recorded execution narrative and verification evidence.
