# S04 Research — Budget + Receipt + Lost-Card Redesign

**Date:** 2026-03-23  
**Status:** Ready for planning

## Requirement Targeting (Active)

S04 directly owns/supports:

- **Owns:**
  - **R055** — Stitch-faithful redesign continuity for Budget, Receipt, and Lost-Card surfaces
  - **R056** — No dead controls in visible in-scope UI for Budget/Receipt/Lost-Card flows
  - **R061** — Keep non-scope receipt utility actions removed (no PDF/report-issue surfaces)
- **Supports:**
  - **R059** — State-fidelity behavior (loading/error/success/empty handling on S04 surfaces)
  - **R063** — Demo-readiness continuity (S04 paths must be coherent in end-to-end iOS demo flow)

## Summary

This slice is **targeted research** (known SwiftUI stack, moderate integration risk).

### Current baseline in code

- `BudgetView.swift` and `BudgetViewModel.swift` are functionally wired to budget endpoints (`getBudget`, `fetchBudgetSummary`, `setBudget`) but are still pre-stitch visual style.
- `LostCardView.swift` is functional (`reportLostCard`) but state handling is inline in the view and not aligned to stitch component patterns.
- `ReceiptView.swift` is functional and already scope-clean (no PDF/report actions), but uses default `List`/`Section` presentation and no stitch tokens.
- S01/S02/S03 stitch primitives (`AppTheme`, `StitchCard`, `StitchPrimaryButtonStyle`) are used in login/home/QR/transactions, but **not** in budget/receipt/lost-card files.
- Receipt routing continuity already exists and must be preserved:
  - `HomeView.swift` → `ReceiptView(transaction:)`
  - `TransactionsView.swift` → `ReceiptView(transaction:)`
- Lost-card entry continuity already exists and must be preserved:
  - `SettingsView.swift` → `NavigationLink("Report Lost Card") { LostCardView() }`

### Highest-risk gaps found

1. **Stitch parity drift on all S04 screens (R055 risk):**
   - No `AppTheme`/`StitchCard`/`StitchPrimaryButtonStyle` usage in:
     - `Views/Budget/BudgetView.swift`
     - `Views/LostCard/LostCardView.swift`
     - `Views/Receipt/ReceiptView.swift`
2. **Budget state fidelity is weak (R059/R056 risk):**
   - `BudgetViewModel.load(...)` has silent generic catches (`catch {}`), so load failures can look like valid zero-state data instead of an explicit recoverable error state.
3. **Lost-card session boundary mismatch (R056/demo-flow risk):**
   - Backend lost-card success invalidates server session; current client success path only flips local `isSuccess` and does not explicitly transition auth state.
   - `LostCardView` does not explicitly handle `APIError.unauthorized` on report call.
4. **Receipt stability/usability fragility:**
   - `ForEach(lineItems, id: \.name)` can collide if duplicate item names appear in a single receipt.
   - Timestamp parser expects one exact format (`yyyy-MM-dd HH:mm:ss`); fallback behavior is acceptable but currently not polished.
5. **Accessibility instrumentation missing on S04 screens:**
   - No accessibility identifiers/labels/hints in Budget/Lost-Card/Receipt views; this weakens deterministic UI verification and assistive UX quality.

## Recommendation

Plan S04 in **behavior-contract-first** order, then visual completion:

1. **Harden S04 state contracts first**
   - Budget: explicit load/save/failure semantics with actionable recovery surface(s)
   - Lost-card: explicit idle/loading/success/error and post-success auth/session transition behavior
   - Receipt: deterministic line-item identity and resilient summary formatting
2. **Apply stitch redesign using existing primitives**
   - Migrate Budget/Receipt/Lost-Card to `AppTheme` + `StitchCard` + `StitchPrimaryButtonStyle`
   - Keep in-scope controls actionable; do not add decorative non-functional utility actions
3. **Close with executable S04 verifier artifacts**
   - Add S04 behavior/design contract tests
   - Add `scripts/verify-m007-s04.sh` + manual checklist (`S04-UAT.md`)

This retires functional dead-end risk before visual polish and matches prior M007 execution pattern (S02/S03).

## Implementation Landscape

### Key files and current role

- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift`
  - Budget screen UI (ring, spent/limit, save-limit form, loading overlay, alert)
- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift`
  - Budget load/save behavior + threshold alert logic (`80%`, `100%`) using keychain flags
- `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift`
  - Receipt detail rendering with line-item fallback when `transaction.items` is nil/empty
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift`
  - Lost-card report flow and current inline state management
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`
  - Lost-card navigation entrypoint (`NavigationLink`)
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
  - Receipt navigation sources that must stay intact
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`
  - Existing stitch contract to reuse directly
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
- `mobile/ios/BankongSetonStudent/Models/BudgetModels.swift`
- `mobile/ios/BankongSetonStudent/Models/TransactionModels.swift`
  - Existing API/model contracts used by S04 flows

### Natural seams for planner tasking

1. **Budget contract seam (highest functional risk)**
   - Files: `BudgetViewModel.swift`, `BudgetView.swift`
   - Goal: explicit state channels + actionable retry/save semantics without silent failure behavior
2. **Receipt seam (redesign + stability)**
   - Files: `ReceiptView.swift` (+ optional model helpers if needed)
   - Goal: stitch-faithful receipt presentation, stable item identity iteration, scope-clean utility surface
3. **Lost-card seam (flow polish + session coherence)**
   - Files: `LostCardView.swift` (and optionally a dedicated view-model file)
   - Goal: explicit state machine and coherent post-success behavior after server-side session invalidation
4. **Navigation continuity seam**
   - Files: `HomeView.swift`, `TransactionsView.swift`, `SettingsView.swift`
   - Goal: preserve existing entrypoints while redesigning destinations
5. **Verification seam**
   - Files: new S04 pytest contracts + `scripts/verify-m007-s04.sh` + `.gsd/.../S04-UAT.md`

## Critical Constraints / Fragility

- **Do not reintroduce out-of-scope receipt actions** (D072 / R061): keep PDF/report-issue utilities absent.
- **Preserve current backend contracts** (`getBudget`, `fetchBudgetSummary`, `setBudget`, `reportLostCard`); no server contract expansion required for S04 closure.
- **Lost-card backend behavior invalidates session on success**; S04 UX must handle that coherently (avoid “success shown but app state contradictory” behavior).
- **Avoid cross-slice scope leakage into S05**: keep Settings rework minimal in S04 (focus destination flow, not full settings architecture).
- **Project file wiring constraint**: new Swift files require explicit `.xcodeproj/project.pbxproj` registration.
- **Environment constraints in this scout host**:
  - `xcodebuild` unavailable (`program not found`)
  - `/bin/bash` unavailable; local verifier scripts run with `rtk proxy sh ...` in this environment

## Don’t Hand-Roll

Use already-proven M007 patterns/components:

- `AppTheme` tokens for color/spacing/typography/radius
- `StitchCard` and `StitchPrimaryButtonStyle` for primary surfaces/actions
- Existing source-contract test style from S02/S03 (`tests/test_verify_m007_*.py`)
- Existing verifier harness style from S02/S03 (`scripts/verify-m007-s02.sh`, `scripts/verify-m007-s03.sh`)

Avoid introducing new UI frameworks or custom navigation architecture for this slice.

## What to Build/Prove First

First proof should be **S04 state coherence**, not pure styling:

1. Budget failure/success states are explicit and non-dead.
2. Lost-card success path transitions coherently with session invalidation behavior.
3. Receipt remains scope-clean and stable with duplicate line-item names.

Then apply full stitch styling and ship verifier artifacts.

## Verification Strategy (for S04 execution)

### Static/contract checks to add

- Budget view-model exposes explicit non-silent load/save failure semantics (no bare silent catches on load paths).
- Budget view uses stitch primitives/tokens and has actionable controls (save/retry/refresh where relevant).
- Lost-card flow has explicit actionable state markers (idle/loading/success/error) with no decorative dead CTA.
- Receipt view remains utility-scope-clean (assert absence of PDF/report/download/report-issue markers).
- Receipt item iteration uses stable identity strategy (not name-only collisions).
- Existing navigation sources still route to receipt and lost-card destinations.

### Suggested commands

- `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py`
- `rtk proxy sh scripts/verify-m007-s04.sh`  
  (canonical cross-platform command remains `rtk proxy bash scripts/verify-m007-s04.sh`)

### Runtime checks (macOS/Xcode host)

- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
- Manual flow checks:
  1. Budget tab: load current values, save valid limit, invalid input remains non-actionable.
  2. Budget error path: network interruption produces explicit recoverable state.
  3. Receipt path from Home and History opens redesigned receipt with correct summary/items.
  4. Receipt shows fallback line item when backend item list is empty.
  5. Lost-card path from Settings reports successfully with coherent post-success behavior.
  6. Lost-card failure path surfaces actionable retry/non-dead behavior.

### Environment note

`xcodebuild` is unavailable in this scout environment, so compile/runtime proof must be produced in macOS executor/device stages.

## Skill-Guided Implementation Notes

Rules applied from activated skills:

- **swiftui**
  - Keep one source of truth per flow state; use explicit state channels instead of implicit UI side effects.
  - Work in small verified steps (`change → verify → next`) and avoid large unverified rewrites.
- **accessibility**
  - Do not rely on color alone (budget risk status needs textual meaning, not ring color only).
  - Add clear accessibility labels/hints/identifiers for S04 controls and state cards.
- **make-interfaces-feel-better**
  - Keep controls with minimum reliable tap targets and restrained interaction feedback.
  - Avoid broad animations/transition-all style behavior; keep interactions crisp for demo pacing.
- **test**
  - Match existing repository testing conventions (pytest source-contract style) and keep checks deterministic.
- **debug-like-expert**
  - Treat lost-card session behavior as a hypothesis to verify against real endpoint semantics before locking UX transitions.
- **qodo-get-rules**
  - Load Qodo rules before implementation edits if not already loaded in the execution context.

## Skills Discovered

Core technologies for this slice:
- SwiftUI / iOS app UI state modeling
- Existing pytest-based contract verification pattern

Relevant skills already installed in environment:
- `swiftui`, `accessibility`, `make-interfaces-feel-better`, `test`, `lint`, `debug-like-expert`, `qodo-get-rules`, `frontend-design`

Missing-skill discovery attempt:
- Command: `rtk proxy npx skills find "iOS SwiftUI"`
- Result: failed (`npx` not available in this environment)

No additional skills were installed during this scout run.

## Sources

- `.gsd/DECISIONS.md` (M007 decisions D070–D080)
- `.gsd/milestones/M007/slices/S01/S01-RESEARCH.md`
- `.gsd/milestones/M007/slices/S02/S02-RESEARCH.md`
- `.gsd/milestones/M007/slices/S03/S03-RESEARCH.md`
- `.gsd/milestones/M007/slices/S03/S03-PLAN.md`
- `.gsd/milestones/M007/slices/S03/S03-UAT.md`
- `.gsd/milestones/M007/slices/S03/tasks/T01-SUMMARY.md`
- `.gsd/milestones/M007/slices/S03/tasks/T02-SUMMARY.md`
- `.gsd/milestones/M007/slices/S03/tasks/T03-SUMMARY.md`
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift`
- `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift`
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/Models/BudgetModels.swift`
- `mobile/ios/BankongSetonStudent/Models/TransactionModels.swift`
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift`
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`
- `scripts/verify-m007-s02.sh`
- `scripts/verify-m007-s03.sh`
- `tests/test_verify_m007_s03_transactions_behavior_contract.py`
- `tests/test_verify_m007_s03_transactions_design_contract.py`
- `backend/api/api_server.py`
