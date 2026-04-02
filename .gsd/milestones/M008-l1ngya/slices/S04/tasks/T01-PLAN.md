---
estimated_steps: 21
estimated_files: 2
skills_used: []
---

# T01: Rollback Transactions/Settings to minimalist scope

## Remove search UI from TransactionsView and personal info card from SettingsView

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

## Inputs

- None specified.

## Expected Output

- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`

## Verification

rtk proxy python -m py_compile mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift && rtk proxy python -m py_compile mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift && echo "T01 source edits verified"
