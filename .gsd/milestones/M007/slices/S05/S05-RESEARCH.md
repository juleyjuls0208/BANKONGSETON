# S05 Research — Settings Rework + Local Persistence + Scope Cleanup

**Date:** 2026-03-23  
**Status:** Ready for planning

## Requirement Targeting (Active)

S05 directly owns/supports:

- **Owns:**
  - **R060** — Local persistence for accent color and personal info edit
  - **R061** — Remove non-scope settings/receipt/secondary actions
- **Supports:**
  - **R055** — Stitch-faithful redesign continuity on Settings surface
  - **R056** — No dead controls in visible in-scope UI
  - **R057** — Keep QR-only direction by avoiding payment-method settings UI
  - **R063** — Demo readiness continuity (settings flow must be coherent in full app journey)

## Summary

This slice is **targeted research** (known SwiftUI stack, moderate integration risk due cross-screen accent propagation and persistence boundaries).

### Current baseline in code

- `SettingsView.swift` is still legacy `Form`-based UI with:
  - theme segmented picker (`selectedTheme`)
  - `NavigationLink("Report Lost Card")`
  - logout button + spinner
- `SettingsViewModel.swift` only persists `selectedTheme` (`theme_mode`) and handles logout state.
- No accent-color preference exists in state, storage, or UI.
- No personal-info edit model/UI exists.
- Settings screen does **not** use stitch primitives (`StitchCard`, `StitchFieldStyle`, `StitchPrimaryButtonStyle`) unlike S02/S03/S04 screens.
- `AppTheme.Palette.accent` exists but is effectively unused; app brand colors are static constants.
- Brand/accent usage is hardcoded in multiple files (`StitchPrimaryButtonStyle`, `StitchTabShell`, `LoginView`, `HomeView`, `QRPayView`) with no shared reactive appearance state.

### Highest-risk gaps found

1. **R060 is completely unimplemented**
   - No accent preference selection/persistence flow.
   - No personal-info edit persistence flow.
2. **Accent propagation seam is missing**
   - Existing colors are static token constants; changing a stored preference won’t automatically update reused components unless a reactive app-wide hook is introduced.
3. **Persistence semantics are ambiguous/fragile in current auth model**
   - `AuthManager.clearAll()` deletes `theme_mode` and `student_name`.
   - `AuthManager.login(...)` always rewrites `student_name` from backend response.
   - If personal-info edit reuses `student_name` naïvely, local edits may be lost on relogin/logout.
4. **S04 continuity coupling must be preserved**
   - Existing S04 contract/verifier asserts `NavigationLink("Report Lost Card")` + `LostCardView()` in `SettingsView`.
   - S05 redesign must either keep these markers or intentionally update downstream contract suites/scripts.
5. **Scope-clean risk during stitch-copy work**
   - D072/R067 explicitly forbids adding stitch-only settings extras: `Privacy & Security`, `Tuition Auto-Pay`, `Campus Discounts`.
   - R057 support requires avoiding payment-method settings rows/actions.

## Recommendation

Plan S05 in **persistence-contract-first** order, then UI polish:

1. **Establish local settings state contract first (R060 core)**
   - Add explicit persisted channels for accent + personal info draft/save.
   - Keep persistence local-only (D071): no backend profile writes.
2. **Add app-wide accent application hook second**
   - Introduce one reactive source of truth consumed by shared primitives/shell.
   - Prove accent visibly affects at least shared shell + primary actions (not only a local Settings subview).
3. **Rework Settings screen to stitch style + scope-clean action map**
   - Use `AppTheme` + stitch primitives.
   - Keep only actionable in-scope controls (personal info edit, accent selection, lost-card nav, logout).
4. **Close with deterministic verifier artifacts**
   - Add S05 behavior/design contract tests + one-command verifier + manual UAT checklist.

## Implementation Landscape

### Key files and current role

- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`
  - Current settings surface; still Form-based and pre-stitch.
- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift`
  - Current settings state; only theme + logout.
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift`
  - Session + local key lifecycle (`student_name`, `theme_mode` clear behavior).
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
  - Consumes `authManager.studentName`; candidate display surface for persisted personal-info edits.
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
  - Static tokens; no reactive accent pipeline today.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift`
  - Shared visual primitives currently hardcoded to static brand colors.
- `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift`
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`
  - Additional brand-color consumers likely affected if accent is app-wide.
- `mobile/ios/BankongSetonStudent/Core/Keychain/KeychainHelper.swift`
  - Existing local persistence primitive used across app.
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`
  - Explicit source registration; new Swift files require pbxproj edits.
- `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py`
- `scripts/verify-m007-s04.sh`
  - Existing continuity constraints around Settings → Lost Card navigation.

### Natural seams for planner tasking

1. **Persistence/state seam (highest priority)**
   - Files: `SettingsViewModel.swift`, `AuthManager.swift` (and optional new local settings model file)
   - Goal: durable local channels for accent + personal info without backend writes.
2. **Accent hook seam (cross-screen integration)**
   - Files: `AppTheme.swift` and/or shared UI primitives (`StitchPrimaryButtonStyle.swift`, `StitchTabShell.swift`, selected view consumers)
   - Goal: make accent preference visibly effective beyond local settings controls.
3. **Settings UI seam (stitch + scope cleanup)**
   - Files: `SettingsView.swift` (+ possible subviews)
   - Goal: stitch-faithful settings cards/inputs; remove out-of-scope groups; keep all visible controls actionable.
4. **Verification seam**
   - Files: new S05 pytest contracts + `scripts/verify-m007-s05.sh` + `.gsd/.../S05-UAT.md`
   - Goal: deterministic closure checks for persistence + scope-clean constraints + continuity anchors.

## Critical Constraints / Fragility

- **D071 / R060:** personal-info and accent persistence must remain local-only (no APIClient profile endpoint usage).
- **D072 / R061 / R067:** do not add non-scope settings groups (Privacy & Security, Tuition Auto-Pay, Campus Discounts) or decorative placeholders.
- **R057 support:** do not introduce payment-method settings rows/management controls.
- **S04 coupling:** keep `Report Lost Card` navigation functional and regression-detectable.
- **Project wiring:** adding new Swift files requires `project.pbxproj` registration.
- **Environment constraints:** this scout host lacks `xcodebuild` and `/bin/bash`; verification scripts should still preserve canonical bash entrypoint but Windows fallback uses `rtk proxy sh` / `rtk proxy python`.

## Don’t Hand-Roll

Reuse established M007 patterns:

- `AppTheme` semantic tokens + `StitchCard` + `StitchFieldStyle` + `StitchPrimaryButtonStyle`
- Existing key/value local persistence path (`KeychainHelper`) unless there is a deliberate reason to introduce a second storage mechanism
- Existing source-contract verification style (`tests/test_verify_m007_*.py` literal assertions)
- Existing verifier harness pattern (`scripts/verify-m007-s0*.sh` phase-based preflight/contract/static checks)

## What to Build/Prove First

First proof should be **persistence + actionability**, not cosmetics:

1. Accent selection writes and restores local preference deterministically.
2. Personal-info edit writes/restores local preference deterministically.
3. At least one non-settings surface reflects persisted state (e.g., display name in Home and/or shared accentized controls).
4. Settings visible controls are all actionable and scope-clean (no dead secondary rows).

Then finish stitch styling and verifier/UAT artifacts.

## Verification Strategy (for S05 execution)

### Static/contract checks to add

Create:
- `tests/test_verify_m007_s05_settings_behavior_contract.py`
- `tests/test_verify_m007_s05_settings_design_contract.py`

Behavior contract should assert markers for:
- persisted accent channel in settings state
- persisted personal-info channel in settings state
- explicit save/apply actions (not decorative controls)
- absence of backend profile write usage from settings flow
- continuity hook for lost-card and logout actions

Design contract should assert markers for:
- stitch primitives/tokens on settings surface
- personal-info inputs + actionable save button
- accent-picker controls + selection state markers
- forbidden strings absent:
  - `Privacy & Security`
  - `Tuition Auto-Pay`
  - `Campus Discounts`
  - payment-method management labels

### Verifier script to add

Create `scripts/verify-m007-s05.sh` with:

1. preflight file existence checks
2. `behavior-contract` phase (`pytest` behavior suite)
3. `design-contract` phase (`pytest` design suite)
4. `static-contract` phase (required/forbidden literal checks)

### Suggested commands

- `rtk proxy python -m pytest -q tests/test_verify_m007_s05_settings_behavior_contract.py tests/test_verify_m007_s05_settings_design_contract.py`
- `rtk proxy bash scripts/verify-m007-s05.sh`
- Windows shell fallback when `/bin/bash` unavailable:
  - `rtk proxy sh scripts/verify-m007-s05.sh`

### Runtime checks (macOS/Xcode host)

- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

Manual S05 UAT flow should cover:
1. Edit personal info in Settings → save → leave screen → re-open (state retained).
2. Restart app (without backend profile write) and verify local state restore.
3. Accent change is visible in shared UI (not only a single inline preview).
4. Lost-card navigation remains functional from Settings.
5. Logout remains actionable and non-dead.
6. No out-of-scope settings groups/actions visible.

### Environment note

`xcodebuild` is unavailable in this scout environment, so compile/runtime proof must be produced by macOS executor/device stages.

## Skill-Guided Implementation Notes

Applied from loaded skills:

- **swiftui**
  - Keep a single source of truth for settings/appearance state; avoid scattering persistence writes directly in multiple views.
  - Verify in small, reversible increments (`change → verify → next`).
- **accessibility**
  - Accent options must not be color-only; include text labels/selection state.
  - Personal-info fields and actions need explicit accessibility labels/hints.
- **make-interfaces-feel-better**
  - Keep accent chips/buttons with reliable tap targets (≥40x40 equivalent).
  - Keep interaction feedback restrained; no heavy transitions.
- **test**
  - Match existing repo test style (pytest source-contract checks + deterministic verifier script).
- **debug-like-expert**
  - Treat persistence behavior as hypotheses to verify explicitly (relaunch/restore), not assumptions.
- **qodo-get-rules**
  - Load Qodo org/repo rules before implementation edits if not already loaded in execution context.

## Skills Discovered

Core technologies for this slice:
- SwiftUI iOS UI/state composition
- Local key/value persistence (Keychain-backed in this repo)
- Existing pytest-based source-contract verification pipeline

Relevant skills already installed:
- `swiftui`, `accessibility`, `make-interfaces-feel-better`, `best-practices`, `test`, `debug-like-expert`, `frontend-design`, `feature-dev`, `qodo-get-rules`

Missing-skill discovery attempt:
- Command: `rtk proxy npx skills find "UserDefaults"`
- Result: failed in this environment (`npx` program not found)

No additional skills were installed during this scout run.

## Sources

- `.gsd/REQUIREMENTS.md` (R055–R063, R067)
- `.gsd/DECISIONS.md` (D070–D072, D074–D081)
- `.gsd/milestones/M007/slices/S01/S01-RESEARCH.md`
- `.gsd/milestones/M007/slices/S02/S02-RESEARCH.md`
- `.gsd/milestones/M007/slices/S03/S03-RESEARCH.md`
- `.gsd/milestones/M007/slices/S04/S04-RESEARCH.md`
- `.gsd/milestones/M007/slices/S04/S04-SUMMARY.md`
- `.gsd/milestones/M007/slices/S04/tasks/T03-SUMMARY.md`
- `.gsd/milestones/M007/slices/S04/S04-UAT.md`
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift`
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift`
- `mobile/ios/BankongSetonStudent/Core/Keychain/KeychainHelper.swift`
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
- `mobile/ios/BankongSetonStudent/UI/Theme/Color+Hex.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift`
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift`
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift`
- `mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift`
- `mobile/ios/BankongSetonStudent/App/ContentView.swift`
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`
- `tests/test_verify_m007_s03_transactions_design_contract.py`
- `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`
- `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py`
- `scripts/verify-m007-s03.sh`
- `scripts/verify-m007-s04.sh`
