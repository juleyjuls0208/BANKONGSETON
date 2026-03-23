---
estimated_steps: 5
estimated_files: 3
skills_used:
  - swiftui
  - frontend-design
  - accessibility
  - make-interfaces-feel-better
  - best-practices
---

# T03: Rework Settings UI to stitch style and remove out-of-scope/dead actions

**Slice:** S05 — Settings Rework + Local Persistence + Scope Cleanup
**Milestone:** M007

## Description

Replace the legacy settings Form with stitch-style groups/components that expose only in-scope, actionable controls. This task delivers the visible S05 UX contract while preserving lost-card and logout continuity.

## Steps

1. Rebuild `SettingsView` layout using stitch visual primitives (cards/fields/buttons) instead of the legacy Form sections.
2. Bind personal-info editing UI to T01 state/actions (`editableDisplayName`, `savePersonalInfo`) and accent picker controls to `selectedAccentHex`/`applyAccent(_:)`.
3. Keep `Report Lost Card` navigation and logout action explicitly wired and visible.
4. Remove all forbidden out-of-scope groups and labels (`Privacy & Security`, `Tuition Auto-Pay`, `Campus Discounts`, payment-method management text).
5. If extracted into additional Swift view files, register those files in `project.pbxproj`.

## Must-Haves

- [ ] Settings visible controls are all actionable (save/apply/navigation/logout) with no decorative dead rows.
- [ ] Forbidden out-of-scope/payment-method strings are absent from settings UI source.
- [ ] Lost-card and logout continuity remain present and wired.

## Verification

- `rtk proxy python -c "from pathlib import Path; t=Path('mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift').read_text(); assert all(x in t for x in ['savePersonalInfo','applyAccent','Report Lost Card','Logout'])"`
- `rtk proxy python -c "from pathlib import Path; t=Path('mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift').read_text(); forbidden=['Privacy & Security','Tuition Auto-Pay','Campus Discounts','Payment Method']; assert all(x not in t for x in forbidden), [x for x in forbidden if x in t]"`

## Inputs

- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift` — current legacy settings UI.
- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift` — persistence actions and state from T01.
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — stitch token/theme usage seam.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — shared action style.
- `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py` — continuity anchor for lost-card settings navigation.

## Expected Output

- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift` — stitch-style, scope-clean, fully actionable settings UI.
- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift` — binding refinements needed by the updated settings interactions.
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj` — source registration updates if new settings subviews are added.

## Observability Impact

- Signals changed: settings UI now surfaces deterministic save/apply state transitions (`personalInfoSaveState`, `accentApplyState`) through visible status/action states.
- Inspection surfaces: `SettingsView.swift` action wiring (`savePersonalInfo`, `applyAccent`, `Report Lost Card`, `Logout`) plus T03 contract commands that assert required markers and forbidden-string absence.
- Failure visibility: if scope cleanup regresses, forbidden labels are caught by static contract checks; if wiring regresses, required marker checks fail.
- Redaction constraints: verification and diagnostics must not print persisted personal-info values; checks remain marker-based.
