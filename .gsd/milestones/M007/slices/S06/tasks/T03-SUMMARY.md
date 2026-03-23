---
id: T03
parent: S06
milestone: M007
provides:
  - Deterministic S06 closure artifacts: expanded motion behavior/design contract tests, phased verifier output, and iOS 17+ UAT/profiling checklist.
key_files:
  - .gsd/milestones/M007/slices/S06/S06-PLAN.md
  - tests/test_verify_m007_s06_motion_behavior_contract.py
  - tests/test_verify_m007_s06_motion_design_contract.py
  - scripts/verify-m007-s06.sh
  - .gsd/milestones/M007/slices/S06/S06-UAT.md
key_decisions:
  - S06 verification localizes regressions via explicit verifier phases (`preflight`, `behavior-contract`, `design-contract`, `static-contract`) with required/forbidden marker guidance.
patterns_established:
  - Motion contract tests now pair policy/reduce-motion assertions with actionability markers so UI controls stay testably live while transitions are tuned.
  - Slice verifier static-contract checks enforce both required transition markers and forbidden `repeatForever` markers across all in-scope motion surfaces.
observability_surfaces:
  - scripts/verify-m007-s06.sh
  - tests/test_verify_m007_s06_motion_behavior_contract.py
  - tests/test_verify_m007_s06_motion_design_contract.py
  - .gsd/milestones/M007/slices/S06/S06-UAT.md
  - rtk proxy python -c "import subprocess, re; ... phases=['preflight','behavior-contract','design-contract','static-contract'] ..."
duration: 1h 04m
verification_result: partial
completed_at: 2026-03-23T10:09:58+08:00
blocker_discovered: false
---

# T03: Add S06 contract tests, phased verifier, and iOS 17+ UAT/perf checklist

**Added full S06 motion closure artifacts: expanded behavior/design contracts, a four-phase fail-fast verifier, and an iOS 17+ manual UAT/profiling checklist.**

## What Happened

I verified local S06 state after T01/T02, then upgraded the two S06 contract test files from minimal presence checks into explicit motion-behavior/design contracts.

- `test_verify_m007_s06_motion_behavior_contract.py` now asserts:
  - centralized `AppTheme.Motion` policy markers,
  - Reduce Motion wiring in primitives and stateful screens,
  - tokenized policy consumption in shared primitives, and
  - preserved in-scope control actionability markers across QR/Transactions/Budget/Lost Card/Home.
- `test_verify_m007_s06_motion_design_contract.py` now asserts:
  - explicit state-transition markers per stateful screen,
  - per-screen policy + Reduce Motion branch markers,
  - no `repeatForever` in all in-scope motion surfaces, and
  - required S06 closure artifacts exist.

I implemented `scripts/verify-m007-s06.sh` using fail-fast phase telemetry (`preflight`, `behavior-contract`, `design-contract`, `static-contract`) with required/forbidden literal guidance for localized failures.

I wrote `.gsd/milestones/M007/slices/S06/S06-UAT.md` with default-motion and Reduce Motion scenarios plus iOS 17+ Animation Hitches profiling steps and shell fallback notes.

I then ran task-level and slice-level verification commands and updated `S06-PLAN.md` to mark T03 complete.

## Verification

- Both S06 contract suites pass.
- `scripts/verify-m007-s06.sh` passes via `sh`, with all four phases surfaced and static required/forbidden checks passing.
- Phase-tag telemetry checks (required tags, failure-marker vocabulary, phase-status regex) pass.
- S06 UAT artifact existence check passes.
- Environment-limited checks still fail on this host:
  - `rtk proxy bash ...` fails because `/bin/bash` is unavailable.
  - `xcodebuild`/`xcrun` are unavailable in this Windows harness.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s06_motion_behavior_contract.py tests/test_verify_m007_s06_motion_design_contract.py` | 0 | ✅ pass | 0.85s |
| 2 | `rtk proxy sh scripts/verify-m007-s06.sh` | 0 | ✅ pass | 4.99s |
| 3 | `rtk proxy bash scripts/verify-m007-s06.sh` | 1 | ❌ fail | 1.17s |
| 4 | `rtk proxy python -c "import subprocess; p=subprocess.run(['rtk','proxy','sh','scripts/verify-m007-s06.sh'], capture_output=True, text=True); out=(p.stdout or '') + (p.stderr or ''); required=['preflight','behavior-contract','design-contract','static-contract']; missing=[x for x in required if x not in out]; assert not missing, missing"` | 0 | ✅ pass | 5.06s |
| 5 | `rtk proxy python -c "import subprocess; p=subprocess.run(['rtk','proxy','sh','scripts/verify-m007-s06.sh'], capture_output=True, text=True); out=(p.stdout or '') + (p.stderr or ''); tags=['preflight','behavior-contract','design-contract','static-contract']; missing=[x for x in tags if x not in out]; assert not missing, missing; assert any(marker in out.lower() for marker in ['fail','pass','missing','required','forbidden'])"` | 0 | ✅ pass | 5.04s |
| 6 | `rtk proxy python -c "import subprocess, re; p=subprocess.run(['rtk','proxy','sh','scripts/verify-m007-s06.sh'], capture_output=True, text=True); out=((p.stdout or '') + (p.stderr or '')).lower(); phases=['preflight','behavior-contract','design-contract','static-contract']; missing=[phase for phase in phases if not re.search(rf'{phase}.*(pass|fail|missing|required|forbidden)', out)]; assert not missing, missing"` | 0 | ✅ pass | 5.05s |
| 7 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail | 0.01s |
| 8 | `rtk proxy xcrun xctrace list templates` | 1 | ❌ fail | 0.01s |
| 9 | `rtk proxy python -c "from pathlib import Path; assert Path('.gsd/milestones/M007/slices/S06/S06-UAT.md').exists()"` | 0 | ✅ pass | 0.05s |

## Diagnostics

- Run `rtk proxy sh scripts/verify-m007-s06.sh` to get phase-localized status and guidance (`preflight`, `behavior-contract`, `design-contract`, `static-contract`).
- Use `tests/test_verify_m007_s06_motion_behavior_contract.py` for policy/reduce-motion/actionability regressions.
- Use `tests/test_verify_m007_s06_motion_design_contract.py` for state-transition marker and no-loop restraint regressions.
- Use `.gsd/milestones/M007/slices/S06/S06-UAT.md` for default-motion/Reduce Motion manual validation and iOS 17+ Animation Hitches profiling evidence.

## Deviations

- None.

## Known Issues

- `rtk proxy bash scripts/verify-m007-s06.sh` fails in this host because `/bin/bash` is unavailable.
- `rtk proxy xcodebuild ...` and `rtk proxy xcrun ...` fail in this host because Apple toolchain binaries are unavailable.
- Qodo rules were not loadable in this environment (`~/.qodo/config.json` missing).

## Files Created/Modified

- `tests/test_verify_m007_s06_motion_behavior_contract.py` — Expanded behavior contract coverage for centralized motion policy, Reduce Motion wiring, primitive token usage, and actionability markers.
- `tests/test_verify_m007_s06_motion_design_contract.py` — Expanded design contract coverage for state-transition markers, reduced-motion branches, restraint guardrails, and closure artifact presence.
- `scripts/verify-m007-s06.sh` — Added new fail-fast S06 verifier with four phases and deterministic required/forbidden static checks.
- `.gsd/milestones/M007/slices/S06/S06-UAT.md` — Added iOS 17+ manual UAT checklist (default motion + Reduce Motion + Animation Hitches profiling).
- `.gsd/milestones/M007/slices/S06/S06-PLAN.md` — Marked T03 as complete (`[x]`).
