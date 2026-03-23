---
id: T01
parent: S06
milestone: M007
provides:
  - Centralized `AppTheme.Motion` policy seam with Reduce Motion-aware animation helpers wired into shared primitives.
key_files:
  - .gsd/milestones/M007/slices/S06/S06-PLAN.md
  - .gsd/milestones/M007/slices/S06/tasks/T01-PLAN.md
  - mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift
  - mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift
  - mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift
  - mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift
  - tests/test_verify_m007_s06_motion_behavior_contract.py
  - tests/test_verify_m007_s06_motion_design_contract.py
  - .gsd/DECISIONS.md
key_decisions:
  - D084 (M007/S06): shared primitive motion policy uses `AppTheme.Motion` intents + tokenized durations/curves + built-in `accessibilityReduceMotion` override.
patterns_established:
  - Shared primitives consume a single motion API (`AppTheme.Motion.animation(for:accessibilityReduceMotion:)`) instead of ad hoc `Animation` literals.
  - Card-level motion is opt-in (`isHighlighted`) to avoid dense-list animation cost by default.
observability_surfaces:
  - tests/test_verify_m007_s06_motion_behavior_contract.py
  - tests/test_verify_m007_s06_motion_design_contract.py
  - rtk proxy python -c "...assert 'accessibilityReduceMotion'..."
  - rtk proxy python -m pytest -q tests/test_verify_m007_s06_motion_behavior_contract.py tests/test_verify_m007_s06_motion_design_contract.py
duration: 1h 08m
verification_result: partial
completed_at: 2026-03-23T00:44:00+08:00
blocker_discovered: false
---

# T01: Establish centralized motion policy and Reduce Motion wiring in shared primitives

**Centralized motion policy in `AppTheme` and wired Reduce Motion-aware behavior into `StitchPrimaryButtonStyle`, `StitchTabShell`, and `StitchCard` with restrained primitive-level motion defaults.**

## What Happened

I completed the required pre-flight observability fixes first: added a diagnostic/status-surface verification step to `S06-PLAN.md` and added an `## Observability Impact` section to `T01-PLAN.md`.  
Then I implemented the shared primitive seam by introducing `AppTheme.Motion` (durations, curve mapping, primitive intents, and Reduce Motion override). `StitchPrimaryButtonStyle` and `StitchTabShell` now consume that policy using `@Environment(\.accessibilityReduceMotion)`. `StitchCard` now also consumes the same policy via an opt-in `isHighlighted` state path so dense surfaces stay static by default.  
Because this is the first task and slice contract tests were missing, I created initial S06 contract tests in `tests/` that intentionally gate unfinished downstream scope (stateful screen Reduce Motion wiring and T03 artifacts).

## Verification

Task-level checks passed:
- Shared primitive wiring check (`accessibilityReduceMotion`, motion policy presence, no `repeatForever`) passed.
- `Animation` presence check in `AppTheme.swift` passed.

Slice-level gate ran and is partial (expected for T01):
- New S06 contract tests run and fail on expected unfinished scope (T02/T03).
- Verifier script/UAT checks fail because T03 has not created those artifacts yet.
- macOS-only checks (`bash`, `xcodebuild`, `xcrun`) fail in this Windows execution environment.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -c "from pathlib import Path; ... assert 'accessibilityReduceMotion' in all_text; assert 'motion' in theme.lower(); assert 'repeatForever' not in all_text"` | 0 | ✅ pass | 0.00s |
| 2 | `rtk proxy python -c "from pathlib import Path; txt=Path('mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift').read_text(); assert 'Animation' in txt"` | 0 | ✅ pass | 0.00s |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m007_s06_motion_behavior_contract.py tests/test_verify_m007_s06_motion_design_contract.py` | 1 | ❌ fail | 0.88s |
| 4 | `rtk proxy sh scripts/verify-m007-s06.sh` | 127 | ❌ fail | 0.03s |
| 5 | `rtk proxy bash scripts/verify-m007-s06.sh` | 1 | ❌ fail | 1.29s |
| 6 | `rtk proxy python -c "import subprocess; ... required=['preflight','behavior-contract','design-contract','static-contract']; ..."` | 1 | ❌ fail | 0.03s |
| 7 | `rtk proxy python -c "import subprocess; ... tags=['preflight','behavior-contract','design-contract','static-contract']; ... any(['fail','pass','missing','required','forbidden'])"` | 1 | ❌ fail | 0.03s |
| 8 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail | 0.01s |
| 9 | `rtk proxy xcrun xctrace list templates` | 1 | ❌ fail | 0.01s |
| 10 | `rtk proxy python -c "from pathlib import Path; assert Path('.gsd/milestones/M007/slices/S06/S06-UAT.md').exists()"` | 1 | ❌ fail | 0.00s |

## Diagnostics

- Shared primitive motion policy is inspectable in `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` under `AppTheme.Motion`.
- Reduce Motion branch visibility is explicit in:
  - `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`
  - `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift`
  - `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift`
- Contract/failure surfaces are now present in:
  - `tests/test_verify_m007_s06_motion_behavior_contract.py` (fails until T02 stateful wiring lands)
  - `tests/test_verify_m007_s06_motion_design_contract.py` (fails until T03 verifier/UAT artifacts land)

## Deviations

- Added initial S06 contract tests during T01 (instead of waiting for T03) because first-task execution instructions required creating slice verification test files when missing.
- Added one additional diagnostic verification command to `S06-PLAN.md` pre-flight to satisfy observability-gap requirement.

## Known Issues

- Slice gate is intentionally partial at T01:
  - Stateful screens (`QRPayView`, `TransactionsView`, `BudgetView`, `LostCardView`, `HomeView`) still lack Reduce Motion wiring (T02 scope).
  - `scripts/verify-m007-s06.sh` and `.gsd/milestones/M007/slices/S06/S06-UAT.md` do not exist yet (T03 scope).
- Host capability limits in this environment:
  - `rtk proxy bash ...` fails (`/bin/bash` unavailable on host).
  - `xcodebuild` and `xcrun` are unavailable on this Windows runner.
- `gsd_save_decision` could not persist to DB in this session; decision D084 was appended manually to `.gsd/DECISIONS.md`.

## Files Created/Modified

- `.gsd/milestones/M007/slices/S06/S06-PLAN.md` — Added diagnostic/status-surface verification step in slice Verification list.
- `.gsd/milestones/M007/slices/S06/tasks/T01-PLAN.md` — Added `## Observability Impact` section.
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — Added centralized `AppTheme.Motion` tokens + helper API with Reduce Motion override.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — Wired press feedback to `AppTheme.Motion` + `accessibilityReduceMotion`.
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift` — Wired tab selection transition to `AppTheme.Motion` + `accessibilityReduceMotion`.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift` — Added motion-policy-driven highlight/render behavior with Reduce Motion support.
- `tests/test_verify_m007_s06_motion_behavior_contract.py` — Created initial behavior contract test coverage for motion seam + reduce-motion scope.
- `tests/test_verify_m007_s06_motion_design_contract.py` — Created initial design/observability contract tests for no-loop + artifact presence.
- `.gsd/DECISIONS.md` — Appended D084 for shared primitive motion policy decision.
