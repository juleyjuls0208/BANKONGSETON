# S05: Settings Rework + Local Persistence + Scope Cleanup

**Goal:** Deliver a stitch-faithful Settings surface where accent choice and personal-info edits persist locally and are reflected in real app UI, while out-of-scope/dead settings actions are removed.
**Demo:** On a fresh app launch, user changes accent + personal info in Settings, leaves and re-enters the screen (and relaunches app) to see values restored; Settings shows only in-scope actionable controls, with working Report Lost Card and Logout.

## Must-Haves

- R060 (owned): Accent preference and personal-info edit persist locally with explicit save/apply actions; no backend profile-write path is introduced.
- R061 (owned): Remove non-scope settings groups/actions (`Privacy & Security`, `Tuition Auto-Pay`, `Campus Discounts`, payment-method management) and avoid decorative dead controls.
- R055 + R056 (support): Settings is rebuilt with stitch primitives/tokens and every visible in-scope control is actionable.
- R057 + R063 (support): Preserve QR-only direction by keeping payment-method settings absent, while maintaining coherent lost-card/logout continuity for demo flow.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s05_settings_behavior_contract.py tests/test_verify_m007_s05_settings_design_contract.py`
- `rtk proxy sh scripts/verify-m007-s05.sh`
- `rtk proxy bash scripts/verify-m007-s05.sh`
- `rtk proxy python -c "import subprocess; p=subprocess.run(['rtk','proxy','sh','scripts/verify-m007-s05.sh'], capture_output=True, text=True); out=(p.stdout or '') + (p.stderr or ''); required=['preflight','behavior-contract','design-contract','static-contract']; missing=[x for x in required if x not in out]; assert not missing, missing"`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
- `rtk proxy python -c "from pathlib import Path; assert Path('.gsd/milestones/M007/slices/S05/S05-UAT.md').exists()"`

## Observability / Diagnostics

- Runtime signals: deterministic local settings channels for accent/profile plus explicit save/apply state transitions in the settings view model.
- Inspection surfaces: `scripts/verify-m007-s05.sh` phase output, pytest contract failures, and visible Settings/Home UI state after relaunch.
- Failure visibility: verifier phases report which contract failed (`behavior-contract`, `design-contract`, `static-contract`) and which marker/forbidden string caused failure.
- Redaction constraints: never print persisted personal-info values in logs/tests; assertions use marker presence and control wiring only.

## Integration Closure

- Upstream surfaces consumed: `SettingsViewModel`, `AuthManager`, `AppTheme`, `StitchPrimaryButtonStyle`, `StitchTabShell`, `HomeView`, and S04 lost-card continuity contracts.
- New wiring introduced in this slice: local-preference state channel (accent/profile) from Settings into shared theme/UI composition and home display surface.
- What remains before the milestone is truly usable end-to-end: S06 motion/performance tuning on iOS 17+ and S07 final integrated device-demo pass.

## Tasks

- [x] **T01: Implement local settings persistence contract for accent and personal info** `est:2h`
  - Why: R060 is currently missing; we need a deterministic local-only persistence layer before UI polish.
  - Files: `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift`, `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift`, `mobile/ios/BankongSetonStudent/Core/Keychain/KeychainHelper.swift`
  - Do: Add persisted channels for selected accent and editable personal info in settings state, expose explicit save/apply methods, and preserve local-only semantics (no backend profile writes).
  - Verify: `rtk proxy python -c "from pathlib import Path; vm=Path('mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift').read_text(); assert 'savePersonalInfo' in vm; assert 'selectedAccent' in vm; assert 'editableDisplayName' in vm; assert 'APIClient' not in vm"`
  - Done when: Settings state can load/save accent + personal info from local persistence deterministically and does not introduce API profile-write calls.
- [x] **T02: Wire reactive accent and persisted display name into shared app surfaces** `est:2h`
  - Why: S05 must prove persistence is not local decoration; saved choices must affect shared UI and survive screen transitions.
  - Files: `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`, `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`, `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift`, `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`, `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`, `mobile/ios/BankongSetonStudent/App/ContentView.swift`
  - Do: Introduce one reactive accent resolution path used by shared shell/primary-action styling and wire persisted personal-info value into home display with safe fallback behavior.
  - Verify: `rtk proxy python -c "from pathlib import Path; shell=Path('mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift').read_text().lower(); btn=Path('mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift').read_text().lower(); vm=Path('mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift').read_text(); assert 'accent' in shell and 'accent' in btn; assert 'resolvedDisplayName' in vm"`
  - Done when: Changing accent/personal info in Settings is reflected in at least shared shell + primary actions + home display path without hardcoded-only fallback.
- [x] **T03: Rework Settings UI to stitch style and remove out-of-scope/dead actions** `est:2h`
  - Why: R061 requires scope cleanup and R055/R056 require stitch-faithful, fully actionable controls.
  - Files: `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`, `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift`, `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`
  - Do: Replace legacy Form with stitch card/list styling, bind personal-info save and accent selection controls with accessible labels/state, keep Report Lost Card and Logout actionable, and remove forbidden non-scope/payment-method groups.
  - Verify: `rtk proxy python -c "from pathlib import Path; t=Path('mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift').read_text(); assert 'Report Lost Card' in t and 'Logout' in t; assert all(x not in t for x in ['Privacy & Security','Tuition Auto-Pay','Campus Discounts','Payment Method'])"`
  - Done when: Settings screen contains only in-scope actionable groups and no visible decorative dead controls.
- [x] **T04: Add S05 behavior/design contracts, verifier script, and UAT closure doc** `est:1h`
  - Why: Slice completion needs deterministic proof that persistence, scope cleanup, and continuity contracts remain intact.
  - Files: `tests/test_verify_m007_s05_settings_behavior_contract.py`, `tests/test_verify_m007_s05_settings_design_contract.py`, `scripts/verify-m007-s05.sh`, `.gsd/milestones/M007/slices/S05/S05-UAT.md`
  - Do: Implement behavior/design contract tests, add phased S05 verifier (`preflight`, `behavior-contract`, `design-contract`, `static-contract`), and write manual UAT checklist including Windows shell fallback note.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s05_settings_behavior_contract.py tests/test_verify_m007_s05_settings_design_contract.py && rtk proxy sh scripts/verify-m007-s05.sh`
  - Done when: Both S05 contract suites and verifier script pass, and S05-UAT captures manual persistence + accent propagation checks for device execution.

## Files Likely Touched

- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift`
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift`
- `mobile/ios/BankongSetonStudent/Core/Keychain/KeychainHelper.swift`
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/App/ContentView.swift`
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`
- `tests/test_verify_m007_s05_settings_behavior_contract.py`
- `tests/test_verify_m007_s05_settings_design_contract.py`
- `scripts/verify-m007-s05.sh`
- `.gsd/milestones/M007/slices/S05/S05-UAT.md`
