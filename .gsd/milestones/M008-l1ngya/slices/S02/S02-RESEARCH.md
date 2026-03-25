# S02 Research — Full UX Rollback Baseline + Native Tab Bar

**Date:** 2026-03-25  
**Slice:** M008-l1ngya/S02  
**Status:** Ready for planning

## Requirement Targeting (Active)

S02 directly owns:

- **R068** — Restore iOS surfaces to pre-M007 interaction baseline (`558d8bc`) before M008 upgrades.
- **R069** — Replace floating custom tab shell with native iOS `TabView` chrome.

S02 supports:

- **R076** (S03-owned) — rollback/minimalism must not break QR continuity.

## Summary

Targeted research. Main risk is scope interpretation, not unfamiliar tech.

### Key finding

`R069` is isolated and straightforward. `R068` is ambiguous if interpreted as full commit rollback.

- Current `MainTabView.swift` uses `StitchTabShell`.
- Baseline (`558d8bc`) `MainTabView.swift` uses native `TabView` + `.tabItem`.
- Full rollback to `558d8bc` would regress now-required contracts (student-ID-only login, QR stack presence, S01 budget reliability behavior).

**Planning interpretation:** use `558d8bc` as **structural UX reference**, not literal full-state restore.

## Recommendation

Plan S02 in this order:

1. Add S02-specific contract tests/verifier first (lock intended rollback interpretation).
2. Migrate root shell to native `TabView` (retire R069).
3. Restore Home/Transactions/Settings interaction scaffolds toward `558d8bc` while preserving post-M007 contract-critical behavior.
4. Re-run S01 iOS budget contract checks as regression guard.

## Implementation Landscape

### Primary files to change

- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`

### Verification artifacts to add

- `tests/test_verify_m008_s02_ios_rollback_contract.py`
- `scripts/verify-m008-s02.sh`

### Files to avoid churning in S02 unless explicitly re-scoped

- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/LostCardViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift`
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`

Reason: tied to S01 closure and existing contract verifiers.

## Natural Seams

### Seam A — Contract harness (first)

Define S02 contracts:

- `MainTabView` uses native `TabView` + `.tabItem`.
- `MainTabView` no longer references `StitchTabShell(`.
- Transactions S02 rollback baseline has no `.searchable(`.
- Home/Transactions/Settings expose baseline structural markers aligned to `558d8bc` reference.

### Seam B — Tab shell replacement

Implement native `TabView` root while preserving tab routing + session-expired alert behavior.

### Seam C — Baseline surface restoration

Reshape Home/Transactions/Settings toward old baseline structure without undoing required newer contracts.

### Seam D — QR scanner compile-risk containment

`Views/QR/QRScannerView.swift` currently contains duplicated `ScannerViewController` declaration blocks (merge artifact). Static marker tests can pass despite this; likely compile risk on Mac runner. Fix in S02 or carry explicit blocker-forward note into S03.

## Constraints / Fragility

- Keep login **student-ID only** (knowledge rule; no PIN contract return).
- Preserve persisted QR continuity tick pattern (`qr_payment_success_continuity_tick`) unless deliberately replaced.
- Avoid accidental S01 regressions in budget/lost-card retry/error channels.
- Host limitation: no `swift` / no `xcodebuild` on this Windows runner; verification here is source-contract based.

## What to Prove First

1. Native `TabView` replacement complete (R069).
2. S02 rollback contract tests pass.
3. S01 iOS budget contract still passes after S02 edits.
4. Student-ID-only login contract still passes.

## Verification Commands

S02 (to add and use):

- `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py`
- `rtk proxy bash scripts/verify-m008-s02.sh`

Regression guards already available:

- `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m007_s09_override_contract.py::test_login_state_and_payload_are_student_id_only`

Windows shell fallback (from project knowledge):

- `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s02.sh`

## Skill-Guided Rules Applied

- **swiftui**: platform-native navigation idioms (`TabView`) and incremental verified changes.
- **build-iphone-apps**: change → verify → next change, avoid large unverified rollback batches.

## Skills Discovered

Relevant installed skills already present:

- `swiftui`
- `build-iphone-apps`
- `test`

Skill discovery for new additions was blocked:

- `rtk proxy npx skills find "xcodebuild"` → `npx` not found.

No new skills installed.

## Sources

- Preloaded milestone artifacts: `ROADMAP`, `CONTEXT`, `DECISIONS`, `REQUIREMENTS`, `KNOWLEDGE`.
- Current iOS sources under `mobile/ios/BankongSetonStudent/` (MainTabView, Home/Transactions/Settings/Budget/LostCard, APIClient, login models/viewmodels, QR views).
- Baseline references via `git show 558d8bc:<path>` for MainTabView/Home/Transactions/Settings.
- Existing verification assets reviewed:
  - `scripts/verify-m008-s01.sh`
  - `tests/test_verify_m008_s01_ios_budget_contract.py`
  - `tests/test_verify_m007_s09_override_contract.py`
  - `tests/test_verify_m007_s01_shell_login_contract.py`
  - `tests/test_verify_m007_s02_qr_behavior_contract.py`
