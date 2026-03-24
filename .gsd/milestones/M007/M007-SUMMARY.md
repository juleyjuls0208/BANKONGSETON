---
id: M007
provides:
  - Stitch-faithful iOS redesign across login, tab shell, home+QR, transactions, budget, receipt, lost-card, and settings using shared AppTheme/Stitch primitives.
  - QR-only payment journey with explicit actionable non-happy-path controls and post-success continuity into Home/Transactions.
  - Transactions search/filter/load-more with required user-visible taxonomy (`QR Pay` / `Card Pay` / `Load`) and explicit loading/empty/error/pagination-failure channels.
  - Local-only settings persistence (accent + personal info), scope-clean settings/receipt surfaces, and centralized motion policy with Reduce Motion parity.
  - Final integration + physical iOS 17+ acceptance evidence package for milestone closure.
key_decisions:
  - D077: Keep QR scan ingestion compatible with full URL and bare token payloads while preserving QR-only path.
  - D080: Transactions search/filter derives from canonical paginated source with split initial vs pagination failure channels.
  - D083: Settings persistence remains local-only and propagates through shared theme/shell seams.
  - D084: Motion quality is enforced via shared `AppTheme.Motion` policy with explicit Reduce Motion fallbacks.
  - D086: Use persisted continuity tick (`qr_payment_success_continuity_tick`) + dedupe guards for cross-tab post-QR refresh continuity.
  - D090: iOS login contract is student-ID-only (no PIN).
  - D091: Runtime evidence must record real host constraints (no synthetic PASS when Apple tooling is unavailable).
patterns_established:
  - Contract-first slice closure (source-contract tests + phased verifiers + UAT-result artifacts).
  - Scope-clean UX enforcement by treating forbidden labels/actions as regression markers.
  - Separation of executor-runtime evidence and physical-device acceptance evidence in final closure.
observability_surfaces:
  - `.gsd/milestones/M007/M007-VALIDATION.md`
  - `.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md`
  - `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json`
  - `scripts/verify-m007-s02.sh` through `scripts/verify-m007-s07.sh`, `scripts/verify-m007-s09.sh`
  - `tests/test_verify_m007_s09_runtime_contract.py`, `tests/test_verify_m007_s09_evidence_contract.py`, `tests/test_verify_m007_s09_override_contract.py`
requirement_outcomes:
  - id: R055
    from_status: active
    to_status: validated
    proof: "S01 design-system/shell/login contracts passed; S09 override contracts + physical-device UAT PASS confirmed dark-mode default and no-PIN login."
  - id: R056
    from_status: active
    to_status: validated
    proof: "S02-S05 actionability contracts plus S09 physical-device UAT matrix (S07-01..S07-11) PASS showed no dead in-scope controls."
  - id: R057
    from_status: active
    to_status: validated
    proof: "S02 QR-only verifier/UAT PASS and S05 scope cleanup retained single QR payment path; S09 UAT confirmed no payment-method chooser surfaces."
  - id: R058
    from_status: active
    to_status: validated
    proof: "S03 behavior/design contracts + UAT PASS validated search/filter/load-more; S09 override contracts/UAT confirmed `QR Pay`/`Card Pay`/`Load` taxonomy."
  - id: R059
    from_status: active
    to_status: validated
    proof: "S02/S03/S04/S06 contracts and UAT artifacts validated loading/empty/error/success fidelity with retry continuity across QR + Transactions + related states."
  - id: R060
    from_status: active
    to_status: validated
    proof: "S05 settings behavior/design contracts + UAT PASS validated local accent/display-name persistence and continuity; reinforced by S09 full-journey UAT."
  - id: R061
    from_status: active
    to_status: validated
    proof: "S04/S05 static scope-contract checks and UAT PASS confirmed non-scope settings groups + receipt utility actions remain removed."
  - id: R062
    from_status: active
    to_status: validated
    proof: "S06 motion contracts/UAT PASS plus S09 physical-device UAT scenarios S07-10/S07-11 PASS validated restrained motion with Reduce Motion parity."
  - id: R063
    from_status: active
    to_status: validated
    proof: "S07 integration/readiness gates were completed and S09 physical iOS 17+ user-confirmed UAT PASS closed on-device readiness."
duration: "S01-S09 cumulative execution ~35h 23m"
verification_result: passed
completed_at: 2026-03-23
---

# M007: iOS UI-UX Rework (Stitch-Parity, QR-Only)

**Completed milestone closure for the Stitch-parity iOS redesign with QR-only flow, validated interaction continuity, and final physical iOS acceptance evidence.**

## What Happened

M007 executed all planned slices (S01-S09) and closed with S09 override remediation + acceptance evidence:

- S01 established shared stitch design system + shell/login baseline.
- S02 delivered QR-only Home→QR flow with explicit actionable non-happy-path controls.
- S03 delivered transactions search/filter/load-more over paginated source with explicit state channels.
- S04 delivered budget/receipt/lost-card redesign with explicit recoverable behavior and scope-clean receipt actions.
- S05 delivered local settings persistence and removal of out-of-scope settings/payment-method surfaces.
- S06 delivered centralized motion policy + Reduce Motion parity across high-impact flows.
- S07 delivered integration closure gate, continuity tick wiring, and final demo-readiness artifacts.
- S08 replaced recovery placeholders with authoritative, machine-auditable slice summaries.
- S09 delivered override remediations (dark default, no PIN, required transactions taxonomy), verifier/runtime proof artifacts, and user-confirmed physical-device UAT PASS.

## Code-Change Verification (Required)

1. Required integration-branch diff command:
   - `rtk git diff --stat HEAD $(rtk git merge-base HEAD master) -- ':!.gsd/'`
   - Result: empty (integration branch already contains milestone commits).

2. Equivalent baseline check from milestone start commit:
   - `rtk git diff --stat b41905e^ HEAD -- ':!.gsd/'`
   - Result: non-`.gsd/` implementation changes confirmed (13 files, 893 insertions, 62 deletions), including iOS app code, S09 verifiers, and S09 contract tests.

**Conclusion:** milestone produced real implementation changes (not planning-only output).

## Success Criteria Verification

1. **Sign-in + redesigned tabs + QR flow + resulting transaction/receipt in cohesive stitch UX** — ✅ Met
   - Evidence: S01/S02/S07 contracts, S09 override checks, and physical-device UAT PASS (`S09-UAT-RESULT.md`).

2. **Transactions search/filter/load-more + required chips + state fidelity** — ✅ Met
   - Evidence: S03 verifier/UAT PASS and S09 override taxonomy contracts confirming `QR Pay` / `Card Pay` / `Load`.

3. **Settings local persistence + scope cleanup** — ✅ Met
   - Evidence: S05 behavior/design/static contracts + UAT PASS.

4. **Polished but restrained motion on iOS 17+ physical device** — ✅ Met
   - Evidence: S06 motion contracts + S09 physical-device UAT scenarios S07-10/S07-11 PASS.

5. **No dead in-scope controls** — ✅ Met
   - Evidence: S02-S05 actionability contracts + S07 integration checks + S09 full scenario matrix PASS.

**Unmet criteria:** none.

## Definition of Done Verification

- All roadmap slices complete (`[x]` S01-S09) — ✅
- All slice summaries present — ✅
- Shared styling/interaction primitives wired across redesigned screens — ✅
- Real app entrypoint proven through full demo journey on physical iOS 17+ device — ✅ (user-confirmed in S09 UAT result)
- Success criteria rechecked against runtime/manual acceptance expectations — ✅
- Final integrated acceptance scenarios (login, QR pay, transactions, budget, settings, lost-card) pass — ✅

## Requirement Transition Validation

Validated transitions recorded for **R055-R063**, all **active → validated**, with proof linked in frontmatter `requirement_outcomes` and corresponding slice artifacts (`S02..S09` verifier/UAT evidence).

## Constraints and Residual Notes

- Windows executor still reports `apple_tooling` phase failure in local runtime proof (`xcodebuild`/`xcrun` unavailable). This is retained as executor-context evidence, while closure verdict is based on required physical-device acceptance proof.

## Files Updated During Milestone Closeout

- `.gsd/milestones/M007/M007-SUMMARY.md` (this file)
- `.gsd/REQUIREMENTS.md` (R055-R063 status + validation updates)
- `.gsd/PROJECT.md` (M007 marked complete in project state and milestone sequence)
- `.gsd/KNOWLEDGE.md` (cross-slice reusable lessons from M007 closure)

## Forward Intelligence

- Preserve S09 override checkpoints as hard regression tests: dark-mode default, no PIN login, transactions taxonomy.
- Keep continuity tick producer/consumer contract intact for post-QR cross-tab refresh.
- For future milestone closeouts, separate executor-host runtime constraints from physical-device acceptance evidence.
