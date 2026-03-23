# S09: macOS Runtime + Physical Device Acceptance Closure

**Goal:** Close the final M007 runtime gate by executing Apple-tooling checks plus physical iOS 17+ acceptance scenarios, then publishing auditable PASS/FAIL evidence.
**Demo:** Reviewer can open `S09-RUNTIME-PROOF.json`/`S09-RUNTIME-PROOF.md` and `S09-UAT-RESULT.md`, verify S07-01..S07-11 were executed on a physical device, and see `M007-VALIDATION.md` updated from remediation ambiguity to an explicit closure verdict with linked evidence.

## Must-Haves

- **R063 (owned):** Physical iOS 17+ acceptance is executed and signed with explicit PASS/FAIL evidence for the full S07 scenario set.
- **R056 (support):** Final in-scope controls remain actionable in device-run evidence (no dead-control regressions hidden behind static checks).
- **R058 + R059 (support):** Transactions search/filter/load-more and loading/empty/error/success state fidelity are re-proven in real runtime walkthrough evidence.
- **R060 + R061 (support):** Local settings persistence and scope-pruned surfaces remain correct in final runtime closure artifacts.
- **R062 + R055 + R057 (support):** Motion quality stays restrained on physical iOS 17+ and stitch-faithful/QR-only continuity remains intact end-to-end.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s09_runtime_contract.py tests/test_verify_m007_s09_evidence_contract.py`
- `rtk proxy sh scripts/verify-m007-s09.sh`
- `rtk proxy python -c "import json; from pathlib import Path; p=Path('.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json'); data=json.loads(p.read_text(encoding='utf-8')); required=['generated_at','host','overall_verdict','phases']; missing=[k for k in required if k not in data]; assert not missing, missing; phase_ids={phase['id'] for phase in data['phases']}; expected={'s07_baseline','apple_tooling','simulator_build','xctrace_templates','artifact_completeness'}; assert expected.issubset(phase_ids), sorted(expected-phase_ids)"`
- `rtk proxy python -c "from pathlib import Path; txt=Path('.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md').read_text(encoding='utf-8'); required=['S07-01','S07-02','S07-03','S07-04','S07-05','S07-06','S07-07','S07-08','S07-09','S07-10','S07-11','Final S09 UAT verdict','Tester','Device model','iOS version','App build','Sign-off']; missing=[x for x in required if x not in txt]; assert not missing, missing"`
- `rtk proxy python -c "from pathlib import Path; txt=Path('.gsd/milestones/M007/M007-VALIDATION.md').read_text(encoding='utf-8'); required=['S09','S09-RUNTIME-PROOF.json','S09-UAT-RESULT.md']; missing=[x for x in required if x not in txt]; assert not missing, missing"`

## Observability / Diagnostics

- Runtime signals: phased verifier output (`phase=...`, `guidance=...`) for baseline contracts, Apple-tooling readiness, simulator build, and artifact-completeness checks.
- Inspection surfaces: `scripts/verify-m007-s09.sh`, `scripts/verify-m007-s09-runtime.py`, `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json`, `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md`, `.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md`.
- Failure visibility: each phase captures command, exit status, timestamp, and next-step guidance; UAT result captures per-scenario failure notes and final sign-off verdict.
- Redaction constraints: no credentials, QR token payloads, or personally identifying data may appear in runtime/UAT evidence artifacts.

## Integration Closure

- Upstream surfaces consumed: `scripts/verify-m007-s07.sh`, `tests/test_verify_m007_s07_integration_behavior_contract.py`, `tests/test_verify_m007_s07_scope_guard_contract.py`, `.gsd/milestones/M007/slices/S07/S07-UAT.md`, and iOS scheme/project files under `mobile/ios/BankongSetonStudent`.
- New wiring introduced in this slice: S09 phased verifier + runtime proof serializer + physical-device UAT result artifact linked into milestone validation.
- What remains before the milestone is truly usable end-to-end: nothing once S09 runtime proof and signed UAT verdict are present and `M007-VALIDATION.md` reflects them.

## Tasks

- [ ] **T01: Author S09 phased runtime verifier and evidence contract tests** `est:1h 20m`
  - Why: S09 closure needs a deterministic, inspectable gate before Apple-host execution and manual UAT can be trusted.
  - Files: `scripts/verify-m007-s09.sh`, `scripts/verify-m007-s09-runtime.py`, `tests/test_verify_m007_s09_runtime_contract.py`, `tests/test_verify_m007_s09_evidence_contract.py`
  - Do: Implement an S09 verifier with phase-tagged diagnostics and guidance hooks, add a runtime-proof serializer for JSON/Markdown artifacts, and add pytest contracts asserting required phase markers plus proof-schema expectations.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s09_runtime_contract.py tests/test_verify_m007_s09_evidence_contract.py && rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s09.sh').read_text(encoding='utf-8'); required=['set -euo pipefail','fail_with_guidance','phase=s07_baseline','phase=apple_tooling','phase=simulator_build','phase=xctrace_templates','phase=artifact_completeness','guidance=']; missing=[x for x in required if x not in txt]; assert not missing, missing"`
  - Done when: S09 verifier/runtime-proof contracts are executable and fail with localized guidance instead of ambiguous shell errors.
- [ ] **T02: Execute Apple-host simulator/runtime checks and publish S09 runtime proof** `est:1h 10m`
  - Why: R063 cannot close from source-only checks; simulator/runtime evidence must be generated on a host with Xcode CLI tooling.
  - Files: `scripts/verify-m007-s09.sh`, `scripts/verify-m007-s09-runtime.py`, `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json`, `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md`, `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/xcshareddata/xcschemes/BankongSetonStudent.xcscheme`
  - Do: Run S09 verifier on an Apple-capable host, execute S07 baseline contracts and simulator build/xctrace phases, and persist machine + human runtime proof artifacts with phase-level verdicts and command evidence.
  - Verify: `rtk proxy sh scripts/verify-m007-s09.sh && rtk proxy python -c "import json; from pathlib import Path; data=json.loads(Path('.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json').read_text(encoding='utf-8')); assert data['overall_verdict'].lower()=='pass', data['overall_verdict']; status={phase['id']: phase['status'].lower() for phase in data['phases']}; required={'s07_baseline':'pass','apple_tooling':'pass','simulator_build':'pass','xctrace_templates':'pass','artifact_completeness':'pass'}; bad={k:(status.get(k),v) for k,v in required.items() if status.get(k)!=v}; assert not bad, bad"`
  - Done when: Runtime proof artifacts are non-empty and show pass verdicts for baseline, Apple tooling, simulator build, xctrace listing, and artifact completeness.
- [ ] **T03: Execute physical-device UAT (S07-01..S07-11) and propagate closure to milestone validation** `est:1h 30m`
  - Why: Final acceptance remains open until physical-device scenarios are explicitly run, signed, and reflected in the milestone validation surface.
  - Files: `.gsd/milestones/M007/slices/S07/S07-UAT.md`, `.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md`, `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md`, `.gsd/milestones/M007/M007-VALIDATION.md`, `tests/test_verify_m007_s09_evidence_contract.py`
  - Do: Execute S07-01 through S07-11 on a physical iOS 17+ device, write signed per-scenario PASS/FAIL evidence and metadata into `S09-UAT-RESULT.md`, and update milestone validation to reference S09 runtime/UAT artifacts with an explicit final verdict.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s09_evidence_contract.py && rtk proxy python -c "from pathlib import Path; txt=Path('.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md').read_text(encoding='utf-8'); required=['S07-01','S07-02','S07-03','S07-04','S07-05','S07-06','S07-07','S07-08','S07-09','S07-10','S07-11','Final S09 UAT verdict','Tester','Device model','iOS version','App build','Sign-off']; missing=[x for x in required if x not in txt]; assert not missing, missing" && rtk proxy python -c "from pathlib import Path; txt=Path('.gsd/milestones/M007/M007-VALIDATION.md').read_text(encoding='utf-8'); required=['S09-RUNTIME-PROOF.json','S09-UAT-RESULT.md']; missing=[x for x in required if x not in txt]; assert not missing, missing"`
  - Done when: Physical-device UAT result is complete and signed for all 11 scenarios, and milestone validation explicitly links S09 runtime + UAT closure evidence.

## Files Likely Touched

- `scripts/verify-m007-s09.sh`
- `scripts/verify-m007-s09-runtime.py`
- `tests/test_verify_m007_s09_runtime_contract.py`
- `tests/test_verify_m007_s09_evidence_contract.py`
- `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json`
- `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md`
- `.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md`
- `.gsd/milestones/M007/M007-VALIDATION.md`
