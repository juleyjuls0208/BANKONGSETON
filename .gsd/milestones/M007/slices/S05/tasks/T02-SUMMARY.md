---
id: T02
parent: S05
milestone: M007
provides:
  - Shared accent resolution via `AppTheme.accentColor(for:)` and app-level accent environment propagation from persisted settings.
  - Reactive shared-surface accent consumption in `StitchTabShell` and `StitchPrimaryButtonStyle`.
  - Home display-name continuity channel (`resolvedDisplayName`) with persisted-settings override and deterministic fallback.
key_files:
  - mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift
  - mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift
  - mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift
  - mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift
  - mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift
  - mobile/ios/BankongSetonStudent/App/ContentView.swift
  - mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift
  - .gsd/milestones/M007/slices/S05/S05-PLAN.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Propagated persisted accent through a root environment channel (`appAccentHex`) plus settings-change notifications instead of coupling shared primitives to `SettingsViewModel` instances.
patterns_established:
  - Deterministic accent fallback path: persisted hex is normalized and validated against known palette values before shared-surface rendering.
  - Deterministic display-name fallback path: persisted settings override → auth/backend name → cached student name → `"Student"`.
observability_surfaces:
  - `Notification.Name.settingsAccentDidChange` and `Notification.Name.settingsDisplayNameDidChange` event channels.
  - Source-level resolver seams in `AppTheme`, `HomeViewModel.resolvedDisplayName`, and shared shell/button primitives.
  - Slice contract checks via S05 pytest/static verification commands.
duration: 1h35m
verification_result: partial
completed_at: 2026-03-23
blocker_discovered: false
---

# T02: Wire reactive accent and persisted display name into shared app surfaces

**Added app-wide persisted accent propagation and home display-name fallback wiring so settings state now drives shared shell/button styling and home identity rendering.**

## What Happened

Implemented a reusable accent resolver seam in `AppTheme` (`normalizedAccentHex`, `accentColor(for:)`, `accentSecondaryColor(for:)`) and introduced an app-level environment key (`appAccentHex`) so shared primitives can read one resolved accent channel.

Wired `StitchPrimaryButtonStyle` and `StitchTabShell` to consume the resolved accent channel instead of hardcoded brand-only colors for active/primary surfaces.

Added runtime settings-change notifications in `SettingsViewModel` for accent/profile saves, then consumed the accent signal in `ContentView` to keep root composition reactive to persisted settings updates.

Added `HomeViewModel.resolvedDisplayName` with deterministic fallback (persisted settings override first, then backend/auth name, then cached name, then `Student`) and wired `HomeView` to use that channel with refresh on auth-name and settings-change events.

Pre-flight observability gap check was already satisfied in `S05-PLAN.md` from prior task work (diagnostic phase-marker command present), so no additional pre-flight patch was needed in this unit.

## Verification

Ran T02 must-have commands to confirm resolver marker presence and home `resolvedDisplayName` seam.

Ran an explicit observability wiring assertion for root accent propagation and settings-change notification channels.

Ran the full slice verification list from `S05-PLAN.md`. As expected for mid-slice execution, T03/T04-dependent checks remain red (stitch settings design markers, verifier script, UAT doc), and environment-dependent commands still fail in this Windows harness (`/bin/bash`, `xcodebuild`).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -c "from pathlib import Path; theme=Path('mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift').read_text(); shell=Path('mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift').read_text().lower(); btn=Path('mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift').read_text().lower(); assert 'accentColor(for' in theme; assert 'accent' in shell and 'accent' in btn"` | 0 | ✅ pass | ~0.1s |
| 2 | `rtk proxy python -c "from pathlib import Path; vm=Path('mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift').read_text(); assert 'resolvedDisplayName' in vm"` | 0 | ✅ pass | ~0.1s |
| 3 | `rtk proxy python -c "from pathlib import Path; content=Path('mobile/ios/BankongSetonStudent/App/ContentView.swift').read_text(); settings_vm=Path('mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift').read_text(); home=Path('mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift').read_text(); assert 'appThemeAccentHex' in content; assert 'settingsAccentDidChange' in content and 'settingsAccentDidChange' in settings_vm; assert 'settingsDisplayNameDidChange' in settings_vm and 'settingsDisplayNameDidChange' in home"` | 0 | ✅ pass | ~0.1s |
| 4 | `rtk proxy python -m pytest -q tests/test_verify_m007_s05_settings_behavior_contract.py tests/test_verify_m007_s05_settings_design_contract.py` | 1 | ❌ fail | 0.34s |
| 5 | `rtk proxy sh scripts/verify-m007-s05.sh` | 127 | ❌ fail | ~0.1s |
| 6 | `rtk proxy bash scripts/verify-m007-s05.sh` | 1 | ❌ fail | ~0.1s |
| 7 | `rtk proxy python -c "import subprocess; p=subprocess.run(['rtk','proxy','sh','scripts/verify-m007-s05.sh'], capture_output=True, text=True); out=(p.stdout or '') + (p.stderr or ''); required=['behavior-contract','design-contract','static-contract']; missing=[x for x in required if x not in out]; assert not missing, missing"` | 1 | ❌ fail | ~0.1s |
| 8 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail | ~0.1s |
| 9 | `rtk proxy python -c "from pathlib import Path; assert Path('.gsd/milestones/M007/slices/S05/S05-UAT.md').exists()"` | 1 | ❌ fail | ~0.1s |

## Diagnostics

- Accent resolver + fallback inspection:
  - `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
  - `normalizedAccentHex(_:)`, `accentColor(for:)`, `accentSecondaryColor(for:)`, `appAccentHex` environment value.
- Shared-surface accent consumption:
  - `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift`
  - `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`
- Runtime update channels:
  - `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift` notification posts (`settingsAccentDidChange`, `settingsDisplayNameDidChange`)
  - `mobile/ios/BankongSetonStudent/App/ContentView.swift` notification consumption + keychain reload fallback.
- Home display-name fallback seam:
  - `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift` (`resolvedDisplayName`, `refreshResolvedDisplayName`, `resolveDisplayName`).

## Deviations

- Used `SettingsViewModel` notification channels to bridge persisted changes into root/shared surfaces within this task, instead of introducing a new dedicated global settings store type.

## Known Issues

- `tests/test_verify_m007_s05_settings_design_contract.py` still fails on missing `SettingsView` stitch markers (`StitchCard`, persistence controls) — expected T03 work.
- `scripts/verify-m007-s05.sh` is still missing — planned for T04.
- `rtk proxy bash ...` fails in this environment because `/bin/bash` is unavailable.
- `xcodebuild` is unavailable in this environment.
- `.gsd/milestones/M007/slices/S05/S05-UAT.md` does not exist yet — planned for T04.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — added normalized persisted-accent resolver APIs and root accent environment key/value helper.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — switched primary button gradient styling to resolved accent channel.
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift` — switched active-tab styling to resolved accent channel.
- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift` — normalized persisted accent writes and emitted accent/display-name change notifications.
- `mobile/ios/BankongSetonStudent/App/ContentView.swift` — wired root composition to persisted accent with notification-driven updates and keychain fallback reload.
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift` — added `resolvedDisplayName` with deterministic persisted/fallback resolution.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — bound display-name UI to `resolvedDisplayName` and refresh triggers.
- `.gsd/milestones/M007/slices/S05/S05-PLAN.md` — marked T02 as completed.
- `.gsd/KNOWLEDGE.md` — documented resolver-map alignment rule for future Settings accent-option updates.
