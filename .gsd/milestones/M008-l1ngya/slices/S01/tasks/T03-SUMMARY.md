---
id: T03
parent: S01
milestone: M008-l1ngya
key_files:
  - scripts/verify-m008-s01.sh
  - tests/test_verify_m008_s01_budget_contract.py
  - tests/test_verify_m008_s01_ios_budget_contract.py
  - tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py
key_decisions:
  - Accepted the existing `scripts/verify-m008-s01.sh` implementation as source-of-truth after local inspection confirmed all T03 must-haves (phased checks, actionable guidance, static contract markers) were present.
  - Executed the canonical S01 `.sh` verifier via explicit Git Bash path when `rtk proxy bash` could not start in this harness, while preserving the verifier script and RTK command contracts unchanged.
duration: ""
verification_result: mixed
completed_at: 2026-03-25T11:23:50.012Z
blocker_discovered: false
---

# T03: Validated the S01 one-command verifier and produced full backend+iOS retry-visibility closure evidence.

**Validated the S01 one-command verifier and produced full backend+iOS retry-visibility closure evidence.**

## What Happened

Activated the required skills (`best-practices`, `build-iphone-apps`, `swiftui`, `test`) and inspected the local T03 artifacts before changing code. `scripts/verify-m008-s01.sh` was already implemented with the expected structure: preflight file guards, three explicit pytest phases (backend contract, iOS contract, retry-visibility regression), static marker assertions for high-risk budget endpoint/retry literals, and phase-scoped failure guidance lines. I verified this against the reference style in `scripts/verify-m007-s04.sh` and the source-contract test suites. No code edits were needed because the planned deliverable already matched the task contract in the current worktree. I then executed the slice/task verification commands and captured evidence. On this Windows harness, the canonical `rtk proxy bash scripts/verify-m008-s01.sh` invocation failed before script startup due missing `/bin/bash` (`execvpe(/bin/bash) failed`), so I ran the same verifier successfully through an explicit Git Bash executor (`rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s01.sh`) and an additional `rtk proxy sh scripts/verify-m008-s01.sh` run, both of which passed all phased checks and static markers. All contract pytest suites passed, including the narrowed failure-path selector and the combined closure suite.

## Verification

Verified the full S01 bar with concrete commands: backend budget contract tests, narrowed unauthorized/unavailable/malformed subset, iOS budget contract markers, and M007/S04 retry-visibility regression suite all passed. The one-command S01 verifier itself passed end-to-end (preflight, backend-contract, ios-contract, retry-visibility-regression, static-contract) when executed via explicit Git Bash path in this environment. Canonical `rtk proxy bash ...` failed due host shell resolution (`/bin/bash` unavailable), not due project code/test regressions.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy bash scripts/verify-m008-s01.sh` | 1 | ❌ fail | 1292ms |
| 2 | `rtk proxy sh scripts/verify-m008-s01.sh` | 0 | ✅ pass | 6473ms |
| 3 | `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s01.sh` | 0 | ✅ pass | 6514ms |
| 4 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py` | 0 | ✅ pass | 3256ms |
| 5 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "unauthorized or unavailable or malformed"` | 0 | ✅ pass | 3169ms |
| 6 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py` | 0 | ✅ pass | 1411ms |
| 7 | `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` | 0 | ✅ pass | 1321ms |
| 8 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py tests/test_verify_m008_s01_ios_budget_contract.py tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` | 0 | ✅ pass | 3373ms |


## Deviations

No source changes were required because `scripts/verify-m008-s01.sh` and referenced contract suites were already compliant in this worktree. Verification command adaptation was required locally: `rtk proxy bash scripts/verify-m008-s01.sh` is not runnable on this host due missing `/bin/bash`, so equivalent `.sh` verifier execution was performed via `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s01.sh` (plus a `rtk proxy sh` parity run).

## Known Issues

Windows-only shell constraint remains: canonical `rtk proxy bash ...` fails where `/bin/bash` is unavailable. Use explicit Git Bash path for `.sh` verifier execution in this environment.

## Files Created/Modified

- `scripts/verify-m008-s01.sh`
- `tests/test_verify_m008_s01_budget_contract.py`
- `tests/test_verify_m008_s01_ios_budget_contract.py`
- `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`
