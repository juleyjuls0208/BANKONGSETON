---
estimated_steps: 4
estimated_files: 4
skills_used:
  - qodo-get-rules
  - test
  - swiftui
  - build-iphone-apps
  - debug-like-expert
---

# T01: Author S09 phased runtime verifier and evidence contract tests

**Slice:** S09 — macOS Runtime + Physical Device Acceptance Closure
**Milestone:** M007

## Description

Create the deterministic S09 verification backbone before any Apple-host/manual execution. This task introduces the phased S09 verifier, runtime-proof serializer, and contract tests that ensure closure artifacts are structurally complete and diagnosable.

## Steps

1. Reuse proven verifier patterns from S07 and M006 to scaffold `scripts/verify-m007-s09.sh` with explicit phases, `fail_with_guidance`, and `set -euo pipefail` semantics.
2. Add `scripts/verify-m007-s09-runtime.py` to emit `.json` + `.md` runtime proof artifacts containing host metadata, phase statuses, command summaries, timestamps, and overall verdict.
3. Add `tests/test_verify_m007_s09_runtime_contract.py` to assert required phase markers (`s07_baseline`, `apple_tooling`, `simulator_build`, `xctrace_templates`, `artifact_completeness`) and structured guidance output semantics.
4. Add `tests/test_verify_m007_s09_evidence_contract.py` to validate runtime-proof schema keys and UAT artifact required markers, so missing evidence fails fast during CI-style checks.

## Must-Haves

- [ ] S09 verifier emits phase-tagged diagnostics and actionable `guidance=` output.
- [ ] Runtime-proof writer produces both JSON and Markdown artifacts with consistent keys and timestamps.
- [ ] Contract tests fail if required S09 phases or evidence markers are removed.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s09_runtime_contract.py tests/test_verify_m007_s09_evidence_contract.py`
- `rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s09.sh').read_text(encoding='utf-8'); required=['set -euo pipefail','fail_with_guidance','phase=s07_baseline','phase=apple_tooling','phase=simulator_build','phase=xctrace_templates','phase=artifact_completeness','guidance=']; missing=[x for x in required if x not in txt]; assert not missing, missing"`

## Observability Impact

- Signals added/changed: phase-level status telemetry and machine-readable runtime proof fields (`phase id`, `status`, `command`, `timestamp`, `guidance`).
- How a future agent inspects this: run `rtk proxy sh scripts/verify-m007-s09.sh` and read `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json`.
- Failure state exposed: missing phase wiring, absent proof fields, and incomplete UAT markers become explicit test/script failures.

## Inputs

- `scripts/verify-m007-s07.sh` — phase/guidance baseline for closure verifiers.
- `tests/test_verify_m007_s07_integration_behavior_contract.py` — marker-based contract-test style to mirror.
- `scripts/verify-m006-s04-live.py` — machine-readable proof artifact pattern.
- `scripts/verify-m006-s05-bundle.py` — bundle/verdict aggregation reference.
- `.gsd/milestones/M007/slices/S09/S09-RESEARCH.md` — S09 phase expectations and required evidence surfaces.

## Expected Output

- `scripts/verify-m007-s09.sh` — phased S09 runtime closure verifier with guidance diagnostics.
- `scripts/verify-m007-s09-runtime.py` — runtime proof serializer for JSON/Markdown artifacts.
- `tests/test_verify_m007_s09_runtime_contract.py` — S09 verifier phase/diagnostic contract assertions.
- `tests/test_verify_m007_s09_evidence_contract.py` — S09 runtime/UAT evidence completeness assertions.
