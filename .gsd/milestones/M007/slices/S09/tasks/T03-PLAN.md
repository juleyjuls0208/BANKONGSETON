---
estimated_steps: 5
estimated_files: 5
skills_used:
  - qodo-get-rules
  - build-iphone-apps
  - swiftui
  - test
  - debug-like-expert
---

# T03: Execute physical-device UAT (S07-01..S07-11) and propagate milestone closure

**Slice:** S09 — macOS Runtime + Physical Device Acceptance Closure
**Milestone:** M007

## Description

Complete the human acceptance gate on a physical iOS 17+ device and wire the result into milestone closure records. This task is the final proof surface for R063 and supporting runtime requirements.

## Steps

1. Use `.gsd/milestones/M007/slices/S07/S07-UAT.md` as the canonical checklist and execute scenarios `S07-01` through `S07-11` on a physical iOS 17+ device against the build proven in S09 runtime proof.
2. Record per-scenario outcomes, observed behavior, and any failure notes in `.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md` with explicit PASS/FAIL status for each scenario ID.
3. Include required run metadata in `S09-UAT-RESULT.md`: tester name, execution date/time, device model, iOS version, app build identifier, and final sign-off block.
4. Update `.gsd/milestones/M007/M007-VALIDATION.md` so S09 closure references both runtime and UAT artifacts; if any scenario fails, document blockers and keep remediation status explicit.
5. Re-run S09 evidence contract checks to guarantee the artifact set is machine-auditable and complete.

## Must-Haves

- [ ] All scenario IDs `S07-01`..`S07-11` appear in S09 UAT result with explicit PASS/FAIL entries.
- [ ] Final UAT artifact contains tester/device/build metadata and sign-off text.
- [ ] Milestone validation links S09 runtime + UAT evidence and states an explicit final closure verdict.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s09_evidence_contract.py`
- `rtk proxy python -c "from pathlib import Path; txt=Path('.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md').read_text(encoding='utf-8'); required=['S07-01','S07-02','S07-03','S07-04','S07-05','S07-06','S07-07','S07-08','S07-09','S07-10','S07-11','Final S09 UAT verdict','Tester','Device model','iOS version','App build','Sign-off']; missing=[x for x in required if x not in txt]; assert not missing, missing"`
- `rtk proxy python -c "from pathlib import Path; txt=Path('.gsd/milestones/M007/M007-VALIDATION.md').read_text(encoding='utf-8'); required=['S09-RUNTIME-PROOF.json','S09-UAT-RESULT.md']; missing=[x for x in required if x not in txt]; assert not missing, missing"`

## Observability Impact

- Signals added/changed: per-scenario physical-device verdicts plus final acceptance sign-off metadata.
- How a future agent inspects this: open `.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md` first, then correlate with `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md` and `M007-VALIDATION.md`.
- Failure state exposed: scenario-level failures are attributable to specific UAT IDs with notes, preventing ambiguous milestone-level remediation status.

## Inputs

- `.gsd/milestones/M007/slices/S07/S07-UAT.md` — canonical scenario definitions and acceptance expectations.
- `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json` — runtime/simulator baseline to tie manual UAT to a concrete build run.
- `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md` — human-readable runtime context for UAT report cross-linking.
- `.gsd/milestones/M007/M007-VALIDATION.md` — milestone-level closure state to update.
- `tests/test_verify_m007_s09_evidence_contract.py` — artifact completeness contract.

## Expected Output

- `.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md` — signed physical-device PASS/FAIL matrix for S07-01..S07-11.
- `.gsd/milestones/M007/M007-VALIDATION.md` — updated closure/remediation verdict with S09 evidence links.
- `.gsd/milestones/M007/slices/S07/S07-UAT.md` — optional run-log/status updates while preserving canonical scenario definitions.
