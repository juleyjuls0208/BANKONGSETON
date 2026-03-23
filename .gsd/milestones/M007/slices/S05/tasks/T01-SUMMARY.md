---
id: T01
parent: S05
milestone: M007
provides:
  - Local-only settings persistence channels for accent and editable display name with explicit save/apply actions.
  - Session-boundary protection so auth clears do not wipe settings-owned keys.
  - Initial S05 behavior/design contract test files for early verification wiring.
key_files:
  - mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift
  - mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift
  - mobile/ios/BankongSetonStudent/Core/Keychain/KeychainHelper.swift
  - mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift
  - tests/test_verify_m007_s05_settings_behavior_contract.py
  - tests/test_verify_m007_s05_settings_design_contract.py
  - .gsd/milestones/M007/slices/S05/S05-PLAN.md
  - .gsd/KNOWLEDGE.md
  - .gsd/DECISIONS.md
key_decisions:
  - Removed APIClient type coupling from SettingsViewModel and routed logout via async closure injection.
  - Preserved settings-owned local keys across AuthManager.clearAll() so session boundaries do not drop settings preferences.
patterns_established:
  - Explicit settings save/apply transition state in the view model (`idle -> applying -> saved`) for inspectable local persistence behavior.
  - Seeded source-contract tests early in the slice and allowed expected partial failures on yet-unimplemented slice surfaces.
observability_surfaces:
  - SettingsViewModel published state transitions (`personalInfoSaveState`, `accentApplyState`)
  - S05 behavior/design pytest contracts in `tests/test_verify_m007_s05_settings_*`
  - Slice verifier phase-marker check added to S05 plan verification commands
duration: 1h20m
verification_result: partial
completed_at: 2026-03-23
blocker_discovered: false
---

# T01: Implement local settings persistence contract for accent and personal info

**Added local-only settings persistence channels for accent/display name, protected them from auth clears, and seeded S05 contract tests with expected partial slice failures.**

## What Happened

Implemented T01 persistence plumbing in `SettingsViewModel` by adding deterministic local keys (`settingsAccentHexKey`, `settingsDisplayNameKey`), local rehydrate on init, explicit actions (`savePersonalInfo()`, `applyAccent(_:)`), and observable save/apply transition states.

To keep the task’s local-only boundary intact, removed direct API client type usage from `SettingsViewModel` and changed logout execution to an injected async action closure; updated `SettingsView` to call that closure with `authManager.logout(apiClient:)`.

Updated `AuthManager.clearAll()` to stop deleting settings-owned preferences and documented the boundary rule in `.gsd/KNOWLEDGE.md`.

Per first-task test requirement, created initial S05 behavior/design contract test files. They intentionally report outstanding slice work (T02/T03/T04 markers) while validating new T01 markers.

Also fixed the pre-flight observability gap by adding a phase-marker diagnostic verification command in `.gsd/milestones/M007/slices/S05/S05-PLAN.md`.

## Verification

Ran T01 must-have checks (required markers, no `APIClient` coupling in `SettingsViewModel`) and an explicit transition-marker check for save/apply state transitions.

Ran the slice-level verification commands from `S05-PLAN.md`. As expected for T01 (intermediate task), the full slice gate is partial:
- S05 pytest contracts run and show the expected not-yet-implemented markers (`resolvedDisplayName`, stitch settings surface).
- `scripts/verify-m007-s05.sh` is not present yet (planned for T04).
- `rtk proxy bash ...` fails in this Windows/WSL-less environment (`/bin/bash` unavailable), consistent with project-known shell constraint.
- `xcodebuild` unavailable in this environment.
- `S05-UAT.md` not present yet (planned for T04).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -c "from pathlib import Path; vm=Path('mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift').read_text(); required=['settingsAccentHexKey','settingsDisplayNameKey','editableDisplayName','selectedAccentHex','savePersonalInfo','applyAccent']; missing=[x for x in required if x not in vm]; assert not missing, missing"` | 0 | ✅ pass | ~0.1s |
| 2 | `rtk proxy python -c "from pathlib import Path; vm=Path('mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift').read_text(); assert 'APIClient' not in vm"` | 0 | ✅ pass | ~0.1s |
| 3 | `rtk proxy python -c "from pathlib import Path; vm=Path('mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift').read_text(); required=['personalInfoSaveState = .applying','personalInfoSaveState = .saved','accentApplyState = .applying','accentApplyState = .saved']; missing=[x for x in required if x not in vm]; assert not missing, missing"` | 0 | ✅ pass | ~0.1s |
| 4 | `rtk proxy python -m pytest -q tests/test_verify_m007_s05_settings_behavior_contract.py tests/test_verify_m007_s05_settings_design_contract.py` | 1 | ❌ fail | 0.34s |
| 5 | `rtk proxy sh scripts/verify-m007-s05.sh` | 127 | ❌ fail | ~0.1s |
| 6 | `rtk proxy bash scripts/verify-m007-s05.sh` | 1 | ❌ fail | ~0.1s |
| 7 | `rtk proxy python -c "import subprocess; p=subprocess.run(['rtk','proxy','sh','scripts/verify-m007-s05.sh'], capture_output=True, text=True); out=(p.stdout or '') + (p.stderr or ''); required=['behavior-contract','design-contract','static-contract']; missing=[x for x in required if x not in out]; assert not missing, missing"` | 1 | ❌ fail | ~0.1s |
| 8 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail | ~0.1s |
| 9 | `rtk proxy python -c "from pathlib import Path; assert Path('.gsd/milestones/M007/slices/S05/S05-UAT.md').exists()"` | 1 | ❌ fail | ~0.1s |

## Diagnostics

- Inspect local persistence contract in `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift` via:
  - key constants: `settingsAccentHexKey`, `settingsDisplayNameKey`
  - state channels: `editableDisplayName`, `selectedAccentHex`
  - transitions: `personalInfoSaveState`, `accentApplyState`
  - actions: `savePersonalInfo()`, `applyAccent(_:)`
- Inspect auth/session boundary in `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift` (`clearAll()` key list + preservation comment).
- Inspect seeded source contracts in:
  - `tests/test_verify_m007_s05_settings_behavior_contract.py`
  - `tests/test_verify_m007_s05_settings_design_contract.py`
- Observability gap pre-flight fix is in `S05-PLAN.md` verification list (phase-marker diagnostic command).

## Deviations

- Added the two S05 source-contract test files in T01 (planned in T04) to satisfy first-task test seeding requirement and enable early contract feedback.
- Updated `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift` in T01 to keep logout flow compiling after removing APIClient coupling from `SettingsViewModel`.
- Patched `S05-PLAN.md` verification section before implementation to satisfy the pre-flight observability-gap requirement.

## Known Issues

- Slice behavior/design contracts are still red for not-yet-implemented T02/T03 markers (`resolvedDisplayName`, stitch settings surface markers).
- `scripts/verify-m007-s05.sh` is still missing (T04 scope).
- `rtk proxy bash scripts/verify-m007-s05.sh` fails in this environment because `/bin/bash` is unavailable.
- `xcodebuild` is unavailable in this environment.
- `.gsd/milestones/M007/slices/S05/S05-UAT.md` is not created yet (T04 scope).

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift` — added deterministic local settings keys, state channels, explicit save/apply actions, and observable transition state.
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift` — protected settings-owned keys from auth/session clear paths.
- `mobile/ios/BankongSetonStudent/Core/Keychain/KeychainHelper.swift` — added `read(forKey:default:)` convenience helper for deterministic local loads.
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift` — rewired logout call to injected async action path.
- `tests/test_verify_m007_s05_settings_behavior_contract.py` — added initial behavior contract checks for settings persistence/auth boundary.
- `tests/test_verify_m007_s05_settings_design_contract.py` — added initial design/scope contract checks for Settings.
- `.gsd/milestones/M007/slices/S05/S05-PLAN.md` — added diagnostic verification step and marked T01 complete.
- `.gsd/KNOWLEDGE.md` — documented auth/session settings-key boundary rule for future tasks.
- `.gsd/DECISIONS.md` — appended D074 documenting settings-key ownership boundary at auth/session clear time.
