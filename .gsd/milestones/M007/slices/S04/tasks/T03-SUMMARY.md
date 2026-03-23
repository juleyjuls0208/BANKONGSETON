---
id: T03
parent: S04
milestone: M007
provides:
  - One-command S04 verifier (`scripts/verify-m007-s04.sh`) with deterministic `behavior-contract`, `design-contract`, and `static-contract` phases
  - Manual S04 acceptance checklist (`S04-UAT.md`) with PASS/FAIL capture for budget, receipt, and lost-card demo paths
  - Reusable preflight path guards so downstream slices can execute S04 closure without rediscovery
key_files:
  - scripts/verify-m007-s04.sh
  - .gsd/milestones/M007/slices/S04/S04-UAT.md
  - .gsd/milestones/M007/slices/S04/S04-PLAN.md
key_decisions:
  - Keep static guardrails in `verify-m007-s04.sh` as literal-source assertions for required/forbidden markers so regressions fail in a named verifier phase with actionable guidance.
patterns_established:
  - S04 verifier structure mirrors prior slices: preflight file checks → pytest contract phases → static marker enforcement with fail-fast guidance.
  - Manual UAT scenarios are encoded with explicit steps/expected/result blocks and a final sign-off gate.
observability_surfaces:
  - `scripts/verify-m007-s04.sh` phase logs: `behavior-contract`, `design-contract`, `static-contract`
  - `.gsd/milestones/M007/slices/S04/S04-UAT.md` scenario outcomes and sign-off checklist
duration: 1h 06m
verification_result: partial
completed_at: 2026-03-23
blocker_discovered: false
---

# T03: Add one-command S04 verifier and manual acceptance checklist for demo closure

**Added an executable S04 verifier script plus a reusable manual UAT checklist covering budget recovery, receipt continuity/scope-clean rendering, and lost-card success/failure flows.**

## What Happened

I created `scripts/verify-m007-s04.sh` following the S02/S03 verifier pattern with strict preflight guards, explicit verifier phases, and fail-fast guidance output.

The verifier now runs both S04 pytest contracts and enforces static source markers for:
- Budget explicit state/action surfaces and retry channels,
- Lost-card phase/action markers,
- Receipt stable indexed item rendering and scope-clean utility-action absence,
- Navigation continuity anchors from Home/Transactions/Settings.

I authored `.gsd/milestones/M007/slices/S04/S04-UAT.md` as the manual acceptance checklist with concrete simulator/device steps and PASS/FAIL capture for all critical demo scenarios (budget save + recovery, receipt entry continuity + fallback behavior, lost-card success + failure/retry behavior).

I also marked T03 complete in `.gsd/milestones/M007/slices/S04/S04-PLAN.md`.

Qodo rules preflight was checked before edits; local Qodo config is unavailable in this environment (`C:/Users/admin/.qodo/config.json`), so no Qodo rules could be loaded.

## Verification

I ran both slice contract pytest commands directly and they passed.

I ran the required slice verifier command path and xcodebuild command path; both failed in this Windows execution environment due missing `/bin/bash` (WSL/bash) and missing `xcodebuild`.

I additionally validated that the newly created verifier contains the required phase/test/checklist anchors and that the UAT checklist references the exact S04 commands/scenarios.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` | 0 | ✅ pass | 0.31s |
| 2 | `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py` | 0 | ✅ pass | 0.31s |
| 3 | `rtk proxy bash scripts/verify-m007-s04.sh` | 1 | ❌ fail | <1s |
| 4 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail | <1s |
| 5 | `rtk proxy sh -n scripts/verify-m007-s04.sh` | 0 | ✅ pass | <1s |
| 6 | `rtk proxy python -c "from pathlib import Path; import sys; text=Path('scripts/verify-m007-s04.sh').read_text(encoding='utf-8'); required=['run_phase \"behavior-contract\"','run_phase \"design-contract\"','phase=static-contract status=running','tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py','tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py','.gsd/milestones/M007/slices/S04/S04-UAT.md']; missing=[item for item in required if item not in text]; print('missing=' + str(missing)); sys.exit(1 if missing else 0)"` | 0 | ✅ pass | <1s |
| 7 | `rtk proxy python -c "from pathlib import Path; import sys; text=Path('.gsd/milestones/M007/slices/S04/S04-UAT.md').read_text(encoding='utf-8'); required=['rtk proxy bash scripts/verify-m007-s04.sh','rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination \'platform=iOS Simulator,name=iPhone 15\' build','### 1) Budget save success flow','### 5) Receipt fallback item behavior + scope-clean constraints','### 7) Lost-card failure + retry/session coherence']; missing=[item for item in required if item not in text]; print('missing=' + str(missing)); sys.exit(1 if missing else 0)"` | 0 | ✅ pass | <1s |
| 8 | Manual checklist in `.gsd/milestones/M007/slices/S04/S04-UAT.md` | N/A | ❌ fail (not run in harness) | Not run |

## Diagnostics

- Run `scripts/verify-m007-s04.sh` for deterministic phase-level closure signals:
  - `behavior-contract`
  - `design-contract`
  - `static-contract`
- Manual demo validation is captured in `.gsd/milestones/M007/slices/S04/S04-UAT.md` with scenario-by-scenario PASS/FAIL fields and final sign-off gate.

## Deviations

- None to task scope/content. Deliverables match the T03 contract.

## Known Issues

- `rtk proxy bash ...` cannot execute in this environment because `/bin/bash` is unavailable.
- `rtk proxy xcodebuild ...` cannot execute in this environment because `xcodebuild` is not installed.
- Manual simulator/device UAT scenarios are authored but were not executed in this harness session.

## Files Created/Modified

- `scripts/verify-m007-s04.sh` — added one-command S04 verifier with preflight, pytest phases, and static required/forbidden marker checks.
- `.gsd/milestones/M007/slices/S04/S04-UAT.md` — added manual S04 acceptance checklist with explicit scenarios and PASS/FAIL capture structure.
- `.gsd/milestones/M007/slices/S04/S04-PLAN.md` — marked T03 as complete (`[x]`).
