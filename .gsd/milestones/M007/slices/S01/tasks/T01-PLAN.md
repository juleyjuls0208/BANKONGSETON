---
estimated_steps: 5
estimated_files: 7
skills_used:
  - qodo-get-rules
  - swiftui
  - feature-dev
  - frontend-design
  - make-interfaces-feel-better
  - best-practices
  - test
---

# T01: Establish shared SwiftUI design tokens + primitives contract

**Slice:** S01 — Design System + Navigation Shell Rework
**Milestone:** M007

## Description

Create the reusable stitch-style foundation (theme tokens + UI primitives) so login/shell/screens can share one visual language instead of repeating ad hoc modifiers.

## Steps

1. Load repo coding rules via `qodo-get-rules` and inspect current style duplication in login/home/transactions files.
2. Add `AppTheme.swift` and `Color+Hex.swift` with semantic tokens (palette, spacing, radius, typography helpers, shadows) that map to stitch language.
3. Add reusable primitives (`StitchCard`, `StitchFieldStyle`, `StitchPrimaryButtonStyle`) and migrate shared color helpers out of feature views.
4. Register new Swift files in `BankongSetonStudent.xcodeproj/project.pbxproj` so the app target compiles them.
5. Add `tests/test_verify_m007_s01_design_system_contract.py` with real assertions for token/primitives file existence and key exported symbols, then run pytest + iOS build.

## Must-Haves

- [ ] Theme/tokens are centralized and semantic (not hardcoded per-screen literals).
- [ ] Shared card/field/button primitives exist and are reusable by later slices.
- [ ] `Color(hex:)` no longer lives only inside `TransactionRowView.swift`.
- [ ] Automated assertions fail if design foundation files/symbols are removed.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

## Inputs

- `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift` — current ad hoc text-field/button styling baseline.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — existing gradient/card literal usage to normalize.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` — current `Color(hex:)` location to migrate.
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj` — required project wiring for new Swift files.
- `.gsd/milestones/M007/slices/S01/S01-RESEARCH.md` — risk/order constraints for foundation-first execution.

## Expected Output

- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — semantic stitch design tokens.
- `mobile/ios/BankongSetonStudent/UI/Theme/Color+Hex.swift` — shared hex color utility moved to theme scope.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift` — reusable surface/card primitive.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchFieldStyle.swift` — reusable text input style primitive.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — reusable primary CTA style primitive.
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj` — app target includes new UI files.
- `tests/test_verify_m007_s01_design_system_contract.py` — executable design-system contract assertions.
