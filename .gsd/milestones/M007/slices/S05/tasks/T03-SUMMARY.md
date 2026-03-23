---
id: T03
parent: S05
milestone: M007
provides:
  - Stitch-style Settings surface with actionable personal-info save, accent apply, lost-card navigation, and logout controls.
  - Scope-clean settings UI source with forbidden out-of-scope/payment-method labels removed.
  - Explicit save/apply observability in UI via state-driven status messaging and idle-reset behavior on value edits.
key_files:
  - mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift
  - mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift
  - .gsd/milestones/M007/slices/S05/S05-PLAN.md
  - .gsd/milestones/M007/slices/S05/tasks/T03-PLAN.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Replaced the legacy `Form` with stitch cards and kept only actionable controls to satisfy the S05 scope-clean contract.
  - Reset settings persistence state back to `.idle` on editable value changes so UI status does not remain falsely "saved/applied" before the next explicit action.
patterns_established:
  - Settings action cards follow the existing stitch pattern: `StitchCard` + tokenized typography/colors + explicit CTA buttons.
  - Save/apply observability is now user-visible and deterministic through state-bound status lines and action progress labels.
observability_surfaces:
  - `SettingsView.swift` status surfaces: `settings-personal-info-status`, `settings-accent-status`
  - `SettingsViewModel` state channels: `personalInfoSaveState`, `accentApplyState` (with idle reset on edit)
  - Source-contract checks: `tests/test_verify_m007_s05_settings_behavior_contract.py`, `tests/test_verify_m007_s05_settings_design_contract.py`
duration: 1h35m
verification_result: partial
completed_at: 2026-03-23
blocker_discovered: false
---

# T03: Rework Settings UI to stitch style and remove out-of-scope/dead actions

**Rebuilt Settings into a stitch-style actionable surface with local profile/accent controls, preserved lost-card/logout continuity, and removed out-of-scope dead actions.**

## What Happened

Replaced the old `Form`-based `SettingsView` with a stitch-faithful scroll/card layout using `StitchCard`, `StitchPrimaryButtonStyle`, and `AppTheme` tokens. The new screen exposes only actionable groups:
- Personal info editor bound to `editableDisplayName` + `savePersonalInfo()`
- Appearance controls bound to `selectedTheme` and `selectedAccentHex` + `applyAccent(_)`
- Account actions preserving `NavigationLink("Report Lost Card")` and async `Logout`

To keep save/apply state truthful after edits, updated `SettingsViewModel` so changes to `editableDisplayName` and `selectedAccentHex` reset persistence state back to `.idle` until the user performs the next explicit save/apply action.

Per pre-flight requirements, also patched observability docs:
- strengthened S05 phase-marker verification (`preflight` + contract phases)
- added `## Observability Impact` to `T03-PLAN.md`

Qodo rules pre-check was executed before code edits; no Qodo config was present in this environment (`~/.qodo/config.json` missing), so execution proceeded using established repo patterns.

## Verification

Ran T03 task-plan checks for required wiring markers and forbidden-scope string removal in `SettingsView.swift`.

Ran S05 behavior/design source contracts; both suites now pass with the T03 settings surface in place.

Ran S04 continuity anchor test for settings-to-lost-card navigation; it passes with the required `NavigationLink("Report Lost Card")` marker retained.

Ran observability marker check to confirm UI contains save/apply state surfaces and identifiers.

Ran the slice-level verification list from `S05-PLAN.md`; expected partial status remains because T04 artifacts are still pending (`scripts/verify-m007-s05.sh`, `S05-UAT.md`) and this Windows harness still lacks `/bin/bash` and `xcodebuild`.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -c "from pathlib import Path; t=Path('mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift').read_text(); assert all(x in t for x in ['savePersonalInfo','applyAccent','Report Lost Card','Logout'])"` | 0 | ✅ pass | ~0.1s |
| 2 | `rtk proxy python -c "from pathlib import Path; t=Path('mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift').read_text(); forbidden=['Privacy & Security','Tuition Auto-Pay','Campus Discounts','Payment Method']; assert all(x not in t for x in forbidden), [x for x in forbidden if x in t]"` | 0 | ✅ pass | ~0.1s |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m007_s05_settings_behavior_contract.py tests/test_verify_m007_s05_settings_design_contract.py` | 0 | ✅ pass | ~0.31s |
| 4 | `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py -k navigation_continuity_anchors_remain_for_home_transactions_and_settings_entrypoints` | 0 | ✅ pass | ~0.31s |
| 5 | `rtk proxy python -c "from pathlib import Path; t=Path('mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift').read_text(); required=['personalInfoSaveState','accentApplyState','settings-personal-info-status','settings-accent-status','Save Personal Info','Apply Accent']; missing=[x for x in required if x not in t]; assert not missing, missing"` | 0 | ✅ pass | ~0.1s |
| 6 | `rtk proxy sh scripts/verify-m007-s05.sh` | 127 | ❌ fail | ~0.1s |
| 7 | `rtk proxy bash scripts/verify-m007-s05.sh` | 1 | ❌ fail | ~0.1s |
| 8 | `rtk proxy python -c "import subprocess; p=subprocess.run(['rtk','proxy','sh','scripts/verify-m007-s05.sh'], capture_output=True, text=True); out=(p.stdout or '') + (p.stderr or ''); required=['preflight','behavior-contract','design-contract','static-contract']; missing=[x for x in required if x not in out]; assert not missing, missing"` | 1 | ❌ fail | ~0.1s |
| 9 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail | ~0.1s |
| 10 | `rtk proxy python -c "from pathlib import Path; assert Path('.gsd/milestones/M007/slices/S05/S05-UAT.md').exists()"` | 1 | ❌ fail | ~0.1s |

## Diagnostics

- UI source seam: `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`
  - cards: `personalInfoCard`, `appearanceCard`, `accountActionsCard`
  - action wiring: `savePersonalInfo`, `applyAccent`, `NavigationLink("Report Lost Card")`, `Logout`
  - observability markers: `settings-personal-info-status`, `settings-accent-status`
- Runtime state seam: `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift`
  - save/apply channels: `personalInfoSaveState`, `accentApplyState`
  - idle-reset behavior on edit via `didSet` for `editableDisplayName` and `selectedAccentHex`

## Deviations

- Added `didSet` idle-reset behavior in `SettingsViewModel` to keep save/apply UI status truthful after edits; this was a local refinement beyond the plan’s minimum wiring requirements.
- Applied pre-flight observability patches to planning artifacts before runtime edits (`S05-PLAN.md` diagnostic marker expansion and `T03-PLAN.md` observability section).

## Known Issues

- `scripts/verify-m007-s05.sh` is not present yet (planned in T04), so shell verifier checks remain red.
- `rtk proxy bash ...` fails in this environment due missing `/bin/bash` (WSL unavailable).
- `xcodebuild` is not installed in this Windows harness.
- `.gsd/milestones/M007/slices/S05/S05-UAT.md` is not created yet (planned in T04).

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift` — replaced legacy `Form` with stitch cards and actionable settings controls bound to local persistence actions.
- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift` — added idle-reset behavior for save/apply state when editable values change.
- `.gsd/milestones/M007/slices/S05/S05-PLAN.md` — strengthened phase-marker diagnostic verification and marked T03 complete.
- `.gsd/milestones/M007/slices/S05/tasks/T03-PLAN.md` — added `## Observability Impact` section per pre-flight requirement.
- `.gsd/KNOWLEDGE.md` — appended settings save/apply idle-reset rule for future agents.
