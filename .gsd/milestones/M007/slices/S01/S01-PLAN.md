# S01: Design System + Navigation Shell Rework

**Goal:** Build a stitch-faithful SwiftUI design foundation and tab/login shell that downstream slices can reuse without re-inventing visual language.
**Demo:** App launches to redesigned login, authenticates into a redesigned tab shell, and shows shared tokens/components reused outside login (home/transactions) while preserving current working interactions.

## Must-Haves

- Directly satisfy **R055** by introducing one shared design system contract (tokens, surfaces, typography, controls) applied to login + navigation shell.
- Preserve in-scope interaction continuity while restyling (supports **R056**): login submit states still work, session-expired alert flow still clears auth, and all tab switches remain interactive.
- Produce reusable shell/style primitives that S02–S05 can consume for QR, transactions, budget, receipt/lost-card, and settings work (supports **R057–R063** cohesion dependency).
- Add executable proof artifacts (real test files with assertions + iOS build command) so visual-contract regressions are detectable by future slices.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
- Manual smoke: login → tab shell transition, tab switching across all 4 tabs, and forced session-expired alert still routes back to sign-in.

## Observability / Diagnostics

- Runtime signals: `LoginView` loading/error state visibility, `AuthManager.showSessionExpiredAlert`, and active tab selection feedback in the custom shell.
- Inspection surfaces: SwiftUI runtime UI state, plus source-contract tests in `tests/test_verify_m007_s01_design_system_contract.py` and `tests/test_verify_m007_s01_shell_login_contract.py`.
- Failure visibility: failing pytest assertions identify missing token usage/wiring; `xcodebuild` compile errors identify project registration or API mismatches.
- Redaction constraints: never persist PIN/student credentials in logs, screenshots, or test fixtures.

## Integration Closure

- Upstream surfaces consumed: `mobile/ios/BankongSetonStudent/App/ContentView.swift`, `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`, `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift`, `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`, `mobile/ios/BankongSetonStudent/Views/Transactions/{TransactionsView.swift,TransactionRowView.swift}`, and `AuthManager`/`LoginViewModel` contracts.
- New wiring introduced in this slice: shared SwiftUI theme/component files, custom tab shell composition, login restyle on shared primitives, and source-level contract tests for design-system reuse.
- What remains before the milestone is truly usable end-to-end: S02–S05 must adopt these primitives across QR, transactions states, budget/receipt/lost-card, and settings persistence/scope cleanup; S06/S07 must complete motion tuning and device-ready integration proof.

## Tasks

- [ ] **T01: Establish shared SwiftUI design tokens + primitives contract** `est:1h 20m`
  - Why: R055 cannot be met screen-by-screen; S01 needs one reusable foundation before shell/login refactors.
  - Files: `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`, `mobile/ios/BankongSetonStudent/UI/Theme/Color+Hex.swift`, `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift`, `mobile/ios/BankongSetonStudent/UI/Components/StitchFieldStyle.swift`, `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`, `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`, `tests/test_verify_m007_s01_design_system_contract.py`
  - Do: Create semantic color/spacing/type/shadow tokens and reusable card/field/button styles, migrate `Color(hex:)` out of feature views into shared theme utilities, register new Swift files in `.xcodeproj`, and add initial pytest assertions that fail when token primitives are missing.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py && rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
  - Done when: Theme/component primitives compile, are project-registered, and design-system contract tests pass.
- [ ] **T02: Recompose MainTabView into a stitch tab shell without breaking routing** `est:1h 10m`
  - Why: S02–S05 depend on a stable, reusable shell contract; default `TabView` styling blocks stitch parity.
  - Files: `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift`, `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`, `mobile/ios/BankongSetonStudent/App/ContentView.swift`, `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`, `tests/test_verify_m007_s01_shell_login_contract.py`
  - Do: Implement custom shell/tab treatment backed by semantic tokens, keep existing tab destinations and labels, preserve session-expired alert behavior (`authManager.clearAll()`), and add contract assertions for tab structure/session alert wiring.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py -k "tab_shell or session_alert" && rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
  - Done when: Styled shell is active, all four tabs remain interactive, and session-expired recovery path still functions.
- [ ] **T03: Restyle LoginView on shared primitives while preserving auth behavior** `est:1h 05m`
  - Why: Login is the first user touchpoint for R055 and must demonstrate tokenized UI without auth regressions.
  - Files: `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift`, `mobile/ios/BankongSetonStudent/UI/Components/StitchFieldStyle.swift`, `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`, `tests/test_verify_m007_s01_shell_login_contract.py`
  - Do: Refactor login layout/branding/form controls to stitch style using shared primitives, preserve `LoginViewModel` loading/error/disabled semantics and async submit action, and expand tests to assert critical login wiring remains intact.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py -k "login" && rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
  - Done when: Login UI is stitch-styled, sign-in CTA is never dead, and test assertions confirm existing auth wiring.
- [ ] **T04: Prove cross-screen reuse by applying primitives to home + transactions surfaces** `est:1h 20m`
  - Why: S01 risk retires only when primitives are reused beyond login/shell, giving S03/S04/S05 a trustworthy visual contract.
  - Files: `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`, `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift`, `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`, `tests/test_verify_m007_s01_design_system_contract.py`, `tests/test_verify_m007_s01_shell_login_contract.py`
  - Do: Replace ad hoc card/color/spacing patterns in home + transaction list/rows with shared primitives, ensure transaction row retains debit/credit meaning and navigable/non-navigable behavior, and finalize contract tests to assert multi-screen primitive adoption.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py tests/test_verify_m007_s01_shell_login_contract.py && rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
  - Done when: At least one non-login destination consumes shared primitives, tests pass, and shell/login/home/transactions visual language is coherent without interaction regressions.

## Files Likely Touched

- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
- `mobile/ios/BankongSetonStudent/UI/Theme/Color+Hex.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchFieldStyle.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift`
- `mobile/ios/BankongSetonStudent/App/ContentView.swift`
- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`
- `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift`
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift`
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`
- `tests/test_verify_m007_s01_design_system_contract.py`
- `tests/test_verify_m007_s01_shell_login_contract.py`
