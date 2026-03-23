# S01 Research — Design System + Navigation Shell Rework (M007)

**Date:** 2026-03-22  
**Slice:** M007/S01  
**Primary requirement:** R055 (Stitch-faithful iOS redesign across in-scope screens)  
**Key supporting impact:** Establishes reusable shell/token contract consumed by S02–S05

## Summary

This slice is a **targeted SwiftUI UI-platform refactor**, not a business-logic change.

Current iOS implementation is functionally wired, but visual/system-level structure is fragmented:

- No shared design system module exists (palette, typography, spacing, surfaces, button/input styles are per-screen ad hoc).
- `MainTabView` uses stock `TabView` with default tab styling and no stitch shell treatment.
- `LoginView` is standalone and hardcoded (fields/buttons/colors not reusable).
- `Color(hex:)` lives inside `TransactionRowView.swift`, but is also consumed by `HomeView`, creating an implicit cross-file coupling.
- Each tab root owns its own `NavigationStack`; this preserves navigation flow today, but shell changes can easily introduce duplicated headers/chrome if not planned.

From roadmap + requirements, S01 should produce the base contract used by downstream slices: **tokens + primitives + shell + login baseline**, while preserving current interaction wiring.

## Requirements Focus (Active)

### Directly owned
- **R055 (primary owner: M007/S01):** stitch-faithful redesign foundation across login + shared shell language.

### Supported indirectly by this slice
- **R056:** no dead controls (S01 must not break current working interactions while restyling shell/login).
- **R057/R058/R059/R060/R061/R062/R063:** all later slices depend on S01’s reusable visual/navigation primitives to stay cohesive.

## Recommendation

Build S01 in this order (highest unblock value first):

1. **Create shared UI foundation** (tokens + primitives) and compile immediately.
2. **Refactor navigation shell** (`MainTabView`, root container) to consume those primitives.
3. **Refactor `LoginView`** to stitch style using the same primitives.
4. **Adopt primitives in at least one downstream destination component** (e.g., transaction row or home card) to prove reuse beyond login/shell and retire visual-drift risk early.

This sequence follows the SwiftUI skill’s “small steps, always verified” and “single source of truth” guidance.

## Implementation Landscape

## Relevant files and what they do now

- `mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift`
  - App root; injects `AuthManager` and `APIClient`.
- `mobile/ios/BankongSetonStudent/App/ContentView.swift`
  - Auth gate (`LoginView` vs `MainTabView`).
- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`
  - Stock `TabView` with 4 tabs; owns session-expired alert.
- `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift`
  - Current login UI (simple fields/button, hardcoded styles).
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
  - Uses `Color(hex:)` gradient balance card; QR entry point.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift`
  - Transaction row styling; currently contains global `Color(hex:)` extension.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
  - Uses default list/nav style; important shell consumer for S03.
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`
  - Manual source registration; new Swift files require pbxproj updates.

## Natural seams for planner decomposition

### Seam A — Design tokens/primitives (platform foundation)
Create reusable, non-flow-specific building blocks:
- Colors, semantic roles (background/surface/primary/critical/success/text tiers)
- Typography scale + weight conventions
- Spacing/radius/shadow constants
- Reusable controls (primary button style, text-field style, card container)
- Shared layout wrappers (screen background, section header pattern)

### Seam B — Navigation shell contract
Refactor `MainTabView` and root shell framing only:
- tab shell visual treatment
- tab selection state and icon/label style
- preserve existing tab destinations and session-expired alert behavior

### Seam C — Login as first consumer
Refactor login screen to consume seam A primitives:
- no login API contract change
- preserve submit/disabled/loading/error behavior
- visual parity proof point for stitch language

### Seam D — Cross-screen adoption proof (minimum viable reuse)
Apply at least one shared primitive outside login/shell (recommended: transaction row card or home balance card container) so downstream slices inherit a tested style contract.

## Constraints and Fragility

- **Project wiring constraint:** `.xcodeproj/project.pbxproj` is explicit/manual. Adding new Swift files without pbxproj entries will silently fail to compile in Xcode.
- **Navigation fragility:** each tab currently wraps its own `NavigationStack`. If shell introduces additional top bars/chrome, duplicated nav treatments are likely.
- **Behavior preservation constraint:** S01 must not alter API/viewmodel behavior; this slice should remain presentation + shell architecture.
- **Design consistency risk:** isolated restyling (login only) fails R055 intent; must prove primitives are reused by multiple destinations.
- **Platform/tooling constraint in this scout environment:** `xcodebuild` is unavailable here (`program not found`), so compile proof must be executed by planner/executor on macOS.

## Don’t Hand-Roll

Prefer native SwiftUI mechanisms already aligned to skill guidance:

- Use `NavigationStack` (already used; do not regress to deprecated `NavigationView`).
- Use `ButtonStyle` / `ViewModifier` / shared constants instead of per-view duplicated `.padding/.background/.cornerRadius` chains.
- Keep one theme source of truth (token namespace) instead of scattered literals.
- Keep animations interruptible and restrained; avoid broad implicit animation on full container state flips.

## Skill-informed implementation rules to carry forward

From loaded skills:

- **swiftui**
  - “Prove, don’t promise”: after each seam, run build checks on macOS.
  - Keep declarative single source of truth for theme tokens.
  - Keep work in small verified steps.
- **make-interfaces-feel-better**
  - Maintain concentric radius relationships on nested surfaces.
  - Preserve minimum tap targets (~40x40) for tab items and action controls.
  - Avoid `transition: all`-style broad transitions; animate specific properties only.
- **frontend-design**
  - Commit to one coherent aesthetic direction across screens (no mixed visual dialects).
- **qodo-get-rules**
  - Before implementation edits, load repo rules and apply ERROR-level constraints if available.

## Verification Plan (for executor on macOS)

1. **Compile gate (required per seam):**
   - `xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
2. **Behavior smoke (manual):**
   - Launch app, verify login -> tab shell -> tab switching still works.
   - Verify session-expired alert still appears from `MainTabView` path.
3. **Structure checks (fast):**
   - Ensure token primitives are referenced by both `LoginView` and at least one non-login screen.
   - Remove/migrate `Color(hex:)` out of `TransactionRowView.swift` if shared globally.
4. **No dead shell controls:**
   - Every visible tab control and login CTA remains interactive and wired.

## Skill Discovery (suggested)

Core technologies in this slice are SwiftUI/Xcode/iOS shell architecture.

Installed relevant skills already present:
- `swiftui`
- `frontend-design`
- `make-interfaces-feel-better`
- `best-practices`

Attempted discovery for uncovered tech (`AVFoundation`) via `npx skills find` failed in this environment (`npx` not found), so no additional install candidates were discovered during scout.

## What to build/prove first

First proof should be **foundation compile + two-screen adoption**:

- Add shared tokens/primitives.
- Refactor `LoginView` + `MainTabView` to consume them.
- Demonstrate one additional consumer (`HomeView` or `TransactionRowView`).

If this compiles and runs, S02–S05 can execute parallel screen-specific redesign work without re-litigating palette/spacing/nav conventions.

## Sources

- `.gsd/REQUIREMENTS.md` (R055–R063 mapping; R055 ownership)
- `.gsd/DECISIONS.md` (D070–D073 scope/motion/persistence constraints)
- `mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift`
- `mobile/ios/BankongSetonStudent/App/ContentView.swift`
- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`
- `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift`
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`
