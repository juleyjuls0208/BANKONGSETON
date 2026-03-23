---
id: T04
parent: S05
milestone: M007
provides:
  - Deterministic S05 behavior/design contract suites covering local settings persistence, scope cleanup, and lost-card/logout continuity markers.
  - A phase-based S05 verifier with fail-fast guidance for `preflight`, `behavior-contract`, `design-contract`, and `static-contract` failures.
  - A manual S05 UAT checklist for persistence/relaunch/accent propagation validation with Windows shell fallback guidance.
key_files:
  - tests/test_verify_m007_s05_settings_behavior_contract.py
  - tests/test_verify_m007_s05_settings_design_contract.py
  - scripts/verify-m007-s05.sh
  - .gsd/milestones/M007/slices/S05/S05-UAT.md
  - .gsd/milestones/M007/slices/S05/S05-PLAN.md
key_decisions:
  - Added an explicit `preflight` phase marker in the S05 verifier so missing artifacts fail with immediate, localized diagnostics before tests run.
  - Kept `rtk proxy sh scripts/verify-m007-s05.sh` as the practical execution path on Windows hosts without `/bin/bash`, while preserving `bash` command parity in docs/verification lists.
patterns_established:
  - S05 verifier static guardrails use deterministic literal presence/absence assertions for required settings markers and forbidden scope strings.
  - UAT closure docs pair automated verifier commands with runtime scenario checklists and host-shell fallback notes.
observability_surfaces:
  - `scripts/verify-m007-s05.sh` phase output: `preflight`, `behavior-contract`, `design-contract`, `static-contract`
  - Pytest contract failure messages from `tests/test_verify_m007_s05_settings_behavior_contract.py` and `tests/test_verify_m007_s05_settings_design_contract.py`
  - Manual runtime checklist in `.gsd/milestones/M007/slices/S05/S05-UAT.md`
duration: 1h20m
verification_result: partial
completed_at: 2026-03-23
blocker_discovered: false
---

# T04: Add S05 behavior/design contracts, verifier script, and UAT closure doc

**Added S05 settings contract suites, a phase-localizing verifier script, and a UAT checklist that closes persistence/accent/lost-card/logout validation.**

## What Happened

Expanded the S05 behavior contract to assert the full local-persistence surface (explicit save/apply transitions, local-only semantics, auth clear boundary protection, lost-card/logout continuity markers, and Home/ContentView propagation markers). Tightened the design contract to enforce stitch markers, actionable control identifiers, and forbidden scope-string absence.

Implemented `scripts/verify-m007-s05.sh` with the required phase model (`preflight`, `behavior-contract`, `design-contract`, `static-contract`) plus fail-fast guidance when markers are missing or forbidden strings leak into the settings surface.

Created `.gsd/milestones/M007/slices/S05/S05-UAT.md` with runtime acceptance scenarios for persistence across navigation/relaunch, accent propagation beyond Settings, scope-clean UI, and lost-card/logout actionability, including explicit `sh` fallback when `/bin/bash` is unavailable.

Qodo rules pre-check was executed; no local Qodo configuration was present (`~/.qodo` missing), so execution followed existing repo patterns.

## Verification

Ran the S05 contract suites directly and through the new verifier script. The `sh` verifier path passes and emits all required phase markers.

Ran the slice verification list from `S05-PLAN.md`. Environment-limited checks still fail in this Windows harness (`/bin/bash` missing; `xcodebuild` unavailable). Added an explicit negative-path invocation of the verifier from the wrong working directory to confirm preflight failures return a non-zero exit code.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s05_settings_behavior_contract.py tests/test_verify_m007_s05_settings_design_contract.py` | 0 | ✅ pass | ~0.32s |
| 2 | `rtk proxy sh scripts/verify-m007-s05.sh` | 0 | ✅ pass | ~1.3s |
| 3 | `rtk proxy bash scripts/verify-m007-s05.sh` | 1 | ❌ fail | ~0.1s |
| 4 | `rtk proxy python -c "import subprocess; p=subprocess.run(['rtk','proxy','sh','scripts/verify-m007-s05.sh'], capture_output=True, text=True); out=(p.stdout or '') + (p.stderr or ''); required=['preflight','behavior-contract','design-contract','static-contract']; missing=[x for x in required if x not in out]; assert not missing, missing"` | 0 | ✅ pass | ~1.3s |
| 5 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail | ~0.1s |
| 6 | `rtk proxy python -c "from pathlib import Path; assert Path('.gsd/milestones/M007/slices/S05/S05-UAT.md').exists()"` | 0 | ✅ pass | ~0.1s |
| 7 | `rtk proxy sh -c "cd tests && ../scripts/verify-m007-s05.sh"` *(negative-path preflight check)* | 2 | ✅ pass | ~0.1s |

## Diagnostics

- Run `rtk proxy sh scripts/verify-m007-s05.sh` to get phase-localized status and guidance.
- Behavior/design regressions surface through deterministic marker assertions in:
  - `tests/test_verify_m007_s05_settings_behavior_contract.py`
  - `tests/test_verify_m007_s05_settings_design_contract.py`
- Use `.gsd/milestones/M007/slices/S05/S05-UAT.md` for runtime confirmation on simulator/device without exposing personal-info values in logs.

## Deviations

- Extended static-contract checks to include shared accent propagation markers (`AppTheme` environment key + shell/button consumers) to strengthen the “beyond Settings” closure signal.
- Added an explicit negative-path verifier invocation to prove non-zero fail behavior, which is stricter than the baseline task verification list.

## Known Issues

- `rtk proxy bash scripts/verify-m007-s05.sh` fails in this host because `/bin/bash` is unavailable.
- `rtk proxy xcodebuild ... build` fails in this host because `xcodebuild` is not installed.

## Files Created/Modified

- `tests/test_verify_m007_s05_settings_behavior_contract.py` — expanded S05 behavior contract markers for local-only persistence semantics, continuity actions, and shared-state propagation.
- `tests/test_verify_m007_s05_settings_design_contract.py` — tightened stitch/actionable marker assertions and legacy/out-of-scope leakage checks.
- `scripts/verify-m007-s05.sh` — added phase-based S05 verifier with preflight diagnostics and static contract guardrails.
- `.gsd/milestones/M007/slices/S05/S05-UAT.md` — added manual closure checklist for persistence, relaunch behavior, accent propagation, scope cleanup, and account-action continuity.
- `.gsd/milestones/M007/slices/S05/S05-PLAN.md` — marked T04 complete.
