---
estimated_steps: 8
estimated_files: 1
skills_used: []
---

# T02: Create S05 integration contract test

Create `tests/test_verify_m008_s05_ios_integration_contract.py` with pytest tests that:
1. Assert MainTabView uses native TabView with four Label tab items (from S02)
2. Assert HomeView contains QR entry CTA and credit-card balance presentation (from S03)
3. Assert TransactionsView has filter-only chips (no search bar) and QR Pay/Card Pay/Load taxonomy (from S04)
4. Assert BudgetView references budget endpoints (from S01)
5. Assert SettingsView has theme+accent controls only (from S04)
6. Assert no forbidden markers: no StitchTabShell, no search bar in transactions, no fullscreen-stitch elements
Name the test file correctly so it is picked up by pytest conventions.

## Inputs

- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift`
- `tests/test_verify_m008_s02_ios_rollback_contract.py`
- `tests/test_verify_m008_s03_ios_home_rollback_contract.py`
- `tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py`

## Expected Output

- `tests/test_verify_m008_s05_ios_integration_contract.py`

## Verification

rtk proxy python -m pytest -q tests/test_verify_m008_s05_ios_integration_contract.py → all tests pass
