---
id: T02
parent: S03
milestone: M008-l1ngya
provides: []
requires: []
affects: []
key_files: ["tests/test_verify_m008_s03_ios_home_rollback_contract.py", "scripts/verify-m008-s03.sh", ".gsd/milestones/M008-l1ngya/slices/S03/tasks/T02-SUMMARY.md"]
key_decisions: ["Use explicit phased verifier boundaries to isolate S03 closure failures by contract surface.", "Emit Windows Git Bash fallback guidance for chained S02 execution when /bin/bash portability issues occur.", "Keep marker assertions file-path-aware so contract drift diagnostics are immediately actionable."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Executed task verification commands and slice-level verifier. py_compile passed for the S03 contract test. pytest suite for tests/test_verify_m008_s03_ios_home_rollback_contract.py passed (4/4). scripts/verify-m008-s03.sh passed all phases and successfully chained scripts/verify-m008-s02.sh, which passed rollback/budget/QR/login regression phases."
completed_at: 2026-03-27T11:40:33.374Z
blocker_discovered: false
---

# T02: Added phased S03 verifier chaining S02 guards and tightened Home rollback contract diagnostics with file-path marker context.

> Added phased S03 verifier chaining S02 guards and tightened Home rollback contract diagnostics with file-path marker context.

## What Happened
---
id: T02
parent: S03
milestone: M008-l1ngya
key_files:
  - tests/test_verify_m008_s03_ios_home_rollback_contract.py
  - scripts/verify-m008-s03.sh
  - .gsd/milestones/M008-l1ngya/slices/S03/tasks/T02-SUMMARY.md
key_decisions:
  - Use explicit phased verifier boundaries to isolate S03 closure failures by contract surface.
  - Emit Windows Git Bash fallback guidance for chained S02 execution when /bin/bash portability issues occur.
  - Keep marker assertions file-path-aware so contract drift diagnostics are immediately actionable.
duration: ""
verification_result: passed
completed_at: 2026-03-27T11:40:33.376Z
blocker_discovered: false
---

# T02: Added phased S03 verifier chaining S02 guards and tightened Home rollback contract diagnostics with file-path marker context.

**Added phased S03 verifier chaining S02 guards and tightened Home rollback contract diagnostics with file-path marker context.**

## What Happened

Loaded required skills, inspected S02 verifier conventions, and adapted to local state where the S03 contract test already existed from T01. Updated tests/test_verify_m008_s03_ios_home_rollback_contract.py so required/forbidden marker failures include file path context. Added scripts/verify-m008-s03.sh with required phases (preflight, s03-home-contract, home-qr-continuity, s02-regression-chain), fail-fast behavior, structured phase logs, actionable guidance lines, and explicit Windows Git Bash fallback guidance for /bin/bash portability failures in chained S02 execution.

## Verification

Executed task verification commands and slice-level verifier. py_compile passed for the S03 contract test. pytest suite for tests/test_verify_m008_s03_ios_home_rollback_contract.py passed (4/4). scripts/verify-m008-s03.sh passed all phases and successfully chained scripts/verify-m008-s02.sh, which passed rollback/budget/QR/login regression phases.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m py_compile tests/test_verify_m008_s03_ios_home_rollback_contract.py` | 0 | ✅ pass | 120ms |
| 2 | `rtk proxy python -m pytest -q tests/test_verify_m008_s03_ios_home_rollback_contract.py` | 0 | ✅ pass | 700ms |
| 3 | `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s03.sh` | 0 | ✅ pass | 7600ms |
| 4 | `rtk grep "phase=|guidance=|execvpe\(/bin/bash\) failed|s03-home-contract|home-qr-continuity|s02-regression-chain" scripts/verify-m008-s03.sh` | 0 | ✅ pass | 90ms |


## Deviations

The S03 contract test file already existed from T01, so this task refined diagnostics and added verifier chaining instead of creating the test file from scratch.

## Known Issues

None.

## Files Created/Modified

- `tests/test_verify_m008_s03_ios_home_rollback_contract.py`
- `scripts/verify-m008-s03.sh`
- `.gsd/milestones/M008-l1ngya/slices/S03/tasks/T02-SUMMARY.md`


## Deviations
The S03 contract test file already existed from T01, so this task refined diagnostics and added verifier chaining instead of creating the test file from scratch.

## Known Issues
None.
