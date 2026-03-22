---
id: T01
parent: S01
milestone: M007
provides:
  - Shared SwiftUI design-token/primitives foundation (theme + components) with executable source-contract checks
key_files:
  - .gsd/milestones/M007/slices/S01/tasks/T01-PLAN.md
  - mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift
  - mobile/ios/BankongSetonStudent/UI/Theme/Color+Hex.swift
  - mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift
  - mobile/ios/BankongSetonStudent/UI/Components/StitchFieldStyle.swift
  - mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift
  - mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift
  - mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj
  - tests/test_verify_m007_s01_design_system_contract.py
  - .gsd/milestones/M007/slices/S01/S01-PLAN.md
key_decisions:
  - D074 — Centralize semantic SwiftUI tokens in `UI/Theme` and primitives in `UI/Components`, with project wiring + contract tests
patterns_established:
  - Semantic `AppTheme` namespace (Palette/Spacing/Radius/Typography/Shadows) for stitch-faithful reuse
  - Source-contract pytest assertions for UI foundation file/symbol/project-registration regressions
observability_surfaces:
  - tests/test_verify_m007_s01_design_system_contract.py
  - rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build
duration: 1h 12m
verification_result: partial
completed_at: 2026-03-22T20:39:00+08:00
blocker_discovered: false
---

# T01: Establish shared SwiftUI design tokens + primitives contract

**Added a shared SwiftUI theme/primitives foundation (with Xcode project wiring and contract tests) and removed `Color(hex:)` from `TransactionRowView` into shared theme scope.**

## What Happened

I first applied the pre-flight fix by adding the missing `## Observability Impact` section to `.gsd/milestones/M007/slices/S01/tasks/T01-PLAN.md`.

I attempted to load Qodo rules per plan, but local Qodo config was unavailable (`~/.qodo/config.json` missing), so no repository rules could be fetched in this environment.

I inspected the baseline styling duplication in `LoginView.swift`, `HomeView.swift`, and `TransactionRowView.swift`, then implemented the design foundation contract:

- Added `UI/Theme/AppTheme.swift` with semantic tokens for palette, spacing, radius, typography, and shadows.
- Added `UI/Theme/Color+Hex.swift` with shared `Color.init(hex:)`.
- Added primitives:
  - `UI/Components/StitchCard.swift`
  - `UI/Components/StitchFieldStyle.swift`
  - `UI/Components/StitchPrimaryButtonStyle.swift`
- Removed the local `Color(hex:)` extension from `Views/Transactions/TransactionRowView.swift` so color parsing now lives in shared theme scope.
- Updated `BankongSetonStudent.xcodeproj/project.pbxproj` to include all new files in groups + sources.
- Added `tests/test_verify_m007_s01_design_system_contract.py` with assertions for file existence, required symbols, migration of `Color(hex:)`, and Xcode project registration entries.
- Marked T01 complete in `.gsd/milestones/M007/slices/S01/S01-PLAN.md`.

## Verification

Task-level verification:
- `rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py` passed.
- `rtk proxy xcodebuild ... build` failed on this host because `xcodebuild` is not installed (non-macOS environment).

Slice-level verification status for this intermediate task:
- Design-system contract test passes.
- Shell/login contract test is not present yet (expected before T02/T03 work).
- iOS build cannot be executed on this host due missing `xcodebuild` binary.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py` | 0 | ✅ pass | 0.86s |
| 2 | `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py` | 4 | ❌ fail (file not created yet in T01 scope) | 0.51s |
| 3 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination "platform=iOS Simulator,name=iPhone 15" build` | 1 | ❌ fail (`xcodebuild` not found on this environment) | 0.02s |

## Diagnostics

- Theme/primitives contract can be inspected through `tests/test_verify_m007_s01_design_system_contract.py`.
- Project wiring presence is inspectable via `project.pbxproj` entries for `AA000030`–`AA000034`, `BB000030`–`BB000034`, and UI groups `EE000018`–`EE000020`.
- `Color(hex:)` migration visibility: `TransactionRowView.swift` no longer declares `extension Color`; shared implementation is now in `UI/Theme/Color+Hex.swift`.

## Deviations

- `qodo-get-rules` loading could not complete because local Qodo configuration was absent (`~/.qodo/config.json` missing).
- iOS compile verification could not run locally due unavailable `xcodebuild` binary in this environment.

## Known Issues

- `tests/test_verify_m007_s01_shell_login_contract.py` does not exist yet and is expected to be delivered by subsequent tasks in this slice.
- Full iOS build proof remains pending execution on a macOS runner with Xcode installed.

## Files Created/Modified

- `.gsd/milestones/M007/slices/S01/tasks/T01-PLAN.md` — added required `## Observability Impact` section (pre-flight fix).
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — added centralized semantic design tokens and shared shadow helper.
- `mobile/ios/BankongSetonStudent/UI/Theme/Color+Hex.swift` — added shared `Color(hex:)` utility.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift` — added reusable card/surface primitive.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchFieldStyle.swift` — added reusable text input style modifier.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — added reusable primary CTA button style.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` — removed local `Color(hex:)` extension after migration to shared theme.
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj` — registered new UI files in groups and compile sources.
- `tests/test_verify_m007_s01_design_system_contract.py` — added executable design-system contract assertions.
- `.gsd/milestones/M007/slices/S01/S01-PLAN.md` — marked T01 checkbox as complete.
- `.gsd/DECISIONS.md` — appended D074 design-foundation decision for downstream slices.
