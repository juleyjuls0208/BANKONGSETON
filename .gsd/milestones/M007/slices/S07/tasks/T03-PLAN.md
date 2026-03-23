---
estimated_steps: 4
estimated_files: 3
skills_used:
  - qodo-get-rules
  - feature-dev
  - test
  - requesting-code-review
  - best-practices
---

# T03: Publish device-demo readiness evidence and close S07 acceptance gate

**Slice:** S07 — Final Integration + Device Demo Readiness Gate
**Milestone:** M007

## Description

Finalize the manual iOS 17+ acceptance protocol and readiness evidence so milestone closure can be judged with explicit pass/fail criteria tied to both automated and human proof.

## Steps

1. Expand `S07-UAT.md` into a complete on-device checklist for login → home → QR pay → receipt/history → budget → settings/lost-card → logout/login, including default-motion and Reduce Motion paths.
2. Add `S07-DEMO-READINESS.md` mapping R063 (plus supporting requirements) to exact automated commands, manual scenarios, and expected evidence artifacts.
3. Update the S07 verifier artifact phase so it checks for required readiness docs and fails with actionable guidance when docs are missing or empty.
4. Run the closure verification set and record outcome/status notes (including environment constraints, if any) in readiness documentation.

## Must-Haves

- [ ] UAT doc contains explicit PASS/FAIL checkpoints for each in-scope demo flow and retry/failure-path behavior.
- [ ] Readiness doc includes requirement-to-proof traceability (at minimum R063, R056, R058, R059, R060, R061, R062).
- [ ] Verifier artifact phase enforces documentation presence and reports missing-evidence diagnostics.

## Verification

- `rtk proxy sh scripts/verify-m007-s07.sh`
- `rtk proxy python -c "from pathlib import Path; u=Path('.gsd/milestones/M007/slices/S07/S07-UAT.md'); r=Path('.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md'); assert u.exists() and r.exists(); ut=u.read_text(encoding='utf-8'); rt=r.read_text(encoding='utf-8'); assert 'PASS' in ut and 'FAIL' in ut; required=['R063','R056','R058','R059','R060','R061','R062']; missing=[x for x in required if x not in rt]; assert not missing, missing"`

## Observability Impact

- Signals added/changed: S07 artifact-check diagnostics explicitly report missing/empty readiness evidence.
- How a future agent inspects this: open `S07-UAT.md` + `S07-DEMO-READINESS.md`, then run `scripts/verify-m007-s07.sh` for gate status.
- Failure state exposed: missing manual proof, missing requirement mapping, or incomplete closure notes fail the verifier with direct guidance.

## Inputs

- `.gsd/milestones/M007/slices/S07/S07-UAT.md` — scaffold from T01 to be expanded into full device checklist.
- `scripts/verify-m007-s07.sh` — S07 verifier requiring final artifact-check wiring.
- `tests/test_verify_m007_s07_integration_behavior_contract.py` — automated closure proof anchors.
- `tests/test_verify_m007_s07_scope_guard_contract.py` — scope/regression proof anchors.
- `.gsd/milestones/M007/slices/S06/S06-UAT.md` — prior slice UAT structure baseline for formatting and rigor.

## Expected Output

- `.gsd/milestones/M007/slices/S07/S07-UAT.md` — finalized manual iOS 17+ pass/fail checklist for full demo journey.
- `.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md` — requirement-to-proof traceability + closure outcome notes.
- `scripts/verify-m007-s07.sh` — artifact-check phase updated to enforce S07 readiness evidence presence.
