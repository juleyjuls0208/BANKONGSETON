# S03 Research — Home Rollback + Credit-Card Hero + QR Continuity

**Date:** 2026-03-27  
**Slice:** M008-l1ngya/S03  
**Status:** Ready for planning

## Requirement Targeting (Active)

S03 directly owns:

- **R070** — Home shows student name + balance in a minimalist credit-card hero.
- **R076** — Home → QR → post-success continuity must survive rollback work.

S03 supports:

- **R068** — Ongoing rollback baseline alignment (without regressing S02 shell/budget/login guards).
- **R075** — Keeps later manual on-device gate feasible by preserving executable regression contracts.

## Summary

Targeted research. Tech is familiar; risk is contract drift while simplifying Home UI.

### Core findings

1. **Home is currently far from the pre-M007 baseline structurally.**  
   `HomeView.swift` now includes motion transitions, multi-card composition (`StitchCard` blocks), QR presentation state guards, and settings-driven display-name refresh hooks. Compared to `558d8bc`, the file has significantly more orchestration and UI state.

2. **R070 is partly present already, but mixed with heavier M007-era scaffolding.**  
   The balance hero exists (`balanceCard` gradient + name + balance), but it is embedded in a broader stitched/animated surface that does not match the requested rollback/minimalist direction.

3. **R076 continuity depends on a specific three-part seam that must not be broken:**
   - `HomeView`: `didConsumePresentedQRSuccess` guard + `@AppStorage("qr_payment_success_continuity_tick")` + `handleQRPaySuccessCompletion()`
   - `QRPayView`: `hasTriggeredSuccessCompletion` + `onSuccess` callback path
   - `TransactionsView`/`TransactionsViewModel`: `task(id: qrPaymentSuccessContinuityTick)` + `lastHandledQRSuccessContinuityTick` dedupe

4. **Full literal rollback to `558d8bc` Home is not viable.**  
   Baseline Home had no QR entry/sheet continuity path; restoring that literally would violate R076.

5. **Current S02 verifier does not assert Home continuity seam.**  
   `scripts/verify-m008-s02.sh` protects shell + budget + QR scanner behavior + login payload, but it does not explicitly gate Home’s success-handoff continuity markers.

## Recommendation

Plan S03 as a **contract-first home-only rollback slice**:

1. Add S03-specific Home contract tests first (lock intended minimalist hero + required QR continuity seam).
2. Refactor `HomeView.swift` toward pre-M007 structure (simpler layout/flow) while preserving the continuity seam and QR entry CTA wiring.
3. Keep `HomeViewModel.load()` and QR refresh method intact unless a direct contract reason requires change.
4. Close with a new S03 phased verifier that includes:
   - new S03 home contract test(s)
   - explicit Home QR continuity node test
   - existing S02 phased verifier as downstream regression guard.

## Implementation Landscape

### Primary files to change

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`  
  (rollback/minimalist restructuring + credit-card hero final shape + preserved QR continuity hooks)

- `tests/test_verify_m008_s03_ios_home_rollback_contract.py` (new)  
  (S03 source-contract markers: hero structure + forbidden heavy-shell markers as chosen + required QR continuity markers)

- `scripts/verify-m008-s03.sh` (new)  
  (phased verifier for S03 + S02 regression chaining)

### Likely unchanged (unless planner explicitly expands scope)

- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`  
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`  
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`  
- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`

These contain working continuity seams already validated by existing contracts.

## Natural Seams

### Seam A — Contract harness first

Create S03 contract tests before UI edits:
- Required: credit-card hero markers (name + balance + label), QR CTA identifier/sheet path, continuity tick increment call path.
- Forbidden (if enforcing rollback minimalism): selected high-churn M007-only home composition markers that S03 is intentionally removing.

### Seam B — Home rollback/minimalism implementation

Refactor only `HomeView.swift` layout structure:
- retain hero as dominant visual anchor,
- keep QR entry affordance and scanner sheet,
- reduce visual/state complexity toward baseline feel.

### Seam C — Regression chaining

Add `scripts/verify-m008-s03.sh` to run:
1. S03 home contract suite
2. Existing Home/QR continuity node test from M007 integration contract
3. `scripts/verify-m008-s02.sh` for shell/budget/QR/login protection

This avoids duplicating S02 guard logic while extending coverage for R070/R076.

## Constraints / Fragility

- **Do not remove continuity tick seam** (`qr_payment_success_continuity_tick`) — project knowledge explicitly identifies this as the cross-tab post-payment continuity mechanism.
- **Do not rely on full-file M007 integration suites** for S03 closure; many enforce soon-to-be-removed surfaces (e.g., transactions search). Use targeted node tests.
- **Windows shell constraint remains active:** use Git Bash path for verifier execution (`rtk proxy "C:\Program Files\Git\bin\bash.exe" ...`).
- **No Swift LSP available in this environment;** source-contract tests are the primary objective signal.

## What to Prove First

1. Home contract test captures intended S03 shape (before implementation).
2. Home UI rewrite lands without breaking QR sheet success handoff.
3. Explicit Home continuity node test still passes.
4. Full S02 verifier still passes (no shell/budget/login/QR-regression fallout).

## Verification Strategy

### Expected commands for S03 closure

- `rtk proxy python -m py_compile tests/test_verify_m008_s03_ios_home_rollback_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m008_s03_ios_home_rollback_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py::test_qr_success_handoff_remains_wired_from_home_sheet_to_refresh_path`
- `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s03.sh`

### Suggested `verify-m008-s03.sh` phases

- `preflight`
- `s03-home-contract`
- `home-qr-continuity`
- `s02-regression-chain`

## Skill-Guided Rules Applied

From loaded **swiftui** skill:

- **Platform-adaptive design:** prefer native/simple iOS composition patterns for rollback minimalism over custom heavy abstractions.
- **Single source of truth:** keep continuity state ownership where it already lives (Home tick source, Transactions tick consumer) instead of introducing parallel flags.
- **Prove, don’t promise:** closure must be executable via source-contract tests + phased verifier, not visual claims.

## Skills Discovered

Installed/relevant skills already present:
- `swiftui`
- `build-iphone-apps`
- `test`

Discovery attempt for missing technology-specific skill:
- `rtk proxy npx skills find "AVFoundation"`
- Result: blocked (`npx` not available in this environment)

No new skills installed during this slice research.

## Sources

- `.gsd/milestones/M008-l1ngya/M008-l1ngya-ROADMAP.md` (preloaded)
- `.gsd/milestones/M008-l1ngya/M008-l1ngya-CONTEXT.md` (preloaded)
- `.gsd/milestones/M008-l1ngya/slices/S02/S02-SUMMARY.md` (preloaded)
- `.gsd/REQUIREMENTS.md` (R068–R076 sections)
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`
- `tests/test_verify_m007_s02_qr_behavior_contract.py`
- `tests/test_verify_m007_s07_integration_behavior_contract.py`
- `tests/test_verify_m008_s02_ios_rollback_contract.py`
- `scripts/verify-m008-s02.sh`
- Baseline references via `git show 558d8bc` for Home and HomeViewModel.