---
estimated_steps: 90
estimated_files: 4
skills_used: []
---

# T02: Create S04 contracts, update S07/S05 contracts, and build phased verifier

## Update M007 continuity contracts + add S04 contracts + write phased verifier

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

## Inputs

- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`

## Expected Output

- `tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py`
- `scripts/verify-m008-s04.sh`
- `tests/test_verify_m007_s07_integration_behavior_contract.py`
- `tests/test_verify_m007_s05_settings_design_contract.py`

## Verification

rtk proxy python -m py_compile tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py && rtk proxy python -m pytest -q tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py && rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py && rtk proxy python -m pytest -q tests/test_verify_m007_s05_settings_design_contract.py && rtk proxy C:/Progra~1/Git/bin/bash.exe scripts/verify-m008-s04.sh
