---
estimated_steps: 4
estimated_files: 3
skills_used:
  - qodo-get-rules
  - swiftui
  - best-practices
  - debug-like-expert
  - code-simplifier
---

# T01: Implement local settings persistence contract for accent and personal info

**Slice:** S05 — Settings Rework + Local Persistence + Scope Cleanup
**Milestone:** M007

## Description

Create the local-only persistence contract that S05 depends on by adding deterministic settings state channels for accent and editable personal info. This task establishes explicit save/apply methods and blocks any accidental backend profile-write behavior.

## Steps

1. Add local persistence key constants (`settingsAccentHexKey`, `settingsDisplayNameKey`) and load/save helpers in `SettingsViewModel`.
2. Add explicit settings state and actions (`editableDisplayName`, `selectedAccentHex`, `savePersonalInfo()`, `applyAccent(_:)`) with deterministic local load on init.
3. Update auth/settings boundary handling so local settings values are not unintentionally dropped by session lifecycle paths unless explicitly reset by settings logic.
4. Keep settings persistence local-only; do not introduce API profile update calls from settings state actions.

## Must-Haves

- [ ] `SettingsViewModel` exposes explicit, callable save/apply actions for personal info and accent.
- [ ] Accent and personal info values persist via local storage keys and reload deterministically.
- [ ] No backend profile-write path is introduced in settings persistence logic.

## Verification

- `rtk proxy python -c "from pathlib import Path; vm=Path('mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift').read_text(); required=['settingsAccentHexKey','settingsDisplayNameKey','editableDisplayName','selectedAccentHex','savePersonalInfo','applyAccent']; missing=[x for x in required if x not in vm]; assert not missing, missing"`
- `rtk proxy python -c "from pathlib import Path; vm=Path('mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift').read_text(); assert 'APIClient' not in vm"`

## Observability Impact

- Signals added/changed: explicit save/apply state transitions for local settings persistence.
- How a future agent inspects this: inspect `SettingsViewModel` methods and storage-key constants, then run S05 behavior contract tests.
- Failure state exposed: missing persistence markers or accidental backend write usage is surfaced by contract assertions.

## Inputs

- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift` — current settings state and logout flow baseline.
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift` — auth lifecycle behavior that can clear local values.
- `mobile/ios/BankongSetonStudent/Core/Keychain/KeychainHelper.swift` — existing local persistence utility.

## Expected Output

- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift` — local persistence keys, state, and save/apply methods for accent + personal info.
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift` — session boundary behavior aligned with local settings persistence.
- `mobile/ios/BankongSetonStudent/Core/Keychain/KeychainHelper.swift` — utility support needed for new settings channels.
