---
id: S07
parent: M007
milestone: M007
provides:
  - Final integration closure gate for M007 combining source contracts, phased verifier diagnostics, and readiness artifacts.
  - QR-success continuity wiring from Home to Transactions with deduped one-shot completion and cross-tab refresh propagation.
  - Device-demo readiness documentation package (`S07-UAT.md` + `S07-DEMO-READINESS.md`) for final manual iOS 17+ acceptance.
requires:
  - S02
  - S03
  - S04
  - S05
  - S06
affects:
  - R056
  - R058
  - R059
  - R060
  - R061
  - R062
  - R063
key_files:
  - tests/test_verify_m007_s07_integration_behavior_contract.py
  - tests/test_verify_m007_s07_scope_guard_contract.py
  - scripts/verify-m007-s07.sh
  - mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift
  - mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift
  - mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift
  - mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift
  - mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift
  - .gsd/milestones/M007/slices/S07/S07-UAT.md
  - .gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md
  - .gsd/milestones/M007/slices/S07/tasks/T02-SUMMARY.md
key_decisions:
  - D085: S07 closure is enforced by phased contract/scope/integration/diagnostic verification instead of ad-hoc manual checking.
  - D086: QR-success continuity is transported via shared persisted tick (`qr_payment_success_continuity_tick`) with producer/consumer dedupe guards.
  - D087: Diagnostic-surface phase hard-fails when readiness artifacts are missing/empty and validates required traceability markers.
patterns_established:
  - Use marker-based source contracts to lock integration seams that are easy to regress during UI refactors.
  - Use one-shot callback guards + persisted continuity scalar for cross-screen state handoff after modal success flows.
  - Keep closure evidence split into executable verifier output + human UAT script + requirement traceability matrix.
observability_surfaces:
  - `scripts/verify-m007-s07.sh` (`phase=...`, `guidance=...`, artifact completeness checks)
  - `tests/test_verify_m007_s07_integration_behavior_contract.py` (required integration markers)
  - `tests/test_verify_m007_s07_scope_guard_contract.py` (forbidden scope-regression markers)
  - `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift` (`QRPayState transition ... reason=...`, token redaction logs)
  - `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift` + `TransactionsViewModel.swift` refresh continuity logs
drill_down_paths:
  - .gsd/milestones/M007/slices/S07/tasks/T01-SUMMARY.md
  - .gsd/milestones/M007/slices/S07/tasks/T02-SUMMARY.md
  - .gsd/milestones/M007/slices/S07/tasks/T03-SUMMARY.md
duration: 3h 50m
verification_result: partial
completed_at: 2026-03-23T14:34:00+08:00
---

# S07: Final Integration + Device Demo Readiness Gate

**S07 delivered the final assembly layer for M007: integration contracts + phased closure verifier + QR-success continuity wiring + readiness/UAT evidence surfaces.**

## What This Slice Actually Delivered

### 1) Deterministic closure gate for final assembly

- Added and enforced S07 source contracts:
  - `tests/test_verify_m007_s07_integration_behavior_contract.py`
  - `tests/test_verify_m007_s07_scope_guard_contract.py`
- Added phased verifier with actionable diagnostics:
  - `scripts/verify-m007-s07.sh`
  - phases: `preflight`, `contract`, `scope`, `integration`, `diagnostic-surface`
  - structured failure output: `phase=<name>` + `guidance=<next step>`

### 2) QR-success continuity wiring across final user journey

- Hardened QR success completion in `QRPayView`:
  - unified manual/auto success completion path
  - one-shot guard to prevent duplicate side-effects
- Added Home continuity producer:
  - increments `@AppStorage("qr_payment_success_continuity_tick")` exactly once per successful dismissal
  - refreshes Home via `HomeViewModel.refreshAfterQRSuccess(...)`
- Added Transactions continuity consumer:
  - `.task(id: qrPaymentSuccessContinuityTick)` in `TransactionsView`
  - `TransactionsViewModel.refreshAfterQRSuccessContinuity(...)` with last-seen dedupe guard
- Preserved existing transactions behavior contract:
  - search/filter derivation over canonical paginated source
  - split initial/pagination failure channels
  - resilient `hasMore` fallback when backend omits `has_more`

### 3) Manual acceptance readiness artifacts for iOS 17+ demo

- Published concrete UAT script:
  - `.gsd/milestones/M007/slices/S07/S07-UAT.md`
  - 11 tailored scenarios covering default + Reduce Motion + failure/retry paths
- Published readiness/traceability matrix:
  - `.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md`
  - maps R063/R056/R058/R059/R060/R061/R062 to automated and manual proof surfaces
- Verifier now enforces readiness artifact existence/non-empty content in `diagnostic-surface` phase.

## Verification

All slice-plan checks were executed.

| # | Command | Exit Code | Verdict | Notes |
|---|---|---:|---|---|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py tests/test_verify_m007_s07_scope_guard_contract.py` | 0 | ✅ PASS | 8 tests passed |
| 2 | `rtk proxy sh scripts/verify-m007-s07.sh` | 0 | ✅ PASS | all phases passed |
| 3 | `rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s07.sh').read_text(encoding='utf-8'); required=['fail_with_guidance','guidance=','phase=preflight','phase=diagnostic-surface']; missing=[x for x in required if x not in txt]; assert not missing, missing"` | 0 | ✅ PASS | required diagnostic markers present |
| 4 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ FAIL | environment constraint: `xcodebuild` program not found |
| 5 | `rtk proxy python -c "from pathlib import Path; paths=[Path('.gsd/milestones/M007/slices/S07/S07-UAT.md'), Path('.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md')]; missing=[str(p) for p in paths if not p.exists() or not p.read_text(encoding='utf-8').strip()]; assert not missing, missing"` | 0 | ✅ PASS | readiness docs present and non-empty |

## Requirement Evidence Update

- **R056/R058/R059/R060/R061/R062:** automated integration/scope contracts and verifier phases pass; manual UAT evidence still required for final human closure semantics.
- **R063:** closure documentation + automated gate exist and pass except simulator build command in this harness; physical iOS 17+ manual PASS/FAIL execution remains required for full validation.

## Diagnostics Confirmed for Downstream Readers

If regression is suspected, run these in order:

1. `rtk proxy sh scripts/verify-m007-s07.sh`
2. `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py`
3. `rtk proxy python -m pytest -q tests/test_verify_m007_s07_scope_guard_contract.py`
4. Inspect `.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md` run log + traceability table.

## Deviations / Constraints

- No functional scope deviation from S07 plan.
- Execution environment lacks Apple build tooling (`xcodebuild`), so simulator build proof cannot be produced here.

## Files Created/Updated in This Closure Pass

- `.gsd/milestones/M007/slices/S07/tasks/T02-SUMMARY.md` — replaced blocker placeholder with full summary, diagnostics, and verification evidence.
- `.gsd/milestones/M007/slices/S07/S07-UAT.md` — rewritten as concrete, slice-specific UAT script with preconditions/steps/expected outcomes/edge checks.
- `.gsd/milestones/M007/slices/S07/S07-SUMMARY.md` — added this compressed slice summary.

## Forward Intelligence (for reassess-roadmap and later milestone readers)

### What this slice established as stable

- Final integration gate shape is now explicit and repeatable.
- QR-success continuity transport pattern (persisted tick + dedupe guards) is the canonical cross-tab post-payment refresh mechanism.
- Readiness artifacts are mandatory closure surfaces, not optional prose.

### What remains before declaring true end-user readiness

- Run iOS build verification in an Apple-capable environment.
- Execute and sign off manual physical-device UAT scenarios S07-01..S07-11.

### What to avoid changing casually

- `qr_payment_success_continuity_tick` producer/consumer contract.
- one-shot guards around QR success completion.
- phase-tagged `guidance=` failure semantics in verifier scripts.
