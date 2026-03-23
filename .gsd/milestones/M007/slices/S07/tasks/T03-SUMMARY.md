---
id: T03
parent: S07
milestone: M007
provides:
  - Final S07 closure evidence package: complete device UAT checklist, requirement-to-proof readiness traceability, and stricter diagnostic-surface artifact enforcement.
key_files:
  - .gsd/milestones/M007/slices/S07/S07-UAT.md
  - .gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md
  - scripts/verify-m007-s07.sh
  - .gsd/DECISIONS.md
key_decisions:
  - Enforced S07 readiness artifacts in verifier `diagnostic-surface` via missing/empty checks with explicit `guidance=` failure lines.
  - Structured manual proof as scenario IDs (S07-01..S07-11) so requirement mapping and manual evidence stay traceable.
patterns_established:
  - Keep closure readiness in two linked docs: execution checklist (`S07-UAT.md`) + evidence matrix (`S07-DEMO-READINESS.md`) tied by scenario IDs.
observability_surfaces:
  - scripts/verify-m007-s07.sh (`phase=diagnostic-surface` hard-fail guidance for missing/empty readiness docs)
  - .gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md (`Verification Run Log` with explicit command status + constraints)
duration: 1h 00m
verification_result: partial
completed_at: 2026-03-23T14:04:00+08:00
blocker_discovered: false
---

# T03: Publish device-demo readiness evidence and close S07 acceptance gate

**Expanded S07 into a closure-ready evidence set by shipping a full PASS/FAIL iOS journey checklist, requirement traceability doc, and artifact-phase verifier enforcement for missing/empty readiness docs.**

## What Happened

I completed the task-plan outputs end-to-end:

1. Replaced the S07 UAT scaffold with a full manual device checklist in `.gsd/milestones/M007/slices/S07/S07-UAT.md`:
   - Covers login → home → QR success/failure-retry → receipt/history → transactions search/filter/load-more → budget retry/save → settings/lost-card → logout/login continuity.
   - Includes explicit PASS/FAIL criteria for each checkpoint.
   - Includes dedicated Reduce Motion parity and Reduce Motion failure/retry paths.
2. Created `.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md`:
   - Maps R063, R056, R058, R059, R060, R061, R062 to automated proof commands, manual scenario IDs, and evidence artifacts.
   - Captures actual closure command outcomes and environment constraints in a run log.
3. Hardened `scripts/verify-m007-s07.sh` artifact enforcement:
   - Added `S07-DEMO-READINESS.md` to diagnostic checks.
   - Added `assert_non_empty_doc` so missing/empty readiness artifacts fail in `phase=diagnostic-surface` with actionable `guidance=` messages.
   - Kept existing phase-tagged output and contract/scope behavior intact.
4. Recorded an observability decision via GSD decision log (D087) so downstream work understands why diagnostic-surface now enforces readiness artifact completeness.

Qodo rules were not loaded in this environment (no Qodo config/API context surfaced during this task run).

## Verification

I executed the task-level and slice-level closure commands after implementing the docs + verifier updates. Source contracts/verifier/docs checks pass; simulator build remains environment-constrained.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py tests/test_verify_m007_s07_scope_guard_contract.py` | 0 | ✅ pass | 1s |
| 2 | `rtk proxy sh scripts/verify-m007-s07.sh` | 0 | ✅ pass | 3s |
| 3 | `rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s07.sh').read_text(encoding='utf-8'); required=['fail_with_guidance','guidance=','phase=preflight','phase=diagnostic-surface']; missing=[x for x in required if x not in txt]; assert not missing, missing"` | 0 | ✅ pass | <1s |
| 4 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail | <1s |
| 5 | `rtk proxy python -c "from pathlib import Path; paths=[Path('.gsd/milestones/M007/slices/S07/S07-UAT.md'), Path('.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md')]; missing=[str(p) for p in paths if not p.exists() or not p.read_text(encoding='utf-8').strip()]; assert not missing, missing"` | 0 | ✅ pass | <1s |
| 6 | `rtk proxy python -c "from pathlib import Path; u=Path('.gsd/milestones/M007/slices/S07/S07-UAT.md'); r=Path('.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md'); assert u.exists() and r.exists(); ut=u.read_text(encoding='utf-8'); rt=r.read_text(encoding='utf-8'); assert 'PASS' in ut and 'FAIL' in ut; required=['R063','R056','R058','R059','R060','R061','R062']; missing=[x for x in required if x not in rt]; assert not missing, missing"` | 0 | ✅ pass | <1s |

## Diagnostics

- Primary closure inspection: `rtk proxy sh scripts/verify-m007-s07.sh`.
- Artifact readiness failure localization now includes:
  - `phase=diagnostic-surface status=failed`
  - `guidance=Missing required readiness artifact ...` or `guidance=Readiness artifact is empty ...`
- Traceability inspection surfaces:
  - `.gsd/milestones/M007/slices/S07/S07-UAT.md` for manual PASS/FAIL execution.
  - `.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md` for requirement mapping and command outcomes.

## Deviations

- None.

## Known Issues

- `xcodebuild` is unavailable in this harness (`program not found`), so simulator build proof cannot be completed here.
- Manual iOS 17+ execution of S07-01..S07-11 remains pending for final human sign-off.

## Files Created/Modified

- `.gsd/milestones/M007/slices/S07/S07-UAT.md` — Replaced scaffold with full PASS/FAIL journey checklist including default-motion and Reduce Motion paths with retry/failure checkpoints.
- `.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md` — Added requirement-to-proof traceability matrix and verification run log with environment constraints.
- `scripts/verify-m007-s07.sh` — Added readiness artifact enforcement for missing/empty docs in diagnostic-surface phase.
- `.gsd/milestones/M007/slices/S07/S07-PLAN.md` — Marked T03 complete.
- `.gsd/DECISIONS.md` — Appended decision D087 for diagnostic-surface readiness artifact enforcement.
