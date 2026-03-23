---
id: T02
parent: S06
milestone: M007
provides:
  - Policy-driven, Reduce Motion-aware state transitions across QR, Transactions, Budget, LostCard, and Home demo-critical flows.
key_files:
  - .gsd/milestones/M007/slices/S06/S06-PLAN.md
  - mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift
  - mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift
  - mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift
  - mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift
  - mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift
  - tests/test_verify_m007_s06_motion_behavior_contract.py
key_decisions:
  - Screen-level transitions reuse `AppTheme.Motion` (`.cardSurface` + `.primaryButtonPress`) and switch to opacity-only transitions when `accessibilityReduceMotion` is enabled.
patterns_established:
  - Stateful screens expose explicit transition keys (`stateTransitionKey`, `transactionStateKey`, `loadStateKey`, etc.) and animate those keys via `AppTheme.Motion.animation(...)`.
  - Reduce Motion paths simplify non-essential movement to opacity-based transitions while preserving all existing controls and accessibility identifiers.
observability_surfaces:
  - tests/test_verify_m007_s06_motion_behavior_contract.py
  - tests/test_verify_m007_s06_motion_design_contract.py
  - rtk proxy python -c "... assert 'accessibilityReduceMotion' in txt; assert 'repeatForever' not in txt"
  - rtk proxy python -c "... assert 'AppTheme.Motion' in stateful files ..."
duration: 1h 32m
verification_result: partial
completed_at: 2026-03-23T10:01:27+08:00
blocker_discovered: false
---

# T02: Apply restrained motion tuning to QR, transactions, budget, lost-card, and home states

**Applied policy-driven Reduce Motion transitions across QR, transactions, budget, lost-card, and home state surfaces.**

## What Happened

I first completed the pre-flight artifact fix by adding an explicit phase-status diagnostic verification command to `.gsd/milestones/M007/slices/S06/S06-PLAN.md`.

Then I tuned each in-scope view to consume shared motion policy at screen/state level:
- `QRPayView`: added keyed state transitions (`scanning/loading/confirming/success/error`) with policy animation and Reduce Motion opacity fallback.
- `TransactionsView`: added state-keyed policy animation for loading/empty/error/list/pagination surfaces and reduced-motion-safe state card transitions.
- `BudgetView`: replaced ad-hoc progress animation with policy animation and added keyed transitions for load/save state cards.
- `LostCardView`: added phase-keyed transitions and a reduced-motion-aware secondary CTA button style for the error dismiss action.
- `HomeView`: added policy-driven keyed transitions for error banner and recent-transactions loading/empty/list surfaces.

I also tightened the S06 behavior contract test to assert stateful screens use `AppTheme.Motion` (not only `accessibilityReduceMotion`).

`qodo-get-rules` was attempted per plan skill usage, but no local Qodo config was present (`~/.qodo/config.json` missing), so execution proceeded without repository rules.

## Verification

I ran both T02 task checks and the full slice verification command set.

Task-level checks passed:
- In-scope stateful files include `accessibilityReduceMotion` and contain no `repeatForever` loops.
- QR/Transactions marker check (`success`/`loading`) passed.
- Direct observability check for `AppTheme.Motion` + transition/animation usage in all five stateful views passed.

Slice-level checks are partial at T02 (expected):
- Behavior contract now passes; design contract still fails because T03-owned artifacts are not created yet (`scripts/verify-m007-s06.sh`, `S06-UAT.md`).
- Script-phase commands that call `scripts/verify-m007-s06.sh` fail because the script does not exist yet (T03 scope).
- `rtk proxy bash ...` fails in this Windows host due missing `/bin/bash`.
- `xcodebuild`/`xcrun` fail because Apple toolchain is unavailable on this host.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -c "from pathlib import Path; files=[...]; txt='\\n'.join(...); assert 'accessibilityReduceMotion' in txt; assert 'repeatForever' not in txt"` | 0 | ✅ pass | 0.05s |
| 2 | `rtk proxy python -c "from pathlib import Path; tx=...; qr=...; assert 'loading' in tx.lower(); assert 'success' in qr.lower()"` | 0 | ✅ pass | 0.05s |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m007_s06_motion_behavior_contract.py tests/test_verify_m007_s06_motion_design_contract.py` | 1 | ❌ fail | 1.81s |
| 4 | `rtk proxy sh scripts/verify-m007-s06.sh` | 127 | ❌ fail | 0.04s |
| 5 | `rtk proxy bash scripts/verify-m007-s06.sh` | 1 | ❌ fail | 1.30s |
| 6 | `rtk proxy python -c "import subprocess; ... required=['preflight','behavior-contract','design-contract','static-contract']; ..."` | 1 | ❌ fail | 0.13s |
| 7 | `rtk proxy python -c "import subprocess; ... tags=['preflight','behavior-contract','design-contract','static-contract']; ... any(['fail','pass','missing','required','forbidden'])"` | 1 | ❌ fail | 0.19s |
| 8 | `rtk proxy python -c "import subprocess, re; ... phases=['preflight','behavior-contract','design-contract','static-contract']; ..."` | 1 | ❌ fail | 0.12s |
| 9 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail | 0.02s |
| 10 | `rtk proxy xcrun xctrace list templates` | 1 | ❌ fail | 0.02s |
| 11 | `rtk proxy python -c "from pathlib import Path; assert Path('.gsd/milestones/M007/slices/S06/S06-UAT.md').exists()"` | 1 | ❌ fail | 0.07s |
| 12 | `rtk proxy python -c "from pathlib import Path; ... assert 'AppTheme.Motion' in each stateful file; assert transition/animation markers ..."` | 0 | ✅ pass | 0.05s |

## Diagnostics

- Screen-level transition seams are now explicit in each stateful view via keyed transition state:
  - `QRPayView.stateTransitionKey`
  - `TransactionsView.transactionStateKey`
  - `BudgetView.loadStateKey` / `saveStateKey`
  - `LostCardView` phase-keyed transition + `LostCardSecondaryButtonStyle`
  - `HomeView.errorBannerStateKey` / `recentTransactionStateKey`
- Shared policy usage is now statically inspectable via `tests/test_verify_m007_s06_motion_behavior_contract.py` (`AppTheme.Motion` + `accessibilityReduceMotion` assertions).
- Infinite decorative loop guard remains covered by `tests/test_verify_m007_s06_motion_design_contract.py` (`repeatForever` forbidden).

## Deviations

- Extended `tests/test_verify_m007_s06_motion_behavior_contract.py` beyond original T02 verify lines to require `AppTheme.Motion` usage in all in-scope stateful screens.
- Added one additional phase-status diagnostic command to the S06 slice verification list to satisfy the pre-flight observability gap.

## Known Issues

- `scripts/verify-m007-s06.sh` and `.gsd/milestones/M007/slices/S06/S06-UAT.md` are still missing (T03-owned scope), so design/slice gates remain partial.
- `rtk proxy bash ...` fails in this host due missing `/bin/bash` (Windows/WSL constraint).
- `xcodebuild` and `xcrun` are unavailable in this host environment, so iOS runtime/toolchain checks cannot pass here.

## Files Created/Modified

- `.gsd/milestones/M007/slices/S06/S06-PLAN.md` — Added explicit phase-status diagnostic verification command for failure-path observability.
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — Added policy-driven keyed state transitions with Reduce Motion fallback.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — Added keyed state/pagination transition animation and reduced-motion transition handling.
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift` — Switched progress/state transitions to shared policy and keyed load/save transition surfaces.
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift` — Added phase transition animation and reduced-motion secondary CTA feedback style.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — Added keyed transition handling for error and recent-transaction states using shared policy.
- `tests/test_verify_m007_s06_motion_behavior_contract.py` — Strengthened behavior contract to require shared motion-policy usage in stateful screens.
