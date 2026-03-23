---
id: T01
parent: S09
milestone: M007
provides:
  - Phased S09 runtime verifier with guidance-first failure output and runtime-proof artifact emission
  - Runtime-proof serializer that upserts phase evidence into JSON+Markdown
  - Contract tests for verifier markers, runtime-proof schema, and UAT marker completeness rules
key_files:
  - scripts/verify-m007-s09.sh
  - scripts/verify-m007-s09-runtime.py
  - tests/test_verify_m007_s09_runtime_contract.py
  - tests/test_verify_m007_s09_evidence_contract.py
  - .gsd/milestones/M007/slices/S09/S09-PLAN.md
  - .gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json
key_decisions:
  - D088 — S09 runtime closure evidence format uses phased shell telemetry + JSON/MD proof artifacts
patterns_established:
  - Phase runner pattern (`run_phase` + `fail_with_guidance`) with per-phase proof upserts
  - Runtime-proof contract validator that enforces required phase IDs and shape keys
observability_surfaces:
  - scripts/verify-m007-s09.sh phase logs (`phase=...`, `guidance=...`)
  - scripts/verify-m007-s09-runtime.py proof updates
  - .gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json
  - .gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md
duration: 1h 05m
verification_result: passed
completed_at: 2026-03-23T18:28:00+08:00
blocker_discovered: false
---

# T01: Author S09 phased runtime verifier and evidence contract tests

**Added an S09 phased runtime gate (`verify-m007-s09.sh`) plus runtime-proof serializer and contract tests that enforce required phase/guidance/evidence structure.**

## What Happened

Implemented `scripts/verify-m007-s09.sh` with explicit phase sequencing for `s07_baseline`, `apple_tooling`, `simulator_build`, `xctrace_templates`, and `artifact_completeness`, including `fail_with_guidance` output and per-phase runtime-proof recording.

Implemented `scripts/verify-m007-s09-runtime.py` to upsert phase entries and emit both JSON and Markdown proof artifacts with host metadata, timestamps, command summaries, guidance, phase counts, and overall verdict logic.

Added `tests/test_verify_m007_s09_runtime_contract.py` to assert verifier marker coverage and runtime serializer behavior, and `tests/test_verify_m007_s09_evidence_contract.py` to enforce runtime-proof shape/phase requirements plus S09 UAT marker completeness rules.

Applied the pre-flight observability gap fix by updating `.gsd/milestones/M007/slices/S09/S09-PLAN.md` verification list with a structured diagnostics marker check for `scripts/verify-m007-s09.sh`.

## Verification

Executed T01 verification commands and then ran the full slice verification gate. T01 contract checks pass. Slice-level runtime/UAT closure checks are partially failing as expected at this stage because Apple tooling is unavailable in this host and T03 evidence artifacts are not authored yet.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s09_runtime_contract.py tests/test_verify_m007_s09_evidence_contract.py` | 0 | ✅ pass | ~0.44s |
| 2 | `rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s09.sh').read_text(...); required=[...]; ..."` | 0 | ✅ pass | ~0.10s |
| 3 | `rtk proxy sh scripts/verify-m007-s09.sh` | 1 | ❌ fail | ~5s |
| 4 | `rtk proxy python -c "import json; ... assert expected.issubset(phase_ids) ..."` | 1 | ❌ fail | ~0.10s |
| 5 | `rtk proxy python -c "from pathlib import Path; txt=Path('.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md').read_text(...); ..."` | 1 | ❌ fail | ~0.10s |
| 6 | `rtk proxy python -c "from pathlib import Path; txt=Path('.gsd/milestones/M007/M007-VALIDATION.md').read_text(...); ..."` | 1 | ❌ fail | ~0.10s |

## Diagnostics

- Run `rtk proxy sh scripts/verify-m007-s09.sh` to execute phased checks with `phase=` and `guidance=` telemetry.
- Inspect `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json` for machine-readable phase records (`id`, `status`, `command`, `exit_code`, `started_at`, `finished_at`, `guidance`).
- Inspect `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md` for reviewer-facing evidence.
- Current host-level failure signature for unresolved phase is explicit: `apple_tooling` fails with `program not found` for `xcodebuild`/`xcrun` and includes next-step guidance.

## Deviations

- Added one extra verification row in `.gsd/milestones/M007/slices/S09/S09-PLAN.md` (structured marker check for `guidance=`/phase tokens) to satisfy the pre-flight observability-gap fix requirement.

## Known Issues

- `apple_tooling` phase fails in this Windows executor because `xcodebuild`/`xcrun` are unavailable.
- `S09-UAT-RESULT.md` is not authored yet (planned for T03), so UAT marker check fails.
- `M007-VALIDATION.md` does not yet reference `S09-RUNTIME-PROOF.json` and `S09-UAT-RESULT.md` (planned for T03).
- Runtime proof currently contains a historical `preflight` fail row from an early run; required-phase verdict logic now keys on canonical S09 phases.

## Files Created/Modified

- `scripts/verify-m007-s09.sh` — new phased runtime verifier with guidance-rich failure handling and proof emission hooks.
- `scripts/verify-m007-s09-runtime.py` — new runtime-proof JSON/Markdown serializer with upsert + contract validation helpers.
- `tests/test_verify_m007_s09_runtime_contract.py` — new verifier/runtime-writer contract tests.
- `tests/test_verify_m007_s09_evidence_contract.py` — new runtime-proof/UAT marker contract tests.
- `.gsd/milestones/M007/slices/S09/S09-PLAN.md` — added diagnostics-focused verification command and marked T01 complete.
- `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json` — generated runtime proof artifact from verifier execution.
- `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md` — generated human-readable runtime proof summary.
- `.gsd/KNOWLEDGE.md` — added `.xcodeproj` directory preflight gotcha.
- `.gsd/DECISIONS.md` — appended D088 via decision save tool.
