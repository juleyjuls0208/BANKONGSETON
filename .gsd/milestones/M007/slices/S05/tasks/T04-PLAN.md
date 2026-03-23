---
estimated_steps: 5
estimated_files: 4
skills_used:
  - test
  - debug-like-expert
  - review
  - best-practices
  - qodo-get-rules
---

# T04: Add S05 behavior/design contracts, verifier script, and UAT closure doc

**Slice:** S05 — Settings Rework + Local Persistence + Scope Cleanup
**Milestone:** M007

## Description

Produce deterministic closure evidence for S05 by adding contract tests, a phase-based verifier script, and a manual UAT checklist. This task turns S05 completion into a mechanical pass/fail gate.

## Steps

1. Create `test_verify_m007_s05_settings_behavior_contract.py` to assert local persistence channels, explicit save/apply actions, local-only semantics (no backend profile writes), and lost-card/logout continuity markers.
2. Create `test_verify_m007_s05_settings_design_contract.py` to assert stitch settings markers and forbidden-scope string absence.
3. Add `scripts/verify-m007-s05.sh` with phases: `preflight`, `behavior-contract`, `design-contract`, `static-contract`.
4. Write `.gsd/milestones/M007/slices/S05/S05-UAT.md` with manual checks for persistence across navigation/relaunch, accent propagation beyond settings, lost-card navigation, and logout actionability.
5. Execute contract tests and verifier script (including Windows shell fallback command path) and ensure failing conditions return non-zero.

## Must-Haves

- [ ] Two S05 pytest contract files exist with deterministic literal assertions.
- [ ] `scripts/verify-m007-s05.sh` fails fast when required markers are missing or forbidden scope leaks appear.
- [ ] `S05-UAT.md` documents runtime validation steps and platform command fallback (`sh` when `/bin/bash` is unavailable).

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s05_settings_behavior_contract.py tests/test_verify_m007_s05_settings_design_contract.py`
- `rtk proxy sh scripts/verify-m007-s05.sh`
- `rtk proxy bash scripts/verify-m007-s05.sh`

## Observability Impact

- Signals added/changed: verifier phase output provides explicit failure localization (`preflight`, `behavior-contract`, `design-contract`, `static-contract`).
- How a future agent inspects this: run the verifier script and contract tests; inspect failing phase output + assertion messages.
- Failure state exposed: missing persistence wiring, scope leakage, and continuity regressions surface as deterministic test/script failures.

## Inputs

- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift` — final S05 settings surface to validate.
- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift` — persistence/action markers to validate.
- `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` — behavior contract style baseline.
- `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py` — design contract style baseline.
- `scripts/verify-m007-s04.sh` — verifier harness style baseline.

## Expected Output

- `tests/test_verify_m007_s05_settings_behavior_contract.py` — S05 behavior contract assertions.
- `tests/test_verify_m007_s05_settings_design_contract.py` — S05 design/scope contract assertions.
- `scripts/verify-m007-s05.sh` — executable S05 verifier harness.
- `.gsd/milestones/M007/slices/S05/S05-UAT.md` — manual acceptance checklist for S05 runtime behavior.
