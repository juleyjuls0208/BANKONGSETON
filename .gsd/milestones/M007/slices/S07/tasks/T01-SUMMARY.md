---
id: T01
parent: S07
milestone: M007
provides:
  - S07 source-contract gate (integration + scope) plus phased verifier diagnostics and initial UAT scaffold.
key_files:
  - tests/test_verify_m007_s07_integration_behavior_contract.py
  - tests/test_verify_m007_s07_scope_guard_contract.py
  - scripts/verify-m007-s07.sh
  - .gsd/milestones/M007/slices/S07/S07-UAT.md
key_decisions:
  - Implemented S07 closure as marker-based source contracts with a phase-tagged shell verifier (`phase=`/`guidance=`) instead of ad hoc grep checks.
  - Kept `$...` shell literals single-quoted in verifier assertions (for example `'text: $viewModel.searchQuery'`) to remain safe under `set -u`.
patterns_established:
  - Split contract enforcement into `contract` (required behavior markers) and `scope` (forbidden regression markers) phases.
  - Added `diagnostic-surface` phase that validates presence/shape of UAT evidence artifacts.
observability_surfaces:
  - scripts/verify-m007-s07.sh (`phase=preflight|contract|scope|integration|diagnostic-surface`, `guidance=` lines on failure)
  - tests/test_verify_m007_s07_integration_behavior_contract.py (QR/Home refresh log markers, continuity seams)
  - tests/test_verify_m007_s07_scope_guard_contract.py (forbidden out-of-scope marker guardrails)
duration: 1h 05m
verification_result: passed
completed_at: 2026-03-23T13:05:00+08:00
blocker_discovered: false
---

# T01: Build S07 integration contracts and phased closure verifier

**Added S07 integration/scope contract tests, shipped a phased `verify-m007-s07.sh` with actionable diagnostics, and seeded `S07-UAT.md` headings consumed by the verifier.**

## What Happened

I implemented all four planned outputs for T01:

1. Created `tests/test_verify_m007_s07_integration_behavior_contract.py` with required final-assembly markers for:
   - QR success handoff and observability (`QRPayView` callback path, `QRPayViewModel` transition logging, Home refresh hook)
   - Home/Transactions receipt access continuity
   - Transactions search/filter/load-more and split error-channel continuity
   - Settings + Lost Card actionability seams
2. Created `tests/test_verify_m007_s07_scope_guard_contract.py` with forbidden-marker checks that prevent out-of-scope payment/settings/receipt utility regressions.
3. Implemented `scripts/verify-m007-s07.sh` with `set -euo pipefail`, `fail_with_guidance`, and explicit phases:
   - `preflight`
   - `contract`
   - `scope`
   - `integration`
   - `diagnostic-surface`
4. Seeded `.gsd/milestones/M007/slices/S07/S07-UAT.md` with verifier-referenced headings and PASS/FAIL checkpoint placeholders.

I also fixed one false-positive guardrail during verification: the scope test originally banned plain text tokens (`NFC Pay`, `Apple Pay`) that appear in a Home-view explanatory comment, so I narrowed the forbidden markers to actionable UI strings/identifiers.

Qodo rules could not be loaded because `~/.qodo/config.json` is not present in this environment.

## Verification

I ran both task-level verification commands and the slice-level verification commands.

- Task-level checks passed:
  - new S07 pytest contracts
  - verifier source-string contract (`set -euo pipefail`, `fail_with_guidance`, `phase=diagnostic-surface`, `guidance=`)
- Slice-level checks partially passed (expected for an intermediate slice task):
  - S07 verifier script passed all current phases
  - verifier marker check passed
  - iOS build command failed because `xcodebuild` is unavailable in this environment
  - readiness-doc presence check failed because `S07-DEMO-READINESS.md` is intentionally not created until T03

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py tests/test_verify_m007_s07_scope_guard_contract.py` | 0 | ✅ pass | 1s |
| 2 | `rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s07.sh').read_text(encoding='utf-8'); required=['set -euo pipefail','fail_with_guidance','phase=diagnostic-surface','guidance=']; missing=[x for x in required if x not in txt]; assert not missing, missing"` | 0 | ✅ pass | 0s |
| 3 | `rtk proxy sh scripts/verify-m007-s07.sh` | 0 | ✅ pass | 3s |
| 4 | `rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s07.sh').read_text(encoding='utf-8'); required=['fail_with_guidance','guidance=','phase=preflight','phase=diagnostic-surface']; missing=[x for x in required if x not in txt]; assert not missing, missing"` | 0 | ✅ pass | 0s |
| 5 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail | 0s |
| 6 | `rtk proxy python -c "from pathlib import Path; paths=[Path('.gsd/milestones/M007/slices/S07/S07-UAT.md'), Path('.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md')]; missing=[str(p) for p in paths if not p.exists() or not p.read_text(encoding='utf-8').strip()]; assert not missing, missing"` | 1 | ❌ fail | 0s |

## Diagnostics

- Primary inspection command: `rtk proxy sh scripts/verify-m007-s07.sh`
- Failure localization comes from structured phase logs:
  - `phase=<name> status=running|passed|failed`
  - `guidance=<actionable next step>`
- Integration observability is contract-anchored via:
  - `QRPayState transition ... reason=...` marker in `QRPayViewModel.swift`
  - Home refresh continuity log marker in `HomeViewModel.swift`

## Deviations

- No plan-level deviation. I only narrowed forbidden marker literals in scope tests to avoid comment-only false positives while preserving the intended scope guard behavior.

## Known Issues

- `xcodebuild` is not available in the current environment, so simulator build verification cannot pass here.
- `.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md` is still missing; this is expected to be created/finalized in T03.

## Files Created/Modified

- `tests/test_verify_m007_s07_integration_behavior_contract.py` — Added S07 final-assembly integration behavior markers.
- `tests/test_verify_m007_s07_scope_guard_contract.py` — Added S07 scope-regression forbidden-marker checks.
- `scripts/verify-m007-s07.sh` — Added phased S07 verifier with guidance-rich diagnostics and safe `set -u` literal assertions.
- `.gsd/milestones/M007/slices/S07/S07-UAT.md` — Added initial UAT scaffold with verifier-referenced headings/checkpoints.
- `.gsd/milestones/M007/slices/S07/S07-PLAN.md` — Marked T01 as complete (`[x]`).
