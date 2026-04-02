# M008-l1ngya: 

## Vision
TBD

## Slice Overview
| ID | Slice | Risk | Depends | Done | After this |
|----|-------|------|---------|------|------------|
| S02 |  | medium | — | ✅ | # S02: Full UX Rollback Baseline + Native Tab Bar — UAT

**Milestone:** M008-l1ngya
**Written:** 2026-03-27T10:09:46.924Z

# S02: Full UX Rollback Baseline + Native Tab Bar — UAT

**Milestone:** M008-l1ngya
**Written:** 2026-03-27

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S02 is a structural shell + regression-gate slice; acceptance is based on source contracts and phased verifier behavior, not device-only runtime interactions.

## Preconditions

- Repo is at `C:\Users\admin\Desktop\projects\BANKONGSETON`.
- Python + pytest are available in the active environment.
- iOS source files and verifier scripts exist at:
  - `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`
  - `tests/test_verify_m008_s02_ios_rollback_contract.py`
  - `scripts/verify-m008-s02.sh`
- On Windows hosts without `/bin/bash`, Git Bash executable is available at `C:\Program Files\Git\bin\bash.exe`.

## Smoke Test

Run:

1. `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s02.sh`
2. **Expected:** all phases pass and final line reports `[verify-m008-s02] status=passed`.

## Test Cases

### 1. Native tab shell contract is present

1. Run `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py::test_main_tab_view_uses_native_tab_view_with_all_four_tab_items`
2. **Expected:** pass; confirms `TabView(selection:)`, four `Label(...)` tab items, and four matching `.tag(...)` markers are present in `MainTabView.swift`.

### 2. Floating stitch shell markers are removed

1. Run `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py::test_main_tab_view_removes_stitch_shell_markers`
2. **Expected:** pass; confirms forbidden markers (`StitchTabShell(`, `StitchTabItem<MainTab>`, `shellTabs`) are absent.

### 3. Session-expired alert behavior is preserved

1. Run `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py::test_main_tab_view_preserves_session_expired_alert_behavior`
2. **Expected:** pass; confirms alert title/text, `Sign In` action, and `authManager.clearAll()` are still wired.

### 4. Regression harness still protects budget/QR/login

1. Run `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s02.sh`
2. **Expected:** each phase passes:
   - `s02-rollback-contract`
   - `budget-regression`
   - `qr-regression`
   - `login-regression`
3. **Expected:** no phase emits `status=failed` or `guidance=` failure lines.

## Edge Cases

### Windows shell-path fallback for verifier execution

1. Run `rtk proxy bash scripts/verify-m008-s02.sh` on a host with no `/bin/bash`.
2. Confirm failure reflects shell-availability issue, not contract regressions.
3. Re-run with `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s02.sh`.
4. **Expected:** second command passes fully, proving verifier semantics are intact under Windows fallback path.

## Failure Signals

- Any missing/forbidden marker assertion in `test_verify_m008_s02_ios_rollback_contract.py`.
- Any `phase=<name> status=failed` line in `scripts/verify-m008-s02.sh` output.
- `guidance=` lines indicating tab-shell drift, budget regression, QR regression, or login payload drift.

## Requirements Proved By This UAT

- R069 — Native `TabView` navigation shell is implemented and protected by executable contract checks.
- R076 (partial guard) — QR continuity regression suite remains enforced during shell rollback.

## Not Proven By This UAT

- Full pre-M007 UX rollback across all iOS surfaces (home hero redesign, transactions UX simplification, settings scope trim).
- On-device performance/feel acceptance on physical iOS hardware (deferred to later M008 slices and final manual acceptance gate).

## Notes for Tester

- Use the phased verifier as the canonical S02 signal first; run individual tests only when a phase fails and deeper triage is needed.
- On Windows, treat `/bin/bash` errors as environment constraints and use Git Bash path execution for authoritative results.
 |
| S03 | Home Rollback + Credit-Card Hero + QR Continuity | high | S02 | ✅ | Home shows minimalist credit-card balance hero with preserved QR entry/continuity checks passing. |
| S04 | Transactions/Settings Minimalist Scope Restoration | high | S03 | ⬜ | Transactions is filter-only (no search) and Settings exposes theme+accent-only appearance controls. |
| S05 | Integrated UX Closure + Requirement Validation | medium | S01, S02, S03, S04 | ⬜ | Integrated login→home→transactions→budget→settings flow passes contract and regression suites with no QR regressions. |
| S06 | Manual On-Device UAT Gate | medium | S05 | ⬜ | User executes manual iOS device acceptance and records explicit PASS/FAIL evidence for milestone closeout. |
