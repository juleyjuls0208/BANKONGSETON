# S07: Final Integration + Device Demo Readiness Gate

**Goal:** Prove the redesigned iOS app works as one coherent end-to-end product (auth → home → QR pay → receipt → transactions/budget/settings/lost-card) and is ready for manual iOS 17+ demo acceptance.
**Demo:** User signs in, completes QR confirm, sees success/receipt, then verifies transactions search/filter/load-more, budget save, settings persistence, lost-card/report, and logout/login continuity without dead controls or out-of-scope surfaces.

## Must-Haves

- R063 (owned): Final integrated app journey passes explicit device-demo readiness gate for iOS 17+ manual acceptance.
- R056 (support): Every visible in-scope control across integrated flows is actionable; no dead-end interactions survive final assembly.
- R058 + R059 (support): Transactions search/filter/load-more and QR/transactions state-fidelity remain correct after cross-screen integration.
- R060 + R061 (support): Local accent/profile persistence and scope cleanup remain intact in full-flow runtime (including relaunch continuity).
- R062 + R055 + R057 (support): Motion remains restrained, stitch-fidelity stays coherent, and QR-only payment direction remains enforced end-to-end.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s07_flow_behavior_contract.py tests/test_verify_m007_s07_scope_guard_contract.py`
- `rtk proxy sh scripts/verify-m007-s07.sh`
- `rtk proxy python -c "import subprocess; p=subprocess.run(['rtk','proxy','sh','scripts/verify-m007-s07.sh'], capture_output=True, text=True); out=(p.stdout or '') + (p.stderr or ''); required=['preflight','flow-contract','scope-contract','integration-contract','artifact-check']; missing=[x for x in required if x not in out]; assert not missing, missing"`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
- `rtk proxy python -c "from pathlib import Path; assert Path('.gsd/milestones/M007/slices/S07/S07-UAT.md').exists()"`

## Observability / Diagnostics

- Runtime signals: explicit integration checkpoints for auth success, QR confirm completion, post-payment refresh, and settings persistence load/save transitions.
- Inspection surfaces: `scripts/verify-m007-s07.sh`, `tests/test_verify_m007_s07_flow_behavior_contract.py`, `tests/test_verify_m007_s07_scope_guard_contract.py`, and `.gsd/milestones/M007/slices/S07/S07-UAT.md`.
- Failure visibility: verifier phases isolate regressions (`preflight`, `flow-contract`, `scope-contract`, `integration-contract`, `artifact-check`) and report required/forbidden marker failures.
- Redaction constraints: never log credentials, tokens, or personal-info values; diagnostics assert contract markers and state transitions only.

## Integration Closure

- Upstream surfaces consumed: S02-S06 QR flow, transactions behavior, budget flow, settings persistence/scope cleanup, and motion policy conventions.
- New wiring introduced in this slice: final cross-screen continuity handoff (post-QR refresh and shared demo-path state checkpoints) plus closure verifier/UAT gate artifacts.
- What remains before the milestone is truly usable end-to-end: nothing.

## Tasks

- [ ] **T01: Add final-assembly contract tests and phased S07 verifier** `est:1h`
  - Why: Final slice needs deterministic closure criteria before implementation so regressions are localized by phase, not discovered ad hoc.
  - Files: `tests/test_verify_m007_s07_flow_behavior_contract.py`, `tests/test_verify_m007_s07_scope_guard_contract.py`, `scripts/verify-m007-s07.sh`
  - Do: Add behavior + scope guard contracts that encode required integrated flow markers and forbidden out-of-scope/dead-control markers; implement fail-fast verifier phases (`preflight`, `flow-contract`, `scope-contract`, `integration-contract`, `artifact-check`).
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s07_flow_behavior_contract.py tests/test_verify_m007_s07_scope_guard_contract.py && rtk proxy sh scripts/verify-m007-s07.sh`
  - Done when: Contracts and verifier fail on missing integration/scope markers and pass when final assembly requirements are satisfied.
- [ ] **T02: Wire cross-screen flow continuity for auth, QR pay, receipt, and transactions/budget refresh** `est:2h`
  - Why: R063/R059 cannot pass if successful QR payment does not reliably propagate to post-payment surfaces and navigation continuity.
  - Files: `mobile/ios/BankongSetonStudent/App/ContentView.swift`, `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`, `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`, `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift`, `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`, `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`, `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift`, `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`, `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift`
  - Do: Ensure successful QR confirm triggers coherent post-payment state updates (balance + transaction history visibility), preserve transactions search/filter/load-more behavior, and keep loading/empty/error/success states explicit and actionable.
  - Verify: `rtk proxy sh scripts/verify-m007-s07.sh`
  - Done when: End-to-end payment journey remains coherent across all downstream surfaces with no stale or contradictory state.
- [ ] **T03: Close final scope/actionability gaps in settings, lost-card, and shell navigation** `est:1h 30m`
  - Why: Final assembly must prove every visible in-scope control is meaningful while forbidden surfaces stay removed.
  - Files: `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`, `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift`, `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift`, `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`, `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift`
  - Do: Verify/fix action wiring for settings persistence + lost-card/logout navigation continuity, and remove any remaining non-scope/dead secondary actions from visible UI.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s07_scope_guard_contract.py && rtk proxy sh scripts/verify-m007-s07.sh`
  - Done when: No visible dead controls remain and forbidden scope elements are absent from final integrated UI surfaces.
- [ ] **T04: Publish S07 device UAT gate and execute closure verification set** `est:1h`
  - Why: Milestone closure requires explicit manual iOS 17+ pass/fail protocol, not only contract/static checks.
  - Files: `.gsd/milestones/M007/slices/S07/S07-UAT.md`, `.gsd/milestones/M007/slices/S07/S07-PLAN.md`
  - Do: Write on-device UAT checklist for full demo journey (default + Reduce Motion paths), include evidence capture expectations, run closure command set, and update plan checkboxes only after proof commands succeed or are explicitly environment-blocked.
  - Verify: `rtk proxy sh scripts/verify-m007-s07.sh && rtk proxy python -c "from pathlib import Path; assert Path('.gsd/milestones/M007/slices/S07/S07-UAT.md').exists()"`
  - Done when: S07-UAT exists with executable acceptance steps and S07 verifier evidence is available for milestone closeout.

## Files Likely Touched

- `mobile/ios/BankongSetonStudent/App/ContentView.swift`
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`
- `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift`
- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift`
- `tests/test_verify_m007_s07_flow_behavior_contract.py`
- `tests/test_verify_m007_s07_scope_guard_contract.py`
- `scripts/verify-m007-s07.sh`
- `.gsd/milestones/M007/slices/S07/S07-UAT.md`
