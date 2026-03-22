# S03 Research — Transactions Redesign + Search/Filter + State Fidelity

**Date:** 2026-03-22  
**Status:** Ready for planning

## Requirement Targeting (Active)

S03 directly owns/supports:

- **Owns:**
  - **R058** — Transactions Search + Filter in iOS
  - **R059** — State-fidelity screens (loading/empty/error/populated behavior for transactions)
- **Supports:**
  - **R055** — Stitch-faithful redesign continuity on Transactions surface
  - **R056** — No dead controls in visible in-scope UI
  - **R063** — On-device demo readiness (transactions path must be coherent)

## Summary

This slice is **targeted research** (known stack, moderate integration risk). The current Transactions screen is partially stitch-themed from S01, but it does **not** implement search/filter yet, and current state handling is too coarse for full R059 fidelity.

### Current baseline in code

- `TransactionsView.swift` already uses `AppTheme`, `StitchCard`, `StitchPrimaryButtonStyle`, and preserves receipt navigation for navigable transactions.
- `TransactionsViewModel.swift` supports initial load + manual load-more with offset-based pagination.
- UI currently has these states:
  - loading overlay
  - error overlay
  - empty overlay
  - populated list + optional load-more card
- There is **no search UI** (`.searchable` not used) and **no filter UI** (chips/menu/segmented control absent).
- Existing test scaffolding for M007 covers S01/S02 only; there are currently **no S03 contract tests**.

### High-risk behavior gaps found

1. **Search/filter missing entirely** (direct R058 gap).
2. **State fidelity granularity is insufficient** (R059 risk):
   - `errorMessage` is a single channel for both initial and pagination failures.
   - Pagination errors can currently mask a populated list with global error overlay behavior.
3. **Pagination contract fragility**:
   - `hasMore = resp.hasMore ?? false` means pagination dies if backend omits `has_more`.
   - Repo backend (`backend/api/api_server.py`) currently documents only `limit` and does not emit `has_more`; offset/filter server params are not present there.
   - Therefore, planner should treat server-side search/filter as unavailable unless explicitly proven in runtime environment.

## Recommendation

Plan S03 around **data/state contract first, UI second**:

1. **Harden transactions state model in ViewModel**
   - separate initial-load state from pagination failure state
   - maintain unfiltered source list + derived filtered list
   - prevent dead-end behavior when filters produce no matches
2. **Add search/filter UI using native SwiftUI surfaces**
   - `.searchable` for text query
   - explicit filter controls (type-first, with “All” default)
3. **Finish with explicit S03 verifier artifacts**
   - pytest source-contract tests (same style as S01/S02)
   - one-command slice verifier script

This sequence retires the highest risk first (state correctness under load/error/filter interactions) before visual polish.

## Implementation Landscape

### Key files and current role

- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
  - Main transactions screen; list rendering, load-more control, state overlays, receipt navigation destination.
- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`
  - Pagination + loading flags + error state.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift`
  - Row visuals and type classification (debit/credit semantics + labels).
- `mobile/ios/BankongSetonStudent/Models/TransactionModels.swift`
  - Transaction model and `isNavigable` logic; candidate place for filter semantics helpers.
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
  - `getTransactions(limit:offset:)` contract (no search/filter params exposed).
- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`
  - History tab entrypoint (`TransactionsView()`) used in full app flow.
- `backend/api/api_server.py`
  - Repo backend reference for `/api/student/transactions` behavior (limit-based history; no explicit search/filter/offset handling in this implementation).
- `tests/test_verify_m007_s01_*.py`, `tests/test_verify_m007_s02_*.py`
  - Existing contract-test style to replicate for S03.
- `scripts/verify-m007-s02.sh`
  - Existing verifier pattern to clone/adapt for S03.

### Natural seams for planner tasking

1. **State contract seam (highest risk)**
   - `TransactionsViewModel.swift`
   - introduce filtered-data derivation + clearer state split:
     - initial loading/error
     - pagination loading/error
     - filtered-empty vs base-empty
2. **Filter/search semantics seam**
   - `TransactionModels.swift` (+ possibly `TransactionsViewModel.swift`)
   - centralize transaction-type grouping and searchable text normalization
3. **UI seam (stitch surface + controls)**
   - `TransactionsView.swift`
   - add search + filter controls with tokenized styling and non-dead interactions
4. **Verification seam**
   - new S03 pytest contracts + `scripts/verify-m007-s03.sh`

## Critical Constraints / Fragility

- **Do not assume backend search/filter support.** Current iOS client and repo backend do not expose it.
- **Preserve existing load-more continuity** while adding filters; filtering must not silently break pagination controls.
- **No decorative dead controls**: any filter chip/menu button shown must mutate visible results/state (R056).
- **Type strings vary by backend path** (`purchase`, `nfc purchase`, `nfc`, `payment`, `load`, `top-up`, `credit`), so filter logic must normalize centrally.
- **Manual Xcode project registration remains a constraint** for new Swift files in this repo (`project.pbxproj` explicit source listing).

## Don’t Hand-Roll

Use already-proven patterns/components:

- `AppTheme` + `StitchCard` + `StitchPrimaryButtonStyle` for visual consistency
- SwiftUI-native search surface (`.searchable`) instead of custom text-field plumbing
- Existing state-machine style from recent M007 work (explicit transitions/reasons in ViewModel where helpful)
- Existing verifier style (pytest contract checks + bash orchestration script)

## Verification Strategy (for S03 execution)

### Static/contract checks (new S03 checks to add)

- Search + filter controls are present and wired in `TransactionsView.swift`.
- ViewModel exposes explicit filter/search state and derives displayed list from source list.
- State-fidelity markers exist for:
  - loading
  - base empty
  - filtered empty (no matches)
  - error (initial and/or pagination)
  - populated state
- Load-more control still calls `viewModel.loadMore(...)` and remains reachable.

### Suggested commands

- `rtk proxy python -m pytest -q tests/test_verify_m007_s03_transactions_behavior_contract.py tests/test_verify_m007_s03_transactions_design_contract.py`
- `rtk proxy bash scripts/verify-m007-s03.sh`

### Runtime checks (macOS/Xcode host)

- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
- Manual flow:
  1. Open History tab with populated data
  2. Search text narrows results immediately
  3. Filter controls change result set meaningfully
  4. No-match state appears with clear recovery action
  5. Load More still works and updates results
  6. Error path does not make the screen feel dead

### Environment note

`xcodebuild` is unavailable in this scout environment (`program not found`), so compile/runtime proof must be produced by macOS executor stage.

## Skill-Guided Implementation Notes

Applied from loaded skills:

- **swiftui**: keep a single source of truth in ViewModel (`allTransactions` + derived `displayedTransactions`), and verify changes with build/tests rather than assumptions.
- **debug-like-expert**: verify real backend contract before assuming server-side filtering/offset semantics; treat unknown API behavior as a testable hypothesis.
- **accessibility**: search/filter controls must have clear labels and non-color-only status signaling; empty/error messages should be descriptive.
- **make-interfaces-feel-better**: keep filter controls tactile and restrained (minimum tap targets, subtle press feedback, avoid over-animation).
- **test**: follow existing repository contract-test style (path-based source assertions + deterministic verifier script).
- **qodo-get-rules**: load org/repo rules before implementation edits if rules have not already been loaded in execution context.

## Skill Discovery (suggest)

Core technologies for this slice:
- SwiftUI/iOS (installed skill available: `swiftui`)
- UI polish/accessibility/testing (installed skills available: `make-interfaces-feel-better`, `accessibility`, `test`)

Missing-skill discovery attempt:
- `rtk npx skills find "AVFoundation"`
- Result in this environment: `program not found` (npx unavailable)

No install action taken.

## Sources

- `.gsd/REQUIREMENTS.md` (R055–R063 mapping)
- `.gsd/DECISIONS.md` (D070–D079, especially M007 scope/state constraints)
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`
- `mobile/ios/BankongSetonStudent/Models/TransactionModels.swift`
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`
- `backend/api/api_server.py` (`/api/student/transactions` behavior)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/TransactionsActivity.kt` (prior-art filter semantics)
- `tests/test_verify_m007_s01_design_system_contract.py`
- `tests/test_verify_m007_s01_shell_login_contract.py`
- `tests/test_verify_m007_s02_qr_behavior_contract.py`
- `scripts/verify-m007-s02.sh`
