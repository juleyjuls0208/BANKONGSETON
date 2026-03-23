# S07: Final Integration + Device Demo Readiness Gate

**Goal:** Close M007 with one coherent, demo-ready iOS runtime path where redesigned screens, QR-only payment, local settings persistence, and state/error handling all work together without dead controls.
**Demo:** On iOS 17+, a user signs in, runs QR pay to completion, sees refreshed home/history data and receipt access, validates transactions search/filter/load-more plus budget/settings/lost-card actions, then confirms logout/login continuity and readiness for manual pass/fail acceptance.

## Must-Haves

- R063 (owned): Final redesigned iOS build is ready for manual install and pass/fail acceptance on physical iOS 17+ across the full app journey.
- R056 (support): Every visible in-scope control in final integrated flows remains actionable; no dead controls survive closure.
- R058 + R059 (support): Transactions search/filter/load-more and QR/transactions loading-empty-error-success states remain coherent after final integration wiring.
- R060 + R061 (support): Local accent/display-name persistence survives real flow boundaries, and out-of-scope settings/receipt/payment-method surfaces remain removed.
- R062 + R055 + R057 (support): Motion remains restrained, stitch-faithful continuity stays intact, and QR-only direction is preserved end-to-end.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py tests/test_verify_m007_s07_scope_guard_contract.py`
- `rtk proxy sh scripts/verify-m007-s07.sh`
- `rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s07.sh').read_text(encoding='utf-8'); required=['fail_with_guidance','guidance=','phase=preflight','phase=diagnostic-surface']; missing=[x for x in required if x not in txt]; assert not missing, missing"`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
- `rtk proxy python -c "from pathlib import Path; paths=[Path('.gsd/milestones/M007/slices/S07/S07-UAT.md'), Path('.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md')]; missing=[str(p) for p in paths if not p.exists() or not p.read_text(encoding='utf-8').strip()]; assert not missing, missing"`

## Observability / Diagnostics

- Runtime signals: explicit `QRPayState` and refresh-transition logs plus phase-tagged verifier output for integration checkpoints.
- Inspection surfaces: `scripts/verify-m007-s07.sh`, `tests/test_verify_m007_s07_integration_behavior_contract.py`, `tests/test_verify_m007_s07_scope_guard_contract.py`, and S07 readiness/UAT docs.
- Failure visibility: phased verifier emits `phase=<name>` status and `guidance=` lines; contract tests isolate missing required markers vs forbidden scope regressions.
- Redaction constraints: diagnostics must never print credentials, auth tokens, or personal data values; evidence stays structural/state-based.

## Integration Closure

- Upstream surfaces consumed: S02 QR flow contracts, S03 transactions derivation/pagination contracts, S04 budget/receipt/lost-card contracts, S05 settings persistence/scope cleanup, and S06 motion policy usage.
- New wiring introduced in this slice: final QR-success continuity handoff across Home/Transactions plus one closure verifier path that composes integration + scope + diagnostic checks.
- What remains before the milestone is truly usable end-to-end: nothing.

## Tasks

- [ ] **T01: Build S07 integration contracts and phased closure verifier** `est:1h 30m`
  - Why: Final assembly needs one deterministic gate that proves integration + scope correctness and exposes actionable failure diagnostics.
  - Files: `tests/test_verify_m007_s07_integration_behavior_contract.py`, `tests/test_verify_m007_s07_scope_guard_contract.py`, `scripts/verify-m007-s07.sh`, `.gsd/milestones/M007/slices/S07/S07-UAT.md`
  - Do: Add source-contract tests for required end-to-end markers and forbidden scope regressions; implement phased verifier with structured `phase=`/`guidance=` output; when asserting literals containing `$` (for example `text: $viewModel.searchQuery`) keep shell literals single-quoted under `set -euo pipefail`.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py tests/test_verify_m007_s07_scope_guard_contract.py && rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s07.sh').read_text(encoding='utf-8'); required=['set -euo pipefail','fail_with_guidance','phase=diagnostic-surface','guidance=']; missing=[x for x in required if x not in txt]; assert not missing, missing"`
  - Done when: S07 tests pass on current codebase and verifier source contains explicit phase diagnostics + failure guidance hooks.
- [ ] **T02: Wire final QR-success continuity across Home and Transactions without state regressions** `est:2h`
  - Why: R063/R059 fail if successful QR payment does not propagate cleanly to post-payment surfaces or breaks existing search/filter/pagination semantics.
  - Files: `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`, `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift`, `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`, `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`, `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`, `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`, `tests/test_verify_m007_s07_integration_behavior_contract.py`
  - Do: Harden QR success completion semantics (single completion path, no duplicate side-effects), propagate refresh continuity to Home/Transactions, and preserve existing transactions search/filter/load-more plus failure-state visibility while keeping all in-scope controls actionable.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py tests/test_verify_m007_s07_scope_guard_contract.py && rtk proxy sh scripts/verify-m007-s07.sh && rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
  - Done when: QR success reliably lands in coherent refreshed app state, S07 contracts/verifier pass, and iOS build succeeds.
- [ ] **T03: Publish device-demo readiness evidence and close S07 acceptance gate** `est:1h`
  - Why: Milestone closure requires explicit manual iOS 17+ pass/fail protocol and traceable evidence, not only source-level checks.
  - Files: `.gsd/milestones/M007/slices/S07/S07-UAT.md`, `.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md`, `scripts/verify-m007-s07.sh`
  - Do: Finalize on-device UAT checklist for full journey (default + Reduce Motion + failure/retry paths), document requirement-to-proof traceability, and ensure verifier artifact checks enforce presence of readiness evidence files.
  - Verify: `rtk proxy sh scripts/verify-m007-s07.sh && rtk proxy python -c "from pathlib import Path; u=Path('.gsd/milestones/M007/slices/S07/S07-UAT.md'); r=Path('.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md'); assert u.exists() and r.exists(); assert 'PASS' in u.read_text(encoding='utf-8'); assert 'R063' in r.read_text(encoding='utf-8')"`
  - Done when: S07 UAT + readiness docs are non-empty, verifier artifact phase passes, and closure evidence is ready for manual device sign-off.

## Files Likely Touched

- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`
- `tests/test_verify_m007_s07_integration_behavior_contract.py`
- `tests/test_verify_m007_s07_scope_guard_contract.py`
- `scripts/verify-m007-s07.sh`
- `.gsd/milestones/M007/slices/S07/S07-UAT.md`
- `.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md`
