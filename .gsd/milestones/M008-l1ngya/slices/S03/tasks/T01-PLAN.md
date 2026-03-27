---
estimated_steps: 5
estimated_files: 4
skills_used:
  - qodo-get-rules
  - swiftui
  - build-iphone-apps
  - test
---

# T01: Refactor HomeView to minimalist credit-card hero while preserving QR continuity seam

**Slice:** S03 — Home Rollback + Credit-Card Hero + QR Continuity
**Milestone:** M008-l1ngya

## Description

Implement the user-facing S03 rollback by simplifying `HomeView` to a minimalist credit-card hero flow while preserving the existing QR success continuity seam required by R076.

## Failure Modes

| Dependency | On error | On timeout | On malformed response |
|------------|----------|-----------|----------------------|
| `HomeViewModel.load(...)` data path | Keep error card/retry surface visible; do not crash or hide Home content | Keep refresh path retriable (`.refreshable` + task reload) and avoid stuck loading states | Preserve safe rendering via existing model defaults and keep diagnostics visible |
| `QRPayView` success callback path | Preserve one-shot guard and continuity tick to avoid duplicate side effects | Do not trap sheet dismissal; allow next presentation to reset guard | Ignore duplicate callback for same presentation and keep single continuity increment |

## Load Profile

- **Shared resources**: Home load/refresh API path and recent transactions rendering.
- **Per-operation cost**: one post-success refresh plus normal initial load.
- **10x breakpoint**: duplicate QR success callbacks creating refresh churn if dedupe guard regresses.

## Negative Tests

- **Malformed inputs**: empty display name and empty transactions list still render stable Home layout.
- **Error paths**: failed refresh after QR completion still leaves visible diagnostics and usable retry path.
- **Boundary conditions**: repeated success callback during one sheet presentation increments continuity tick exactly once.

## Steps

1. Load repo constraints via `qodo-get-rules`, then inspect current Home structure and continuity seam markers in `HomeView.swift` before editing.
2. Refactor Home layout to minimalist credit-card hero composition (name, balance, `Current Balance`) and keep lightweight QR entry + recent transactions sections.
3. Preserve QR continuity mechanics exactly: `didConsumePresentedQRSuccess`, `@AppStorage("qr_payment_success_continuity_tick")`, one-shot guard, tick increment, and `refreshAfterQRSuccess(...)` call.
4. Keep error/loading/empty states understandable with simpler composition and no shell-level/tab-level changes.
5. Run targeted continuity-node regression test and iterate until passing.

## Must-Haves

- [ ] `HomeView.swift` expresses a minimalist credit-card hero with student name + peso balance + `Current Balance` label.
- [ ] QR entry button and `.sheet(isPresented: $showQrPay)` wiring remain intact.
- [ ] Continuity seam markers remain present and behaviorally unchanged.
- [ ] No reintroduction of custom floating shell/tab abstractions.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py::test_qr_success_handoff_remains_wired_from_home_sheet_to_refresh_path`
- `rtk grep "qr_payment_success_continuity_tick\|didConsumePresentedQRSuccess\|handleQRPaySuccessCompletion" mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`

## Observability Impact

- Signals added/changed: preserves Home QR continuity logs and duplicate-callback guard logs.
- How a future agent inspects this: run the targeted continuity-node pytest above and inspect Home seam markers.
- Failure state exposed: continuity seam drift is surfaced by missing-marker assertions and failing refresh-path checks.

## Inputs

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`
- `tests/test_verify_m007_s07_integration_behavior_contract.py`

## Expected Output

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
