---
estimated_steps: 5
estimated_files: 6
skills_used:
  - qodo-get-rules
  - build-iphone-apps
  - swiftui
  - test
  - debug-like-expert
---

# T03: Re-run runtime + physical-device UAT and publish post-override closure evidence

**Slice:** S09 — Override Remediation + Final Device Acceptance Closure
**Milestone:** M007

## Description

After T02 remediation, execute final runtime/device acceptance and publish evidence that specifically proves the override requirements are satisfied on real iOS behavior.

## Steps

1. Execute `scripts/verify-m007-s09.sh` on an Apple-capable host using the post-override codebase and regenerate runtime proof artifacts.
2. Run physical-device iOS 17+ UAT across the S07 scenario set, plus explicit override checkpoints: dark mode default launch, login without PIN, and transactions filters `QR Pay`/`Card Pay`/`Load`.
3. Record per-scenario PASS/FAIL and override-specific evidence markers in `.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md` with tester/device/build metadata.
4. Update `.gsd/milestones/M007/M007-VALIDATION.md` so final milestone closure references the refreshed runtime + UAT artifacts and declares explicit post-override verdict.
5. Re-run S09 evidence/override contract checks to ensure artifacts remain machine-auditable.

## Must-Haves

- [ ] Runtime proof artifacts reflect post-override execution (not stale pre-override runs).
- [ ] UAT artifact explicitly states pass/fail for dark mode default, no-PIN login, and `QR Pay`/`Card Pay`/`Load` filters.
- [ ] Milestone validation references refreshed S09 artifacts and provides a final closure verdict.

## Verification

- `rtk proxy sh scripts/verify-m007-s09.sh`
- `rtk proxy python -m pytest -q tests/test_verify_m007_s09_evidence_contract.py tests/test_verify_m007_s09_override_contract.py`
- `rtk proxy python -c "import json; from pathlib import Path; data=json.loads(Path('.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json').read_text(encoding='utf-8')); assert data['overall_verdict'].lower()=='pass', data['overall_verdict']"`
- `rtk proxy python -c "from pathlib import Path; txt=Path('.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md').read_text(encoding='utf-8'); required=['Dark mode default verified','Login PIN removed','Transactions filters: QR Pay, Card Pay, Load','Final S09 UAT verdict','Tester','Device model','iOS version','App build','Sign-off']; missing=[x for x in required if x not in txt]; assert not missing, missing"`
- `rtk proxy python -c "from pathlib import Path; txt=Path('.gsd/milestones/M007/M007-VALIDATION.md').read_text(encoding='utf-8'); required=['S09-RUNTIME-PROOF.json','S09-UAT-RESULT.md','post-override']; missing=[x for x in required if x not in txt]; assert not missing, missing"`

## Observability Impact

- Signals added/changed: post-override runtime/UAT closure markers and explicit override checkpoint status in evidence docs.
- How a future agent inspects this: open `S09-RUNTIME-PROOF.json` for machine verdicts, then `S09-UAT-RESULT.md` + `M007-VALIDATION.md` for signed human acceptance narrative.
- Failure state exposed: any unresolved override item blocks closure with scenario-level attribution instead of generic “UAT failed”.

## Inputs

- `scripts/verify-m007-s09.sh` — phased runtime verifier.
- `scripts/verify-m007-s09-runtime.py` — runtime proof serializer.
- `tests/test_verify_m007_s09_evidence_contract.py` — artifact schema/completeness checks.
- `tests/test_verify_m007_s09_override_contract.py` — override-specific source/evidence checks.
- `.gsd/milestones/M007/slices/S07/S07-UAT.md` — canonical scenario checklist.

## Expected Output

- `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json` and `.md` refreshed with post-override run data.
- `.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md` containing override checkpoints plus full signed scenario matrix.
- `.gsd/milestones/M007/M007-VALIDATION.md` updated with explicit post-override final closure verdict.
