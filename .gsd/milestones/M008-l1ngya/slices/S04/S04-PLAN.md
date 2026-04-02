# S04: Transactions/Settings Minimalist Scope Restoration

**Goal:** R071 (filter-only transactions, no search bar) and R072 (theme+accent-only Settings) are implemented in source files, verified by S04-specific contracts, and the S03→S02 regression guard chain remains green.
**Demo:** After this: Transactions is filter-only (no search) and Settings exposes theme+accent-only appearance controls.

## Tasks
- [x] **T01: Removed search UI from TransactionsView and personal info card from SettingsView; renamed filter variable and updated labels/accessibility IDs.** — ## Remove search UI from TransactionsView and personal info card from SettingsView

### Files to modify
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`

### Steps — TransactionsView.swift
1. Read `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`.
2. Remove the entire `.searchable(text: $viewModel.searchQuery, placement: .navigationBarDrawer(displayMode: .always), prompt: "Search by type, date, or amount")` modifier block from the `NavigationStack` body. The search binding `viewModel.searchQuery` stays in the VM for backward compatibility; only the UI surface is removed.
3. Rename `hasActiveSearchOrFilter` to `hasActiveFilter` and change its body to: `viewModel.selectedFilter != .all`. This makes the "clear" toggle reflect only active filter state after search is removed.
4. In `filterControlsCard`, change the `Button` label from `Label("Clear Search & Filter", systemImage: "xmark.circle")` to `Label("Clear Filter", systemImage: "xmark.circle")`. Keep the call to `viewModel.clearSearchAndFilter()` — it is idempotent for filter-only use and keeps the VM contract intact. Update the `accessibilityIdentifier` to `"transactions-clear-filter-button"` and `accessibilityHint` to `"Resets type filter"`.
5. Keep the filter `Picker` (segmented `TransactionFilter` control), the `filterControlsCard` wrapping `StitchCard`, all `transactionStateRows`, the QR continuity tick `task(id: qrPaymentSuccessContinuityTick)` and `@AppStorage` property, the `.refreshable` modifier, the `NavigationStack` outer wrapper, and all `@EnvironmentObject` / `@StateObject` properties. No changes to those.

### Steps — SettingsView.swift
1. Read `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`.
2. In the root `VStack(spacing: AppTheme.Spacing.lg)` inside `ScrollView`, remove the line `personalInfoCard`. The resulting VStack content should be:
   ```swift
   appearanceCard
   accountActionsCard
   ```
3. Keep `appearanceCard` (theme picker + accent options + Apply Accent button + status text), `accountActionsCard` (Report Lost Card navigation link + destructive Logout button), the `NavigationStack`, the `preferredColorScheme` modifier, and all `@EnvironmentObject` / `@StateObject` properties. No changes to those.
4. Do NOT delete `SettingsViewModel`'s `editableDisplayName` property, `personalInfoSaveState` enum, or `savePersonalInfo()` method — they are still referenced in the VM and removing them would cause compile errors in the VM. S04 is a UI-only rollback, not a VM cleanup pass.

### Verify
Run `rtk proxy python -m py_compile mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` and `rtk proxy python -m py_compile mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift` to confirm syntactic validity. Actual compilation requires Xcode; source-level check confirms no obvious syntax errors.
  - Estimate: 15-30 min
  - Files: mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift, mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift
  - Verify: rtk proxy python -m py_compile mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift && rtk proxy python -m py_compile mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift && echo "T01 source edits verified"
- [x] **T02: S04 rollback contract test (4 tests), S04 verifier shell script, updated S07/S05 contracts, and full source cleanup all done — chain green** — ## Update M007 continuity contracts + add S04 contracts + write phased verifier

### Files to modify
- `tests/test_verify_m007_s07_integration_behavior_contract.py`
- `tests/test_verify_m007_s05_settings_design_contract.py`

### Files to create
- `tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py`
- `scripts/verify-m008-s04.sh`

---

### Steps — Update S07 continuity contract

`tests/test_verify_m007_s07_integration_behavior_contract.py` currently asserts `.searchable(` is present in `TransactionsView.swift`. S04 removes that modifier, so this assertion must be updated to match the new filter-only baseline. The S03 verifier chains S07, so this update is required to keep the S03→S02 guard chain green after S04 lands.

1. Read `tests/test_verify_m007_s07_integration_behavior_contract.py`.
2. In `test_transactions_search_filter_load_more_continuity_markers_remain_intact`, inside the `TRANSACTIONS_VIEW_PATH` assertions block:
   - REMOVE: `"'.searchable('",`
   - REMOVE: `"'text: $viewModel.searchQuery',",`
   - REMOVE: `"'\"transactions-clear-search-filter-button\"'",`
   - ADD after `"'Picker(\\"Transaction Type\\", selection: $viewModel.selectedFilter)',": `"'\"transactions-filter-picker\"'",` (assert the filter picker identifier is present).
3. Rename the test function from `test_transactions_search_filter_load_more_continuity_markers_remain_intact` to `test_transactions_filter_only_and_load_more_continuity_markers_remain_intact`.
4. Add a new `assert_required_markers` block inside the `TRANSACTIONS_VIEW_PATH` section asserting the absence of searchable UI surface is confirmed by presence of the filter picker:
   ```python
   assert_required_markers(
       TRANSACTIONS_VIEW_PATH,
       [
           'Picker("Transaction Type", selection: $viewModel.selectedFilter)',
           'ForEach(TransactionFilter.allCases, id: \\.(self))',
           '"transactions-filter-picker"',
       ],
       "transactions_filter_only",
   )
   ```
5. Keep ALL other assertions in S07 unchanged (QR continuity tick, receipt navigation, VM dedupe guard, Settings lost-card/logout actionability).

---

### Steps — Update S05 settings design contract

`tests/test_verify_m007_s05_settings_design_contract.py` asserts `"Personal Info"` and several personal-info accessibility identifiers are rendered in `SettingsView.swift`. S04 removes `personalInfoCard`, so this assertion must be updated.

1. Read `tests/test_verify_m007_s05_settings_design_contract.py`.
2. In `test_settings_scope_cleanup_keeps_only_in_scope_actions_visible`:
   - REMOVE `"Personal Info",` from `required_entries`.
   - In `test_settings_design_contract_requires_stitch_surface_tokens_status_markers_and_actionable_controls`:
     - REMOVE `"settings-display-name-field",`
     - REMOVE `"settings-save-personal-info-button",`
     - REMOVE `"settings-personal-info-status",`
     - REMOVE `"editableDisplayName",`
     - REMOVE `"savePersonalInfo",`
   - ADD to `required_entries` after the existing ones: `"appearanceCard",` and `"accountActionsCard",` to explicitly assert these cards remain.

---

### Steps — Create S04 rollback contract test

1. Create `tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py` using the same structure as `tests/test_verify_m008_s03_ios_home_rollback_contract.py` as a reference pattern.
2. Add these test functions:

a. `test_transactions_is_filter_only_with_no_searchable_surface`:
   - Assert `.searchable(` is NOT in `TransactionsView.swift` (forbidden marker).
   - Assert `.searchable(text:` is NOT in `TransactionsView.swift`.
   - Assert `Picker("Transaction Type", selection: $viewModel.selectedFilter)` IS present.
   - Assert `"transactions-filter-picker"` IS present.
   - Assert `"transactions-clear-filter-button"` IS present.

b. `test_transactions_qr_continuity_seam_remains_intact_after_rollback`:
   - Assert `@AppStorage("qr_payment_success_continuity_tick")` IS present in `TransactionsView.swift`.
   - Assert `.task(id: qrPaymentSuccessContinuityTick)` IS present.
   - Assert `await viewModel.refreshAfterQRSuccessContinuity(` IS present.
   - Assert `lastHandledQRSuccessContinuityTick` IS present in `TransactionsViewModel.swift`.
   - Assert `guard continuityTick > lastHandledQRSuccessContinuityTick` IS present.

c. `test_transactions_receipt_and_load_more_remain_actionable`:
   - Assert `.navigationDestination(for: Transaction.self)` IS present.
   - Assert `ReceiptView(transaction: transaction)` IS present.
   - Assert `viewModel.loadMore(apiClient:` IS present.
   - Assert `"transactions-load-more-button"` IS present.

d. `test_settings_appearance_and_account_cards_render_without_personal_info_card`:
   - Assert `appearanceCard` IS present in `SettingsView.swift`.
   - Assert `accountActionsCard` IS present in `SettingsView.swift`.
   - Assert `"Personal Info"` is NOT present (forbidden — personalInfoCard is removed).
   - Assert `personalInfoCard` IS NOT present (forbidden).
   - Assert `"Report Lost Card"` IS present.
   - Assert `"Logout"` IS present.

---

### Steps — Create phased S04 verifier

1. Create `scripts/verify-m008-s04.sh` modeled after `scripts/verify-m008-s03.sh`. Use `C:/Progra~1/Git/bin/bash.exe` for all bash invocations.
2. Required files to check in preflight: `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`, `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`, `tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py`, `scripts/verify-m008-s03.sh`.
3. Phases to run in order:
   a. `preflight` — require all required files.
   b. `s04-transactions-settings-contract` — run `rtk proxy python -m pytest -q tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py`.
   c. `s03-regression-chain` — run `rtk proxy C:/Progra~1/Git/bin/bash.exe scripts/verify-m008-s03.sh` (which chains S02).
   d. `status=passed` on full success.
4. Each phase uses `fail_with_guidance` with `guidance=` output for failure localization.

### Verify
```
rtk proxy python -m py_compile tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py && \
rtk proxy python -m pytest -q tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py && \
rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py && \
rtk proxy python -m pytest -q tests/test_verify_m007_s05_settings_design_contract.py && \
rtk proxy C:/Progra~1/Git/bin/bash.exe scripts/verify-m008-s04.sh
```
All commands should exit 0 / pass.
  - Estimate: 30-45 min
  - Files: tests/test_verify_m007_s07_integration_behavior_contract.py, tests/test_verify_m007_s05_settings_design_contract.py, tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py, scripts/verify-m008-s04.sh
  - Verify: rtk proxy python -m py_compile tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py && rtk proxy python -m pytest -q tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py && rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py && rtk proxy python -m pytest -q tests/test_verify_m007_s05_settings_design_contract.py && rtk proxy C:/Progra~1/Git/bin/bash.exe scripts/verify-m008-s04.sh
