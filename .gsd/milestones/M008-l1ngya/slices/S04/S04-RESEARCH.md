# S04 Research — Transactions/Settings Minimalist Scope Restoration

**Date:** 2026-03-27  
**Slice:** M008-l1ngya/S04  
**Status:** Ready for planning

## Requirement Targeting (Active)

S04 directly owns:

- **R071** — Transactions is filter-only (no search bar).
- **R072** — Settings appearance controls are limited to theme + accent.

S04 supports:

- **R076 (guard continuity)** — maintain QR success continuity protections while Transactions/Settings rollback lands.
- **R069 (regression guard)** — keep native TabView shell guard active by chaining upstream verifier (`S03 -> S02`).

## Summary

Targeted research. Technology is familiar (SwiftUI + pytest source contracts); risk is **using the wrong regression gates** and blocking intended rollback changes.

### Core findings

1. **Transactions currently enforces search + filter together; S04 needs filter-only.**  
   `TransactionsView.swift` currently includes:
   - `.searchable(text: $viewModel.searchQuery, prompt: "Search by type, date, or amount")`
   - `hasActiveSearchOrFilter` and `Clear Search & Filter` controls
   - continuity hooks (`@AppStorage("qr_payment_success_continuity_tick")`, `.task(id: ...)`, `refreshAfterQRSuccessContinuity`)

2. **Transactions continuity seam is independent of search UI and must be preserved.**  
   Continuity seam lives in:
   - `TransactionsView.swift` (`@AppStorage` tick + `.task(id:)` consumer)
   - `TransactionsViewModel.swift` (`lastHandledQRSuccessContinuityTick`, dedupe guard, `refreshAfterQRSuccessContinuity`)

3. **Settings currently includes three surfaces, not minimalist scope.**  
   `SettingsView.swift` currently renders:
   - `personalInfoCard` (display-name field + Save Personal Info)
   - `appearanceCard` (theme + accent options + Apply Accent)
   - `accountActionsCard` (Report Lost Card + Logout)

4. **Appearance controls are already theme+accent-only, but Personal Info is extra scope.**  
   `appearanceCard` itself is in-scope; `personalInfoCard` is likely out-of-scope for S04 minimalist restoration.

5. **Legacy M007 suites will conflict with S04 intent if chained directly.**  
   Currently green suites:
   - `tests/test_verify_m007_s03_transactions_design_contract.py`
   - `tests/test_verify_m007_s05_settings_design_contract.py`

   These explicitly require markers S04 is likely to remove (search wiring, personal-info controls). They should **not** be used as S04 closure gates.

6. **Upstream phased guard chain is healthy and should be reused unchanged.**  
   `rtk proxy C:/Progra~1/Git/bin/bash.exe scripts/verify-m008-s03.sh` currently passes and already chains `verify-m008-s02.sh` (tab shell + budget + QR + login guards).

## Recommendation

Use a **new S04-specific contract suite + phased verifier**, then chain upstream S03 guards.

- Add S04 contracts that assert:
  - Transactions has filter picker but no searchable surface.
  - Transactions QR continuity hooks remain wired.
  - Settings keeps theme+accent appearance controls.
  - Settings removes personal-info editing surface.
  - (If retained) lost-card/logout account actions remain actionable.
- Add `scripts/verify-m008-s04.sh` with phases:
  1. `s04-transactions-settings-contract`
  2. `s04-local-continuity` (if separated)
  3. `s03-regression-chain`

This keeps rollback intent explicit while preserving inherited safety rails.

## Implementation Landscape

### Files that define S04 behavior

- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
  - Search bar + filter controls + explicit state cards + load-more UI + continuity tick consumer.
- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`
  - Canonical+derived list state; filter/search derivation; continuity tick dedupe.
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`
  - Personal Info / Appearance / Account Actions cards.
- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift`
  - Theme/accent persistence, optional display-name persistence channel, logout action wrapper.

### Files to add for closure

- `tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py` (new)
- `scripts/verify-m008-s04.sh` (new, phased verifier chaining `scripts/verify-m008-s03.sh`)

## Natural Seams (planner-ready)

### Seam A — Transactions filter-only rollback

Scope:
- Remove `.searchable(...)` UI surface from `TransactionsView.swift`.
- Keep segmented filter path (`selectedFilter`) and filter reset action.
- Preserve continuity tick hooks and load-more/error-state channels.

Risk note:
- If `searchQuery` is removed from VM/model, this is wider blast radius. Lowest-risk route is UI removal first, VM cleanup optional.

### Seam B — Settings minimalist scope restoration

Scope:
- Keep `appearanceCard` (theme + accent only).
- Remove `personalInfoCard` from rendered UI.
- Decide whether to retain `accountActionsCard` (recommended: retain to avoid regressing logout/lost-card actionability).

Risk note:
- Hard-removing display-name persistence channels from VM/Home creates cross-file drift; not required to satisfy R072.

### Seam C — S04 contract + phased verifier

Scope:
- Add S04 source-contract tests for no-search + appearance scope.
- Add phased script `verify-m008-s04.sh` and chain `verify-m008-s03.sh`.
- Use Windows-safe short Git Bash path in verification guidance/plan commands.

## Constraints / Fragility

- **Do not chain legacy M007 design suites** for S04 closure; they encode pre-rollback scope (search + personal info required).
- **Preserve QR continuity seam markers** in Transactions (`@AppStorage` tick, task(id:), VM dedupe guard).
- **Keep no-space Git Bash invocation** for plan-level verifier command strings: `C:/Progra~1/Git/bin/bash.exe`.
- **Auth clear boundary remains active:** settings-owned keys (`theme_mode`, `settings_accent_hex`, `settings_display_name`) must not be deleted by `AuthManager.clearAll()`.
- **Accent options must stay aligned to `AppTheme.accentPairsByHex`**.

## What to Prove First

1. New S04 contract test correctly distinguishes intended removals (search/personal-info) from regressions.
2. Transactions filter-only surface compiles and still handles QR continuity refresh path.
3. Settings renders only intended minimalist scope for this slice.
4. Upstream S03 verifier chain remains green after S04 edits.

## Verification Strategy

### Current baseline (already green during research)

- `rtk proxy python -m pytest -q tests/test_verify_m007_s03_transactions_design_contract.py tests/test_verify_m007_s05_settings_design_contract.py`
- `rtk proxy C:/Progra~1/Git/bin/bash.exe scripts/verify-m008-s03.sh`

### Expected S04 closure commands

- `rtk proxy python -m py_compile tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py`
- `rtk proxy C:/Progra~1/Git/bin/bash.exe scripts/verify-m008-s04.sh`

### Suggested `verify-m008-s04.sh` phases

- `preflight`
- `s04-transactions-settings-contract`
- `s04-continuity-guard` (if split from contract file)
- `s03-regression-chain`

## Skill-Guided Rules Applied

From loaded `swiftui` skill:

- **Platform-adaptive design:** prefer native/simple SwiftUI surfaces for rollback minimalism over layered custom chrome.
- **Single source of truth:** keep transaction continuity state ownership in existing VM+AppStorage seam; avoid duplicate continuity flags.
- **Prove, don’t promise:** closure should remain command-verifiable via phased scripts and source contracts.

## Skills Discovered

Already installed and relevant:
- `swiftui`
- `test`

Discovery attempt for potentially missing test-ecosystem skill:
- `rtk proxy npx skills find "pytest"`
- Result: blocked (`npx` not available in this environment)

No additional skills installed in this research unit.

## Sources

- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`
- `mobile/ios/BankongSetonStudent/Models/TransactionModels.swift`
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`
- `mobile/ios/BankongSetonStudent/App/ContentView.swift`
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift`
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
- `tests/test_verify_m007_s03_transactions_behavior_contract.py`
- `tests/test_verify_m007_s03_transactions_design_contract.py`
- `tests/test_verify_m007_s05_settings_behavior_contract.py`
- `tests/test_verify_m007_s05_settings_design_contract.py`
- `tests/test_verify_m007_s07_integration_behavior_contract.py`
- `tests/test_verify_m007_s09_override_contract.py`
- `scripts/verify-m008-s02.sh`
- `scripts/verify-m008-s03.sh`
- Baseline references via:
  - `rtk git show 558d8bc:mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
  - `rtk git show 558d8bc:mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`
  - `rtk git show 558d8bc:mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`
  - `rtk git show 558d8bc:mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift`
