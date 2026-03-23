---
estimated_steps: 5
estimated_files: 7
skills_used:
  - qodo-get-rules
  - build-iphone-apps
  - swiftui
  - test
  - debug-like-expert
---

# T02: Implement override UI remediation (stitch parity, dark-mode default, no PIN, new transaction filters)

**Slice:** S09 — Override Remediation + Final Device Acceptance Closure
**Milestone:** M007

## Description

Apply the user-issued override that reopens M007 UX acceptance. This task removes legacy visual/interaction regressions by enforcing dark-mode startup, removing PIN from login, and replacing transaction filters with `QR Pay`, `Card Pay`, and `Load`.

## Steps

1. Update app bootstrap/theme wiring so the student app launches in dark mode by default for authenticated and unauthenticated flows.
2. Refactor login UI/view-model to remove PIN input/state while preserving required sign-in behavior and stitch reference layout parity.
3. Update transactions filter taxonomy in view + view-model logic: remove `Debit`/`Credit Card`, add `QR Pay`/`Card Pay`/`Load`, and map them deterministically to existing transaction data.
4. Sweep affected surfaces for remaining legacy UI markers on overridden screens and align spacing/typography/components with stitch references.
5. Add/refresh override contract checks (`tests/test_verify_m007_s09_override_contract.py`) so future regressions on dark mode/PIN/filter taxonomy fail fast.

## Must-Haves

- [ ] Dark mode is the default launch appearance (no light-first startup regression).
- [ ] Login has no PIN field/control/state in visible UI.
- [ ] Transactions filter options visible to users are exactly `QR Pay`, `Card Pay`, and `Load`.
- [ ] Override contract tests exist and fail on legacy labels/components.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s09_override_contract.py`
- `rtk proxy python -c "from pathlib import Path; app=Path('mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift').read_text(encoding='utf-8'); assert '.dark' in app or 'UIUserInterfaceStyle' in app"`
- `rtk proxy python -c "from pathlib import Path; login=Path('mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift').read_text(encoding='utf-8'); assert 'PIN' not in login, 'PIN control still present'"`
- `rtk proxy python -c "from pathlib import Path; tx=Path('mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift').read_text(encoding='utf-8'); required=['QR Pay','Card Pay','Load']; missing=[x for x in required if x not in tx]; assert not missing, missing; banned=['Debit','Credit Card']; bad=[x for x in banned if x in tx]; assert not bad, bad"`

## Observability Impact

- Signals added/changed: override-specific static contracts for theme mode, login field set, and transaction filter taxonomy.
- How a future agent inspects this: run `tests/test_verify_m007_s09_override_contract.py`, then inspect login/transactions/app-bootstrap source.
- Failure state exposed: diagnostics identify whether failure is `dark_mode_default`, `login_pin_present`, `legacy_filter_label`, or `stitch_drift`.

## Inputs

- `mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift` — startup theme and root-shell wiring.
- `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift` — login visual/control surface.
- `mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift` — login state handling.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — filter chip UI.
- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift` — filter behavior mapping.
- `C:\Users\admin\Downloads\stitch_redesigned_login` — visual parity source.

## Expected Output

- Updated iOS source implementing override fixes for dark mode, login, and transactions filters.
- `tests/test_verify_m007_s09_override_contract.py` covering the new acceptance markers.
- No remaining visible legacy `PIN` login control or `Debit`/`Credit Card` filter taxonomy in overridden screens.
