# S07 Demo Readiness

## Purpose

This document is the final acceptance-gate evidence for M007/S07.
It maps requirement scope to both automated proof and manual on-device proof so closure can be judged with explicit PASS/FAIL evidence.

## Acceptance Scope

- Primary closure requirement: **R063** (device-demo readiness for full iOS 17+ journey).
- Supporting requirements: **R056, R058, R059, R060, R061, R062** (plus inherited continuity constraints from prior slices).

## Automated Verification Commands (Closure Set)

1. `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py tests/test_verify_m007_s07_scope_guard_contract.py`
2. `rtk proxy sh scripts/verify-m007-s07.sh`
3. `rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s07.sh').read_text(encoding='utf-8'); required=['fail_with_guidance','guidance=','phase=preflight','phase=diagnostic-surface']; missing=[x for x in required if x not in txt]; assert not missing, missing"`
4. `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
5. `rtk proxy python -c "from pathlib import Path; paths=[Path('.gsd/milestones/M007/slices/S07/S07-UAT.md'), Path('.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md')]; missing=[str(p) for p in paths if not p.exists() or not p.read_text(encoding='utf-8').strip()]; assert not missing, missing"`

Task-level must-have check:

6. `rtk proxy python -c "from pathlib import Path; u=Path('.gsd/milestones/M007/slices/S07/S07-UAT.md'); r=Path('.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md'); assert u.exists() and r.exists(); ut=u.read_text(encoding='utf-8'); rt=r.read_text(encoding='utf-8'); assert 'PASS' in ut and 'FAIL' in ut; required=['R063','R056','R058','R059','R060','R061','R062']; missing=[x for x in required if x not in rt]; assert not missing, missing"`

## Manual Scenario Index (from `S07-UAT.md`)

- S07-01 Login → Home bootstrap continuity
- S07-02 Home controls + QR entry actionability
- S07-03 QR happy path continuity
- S07-04 QR failure + retry path
- S07-05 Post-QR refresh + receipt access
- S07-06 Transactions search/filter/load-more + retry
- S07-07 Budget load/save + retry behavior
- S07-08 Settings persistence + lost-card actionability
- S07-09 Logout/login continuity with persisted local settings
- S07-10 Reduce Motion parity across full journey
- S07-11 Reduce Motion failure/retry parity

## Requirement-to-Proof Traceability

| Requirement | Scope assertion | Automated proof | Manual proof scenarios | Evidence artifact(s) | Status |
|---|---|---|---|---|---|
| R063 | Final redesigned iOS build is demo-ready end-to-end on iOS 17+ | Commands #1, #2, #4, #5 | S07-01 through S07-11 | `S07-UAT.md`, verifier output, iOS build output | ⚠️ Source/document gates pass, but `xcodebuild` unavailable in this environment and manual device sign-off still pending |
| R056 | Visible in-scope controls remain actionable; no dead controls | Command #1 (integration markers), command #2 (integration/scope phases) | S07-02, S07-06, S07-07, S07-08, S07-10, S07-11 | Contract tests + manual checklist results | ⚠️ Automated contract PASS; manual PASS/FAIL evidence pending |
| R058 | Transactions search/filter/load-more behavior remains coherent | Command #1 (transactions markers), command #2 | S07-06, S07-10, S07-11 | Contract tests + manual checklist results | ⚠️ Automated contract PASS; manual PASS/FAIL evidence pending |
| R059 | QR + transactions loading/empty/error/success states remain coherent | Command #1, command #2 | S07-03, S07-04, S07-05, S07-06, S07-11 | Contract tests + manual checklist results | ⚠️ Automated contract PASS; manual PASS/FAIL evidence pending |
| R060 | Local settings persistence survives real flow boundaries | Command #1 (settings markers), command #2 | S07-08, S07-09 | Manual continuity checklist + verifier output | ⚠️ Marker/verifier PASS; manual persistence proof pending |
| R061 | Out-of-scope settings/receipt/payment-method surfaces stay removed | Command #1 (scope contract), command #2 (scope phase) | S07-02, S07-08 | Scope contract output + manual spot checks | ⚠️ Automated scope guard PASS; manual spot-check evidence pending |
| R062 | Motion remains restrained while preserving clarity/actionability | Command #1 (continuity markers), command #2 | S07-10, S07-11 | Manual reduced-motion evidence + verifier output | ⚠️ Automated support PASS; manual Reduce Motion PASS/FAIL evidence pending |

## Verification Run Log

| Command | Exit code | Status | Notes |
|---|---:|---|---|
| `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py tests/test_verify_m007_s07_scope_guard_contract.py` | 0 | ✅ PASS | 8 contract tests passed. |
| `rtk proxy sh scripts/verify-m007-s07.sh` | 0 | ✅ PASS | All verifier phases passed (`preflight`, `contract`, `scope`, `integration`, `diagnostic-surface`). |
| `rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s07.sh').read_text(encoding='utf-8'); required=['fail_with_guidance','guidance=','phase=preflight','phase=diagnostic-surface']; missing=[x for x in required if x not in txt]; assert not missing, missing"` | 0 | ✅ PASS | Verifier source still contains required diagnostic markers. |
| `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ FAIL | `xcodebuild` is not available in the current harness (`program not found`). |
| `rtk proxy python -c "from pathlib import Path; paths=[Path('.gsd/milestones/M007/slices/S07/S07-UAT.md'), Path('.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md')]; missing=[str(p) for p in paths if not p.exists() or not p.read_text(encoding='utf-8').strip()]; assert not missing, missing"` | 0 | ✅ PASS | Both readiness artifacts exist and are non-empty. |
| `rtk proxy python -c "from pathlib import Path; u=Path('.gsd/milestones/M007/slices/S07/S07-UAT.md'); r=Path('.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md'); assert u.exists() and r.exists(); ut=u.read_text(encoding='utf-8'); rt=r.read_text(encoding='utf-8'); assert 'PASS' in ut and 'FAIL' in ut; required=['R063','R056','R058','R059','R060','R061','R062']; missing=[x for x in required if x not in rt]; assert not missing, missing"` | 0 | ✅ PASS | Task must-have mapping and PASS/FAIL markers validated. |

## Environment Constraints / Notes

- This execution environment does not provide Apple `xcodebuild`; simulator build verification cannot be completed here.
- Manual on-device pass/fail execution (S07-01..S07-11) is still required for final closure evidence.

## Closure Recommendation

- Current recommendation: **Conditional-ready** — automated source/document/verifier gates pass, but final S07 closure still requires iOS-capable environment build plus manual UAT sign-off completion in `S07-UAT.md`.
- Manual sign-off owner/date: _TBD_
