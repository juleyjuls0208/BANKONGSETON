---
estimated_steps: 4
estimated_files: 6
skills_used:
  - swiftui
  - make-interfaces-feel-better
  - accessibility
  - best-practices
  - debug-like-expert
---

# T02: Wire reactive accent and persisted display name into shared app surfaces

**Slice:** S05 — Settings Rework + Local Persistence + Scope Cleanup
**Milestone:** M007

## Description

Make the persisted settings from T01 visible beyond Settings by introducing a shared accent resolution path and a persisted display-name read path used by home/shell surfaces. This task closes the integration seam required for S05 and de-risks S06/S07 composition.

## Steps

1. Add an accent resolver API in `AppTheme` (e.g., `accentColor(for:)`) that maps persisted preference values to concrete SwiftUI colors.
2. Thread accent preference through app composition so shared primitives (`StitchTabShell`, `StitchPrimaryButtonStyle`) consume resolved accent instead of hardcoded-only brand color usage.
3. Add a resolved display-name path (e.g., `resolvedDisplayName`) in home state flow so persisted personal info override is shown with backend-name fallback.
4. Ensure fallback behavior is deterministic: missing/invalid local values use safe defaults without breaking shell/home rendering.

## Must-Haves

- [ ] `AppTheme` exposes a reusable accent resolver consumed by shared UI surfaces.
- [ ] At least tab shell and primary action styling use persisted accent state.
- [ ] Home display path reads persisted personal info override with safe fallback.

## Verification

- `rtk proxy python -c "from pathlib import Path; theme=Path('mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift').read_text(); shell=Path('mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift').read_text().lower(); btn=Path('mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift').read_text().lower(); assert 'accentColor(for' in theme; assert 'accent' in shell and 'accent' in btn"`
- `rtk proxy python -c "from pathlib import Path; vm=Path('mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift').read_text(); assert 'resolvedDisplayName' in vm"`

## Observability Impact

- Signals added/changed: explicit resolved accent/display-name pathways consumed by shared UI components.
- How a future agent inspects this: inspect `AppTheme`, shell/button primitives, and `HomeViewModel` for resolver wiring; then run S05 contract tests.
- Failure state exposed: missing resolver wiring appears as default-color regression and contract/static assertion failures.

## Inputs

- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift` — persisted accent and personal-info state/actions from T01.
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — current static palette/tokens.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — shared action styling seam.
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift` — shared shell styling seam.
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift` — home display data flow.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — home UI display surface.

## Expected Output

- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — accent resolver for persisted settings values.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — shared primary action style wired to resolved accent.
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift` — shell accent surfaces wired to persisted accent state.
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift` — resolved display-name path with fallback.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — home label usage aligned with resolved display name.
- `mobile/ios/BankongSetonStudent/App/ContentView.swift` — composition wiring needed to pass persisted settings into shared surfaces.
