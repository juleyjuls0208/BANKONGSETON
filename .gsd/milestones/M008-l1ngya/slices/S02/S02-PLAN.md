# S02: Full UX Rollback Baseline + Native Tab Bar

**Goal:** ---
id: S02
parent: M008-l1ngya
milestone: M008-l1ngya
provides:
  - Native `TabView` root shell baseline for M008 rollback work (R069).
  - Deterministic regression gate command for downstream slices (`scripts/verify-m008-s02.sh`).
requires:
  []
affects:
  - S03
  - S04
  - S05
  - S06
key_files:
  - mobile/ios/BankongSetonStudent/Views/MainTabView.swift
  - tests/test_verify_m008_s02_ios_rollback_contract.py
  - scripts/verify-m008-s02.sh
  - .gsd/milestones/M008-l1ngya/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/DECISIONS.md
  - .gsd/PROJECT.md
key_decisions:
  - Kept `MainTab` enum metadata and session-expired alert flow unchanged while replacing only the root shell composition with native `TabView`.
  - Locked rollback closure to one phased verifier (`scripts/verify-m008-s02.sh`) that co-runs shell, budget, QR, and login regression suites with phase-scoped guidance output.
patterns_established:
  - For rollback slices that touch shared UI scaffolding, bind closure to one phased verifier that includes adjacent-regression suites, not only local assertions.
  - Preserve existing session/auth failure surfaces while swapping structural UI containers to prevent hidden boundary regressions.
observability_surfaces:
  - `scripts/verify-m008-s02.sh` phase logs (`phase=<name> status=...`) with guidance lines on failures.
  - Contract tests in `tests/test_verify_m008_s02_ios_rollback_contract.py` that expose shell-drift signatures (missing native markers, forbidden stitch markers, alert contract drift).
drill_down_paths:
  - .gsd/milestones/M008-l1ngya/slices/S02/tasks/T01-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-03-27T10:09:46.924Z
blocker_discovered: false
---

# S02: Full UX Rollback Baseline + Native Tab Bar

**Native iOS tab navigation now runs on `TabView` (floating stitch shell removed) with a phased rollback verifier that also protects budget, QR, and login contracts.**

## What Happened

S02 delivered the structural navigation rollback anchor for M008 by replacing `StitchTabShell`/`StitchTabItem` composition in `MainTabView` with native `TabView(selection:)` and four native tab items (`Home`, `History`, `Budget`, `Settings`). The change intentionally preserved existing auth/session-expiry behavior (`showSessionExpiredAlert`, `Sign In`, `authManager.clearAll()`) so rollback of chrome did not alter session boundary semantics. To make this slice executable and safe for downstream rollback work, the slice added a dedicated source-contract suite (`tests/test_verify_m008_s02_ios_rollback_contract.py`) and a phased harness (`scripts/verify-m008-s02.sh`) that validates shell migration and keeps budget, QR, and student-ID-only login regressions in the same closure command.

## Verification

Re-ran all slice contracts and phased checks successfully:
- `rtk proxy python -m py_compile tests/test_verify_m008_s02_ios_rollback_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_behavior_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m007_s09_override_contract.py::test_login_state_and_payload_are_student_id_only`
- `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s02.sh`
All passed, including all verifier phases and final `status=passed`.

## Requirements Advanced

- R068 — Implemented native tab chrome in `MainTabView` and removed stitch-shell markers while preserving root app navigation semantics.
- R069 — Delivered native `TabView` + `.tabItem` shell replacement with explicit source-contract enforcement.
- R076 — Embedded QR continuity regression checks in the phased S02 verifier to ensure rollback work does not break existing QR-path contracts.

## Requirements Validated

- R069 — `tests/test_verify_m008_s02_ios_rollback_contract.py` and `scripts/verify-m008-s02.sh` pass with native tab markers present and stitch-shell markers absent.

## New Requirements Surfaced

- None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

`rtk proxy bash scripts/verify-m008-s02.sh` is not runnable on this Windows host when `/bin/bash` is absent; verifier execution uses `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s02.sh` with identical script semantics.

## Known Limitations

S02 only establishes the navigation-shell rollback baseline and guards; broader pre-M007 surface rollback (home card-style hero, transactions filter-only UX, settings minimalism refinements) remains for subsequent slices. Swift LSP diagnostics are still unavailable on this host, so proof is contract-test/verifier driven.

## Follow-ups

S03 should proceed from this shell baseline and avoid reintroducing custom floating-tab abstractions. Keep `scripts/verify-m008-s02.sh` in the default pre-merge loop while Home rollback and QR continuity refinements land, so tab-shell drift is caught before later UX slices.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift` — Replaced floating stitch shell with native `TabView` + `.tabItem` labels/tags while preserving session-expired alert behavior.
- `tests/test_verify_m008_s02_ios_rollback_contract.py` — Added rollback source-contract tests asserting native tab markers, stitch-shell absence, and session-expired alert continuity.
- `scripts/verify-m008-s02.sh` — Added phased S02 verifier with `preflight`, `s02-rollback-contract`, `budget-regression`, `qr-regression`, and `login-regression` stages plus phase-scoped guidance output.
- `.gsd/DECISIONS.md` — Appended S02 decisions: rollback verifier composition and R069 validation evidence.
- `.gsd/PROJECT.md` — Refreshed project current-state section to include delivered S02 navigation/verification baseline.

**Demo:** After this: # S02: Full UX Rollback Baseline + Native Tab Bar — UAT

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


## Tasks
- [x] **T01: Replaced the iOS floating tab shell with native TabView and added S02 rollback-contract + phased verifier harness.** — 
