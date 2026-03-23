---
id: S04
parent: M007
milestone: M007
provides:
  - Stitch-faithful Budget, Receipt, and Lost-Card surfaces with explicit recoverable state behavior.
  - Receipt continuity + scope-clean constraints (no utility-action clutter) with stable fallback line-item rendering.
  - Deterministic S04 proof surfaces (contracts + verifier + UAT result artifact) for downstream integration closure.
requires:
  - S01
  - S02
  - S03
affects:
  - R055
  - R056
  - R059
  - R061
  - R063
key_files:
  - mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift
  - mobile/ios/BankongSetonStudent/ViewModels/LostCardViewModel.swift
  - mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift
  - mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift
  - mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift
  - tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py
  - tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py
  - scripts/verify-m007-s04.sh
  - .gsd/milestones/M007/slices/S04/S04-UAT-RESULT.md
key_decisions:
  - D081: Use behavior-contract-first execution order and a dedicated `LostCardViewModel` seam for deterministic lost-card state handling.
  - D082: Preserve receipt line-item identity via indexed rendering with fallback markers to prevent collisions and empty-state ambiguity.
patterns_established:
  - Keep Budget and Lost-Card state machines explicit (`idle/loading/success/error`) with visible retry/save/report actions.
  - Keep Receipt UX scope-clean by preserving continuity surfaces while excluding non-scope utility actions.
observability_surfaces:
  - scripts/verify-m007-s04.sh (`phase=behavior-contract|design-contract|static-contract`)
  - tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py
  - tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py
  - .gsd/milestones/M007/slices/S04/S04-UAT-RESULT.md
drill_down_paths:
  - .gsd/milestones/M007/slices/S04/tasks/T01-SUMMARY.md
  - .gsd/milestones/M007/slices/S04/tasks/T02-SUMMARY.md
  - .gsd/milestones/M007/slices/S04/tasks/T03-SUMMARY.md
duration: 4h 06m
verification_result: partial
completed_at: 2026-03-23T07:40:39+08:00
---

# S04: Budget + Receipt + Lost-Card Redesign

**Delivered explicit Budget/Lost-Card recovery behavior and scope-clean Receipt continuity with artifact-backed S04 pass evidence.**

## What Happened

S04 closed the remaining state/actionability gaps in Budget, Receipt, and Lost-Card flows while preserving visual cohesion and scope boundaries.

- Made Budget load/save states explicit and retryable, avoiding silent failure behavior.
- Introduced deterministic Lost-Card flow handling with dedicated view-model state seams and coherent retry/session outcomes (D081).
- Kept Receipt continuity from Home/Transactions while enforcing scope-clean UX (no PDF/report/download utility controls).
- Stabilized Receipt item rendering with indexed identity + fallback markers so sparse or repeated item data remains deterministic (D082).

All summary claims are backed by `.gsd/milestones/M007/slices/S08/tasks/T01-EVIDENCE-MATRIX.md` and S04 verifier/UAT artifacts.

## Verification

Evidence captured for S04:

- `rtk proxy sh scripts/verify-m007-s04.sh` → PASS (`behavior-contract`, `design-contract`, `static-contract`).
- `.gsd/milestones/M007/slices/S04/S04-UAT-RESULT.md` → `uatType: artifact-driven`, `verdict: PASS`.

Environment constraint carried in evidence: `/bin/bash` and `xcodebuild` were unavailable in this Windows executor; host-compatible shell execution and artifact-driven checks provided closure evidence.

## Requirements Advanced

- **R055** — applied stitch primitives across Budget, Receipt, and Lost-Card surfaces.
- **R056** — ensured visible S04 controls remain actionable (`save`, `retry`, `report`, completion actions).
- **R061** — enforced receipt scope cleanliness by keeping utility-action controls absent.
- **R059** — surfaced explicit recoverable state behavior for Budget and Lost-Card flows.
- **R063** — produced deterministic verifier/UAT artifacts for downstream final gate reuse.

## Requirements Validated

- **R061** — validated at artifact level through static-contract checks and UAT PASS evidence confirming utility-action absence.
- **R059** — validated at artifact level through behavior-contract checks and UAT PASS evidence for recoverable failure paths.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- No S04 scope deviation; command-path adjustments were host compatibility adaptations only.

## Known Limitations

- macOS simulator/device build proof remains deferred to final milestone gate because `xcodebuild` is unavailable on this host.

## Follow-ups

- Execute S04 simulator/device checks in an Apple-capable environment during final readiness closure.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift` — explicit load/save failure channels and retry flows.
- `mobile/ios/BankongSetonStudent/ViewModels/LostCardViewModel.swift` — deterministic lost-card state seam and recovery handling.
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift` — stitch-aligned state/action surfaces for budget workflows.
- `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift` — continuity-preserving, scope-clean receipt rendering with fallback markers.
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift` — explicit success/error actionability and retry UX.
- `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` — behavior-contract guardrails for Budget/Lost-Card state transitions.
- `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py` — design/scope guardrails for Budget/Receipt/Lost-Card.
- `scripts/verify-m007-s04.sh` — one-command S04 phased verifier.
- `.gsd/milestones/M007/slices/S04/S04-UAT-RESULT.md` — authoritative artifact-driven UAT verdict.

## Forward Intelligence

### What the next slice should know
- S04 closure depends on explicit state markers in Budget/Lost-Card and static scope guards in Receipt; preserve these seams when touching adjacent flows.

### What's fragile
- Receipt line-item identity and fallback markers are regression-prone if list rendering is simplified without preserving indexed identity semantics.

### Authoritative diagnostics
- `scripts/verify-m007-s04.sh` plus `.gsd/milestones/M007/slices/S04/S04-UAT-RESULT.md` are the canonical trust surfaces for S04 behavior/scope integrity.

### What assumptions changed
- Assumption: receipt item rendering keyed by name-only was sufficient.
- Actual: stable indexed identity + fallback markers are required to keep receipt rendering deterministic across sparse/repeated backend payloads.
