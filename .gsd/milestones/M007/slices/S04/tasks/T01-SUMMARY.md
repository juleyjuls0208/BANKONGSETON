---
id: T01
parent: S04
milestone: M007
provides:
  - Explicit budget load/save failure channels with retry hooks and non-silent markers
  - Dedicated LostCardViewModel phase state machine wired to LostCardView actions
  - S04 behavior contract pytest suite for budget/lost-card/auth coherence
key_files:
  - mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift
  - mobile/ios/BankongSetonStudent/ViewModels/LostCardViewModel.swift
  - mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift
  - mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj
  - tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py
key_decisions:
  - Treat `APIError.cardLost` during lost-card reporting as a terminal success-phase transition before invoking `AuthManager.handleCardLost()` so card-lost semantics remain coherent with auth/session boundaries.
patterns_established:
  - Replace silent catch paths with explicit published failure channels and retry methods (`retryLoad`, `retryLastSave`, `retryReport`).
  - Use enum-backed phase transitions (`idle/loading/success/error`) with reason-tagged logs for lost-card flow observability.
observability_surfaces:
  - `BudgetViewModel.loadErrorMessage` / `saveErrorMessage` / `hasLoadFailureState` / `hasSaveFailureState`
  - `LostCardViewModel.phase` + transition logs (`LostCardFlowPhase transition ... reason=...`)
  - `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`
duration: 1h 28m
verification_result: partial
completed_at: 2026-03-23
blocker_discovered: false
---

# T01: Harden Budget and Lost-Card behavior contracts with explicit recoverable state channels

**Added explicit Budget error/retry channels and a phase-driven Lost-Card flow model, then locked both with an S04 behavior contract test suite.**

## What Happened

I implemented the behavior-contract foundation for S04 by removing BudgetViewModel’s silent failure paths and introducing explicit published load/save failure channels with recoverable retry methods.

I added a new `LostCardViewModel` with explicit `idle/loading/success/error` flow phases, reason-tagged transitions for observability, and coherent handling for `APIError.unauthorized`, `APIError.cardLost`, and generic failures at the `AuthManager` session boundary.

I rewired `LostCardView` to consume the new view-model contract so each visible phase exposes a real action (report, retry, or post-success exit) with no dead in-scope controls.

I created `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` to assert the required source-level behavior markers (Budget error channels/retry hooks, Lost-Card state machine, and auth/session coherence hooks).

I also updated the Xcode project file to include `LostCardViewModel.swift` in target sources.

Qodo rules loading was attempted first, but local Qodo config (`C:/Users/admin/.qodo/config.json`) is not present in this environment, so no Qodo rules could be loaded/applied for this task.

## Verification

I ran the task-level behavior contract test and the required build check command. The behavior contract test passed. Build verification could not complete because `xcodebuild` is not installed in this execution environment.

I also ran the slice-level checks required by S04. As expected for T01 (with T02/T03 artifacts not yet implemented), the design contract and one-command verifier checks failed due missing file/artifact/tooling.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` | 0 | ✅ pass | 0.31s |
| 2 | `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py` | 4 | ❌ fail | 0.00s |
| 3 | `rtk proxy bash scripts/verify-m007-s04.sh` | 1 | ❌ fail | <1s |
| 4 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail | 21.2s |
| 5 | Manual checklist in `.gsd/milestones/M007/slices/S04/S04-UAT.md` | N/A | ❌ fail | Not run |

## Diagnostics

- Budget failure channels are inspectable in `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift` via:
  - `loadErrorMessage`
  - `saveErrorMessage`
  - `pendingRetryLimit`
  - `hasLoadFailureState` / `hasSaveFailureState`
- Lost-card flow phase is inspectable in `mobile/ios/BankongSetonStudent/ViewModels/LostCardViewModel.swift` via:
  - `LostCardFlowPhase` (`idle/loading/success/error`)
  - transition logs: `[LostCardViewModel] LostCardFlowPhase transition ... reason=...`
- Contract surface is enforced by:
  - `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`

## Deviations

- Could not load Qodo rules because required local configuration is missing (`C:/Users/admin/.qodo/config.json`).

## Known Issues

- `xcodebuild` is unavailable in this environment (`program not found`), so iOS build verification must be re-run on a macOS/Xcode-capable host.
- `rtk proxy bash ...` currently fails on this Windows host due missing `/bin/bash` (WSL/bash unavailable), so `scripts/verify-m007-s04.sh` could not execute here.
- `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py` is not present yet (expected to be delivered in T02).
- `.gsd/milestones/M007/slices/S04/S04-UAT.md` is not present yet (expected to be delivered in T03).

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift` — added explicit load/save failure channels, retry hooks, and non-silent budget segment failure handling.
- `mobile/ios/BankongSetonStudent/ViewModels/LostCardViewModel.swift` — added new lost-card phase state machine with auth-aware outcome handling.
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift` — rewired UI to phase-driven actions (report/loading/retry/success exit).
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj` — registered `LostCardViewModel.swift` in project groups and source build phase.
- `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` — added S04 behavior contract assertions for budget/lost-card/auth coherence.
- `.gsd/milestones/M007/slices/S04/S04-PLAN.md` — marked T01 as complete (`[x]`).
