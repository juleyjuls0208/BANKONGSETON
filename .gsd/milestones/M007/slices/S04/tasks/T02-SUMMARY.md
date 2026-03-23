---
id: T02
parent: S04
milestone: M007
provides:
  - Stitch-faithful Budget/Receipt/Lost-Card SwiftUI surfaces using AppTheme + StitchCard + stitch action styling
  - Explicit and accessible Budget/Lost-Card state cards with actionable save/retry/refresh/report CTAs
  - S04 design contract test coverage for scope-clean receipt UX, stable line-item identity, and navigation continuity anchors
key_files:
  - mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift
  - mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift
  - mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift
  - tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py
  - .gsd/milestones/M007/slices/S04/S04-PLAN.md
key_decisions:
  - Receipt line-item rendering now uses indexed identity (`Array(lineItems.enumerated())` with `id: \.index`) to prevent duplicate-name collisions.
  - S04 source-contract stability for LostCard keeps literal button-title markers (`Button("Report Lost Card")`, `Button("Retry Report")`) where behavior tests assert exact source anchors.
patterns_established:
  - Model explicit UI states as dedicated stitch cards with deterministic accessibility identifiers/hints and real CTA wiring.
  - Enforce redesign scope with source-contract tests that assert both required markers and forbidden utility surfaces.
observability_surfaces:
  - `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py`
  - Budget identifiers: `budget-state-loading-card`, `budget-state-load-error-card`, `budget-state-ready-card`, `budget-state-save-error-card`, `budget-state-save-success-card`
  - Receipt identifiers: `receipt-summary-card`, `receipt-items-card`, `receipt-fallback-item-marker`, `receipt-line-item-row-<index>`
  - Lost-card identifiers: `lost-card-state-idle/loading/success/error`, `lost-card-report-button`, `lost-card-retry-button`, `lost-card-success-done-button`
duration: 1h 32m
verification_result: partial
completed_at: 2026-03-23
blocker_discovered: false
---

# T02: Redesign Budget, Receipt, and Lost-Card views with stitch primitives, accessibility markers, and scope-clean controls

**Redesigned the S04 Budget/Receipt/Lost-Card SwiftUI screens with stitch state cards, stable receipt item identity, and executable design-contract coverage.**

## What Happened

I re-aligned Budget and Lost-Card UI composition to the T01 state contracts, then rebuilt all three S04 screens around `AppTheme`, `StitchCard`, and stitch-styled actionable controls.

In `BudgetView`, I replaced the non-stitch shell with explicit state cards for loading/load-error/ready/save-error/save-success, added actionable retry/refresh/save paths (`retryLoad`, `retryLastSave`, `setBudget`, `load`), and attached deterministic accessibility identifiers/hints for key cards and controls.

In `ReceiptView`, I migrated layout to stitch cards, kept receipt scope clean (no PDF/download/report utilities), added fallback-item markering, and replaced name-only row identity with indexed rendering (`Array(lineItems.enumerated())`, `id: \.index`) to keep duplicate item names stable.

In `LostCardView`, I redesigned the screen using stitch tokens while preserving the phase-driven action map from `LostCardViewModel` (`idle/loading/success/error`), ensuring each visible CTA still maps to real behavior (report, retry, dismiss) and is covered by explicit accessibility markers.

I added `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py` to enforce stitch usage, accessibility/state markers, receipt scope guards, stable line-item iteration markers, and Home/Transactions/Settings navigation continuity anchors.

I also recorded the receipt identity choice in `.gsd/DECISIONS.md` and appended a source-contract gotcha entry in `.gsd/KNOWLEDGE.md` for future S04 refactors.

## Verification

I ran the new S04 design contract suite and re-ran the existing S04 behavior contract suite to ensure no regressions from the view rewrites.

I also executed the slice-level verifier and iOS build checks as required by S04; both fail in this Windows execution environment due missing `/bin/bash` and missing `xcodebuild`.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py` | 0 | ✅ pass | 0.31s |
| 2 | `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` | 0 | ✅ pass | 0.31s |
| 3 | `rtk proxy bash scripts/verify-m007-s04.sh` | 1 | ❌ fail | <1s |
| 4 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail | <1s |
| 5 | Manual checklist in `.gsd/milestones/M007/slices/S04/S04-UAT.md` | N/A | ❌ fail | Not run |

## Diagnostics

- Budget explicit-state surfaces are inspectable in `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift` via:
  - `budget-state-loading-card`
  - `budget-state-load-error-card`
  - `budget-state-ready-card`
  - `budget-state-save-error-card`
  - `budget-state-save-success-card`
  - actionable CTAs: `budget-save-button`, `budget-retry-load-button`, `budget-retry-save-button`, `budget-refresh-button`
- Receipt stability/scope markers are inspectable in `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift` via:
  - `Array(lineItems.enumerated())` + `ForEach(..., id: \.index)`
  - `receipt-fallback-item-marker`
  - `receipt-line-item-row-<index>`
  - explicit scope guard comment and absence of receipt utility-action markers
- Lost-card phase/action markers are inspectable in `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift` via:
  - `switch viewModel.phase`
  - `lost-card-state-idle/loading/success/error`
  - `lost-card-report-button`, `lost-card-retry-button`, `lost-card-success-done-button`, `lost-card-error-dismiss-button`
- Contract enforcement command:
  - `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py`

## Deviations

- No plan-breaking deviations. I additionally documented one implementation decision in `.gsd/DECISIONS.md` and one recurring contract-test gotcha in `.gsd/KNOWLEDGE.md` to reduce downstream rediscovery.

## Known Issues

- `rtk proxy xcodebuild ...` cannot run in this environment because `xcodebuild` is not installed.
- `rtk proxy bash ...` cannot run in this environment because `/bin/bash` (WSL/bash) is unavailable.
- Manual UAT checklist execution remains pending for downstream slice closure.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift` — redesigned budget screen with stitch cards, explicit state cards, actionable save/retry/refresh controls, and accessibility markers.
- `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift` — redesigned receipt screen with stitch styling, scope-clean behavior, fallback marker, and stable indexed line-item rendering.
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift` — redesigned lost-card screen with stitch styling and phase-bound actionable controls + accessibility markers.
- `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py` — added executable design contract assertions for S04 stitch usage, accessibility, scope guard, stable receipt iteration, and navigation continuity.
- `.gsd/milestones/M007/slices/S04/S04-PLAN.md` — marked T02 as complete (`[x]`).
- `.gsd/DECISIONS.md` — appended D082 for receipt indexed line-item identity decision.
- `.gsd/KNOWLEDGE.md` — appended S04 source-contract literal marker gotcha.
