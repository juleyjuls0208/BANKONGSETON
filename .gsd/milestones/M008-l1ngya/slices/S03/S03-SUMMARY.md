---
id: S03
parent: M008-l1ngya
milestone: M008-l1ngya
provides:
  - Minimalist credit-card Home hero rollback without breaking QR success continuity behavior.
  - Canonical S03 one-command verifier that proves Home rollback + continuity + chained S02 regression safety.
requires:
  - slice: S02
    provides: Native TabView rollback baseline and `scripts/verify-m008-s02.sh` regression guard phases chained by S03 verifier.
affects:
  - S04
  - S05
key_files:
  - mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift
  - tests/test_verify_m008_s03_ios_home_rollback_contract.py
  - scripts/verify-m008-s03.sh
  - .gsd/milestones/M008-l1ngya/slices/S03/S03-PLAN.md
  - .gsd/milestones/M008-l1ngya/slices/S03/tasks/T02-PLAN.md
  - .gsd/DECISIONS.md
  - .gsd/KNOWLEDGE.md
  - .gsd/PROJECT.md
key_decisions:
  - Keep Home rollback visual-only and preserve QR continuity seam internals unchanged.
  - Use phased verifier boundaries and chain S02 guards so Home rollback cannot pass in isolation.
  - Use no-space Git Bash short-path invocation (`C:/Progra~1/Git/bin/bash.exe`) for plan-level verify commands in Windows automation.
patterns_established:
  - Rollback-with-seam-preservation: simplify SwiftUI surface composition while locking continuity callback/tick contracts with targeted regression tests.
  - Phased verifier chaining: local slice contract phases first, then upstream guard-chain phases for inherited boundaries.
  - Windows-safe verifier invocation: avoid quoted spaced executable paths in automation-consumed command strings.
observability_surfaces:
  - `scripts/verify-m008-s03.sh` phase logs (`phase=<name> status=...`) with `guidance=` failure hints.
  - Home/continuity diagnostic markers used by regression contracts (`didConsumePresentedQRSuccess`, continuity tick handoff).
drill_down_paths:
  - .gsd/milestones/M008-l1ngya/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M008-l1ngya/slices/S03/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-03-27T11:47:26.134Z
blocker_discovered: false
---

# S03: Home Rollback + Credit-Card Hero + QR Continuity

**Delivered a minimalist credit-card Home rollback while preserving QR success continuity seams and adding a phased S03 verifier that chains S02 regression guards.**

## What Happened

S03 completed in two steps: Home surface rollback and closure hardening. T01 simplified `HomeView` to a lightweight credit-card hero + recent activity surface, but explicitly kept the QR success seam intact (`didConsumePresentedQRSuccess`, continuity tick increment, and refresh handoff) so cross-screen continuity behavior does not regress during UI rollback. T01 also kept explicit failure recovery visible via an in-card retry path. T02 then hardened closure with `scripts/verify-m008-s03.sh`, a phased verifier that runs preflight, S03 Home rollback contract tests, the targeted M007 continuity-node regression, and finally chains S02 rollback/budget/QR/login guards. During closure we fixed a command-execution fragility in Windows automation by switching plan-level verifier invocation to `C:/Progra~1/Git/bin/bash.exe` (no-space path), which avoids quote-tokenization failures seen with `"C:\Program Files\..."` command strings.

## Verification

Executed all slice-level checks from the plan successfully:
- `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py::test_qr_success_handoff_remains_wired_from_home_sheet_to_refresh_path` (pass)
- `rtk proxy python -m py_compile tests/test_verify_m008_s03_ios_home_rollback_contract.py && rtk proxy C:/Progra~1/Git/bin/bash.exe scripts/verify-m008-s03.sh` (pass)

`verify-m008-s03.sh` passed all phases, including chained `scripts/verify-m008-s02.sh` regression phases (`s02-rollback-contract`, `budget-regression`, `qr-regression`, `login-regression`).

## Requirements Advanced

- R070 — Implemented and contract-verified the Home credit-card hero rollback surface in `HomeView.swift` with S03 rollback marker checks.
- R076 — Preserved and re-verified the QR success continuity seam and chained continuity-node regression checks through the S03 verifier.
- R069 — Kept native TabView rollback guard enforcement active in S03 by chaining `scripts/verify-m008-s02.sh` inside S03 closure.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

- **Health signal**: `scripts/verify-m008-s03.sh` returns `[verify-m008-s03] status=passed` with all phases (`s03-home-contract`, `home-qr-continuity`, `s02-regression-chain`) passing.
- **Failure signal**: Any `phase=<name> status=failed` plus `guidance=` output, or Windows command-path `os error 123` in automation when quoted-space paths are used.
- **Recovery**: Re-run failed phase command directly, restore missing/forbidden markers, then re-run `rtk proxy C:/Progra~1/Git/bin/bash.exe scripts/verify-m008-s03.sh` to confirm closure.
- **Monitoring gaps**: This slice uses source-contract gates only; it does not include runtime telemetry for on-device animation/UX feel regressions.

## Deviations

T01 introduced the initial S03 Home contract test earlier than originally split in plan sequencing (test creation landed before T02). Closure also hardened the T02/S03 plan verifier command to the no-space Git Bash short path for runner compatibility.

## Known Limitations

This slice proves source contracts and verifier-chain behavior only; it does not prove final on-device UX feel/performance acceptance for the Home rollback. Full integrated user-flow validation remains in downstream slices (S05/S06).

## Follow-ups

Carry the no-space Git Bash invocation pattern into downstream M008 plan-level verify commands to avoid command-tokenization failures in automation. In S04/S05, keep `scripts/verify-m008-s03.sh` as an upstream gate before declaring integrated rollback closure.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — Rolled Home to minimalist credit-card hero while preserving QR success callback/tick refresh seam and explicit retry surface.
- `tests/test_verify_m008_s03_ios_home_rollback_contract.py` — Added/maintained Home rollback source-contract checks for required and forbidden markers with actionable diagnostics.
- `scripts/verify-m008-s03.sh` — Added phased S03 verifier and updated Windows invocation strategy to prefer short-path Git Bash for automation-safe execution.
- `.gsd/milestones/M008-l1ngya/slices/S03/S03-PLAN.md` — Updated slice-level verify command to the no-space Git Bash short path.
- `.gsd/milestones/M008-l1ngya/slices/S03/tasks/T02-PLAN.md` — Updated task-level verify guidance/command to no-space Git Bash short path.
- `.gsd/DECISIONS.md` — Appended S03 decisions for seam boundary and Windows verifier invocation pattern.
- `.gsd/KNOWLEDGE.md` — Appended Windows command-tokenization gotcha and short-path verifier rule for future slices.
- `.gsd/PROJECT.md` — Refreshed current-state section to include delivered S03 rollback + verifier-chain capability.
