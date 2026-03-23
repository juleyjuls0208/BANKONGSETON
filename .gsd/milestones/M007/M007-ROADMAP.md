# M007: iOS UI-UX Rework (Stitch-Parity, QR-Only)

**Vision:** Complete rework of the existing iOS app to closely copy the Stitch redesign package with fully interactive in-scope behavior, QR-only payment UX, and physical iOS 17+ demo readiness.

## Success Criteria

- User can complete sign-in, navigate redesigned tabs, run QR pay flow, and view resulting transaction/receipt in a visually cohesive stitch-faithful experience.
- Transactions screen supports working search/filter/load-more and clearly handles loading, empty, error, and populated states.
- Settings supports local persistence for accent color and personal info edit interaction while removing out-of-scope settings groups and payment-method UX.
- App interactions and animations feel polished but not "too fancy/slow" on iOS 17+ physical device.
- No visible in-scope control is dead during demo flow.

## Key Risks / Unknowns

- Visual fidelity drift across many screens/states — inconsistency can break the "copy" requirement.
- Motion/performance tradeoff on physical iOS 17+ hardware — over-animated transitions can feel slow.
- Scope leakage from stitch-only extras — accidental inclusion can create non-functional UI and confusion.
- Mixed local + backend state boundaries — unclear ownership can produce contradictory UX.

## Proof Strategy

- Visual fidelity drift → retire in S01 by proving stitch design tokens/components/shell are applied and reused across multiple destination screens.
- Motion/performance tradeoff → retire in S06 by proving tuned animation set on iOS 17+ with restrained transitions and interaction responsiveness.
- Scope leakage from stitch-only extras → retire in S05 by proving all out-of-scope settings/receipt/payment-method surfaces are removed.
- Mixed local + backend state boundaries → retire in S07 by proving final integrated flow where local-only settings and backend-driven data coexist without dead-end behavior.

## Verification Classes

- Contract verification: Swift build/test checks + structural assertions that required views/actions exist and out-of-scope actions are absent.
- Integration verification: real app flow across auth, QR cart/confirm, transactions, budget save, and lost-card/report using current backend contracts.
- Operational verification: iOS 17+ install/run behavior with responsive interaction and no animation-induced sluggishness.
- UAT / human verification: user-installed on-device walkthrough with explicit manual pass/fail.

## Milestone Definition of Done

This milestone is complete only when all are true:

- All slice deliverables are complete with no dead in-scope controls.
- Shared styling and interaction primitives are wired across all redesigned screens, not just isolated pages.
- The real app entrypoint can run full demo journey on iOS 17+ device.
- Success criteria are re-checked against runtime behavior and manual device acceptance expectations.
- Final integrated acceptance scenarios pass for login, QR pay, transactions, budget, settings, and lost-card flows.

## Requirement Coverage

- Covers: R055, R056, R057, R058, R059, R060, R061, R062, R063
- Partially covers: none
- Leaves for later: R064
- Orphan risks: none

## Slices

- [x] **S01: Design System + Navigation Shell Rework** `risk:high` `depends:[]`
  > After this: login and tab shell render with stitch visual language (palette, spacing, typography, card depth, nav treatment) and become the reusable base for all downstream screens.

- [x] **S02: Home + QR Flow Redesign (QR-Only)** `risk:high` `depends:[S01]`
  > After this: redesigned home and QR scan/loading/confirm/success/error flows are interactive, payment-method selection surfaces are removed, and QR remains the only payment UX.

- [x] **S03: Transactions Redesign + Search/Filter + State Fidelity** `risk:high` `depends:[S01]`
  > After this: transactions screen matches stitch states (loading/empty/error/populated) with working search/filter plus existing pagination continuity.

- [x] **S04: Budget + Receipt + Lost-Card Redesign** `risk:medium` `depends:[S01]`
  > After this: budget, receipt, and lost-card flows are redesigned and interactive with in-scope behavior; receipt utility actions removed per scope.

- [x] **S05: Settings Rework + Local Persistence + Scope Cleanup** `risk:medium` `depends:[S01]`
  > After this: accent color and personal info edit persist locally, non-scope settings groups are removed, and no decorative secondary dead actions remain.

- [x] **S06: Motion and Performance Tuning (iOS 17+)** `risk:medium` `depends:[S02,S03,S04,S05]`
  > After this: transitions/micro-interactions feel premium but restrained (not too fancy/slow) on iOS 17+ runtime.

- [x] **S07: Final Integration + Device Demo Readiness Gate** `risk:low` `depends:[S02,S03,S04,S05,S06]`
  > After this: complete end-to-end app journey is coherent and demo-ready for manual on-device pass/fail acceptance.
- [ ] **S08: Summary Backfill + Evidence Consolidation** `risk:low` `depends:[S07]`
  > After this: placeholder summaries for S02–S06 are replaced with authoritative slice summaries that reconcile task deliverables, verifier outputs, and UAT verdicts for audit-grade traceability.
- [ ] **S09: macOS Runtime + Physical Device Acceptance Closure** `risk:high` `depends:[S07]`
  > After this: xcodebuild/simulator checks and full physical iOS 17+ UAT scenarios (S07-01..S07-11) are executed with recorded PASS/FAIL evidence, resolving the on-device readiness gate.

## Boundary Map

### S01 → S02

Produces:
- Shared visual tokens and reusable styling primitives for stitch parity (colors, card surfaces, typography scale, interaction states)
- Updated navigation shell contract for home/transactions/budget/settings flow
- Login visual contract and base component language

Consumes:
- nothing (first slice)

### S01 → S03

Produces:
- Reusable list row/card/headline/status styling primitives aligned to stitch ledger screens
- Top app bar + bottom nav shell conventions reused by transactions variants

Consumes:
- nothing (first slice)

### S01 → S04

Produces:
- Shared detail-screen layout patterns (hero value, section cards, semantic status styling)
- Reusable interactive component behavior (press states, disabled/loading patterns)

Consumes:
- nothing (first slice)

### S01 → S05

Produces:
- Shared settings-group/list item styling contract and local persistence UI conventions
- App-wide accent application hooks for downstream settings controls

Consumes:
- nothing (first slice)

### S02 → S06

Produces:
- QR flow state machine visuals and interactions (scan/loading/confirm/success/error)
- Home primary CTA and QR-only payment UX contract

Consumes from S01:
- shell + tokenized styling primitives

### S03 → S06

Produces:
- Transactions search/filter interaction surface and state-specific presentation contracts

Consumes from S01:
- list and app-bar styling contracts

### S04 → S06

Produces:
- Budget/receipt/lost-card refined interaction patterns requiring animation tuning alignment

Consumes from S01:
- shared detail-view component language

### S05 → S06

Produces:
- Settings local-persistence interaction surfaces (accent + personal info edit) and scope-pruned settings map

Consumes from S01:
- settings visual/grouping contract

### S02,S03,S04,S05,S06 → S07

Produces:
- Fully assembled redesigned app journey for manual device acceptance
- Final no-dead-control invariant across all in-scope flows
- Physical demo readiness evidence against iOS 17+ behavior expectations

Consumes:
- Home/QR flow from S02
- Transactions behavior from S03
- Budget/receipt/lost-card behavior from S04
- Settings local persistence and scope cleanup from S05
- Motion/performance tuning from S06
