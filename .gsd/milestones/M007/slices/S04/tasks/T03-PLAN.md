---
estimated_steps: 4
estimated_files: 4
skills_used:
  - test
  - lint
  - review
  - code-review
---

# T03: Add one-command S04 verifier and manual acceptance checklist for demo closure

**Slice:** S04 — Budget + Receipt + Lost-Card Redesign
**Milestone:** M007

## Description

Close S04 with repeatable proof artifacts: one command to run S04 contract checks plus static guardrails, and a manual acceptance checklist that downstream slices can execute during simulator/device demo validation.

## Steps

1. Author `scripts/verify-m007-s04.sh` following S02/S03 verifier style: preflight file checks, behavior/design pytest phases, and static literal checks for required/forbidden S04 markers.
2. Include static assertions for Budget/Lost-Card state/action markers, receipt scope-clean constraints (utility actions absent), stable receipt iteration marker, and navigation continuity anchors from Home/Transactions/Settings.
3. Write `.gsd/milestones/M007/slices/S04/S04-UAT.md` with explicit manual scenarios (budget save + failure recovery, receipt from home/history, receipt fallback item behavior, lost-card success/failure).
4. Validate the verifier command path and checklist references, then ensure outputs are ready for S06/S07 reuse without additional discovery.

## Must-Haves

- [ ] `scripts/verify-m007-s04.sh` runs both S04 pytest suites and fails fast with actionable guidance.
- [ ] Static checks enforce both required S04 markers and forbidden receipt utility actions.
- [ ] Manual checklist covers all critical S04 demo paths with PASS/FAIL capture structure.
- [ ] Verifier/checklist references only concrete repository paths and executable commands.

## Verification

- `rtk proxy bash scripts/verify-m007-s04.sh`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

## Observability Impact

- Signals added/changed: deterministic S04 verification phases (`behavior-contract`, `design-contract`, `static-contract`) with explicit failure guidance.
- How a future agent inspects this: run `scripts/verify-m007-s04.sh` and follow `.gsd/milestones/M007/slices/S04/S04-UAT.md` scenario outcomes.
- Failure state exposed: missing markers/scope regressions are localized to named verifier phases rather than discovered late during integrated demo.

## Inputs

- `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` — behavior checks produced in T01.
- `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py` — design/scope checks produced in T02.
- `scripts/verify-m007-s03.sh` — reference verifier structure/patterns for phase logging and static checks.
- `.gsd/milestones/M007/slices/S03/S03-UAT.md` — reference manual checklist format.

## Expected Output

- `scripts/verify-m007-s04.sh` — one-command S04 verifier with pytest + static guardrails.
- `.gsd/milestones/M007/slices/S04/S04-UAT.md` — manual S04 acceptance checklist for simulator/device validation.
- `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` — updated/finalized behavior test references used by the verifier.
- `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py` — updated/finalized design test references used by the verifier.
