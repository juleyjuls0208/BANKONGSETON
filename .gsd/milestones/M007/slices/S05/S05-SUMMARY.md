---
id: S05
parent: M007
milestone: M007
provides:
  - Stitch-faithful Settings redesign with local persistence for personal-info edits and accent preference across app surfaces.
  - Scope-clean account/settings surface with only in-scope actionable controls and no dead/non-scope settings groups.
  - Deterministic S05 proof surfaces (contracts + phased verifier + UAT result artifact) for downstream integration closure.
requires:
  - S01
  - S02
  - S03
  - S04
affects:
  - R055
  - R056
  - R057
  - R060
  - R061
  - R063
key_files:
  - mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift
  - mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift
  - mobile/ios/BankongSetonStudent/Core/Keychain/KeychainHelper.swift
  - mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift
  - mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift
  - mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift
  - mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift
  - mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift
  - mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift
  - mobile/ios/BankongSetonStudent/App/ContentView.swift
  - tests/test_verify_m007_s05_settings_behavior_contract.py
  - tests/test_verify_m007_s05_settings_design_contract.py
  - scripts/verify-m007-s05.sh
  - .gsd/milestones/M007/slices/S05/S05-UAT.md
  - .gsd/milestones/M007/slices/S05/S05-UAT-RESULT.md
key_decisions:
  - D083: Persist settings-owned accent/personal-info locally and propagate through shared theme/UI seams without backend profile writes.
patterns_established:
  - Keep settings persistence explicit and observable via save/apply state channels (`idle -> applying -> saved`) rather than implicit auto-save behavior.
  - Keep auth/session clear boundaries separate from settings-owned keys so logout/session expiry does not erase user-configured local preferences.
observability_surfaces:
  - scripts/verify-m007-s05.sh (`phase=preflight|behavior-contract|design-contract|static-contract`)
  - tests/test_verify_m007_s05_settings_behavior_contract.py
  - tests/test_verify_m007_s05_settings_design_contract.py
  - .gsd/milestones/M007/slices/S05/S05-UAT-RESULT.md
drill_down_paths:
  - .gsd/milestones/M007/slices/S05/tasks/T01-SUMMARY.md
  - .gsd/milestones/M007/slices/S05/tasks/T02-SUMMARY.md
  - .gsd/milestones/M007/slices/S05/tasks/T03-SUMMARY.md
  - .gsd/milestones/M007/slices/S05/tasks/T04-SUMMARY.md
duration: 5h 50m
verification_result: partial
completed_at: 2026-03-23T09:13:00+08:00
---

# S05: Settings Rework + Local Persistence + Scope Cleanup

**Delivered local settings persistence and scope-clean account actions with deterministic verifier/UAT evidence and shared-surface propagation.**

## What Happened

S05 replaced the prior settings gap with an end-to-end local persistence path that stays visible in real app surfaces.

- Implemented explicit local persistence channels for display name and accent preference in `SettingsViewModel`, with save/apply transitions and deterministic rehydrate behavior.
- Preserved local settings across auth/session clears by keeping settings-owned keys outside `AuthManager.clearAll()` deletion scope.
- Wired persisted accent + display-name signals into shared shell/button/home surfaces using one normalized accent resolver path (`AppTheme`) and runtime settings-change notifications.
- Rebuilt `SettingsView` into stitch cards with actionable in-scope controls only, while preserving `Report Lost Card` and `Logout` continuity and removing out-of-scope/payment-method controls.
- Added/expanded behavior + design contract tests, phased verifier script, and closure UAT artifacts for reproducible audit evidence.

All claims in this summary are reconciled against `.gsd/milestones/M007/slices/S08/tasks/T01-EVIDENCE-MATRIX.md` plus S05 verifier/UAT artifacts.

## Verification

Evidence captured for S05:

- `rtk proxy sh scripts/verify-m007-s05.sh` → PASS (`preflight`, `behavior-contract`, `design-contract`, `static-contract`).
- `.gsd/milestones/M007/slices/S05/S05-UAT-RESULT.md` → `uatType: artifact-driven`, `verdict: PASS`.

Environment constraints retained in evidence:
- `rtk proxy bash scripts/verify-m007-s05.sh` is not usable on this Windows host (`/bin/bash` unavailable).
- `xcodebuild` is unavailable in this host; simulator/device runtime build proof remains deferred to milestone-final Apple-capable execution.

## Requirements Advanced

- **R060** — delivered local accent/display-name persistence with explicit save/apply controls and cross-surface propagation.
- **R061** — removed non-scope settings groups/actions and retained only in-scope actionable settings/account controls.
- **R055/R056** — rebuilt Settings with stitch primitives and explicit actionability for all visible in-scope controls.
- **R057** — preserved QR-only direction by keeping payment-method management/settings absent.
- **R063** — produced deterministic behavior/design/verifier/UAT evidence surfaces for downstream closure.

## Requirements Validated

- **R060** — validated at artifact level through behavior/design contracts, phased verifier PASS, and S05 UAT-result PASS evidence.
- **R061** — validated at artifact level via forbidden-scope string checks in design/static contracts and UAT-result PASS evidence.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- No product-scope deviation from S05 plan; host-compatible shell/tooling paths were used for artifact closure in this executor.

## Known Limitations

- Apple-tooling runtime proof (`xcodebuild`) is unavailable in this environment and remains required in the final milestone device-readiness gate.

## Follow-ups

- Re-run S05 simulator/device runtime checks in a macOS/iOS-capable environment during final milestone closure.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift` — local settings persistence channels, save/apply transitions, and runtime notification emitters.
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift` — auth/session clear boundary updated to preserve settings-owned keys.
- `mobile/ios/BankongSetonStudent/Core/Keychain/KeychainHelper.swift` — deterministic local read helper for settings rehydrate path.
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift` — stitch-style actionable settings cards with scope-clean controls.
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — normalized accent resolver used by shared surfaces.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — accent-aware shared primary action styling.
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift` — accent-aware tab-shell active state styling.
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift` — persisted display-name continuity resolver.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — display-name continuity consumption path.
- `mobile/ios/BankongSetonStudent/App/ContentView.swift` — root accent environment propagation and update handling.
- `tests/test_verify_m007_s05_settings_behavior_contract.py` — behavior contract guardrails for local persistence and continuity actionability.
- `tests/test_verify_m007_s05_settings_design_contract.py` — design/scope guardrails for stitch/actionable/no-dead-control settings surface.
- `scripts/verify-m007-s05.sh` — one-command phased S05 verifier.
- `.gsd/milestones/M007/slices/S05/S05-UAT.md` — manual closure checklist.
- `.gsd/milestones/M007/slices/S05/S05-UAT-RESULT.md` — authoritative artifact-driven UAT verdict.

## Forward Intelligence

### What the next slice should know
- S05 continuity depends on settings-owned local keys plus shared accent/display-name propagation seams; changing either side can silently regress cross-screen persistence.

### What's fragile
- Key ownership boundaries are regression-prone: deleting settings keys in auth/session clear paths or adding unregistered accent values can break persistence continuity.

### Authoritative diagnostics
- `scripts/verify-m007-s05.sh` plus `.gsd/milestones/M007/slices/S05/S05-UAT-RESULT.md` are the canonical trust surfaces for S05 behavior/design/scope closure.

### What assumptions changed
- Assumption: settings persistence could stay local to Settings screen rendering.
- Actual: persistence must propagate through shared shell/buttons/home to be meaningful for demo continuity and requirement closure.